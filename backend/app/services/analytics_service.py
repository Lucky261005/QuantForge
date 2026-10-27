"""Cross-backtest analytics: multi-strategy comparison and portfolio optimization.
Both reuse services/repositories rather than re-implementing data access."""

import pandas as pd
from sqlalchemy.orm import Session

from app.backtesting.optimizer import OptimizationMethod, optimize_portfolio
from app.models.backtest import BacktestStatus
from app.models.user import User
from app.repositories.backtest import BacktestRepository
from app.schemas.backtest import CompareEntry, CompareResponse
from app.schemas.optimizer import OptimizeResponse
from app.services.market_data_service import MarketDataService
from app.utils.exceptions import NotFoundError, PermissionDeniedError, ValidationFailedError


class AnalyticsService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.backtests = BacktestRepository(db)
        self.market_data = MarketDataService(db)

    def compare(self, backtest_ids: list[int], user: User) -> CompareResponse:
        entries: list[CompareEntry] = []
        returns_by_backtest: dict[str, pd.Series] = {}

        for backtest_id in backtest_ids:
            backtest = self.backtests.get_with_strategy(backtest_id)
            if not backtest:
                raise NotFoundError(f"Backtest {backtest_id} not found")
            if backtest.owner_id != user.id:
                raise PermissionDeniedError(f"You do not have access to backtest {backtest_id}")
            if backtest.status != BacktestStatus.COMPLETED or backtest.result is None:
                raise ValidationFailedError(f"Backtest {backtest_id} has not completed yet")

            result = backtest.result
            label = backtest.name or f"Backtest {backtest.id}"
            entries.append(
                CompareEntry(
                    backtest_id=backtest.id,
                    name=backtest.name,
                    strategy_type=backtest.strategy.strategy_type,
                    metrics={
                        "total_return_pct": result.total_return_pct,
                        "cagr_pct": result.cagr_pct,
                        "volatility_pct": result.volatility_pct,
                        "sharpe_ratio": result.sharpe_ratio,
                        "sortino_ratio": result.sortino_ratio,
                        "calmar_ratio": result.calmar_ratio,
                        "omega_ratio": result.omega_ratio,
                        "max_drawdown_pct": result.max_drawdown_pct,
                        "ulcer_index": result.ulcer_index,
                        "var_95_pct": result.var_95_pct,
                        "cvar_95_pct": result.cvar_95_pct,
                        "max_consecutive_losses": result.max_consecutive_losses,
                        "recovery_days": result.recovery_days,
                        "num_trades": result.num_trades,
                        "win_rate_pct": result.win_rate_pct,
                        "profit_factor": result.profit_factor,
                        "expectancy": result.expectancy,
                        "alpha": result.alpha,
                        "beta": result.beta,
                        "sharpe_ratio_ci_low": result.sharpe_ratio_ci_low,
                        "sharpe_ratio_ci_high": result.sharpe_ratio_ci_high,
                        "cagr_pct_ci_low": result.cagr_pct_ci_low,
                        "cagr_pct_ci_high": result.cagr_pct_ci_high,
                    },
                    equity_curve=result.equity_curve,
                )
            )
            daily = pd.Series(
                {row["date"]: row["return_pct"] for row in result.daily_returns},
                name=label,
            )
            returns_by_backtest[label] = daily

        combined = pd.DataFrame(returns_by_backtest)
        corr = combined.corr().fillna(0.0)
        correlation_matrix = {row: {col: float(corr.loc[row, col]) for col in corr.columns} for row in corr.index}

        return CompareResponse(entries=entries, correlation_matrix=correlation_matrix)

    def optimize(
        self, symbols: list[str], start_date, end_date, method: OptimizationMethod, risk_free_rate: float
    ) -> OptimizeResponse:
        returns_by_symbol = {}
        for symbol in symbols:
            bars = self.market_data.get_ohlcv(symbol, start_date, end_date)
            if len(bars) < 10:
                raise ValidationFailedError(f"Not enough market data for '{symbol}' to optimize — download it first.")
            closes = pd.Series({row["date"]: row["close"] for row in bars})
            returns_by_symbol[symbol] = closes.pct_change().dropna()

        returns_df = pd.DataFrame(returns_by_symbol).dropna()
        result = optimize_portfolio(returns_df, method, risk_free_rate)
        return OptimizeResponse(
            method=result.method,
            weights=result.weights,
            expected_return_pct=result.expected_return_pct,
            expected_volatility_pct=result.expected_volatility_pct,
            sharpe_ratio=result.sharpe_ratio,
        )
