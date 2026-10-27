"""Vectorized-signal, trade-level-iterated backtest engine.

Signals come out of the strategy layer as a vector aligned to the price index;
the engine only iterates row-by-row to do what genuinely requires path
dependence — stop-loss/take-profit checks against intrabar high/low, and trade
entry/exit bookkeeping. Everything else (indicator computation, signal
generation) is already vectorized upstream. This is the standard tradeoff for
daily-bar research backtesting — see docs/ARCHITECTURE.md §2.
"""

from dataclasses import dataclass
from datetime import date as date_type

import numpy as np
import pandas as pd

from app.models.trade import ExitReason, TradeSide


@dataclass
class BacktestConfig:
    initial_capital: float = 100_000.0
    commission_pct: float = 0.001
    slippage_pct: float = 0.0005
    position_size_pct: float = 1.0
    stop_loss_pct: float | None = None
    take_profit_pct: float | None = None
    # Override `commission_pct` for the buy leg (`entry_cost_pct`) and the sell leg
    # (`exit_cost_pct`) when set. Named for a long trade; a short opens with the sell leg
    # and closes with the buy leg. Used by the Indian equity charge model (STT/stamp duty
    # differ between buy and sell); None for the flat-commission model.
    entry_cost_pct: float | None = None
    exit_cost_pct: float | None = None

    def buy_leg_cost_pct(self) -> float:
        return self.entry_cost_pct if self.entry_cost_pct is not None else self.commission_pct

    def sell_leg_cost_pct(self) -> float:
        return self.exit_cost_pct if self.exit_cost_pct is not None else self.commission_pct


@dataclass
class SimulatedTrade:
    side: TradeSide
    entry_date: date_type
    entry_price: float
    exit_date: date_type
    exit_price: float
    quantity: float
    pnl: float
    pnl_pct: float
    exit_reason: ExitReason


@dataclass
class _OpenPosition:
    side: TradeSide
    entry_date: date_type
    entry_price: float
    quantity: float
    notional: float  # capital committed at entry, net of entry commission


@dataclass
class SingleAssetBacktestResult:
    equity_curve: pd.Series
    trades: list[SimulatedTrade]


def _as_date(value) -> date_type:
    return value.date() if hasattr(value, "date") else value


