"""Orchestrates a backtest run: validates the request, executes the vectorized
engine against stored market data, and persists metrics/trades. `execute()` is
called both by the Celery task (async, production path) and directly/synchronously
when Celery's broker is unreachable (dev fallback) — see app.tasks.backtest_tasks.
"""

import hashlib
import json
import time

import pandas as pd
from sqlalchemy.orm import Session

from app.backtesting.charges import ChargeModel, IndianChargesConfig, compute_entry_exit_cost_pct
from app.backtesting.engine import (
    BacktestConfig,
    run_multi_asset_backtest_with_rebalancing,
    run_single_asset_backtest,
)
from app.backtesting.metrics import compute_performance_metrics
from app.core.logging import get_logger
from app.db.base_class import utcnow
from app.models.backtest import Backtest, BacktestResult, BacktestStatus
from app.models.trade import Trade
from app.models.user import User
from app.repositories.asset import AssetRepository
from app.repositories.backtest import BacktestRepository, TradeRepository
from app.repositories.strategy import StrategyRepository
from app.schemas.backtest import BacktestCreate
from app.services.market_data_service import MarketDataService
from app.strategies import strategy_registry
from app.utils.exceptions import NotFoundError, PermissionDeniedError, ValidationFailedError

logger = get_logger(__name__)


def _strategy_version_hash(strategy_type: str, parameters: dict) -> str:
    payload = json.dumps({"strategy_type": strategy_type, "parameters": parameters}, sort_keys=True)
    return hashlib.sha256(payload.encode()).hexdigest()[:16]


def _bars_to_df(bars: list[dict]) -> pd.DataFrame:
    df = pd.DataFrame(bars)
    df["date"] = pd.to_datetime(df["date"])
    return df.set_index("date").sort_index()