def run_single_asset_backtest(df: pd.DataFrame, signal: pd.Series, config: BacktestConfig) -> SingleAssetBacktestResult:
    """Simulate one asset. `signal` must be aligned to `df.index` with values in
    {-1, 0, 1}; it is lagged by one bar internally so today's execution only ever
    uses information available at yesterday's close (no lookahead bias). Stop-loss
    and take-profit are checked intrabar against today's high/low, ahead of any
    signal-based exit. A bar that opens beyond the stop or target fills at that open (the
    price actually available after a gap), not at the untouched trigger level.

    Short positions are modeled symmetrically to longs (PnL = quantity * (entry -
    exit)) with the same capital-reservation accounting — a standard research-tool
    simplification that does not model real short-sale margin/borrow mechanics.
    """
    desired_position = signal.shift(1).fillna(0.0)

    dates = df.index
    close = df["close"].to_numpy()
    open_ = df["open"].to_numpy() if "open" in df else close
    high = df["high"].to_numpy()
    low = df["low"].to_numpy()
    desired = desired_position.to_numpy()

    cash = config.initial_capital
    open_pos: _OpenPosition | None = None
    trades: list[SimulatedTrade] = []
    equity_values = np.empty(len(df))

    n = len(df)
    for t in range(n):
        is_last_day = t == n - 1
        current_date = _as_date(dates[t])

        if open_pos is not None:
            exit_price: float | None = None
            exit_reason: ExitReason | None = None

            # A gap through the level fills at the open: worse than the stop, better than the target.
            if open_pos.side == TradeSide.LONG:
                stop = open_pos.entry_price * (1 - config.stop_loss_pct) if config.stop_loss_pct else None
                target = open_pos.entry_price * (1 + config.take_profit_pct) if config.take_profit_pct else None
                if stop is not None and low[t] <= stop:
                    exit_price = min(open_[t], stop)
                    exit_reason = ExitReason.STOP_LOSS
                elif target is not None and high[t] >= target:
                    exit_price = max(open_[t], target)
                    exit_reason = ExitReason.TAKE_PROFIT
            else:
                stop = open_pos.entry_price * (1 + config.stop_loss_pct) if config.stop_loss_pct else None
                target = open_pos.entry_price * (1 - config.take_profit_pct) if config.take_profit_pct else None
                if stop is not None and high[t] >= stop:
                    exit_price = max(open_[t], stop)
                    exit_reason = ExitReason.STOP_LOSS
                elif target is not None and low[t] <= target:
                    exit_price = min(open_[t], target)
                    exit_reason = ExitReason.TAKE_PROFIT

            target_side = TradeSide.LONG if desired[t] > 0 else TradeSide.SHORT if desired[t] < 0 else None
            if exit_reason is None and is_last_day:
                exit_price = close[t]
                exit_reason = ExitReason.END_OF_BACKTEST
            elif exit_reason is None and target_side != open_pos.side:
                exit_price = close[t]
                exit_reason = ExitReason.SIGNAL

            if exit_reason is not None:
                if open_pos.side == TradeSide.LONG:
                    exit_price_adj = exit_price * (1 - config.slippage_pct)
                    gross_pnl = open_pos.quantity * (exit_price_adj - open_pos.entry_price)
                else:
                    exit_price_adj = exit_price * (1 + config.slippage_pct)
                    gross_pnl = open_pos.quantity * (open_pos.entry_price - exit_price_adj)

                # Closing a long sells; closing a short buys back.
                exit_pct = config.sell_leg_cost_pct() if open_pos.side == TradeSide.LONG else config.buy_leg_cost_pct()
                commission_exit = open_pos.quantity * exit_price_adj * exit_pct
                net_pnl = gross_pnl - commission_exit
                cash += open_pos.notional + net_pnl

                trades.append(
                    SimulatedTrade(
                        side=open_pos.side,
                        entry_date=open_pos.entry_date,
                        entry_price=open_pos.entry_price,
                        exit_date=current_date,
                        exit_price=exit_price_adj,
                        quantity=open_pos.quantity,
                        pnl=net_pnl,
                        pnl_pct=(net_pnl / open_pos.notional) if open_pos.notional else 0.0,
                        exit_reason=exit_reason,
                    )
                )
                open_pos = None

        if open_pos is None and not is_last_day and desired[t] != 0:
            side = TradeSide.LONG if desired[t] > 0 else TradeSide.SHORT
            raw_entry_price = close[t]
            entry_price = (
                raw_entry_price * (1 + config.slippage_pct)
                if side == TradeSide.LONG
                else raw_entry_price * (1 - config.slippage_pct)
            )
            allocation = cash * config.position_size_pct
            # Opening a long buys; opening a short sells.
            entry_pct = config.buy_leg_cost_pct() if side == TradeSide.LONG else config.sell_leg_cost_pct()
            commission_entry = allocation * entry_pct
            notional = allocation - commission_entry
            quantity = notional / entry_price if entry_price > 0 else 0.0
            cash -= allocation
            open_pos = _OpenPosition(
                side=side, entry_date=current_date, entry_price=entry_price, quantity=quantity, notional=notional
            )

        if open_pos is not None:
            if open_pos.side == TradeSide.LONG:
                unrealized = open_pos.quantity * (close[t] - open_pos.entry_price)
            else:
                unrealized = open_pos.quantity * (open_pos.entry_price - close[t])
            equity_values[t] = cash + open_pos.notional + unrealized
        else:
            equity_values[t] = cash

    equity_curve = pd.Series(equity_values, index=df.index, name="equity")
    return SingleAssetBacktestResult(equity_curve=equity_curve, trades=trades)


@dataclass
class MultiAssetBacktestResult:
    equity_curve: pd.Series
    trades_by_symbol: dict[str, list[SimulatedTrade]]


def run_multi_asset_backtest(
    data_by_symbol: dict[str, pd.DataFrame],
    signal_by_symbol: dict[str, pd.Series],
    config: BacktestConfig,
) -> MultiAssetBacktestResult:
    """Equal-weight portfolio across symbols: capital is split evenly, each symbol
    runs the (identical) strategy independently, and the per-symbol equity curves
    are summed. This is a deliberately simple multi-asset model — true portfolio
    rebalancing/allocation is the job of the separate portfolio optimizer service."""
    symbols = list(data_by_symbol.keys())
    per_symbol_capital = config.initial_capital / len(symbols)
    sub_config = BacktestConfig(
        initial_capital=per_symbol_capital,
        commission_pct=config.commission_pct,
        slippage_pct=config.slippage_pct,
        position_size_pct=config.position_size_pct,
        stop_loss_pct=config.stop_loss_pct,
        take_profit_pct=config.take_profit_pct,
        entry_cost_pct=config.entry_cost_pct,
        exit_cost_pct=config.exit_cost_pct,
    )

    results = {
        symbol: run_single_asset_backtest(data_by_symbol[symbol], signal_by_symbol[symbol], sub_config)
        for symbol in symbols
    }

    combined = pd.concat([r.equity_curve.rename(s) for s, r in results.items()], axis=1)
    # Before a symbol's first bar its capital sits uninvested, so it counts at its starting
    # value; back-filling would borrow a later, already-traded equity value.
    combined = combined.ffill().fillna(per_symbol_capital)
    portfolio_equity = combined.sum(axis=1).rename("equity")

    return MultiAssetBacktestResult(
        equity_curve=portfolio_equity, trades_by_symbol={s: r.trades for s, r in results.items()}
    )


def _rebalance_period_boundaries(index: pd.DatetimeIndex, frequency: str) -> list[pd.Timestamp]:
    freq = {"monthly": "MS", "quarterly": "QS"}[frequency]
    boundaries = list(pd.date_range(index[0], index[-1], freq=freq))
    if not boundaries or boundaries[0] > index[0]:
        boundaries.insert(0, index[0])
    boundaries.append(index[-1] + pd.Timedelta(days=1))
    return boundaries


def run_multi_asset_backtest_with_rebalancing(
    data_by_symbol: dict[str, pd.DataFrame],
    signal_by_symbol: dict[str, pd.Series],
    config: BacktestConfig,
    rebalance_frequency: str = "none",
) -> MultiAssetBacktestResult:
    """Additive alternative to `run_multi_asset_backtest` for when periodic
    rebalancing-to-equal-weight is wanted: at each rebalance boundary (month/quarter
    start), every symbol's position is closed (via that segment's own end-of-data
    force-close) and the resulting total equity is redistributed evenly across
    symbols for the next segment — so a rebalance's transaction costs are actually
    modeled, not a costless capital reshuffle. `rebalance_frequency="none"`
    (the default) delegates straight to `run_multi_asset_backtest`, so existing
    callers are completely unaffected by this function's existence.

    One documented simplification: each segment restarts `signal.shift(1)` fresh,
    so the first bar of every new rebalance period is flat even if the prior
    period ended in a position it would have carried through — a real desk would
    carry it; this keeps each segment self-contained and easy to reason about.
    """
    if rebalance_frequency == "none":
        return run_multi_asset_backtest(data_by_symbol, signal_by_symbol, config)
    if rebalance_frequency not in ("monthly", "quarterly"):
        raise ValueError(f"Unknown rebalance_frequency '{rebalance_frequency}'")

    symbols = list(data_by_symbol.keys())
    all_dates = sorted(set().union(*(set(df.index) for df in data_by_symbol.values())))
    master_index = pd.DatetimeIndex(all_dates)
    boundaries = _rebalance_period_boundaries(master_index, rebalance_frequency)

    trades_by_symbol: dict[str, list[SimulatedTrade]] = {s: [] for s in symbols}
    equity_segments: list[pd.Series] = []
    current_capital = config.initial_capital

    for i in range(len(boundaries) - 1):
        seg_start, seg_end = boundaries[i], boundaries[i + 1]
        per_symbol_capital = current_capital / len(symbols)
        sub_config = BacktestConfig(
            initial_capital=per_symbol_capital,
            commission_pct=config.commission_pct,
            slippage_pct=config.slippage_pct,
            position_size_pct=config.position_size_pct,
            stop_loss_pct=config.stop_loss_pct,
            take_profit_pct=config.take_profit_pct,
            entry_cost_pct=config.entry_cost_pct,
            exit_cost_pct=config.exit_cost_pct,
        )

        segment_equity_parts = []
        segment_total_end = 0.0
        for symbol in symbols:
            df = data_by_symbol[symbol]
            seg_df = df.loc[(df.index >= seg_start) & (df.index < seg_end)]
            if seg_df.empty:
                segment_total_end += per_symbol_capital
                continue
            seg_signal = signal_by_symbol[symbol].loc[seg_df.index]
            result = run_single_asset_backtest(seg_df, seg_signal, sub_config)
            trades_by_symbol[symbol].extend(result.trades)
            segment_equity_parts.append(result.equity_curve)
            segment_total_end += float(result.equity_curve.iloc[-1]) if len(result.equity_curve) else per_symbol_capital

        if segment_equity_parts:
            # Leading gaps hold a symbol's starting capital (no back-fill from later values), and
            # symbols with no bars this period still own their uninvested share of capital.
            idle_capital = per_symbol_capital * (len(symbols) - len(segment_equity_parts))
            combined = pd.concat(segment_equity_parts, axis=1).ffill().fillna(per_symbol_capital).sum(axis=1)
            equity_segments.append(combined + idle_capital)
        current_capital = segment_total_end

    equity_curve = pd.concat(equity_segments).sort_index()
    equity_curve = equity_curve[~equity_curve.index.duplicated(keep="last")]
    equity_curve.name = "equity"
    return MultiAssetBacktestResult(equity_curve=equity_curve, trades_by_symbol=trades_by_symbol)