class BacktestService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.backtests = BacktestRepository(db)
        self.trades = TradeRepository(db)
        self.strategies = StrategyRepository(db)
        self.assets = AssetRepository(db)
        self.market_data = MarketDataService(db)

    def create(self, owner_id: int, payload: BacktestCreate) -> Backtest:
        strategy = self.strategies.get(payload.strategy_id)
        if not strategy:
            raise NotFoundError("Strategy not found")
        if strategy.owner_id != owner_id and not strategy.is_public:
            raise PermissionDeniedError("You do not have access to this strategy")

        try:
            strategy_registry.get(strategy.strategy_type)
        except KeyError as exc:
            raise ValidationFailedError(str(exc)) from exc

        backtest = Backtest(
            owner_id=owner_id,
            strategy_id=strategy.id,
            name=payload.name,
            symbols=payload.symbols,
            start_date=payload.start_date,
            end_date=payload.end_date,
            initial_capital=payload.initial_capital,
            commission_pct=payload.commission_pct,
            slippage_pct=payload.slippage_pct,
            position_size_pct=payload.position_size_pct,
            stop_loss_pct=payload.stop_loss_pct,
            take_profit_pct=payload.take_profit_pct,
            benchmark_symbol=payload.benchmark_symbol.upper(),
            charge_model=payload.charge_model,
            brokerage_pct=payload.brokerage_pct,
            risk_free_rate_annual=payload.risk_free_rate_annual,
            rebalance_frequency=payload.rebalance_frequency,
            status=BacktestStatus.PENDING,
            parameters_snapshot=strategy.parameters,
            strategy_version_hash=_strategy_version_hash(strategy.strategy_type, strategy.parameters),
        )
        backtest = self.backtests.create(backtest)
        self.backtests.commit()
        return backtest

    def get_owned(self, backtest_id: int, user: User) -> Backtest:
        backtest = self.backtests.get(backtest_id)
        if not backtest:
            raise NotFoundError("Backtest not found")
        if backtest.owner_id != user.id:
            raise PermissionDeniedError("You do not have access to this backtest")
        return backtest

    def list_for_owner(self, owner_id: int, offset: int, limit: int) -> tuple[list[Backtest], int]:
        return self.backtests.list_for_owner(owner_id, offset, limit), self.backtests.count_for_owner(owner_id)

    def delete(self, backtest_id: int, user: User) -> None:
        backtest = self.get_owned(backtest_id, user)
        self.backtests.delete(backtest)
        self.backtests.commit()

    # --- Execution (runs in the Celery worker process, or synchronously as a fallback) ---

    def _load_data_and_signals(
        self, backtest: Backtest, start_date=None, end_date=None
    ) -> tuple[dict[str, pd.DataFrame], dict[str, pd.Series]]:
        """Shared by `execute()` and the read-only analyses below (cost sensitivity,
        walk-forward validation) — loads OHLCV for every symbol and regenerates the
        strategy's signal from `backtest.parameters_snapshot`, optionally over a
        narrower date range than the backtest's own (used by walk-forward windows)."""
        strategy_row = self.strategies.get(backtest.strategy_id)
        strategy_impl = strategy_registry.get(strategy_row.strategy_type)
        params = backtest.parameters_snapshot
        range_start = start_date or backtest.start_date
        range_end = end_date or backtest.end_date

        data_by_symbol: dict[str, pd.DataFrame] = {}
        signal_by_symbol: dict[str, pd.Series] = {}
        for symbol in backtest.symbols:
            bars = self.market_data.get_ohlcv(symbol, range_start, range_end)
            if len(bars) < 5:
                raise ValidationFailedError(
                    f"Not enough market data for '{symbol}' between {range_start} and "
                    f"{range_end}. Download it first via POST /assets/download."
                )
            df = _bars_to_df(bars)
            data_by_symbol[symbol] = df
            signal_by_symbol[symbol] = strategy_impl.compute(df, **params)
        return data_by_symbol, signal_by_symbol

    def _config_for(self, backtest: Backtest, cost_multiplier: float = 1.0) -> BacktestConfig:
        entry_cost_pct = exit_cost_pct = None
        if backtest.charge_model != ChargeModel.FLAT:
            charges = IndianChargesConfig(brokerage_pct=backtest.brokerage_pct * cost_multiplier)
            entry_cost_pct, exit_cost_pct = compute_entry_exit_cost_pct(
                charges, delivery=backtest.charge_model == ChargeModel.INDIAN_EQUITY_DELIVERY
            )
        return BacktestConfig(
            initial_capital=backtest.initial_capital,
            commission_pct=backtest.commission_pct * cost_multiplier,
            slippage_pct=backtest.slippage_pct * cost_multiplier,
            position_size_pct=backtest.position_size_pct,
            stop_loss_pct=backtest.stop_loss_pct,
            take_profit_pct=backtest.take_profit_pct,
            entry_cost_pct=entry_cost_pct,
            exit_cost_pct=exit_cost_pct,
        )

    def _run_engine(
        self, backtest: Backtest, data_by_symbol: dict, signal_by_symbol: dict, config: BacktestConfig
    ) -> tuple[pd.Series, list]:
        if len(backtest.symbols) == 1:
            symbol = backtest.symbols[0]
            single = run_single_asset_backtest(data_by_symbol[symbol], signal_by_symbol[symbol], config)
            return single.equity_curve, single.trades
        multi = run_multi_asset_backtest_with_rebalancing(
            data_by_symbol, signal_by_symbol, config, rebalance_frequency=backtest.rebalance_frequency
        )
        flat_trades = [t for ts in multi.trades_by_symbol.values() for t in ts]
        return multi.equity_curve, flat_trades

    def analyze_cost_sensitivity(
        self, backtest_id: int, user: User, multipliers: list[float] | None = None
    ) -> list[dict]:
        """Re-runs a completed backtest's exact signals at several transaction-cost
        multipliers (0x, 0.5x, 1x, 1.5x, 2x commission+slippage by default) so a
        return figure can be read alongside how sensitive it is to the cost
        assumptions that produced it — a single fixed-cost backtest result invites
        exactly the "did you just pick favorable costs" question this answers."""
        backtest = self.get_owned(backtest_id, user)
        if backtest.status != BacktestStatus.COMPLETED:
            raise ValidationFailedError(f"Backtest is '{backtest.status.value}', not completed yet")

        multipliers = multipliers or [0.0, 0.5, 1.0, 1.5, 2.0]
        data_by_symbol, signal_by_symbol = self._load_data_and_signals(backtest)

        results = []
        for multiplier in multipliers:
            config = self._config_for(backtest, cost_multiplier=multiplier)
            equity_curve, trades = self._run_engine(backtest, data_by_symbol, signal_by_symbol, config)
            metrics = compute_performance_metrics(
                equity_curve, trades, risk_free_rate_annual=backtest.risk_free_rate_annual
            )
            results.append(
                {
                    "cost_multiplier": multiplier,
                    "effective_commission_pct": backtest.commission_pct * multiplier,
                    "effective_slippage_pct": backtest.slippage_pct * multiplier,
                    "total_return_pct": metrics.total_return_pct,
                    "sharpe_ratio": metrics.sharpe_ratio,
                    "max_drawdown_pct": metrics.max_drawdown_pct,
                    "num_trades": metrics.num_trades,
                }
            )
        return results

    def run_walk_forward_validation(self, backtest_id: int, user: User, n_windows: int = 4) -> list[dict]:
        """Splits the backtest's date range into `n_windows` contiguous, equal-length
        out-of-sample windows and re-runs the SAME strategy parameters (no parameter
        re-optimization) independently on each. This is walk-forward *validation* —
        checking whether performance holds up across different market regimes —
        not full walk-forward *optimization*, which would re-search parameters per
        window; that distinction matters and is documented rather than implied."""
        backtest = self.get_owned(backtest_id, user)
        if backtest.status != BacktestStatus.COMPLETED:
            raise ValidationFailedError(f"Backtest is '{backtest.status.value}', not completed yet")
        if n_windows < 2:
            raise ValidationFailedError("n_windows must be at least 2")

        boundaries = pd.date_range(backtest.start_date, backtest.end_date, periods=n_windows + 1)
        config = self._config_for(backtest)

        windows = []
        for i in range(n_windows):
            window_start = boundaries[i].date()
            window_end = boundaries[i + 1].date()
            try:
                data_by_symbol, signal_by_symbol = self._load_data_and_signals(
                    backtest, start_date=window_start, end_date=window_end
                )
            except ValidationFailedError:
                windows.append(
                    {
                        "window": i + 1,
                        "start_date": str(window_start),
                        "end_date": str(window_end),
                        "error": "insufficient data",
                    }
                )
                continue
            equity_curve, trades = self._run_engine(backtest, data_by_symbol, signal_by_symbol, config)
            metrics = compute_performance_metrics(
                equity_curve, trades, risk_free_rate_annual=backtest.risk_free_rate_annual
            )
            windows.append(
                {
                    "window": i + 1,
                    "start_date": str(window_start),
                    "end_date": str(window_end),
                    "total_return_pct": metrics.total_return_pct,
                    "sharpe_ratio": metrics.sharpe_ratio,
                    "max_drawdown_pct": metrics.max_drawdown_pct,
                    "num_trades": metrics.num_trades,
                }
            )
        return windows

    def execute(self, backtest_id: int) -> None:
        backtest = self.backtests.get(backtest_id)
        if backtest is None:
            logger.error("backtest_not_found_for_execution", backtest_id=backtest_id)
            return

        backtest.status = BacktestStatus.RUNNING
        backtest.started_at = utcnow()
        self.db.commit()
        start_time = time.time()

        try:
            data_by_symbol, signal_by_symbol = self._load_data_and_signals(backtest)

            entry_cost_pct = exit_cost_pct = None
            if backtest.charge_model != ChargeModel.FLAT:
                charges = IndianChargesConfig(brokerage_pct=backtest.brokerage_pct)
                entry_cost_pct, exit_cost_pct = compute_entry_exit_cost_pct(
                    charges, delivery=backtest.charge_model == ChargeModel.INDIAN_EQUITY_DELIVERY
                )

            config = BacktestConfig(
                initial_capital=backtest.initial_capital,
                commission_pct=backtest.commission_pct,
                slippage_pct=backtest.slippage_pct,
                position_size_pct=backtest.position_size_pct,
                stop_loss_pct=backtest.stop_loss_pct,
                take_profit_pct=backtest.take_profit_pct,
                entry_cost_pct=entry_cost_pct,
                exit_cost_pct=exit_cost_pct,
            )

            if len(backtest.symbols) == 1:
                symbol = backtest.symbols[0]
                single = run_single_asset_backtest(data_by_symbol[symbol], signal_by_symbol[symbol], config)
                equity_curve = single.equity_curve
                trades_by_symbol = {symbol: single.trades}
            else:
                multi = run_multi_asset_backtest_with_rebalancing(
                    data_by_symbol, signal_by_symbol, config, rebalance_frequency=backtest.rebalance_frequency
                )
                equity_curve = multi.equity_curve
                trades_by_symbol = multi.trades_by_symbol

            flat_trades = [(symbol, t) for symbol, ts in trades_by_symbol.items() for t in ts]

            benchmark_returns = None
            try:
                benchmark_bars = self.market_data.get_ohlcv(
                    backtest.benchmark_symbol, backtest.start_date, backtest.end_date
                )
                if len(benchmark_bars) >= 5:
                    benchmark_df = _bars_to_df(benchmark_bars)
                    benchmark_returns = benchmark_df["close"].pct_change().fillna(0.0)
            except Exception:  # noqa: BLE001 — benchmark is best-effort, never fails the backtest
                logger.warning("benchmark_unavailable", symbol=backtest.benchmark_symbol)

            metrics = compute_performance_metrics(
                equity_curve,
                [t for _, t in flat_trades],
                benchmark_returns=benchmark_returns,
                risk_free_rate_annual=backtest.risk_free_rate_annual,
            )

            result = BacktestResult(
                backtest_id=backtest.id,
                total_return_pct=metrics.total_return_pct,
                cagr_pct=metrics.cagr_pct,
                volatility_pct=metrics.volatility_pct,
                sharpe_ratio=metrics.sharpe_ratio,
                sortino_ratio=metrics.sortino_ratio,
                calmar_ratio=metrics.calmar_ratio,
                omega_ratio=metrics.omega_ratio,
                max_drawdown_pct=metrics.max_drawdown_pct,
                ulcer_index=metrics.ulcer_index,
                var_95_pct=metrics.var_95_pct,
                cvar_95_pct=metrics.cvar_95_pct,
                max_consecutive_losses=metrics.max_consecutive_losses,
                recovery_days=metrics.recovery_days,
                num_trades=metrics.num_trades,
                win_rate_pct=metrics.win_rate_pct,
                profit_factor=metrics.profit_factor,
                expectancy=metrics.expectancy,
                alpha=metrics.alpha,
                beta=metrics.beta,
                sharpe_ratio_ci_low=metrics.sharpe_ratio_ci_low,
                sharpe_ratio_ci_high=metrics.sharpe_ratio_ci_high,
                cagr_pct_ci_low=metrics.cagr_pct_ci_low,
                cagr_pct_ci_high=metrics.cagr_pct_ci_high,
                equity_curve=metrics.equity_curve,
                drawdown_curve=metrics.drawdown_curve,
                monthly_returns=metrics.monthly_returns,
                daily_returns=metrics.daily_returns,
            )
            self.db.add(result)

            for symbol, sim_trade in flat_trades:
                asset = self.assets.get_by_symbol(symbol)
                self.db.add(
                    Trade(
                        backtest_id=backtest.id,
                        asset_id=asset.id,
                        side=sim_trade.side,
                        entry_date=sim_trade.entry_date,
                        entry_price=sim_trade.entry_price,
                        exit_date=sim_trade.exit_date,
                        exit_price=sim_trade.exit_price,
                        quantity=sim_trade.quantity,
                        pnl=sim_trade.pnl,
                        pnl_pct=sim_trade.pnl_pct,
                        exit_reason=sim_trade.exit_reason,
                    )
                )

            backtest.status = BacktestStatus.COMPLETED
            backtest.completed_at = utcnow()
            backtest.runtime_seconds = time.time() - start_time
            self.db.commit()
            logger.info("backtest_completed", backtest_id=backtest.id, runtime=backtest.runtime_seconds)

        except Exception as exc:  # noqa: BLE001 — must always mark the backtest failed, not raise
            self.db.rollback()
            backtest = self.backtests.get(backtest_id)
            if backtest is not None:
                backtest.status = BacktestStatus.FAILED
                backtest.error_message = str(exc)[:2000]
                backtest.completed_at = utcnow()
                backtest.runtime_seconds = time.time() - start_time
                self.db.commit()
            logger.error("backtest_failed", backtest_id=backtest_id, error=str(exc))
