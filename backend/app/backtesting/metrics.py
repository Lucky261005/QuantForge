"""Performance and risk analytics computed once per completed backtest.

All percentage fields are expressed in percent (e.g. 12.5 means 12.5%), except
ratios (Sharpe/Sortino/Calmar/Omega) which are unitless, matching how they're
conventionally quoted in research.
"""

from dataclasses import dataclass, field
from typing import Any

import numpy as np
import pandas as pd

from app.backtesting.engine import SimulatedTrade

TRADING_DAYS_PER_YEAR = 252
_OMEGA_CAP = 999.0  # avoids emitting a non-JSON-serializable `inf` when there are no losing days


@dataclass
class PerformanceMetrics:
    total_return_pct: float
    cagr_pct: float
    volatility_pct: float
    sharpe_ratio: float
    sortino_ratio: float
    calmar_ratio: float
    omega_ratio: float
    max_drawdown_pct: float
    ulcer_index: float
    var_95_pct: float
    cvar_95_pct: float
    max_consecutive_losses: int
    recovery_days: int | None
    num_trades: int
    win_rate_pct: float
    profit_factor: float
    expectancy: float
    alpha: float
    beta: float
    sharpe_ratio_ci_low: float
    sharpe_ratio_ci_high: float
    cagr_pct_ci_low: float
    cagr_pct_ci_high: float
    equity_curve: list[dict[str, Any]] = field(default_factory=list)
    drawdown_curve: list[dict[str, Any]] = field(default_factory=list)
    monthly_returns: list[dict[str, Any]] = field(default_factory=list)
    daily_returns: list[dict[str, Any]] = field(default_factory=list)


def _safe_div(numerator: float, denominator: float, default: float = 0.0) -> float:
    return numerator / denominator if denominator else default


def _max_drawdown_series(equity: pd.Series) -> pd.Series:
    running_max = equity.cummax()
    return (equity / running_max) - 1.0


def _max_consecutive_losses(trades: list[SimulatedTrade]) -> int:
    streak = longest = 0
    for trade in trades:
        if trade.pnl < 0:
            streak += 1
            longest = max(longest, streak)
        else:
            streak = 0
    return longest


def _recovery_days(equity: pd.Series, drawdown: pd.Series) -> int | None:
    trough_idx = drawdown.idxmin()
    if pd.isna(trough_idx):
        return None
    peak_value = equity.loc[:trough_idx].max()
    after_trough = equity.loc[trough_idx:]
    recovered = after_trough[after_trough >= peak_value]
    if recovered.empty:
        return None
    recovery_idx = recovered.index[0]
    return int((recovery_idx - trough_idx).days) if hasattr(recovery_idx, "__sub__") else None


def _block_bootstrap_indices(n: int, block_size: int, rng: np.random.Generator) -> np.ndarray:
    """Resamples `n` observations as contiguous blocks of `block_size` (with
    replacement) rather than individual i.i.d. draws — preserves some of daily
    returns' autocorrelation/volatility-clustering structure, which a naive
    per-day bootstrap would destroy."""
    n_blocks = int(np.ceil(n / block_size))
    if n <= block_size:
        return np.tile(np.arange(n), n_blocks)[:n]
    starts = rng.integers(0, n - block_size + 1, size=n_blocks)
    idx = np.concatenate([np.arange(s, s + block_size) for s in starts])
    return idx[:n]


def compute_bootstrap_confidence_intervals(
    daily_returns: pd.Series,
    n_bootstrap: int = 500,
    confidence: float = 0.95,
    block_size: int = 20,
    seed: int = 42,
    rf_daily: float = 0.0,
) -> tuple[float, float, float, float]:
    """Block-bootstrap confidence intervals for Sharpe and CAGR. A point estimate
    alone ("Sharpe = 1.2") implies more statistical confidence than a few hundred
    daily-return observations can actually support — quoting an interval alongside
    it is standard practice in real quant research and conspicuously absent from
    most backtesting-tool output. Deterministic given `seed`: re-running the same
    backtest always reproduces the same interval, never a different one by chance.

    Sharpe is computed on returns in excess of `rf_daily`, the same way as the point
    estimate, so the interval describes the number it is quoted next to.

    Returns (sharpe_ci_low, sharpe_ci_high, cagr_pct_ci_low, cagr_pct_ci_high).
    """
    returns = daily_returns.to_numpy()
    n = len(returns)
    n_years = max(n / TRADING_DAYS_PER_YEAR, 1e-9)

    if n < block_size * 2:
        # Too little data for a meaningful block bootstrap — report the point
        # estimate as a degenerate (zero-width) interval rather than a misleading range.
        excess = returns - rf_daily
        std = excess.std(ddof=0)
        sharpe = (excess.mean() / std * np.sqrt(TRADING_DAYS_PER_YEAR)) if std > 0 else 0.0
        cagr = (float(np.prod(1 + returns)) ** (1 / n_years) - 1) * 100 if n else 0.0
        return float(sharpe), float(sharpe), float(cagr), float(cagr)

    rng = np.random.default_rng(seed)
    sharpes = np.empty(n_bootstrap)
    cagrs = np.empty(n_bootstrap)

    for i in range(n_bootstrap):
        sample = returns[_block_bootstrap_indices(n, block_size, rng)]
        excess = sample - rf_daily
        std = excess.std(ddof=0)
        sharpes[i] = (excess.mean() / std * np.sqrt(TRADING_DAYS_PER_YEAR)) if std > 0 else 0.0
        cagrs[i] = (float(np.prod(1 + sample)) ** (1 / n_years) - 1) * 100

    tail = (1 - confidence) / 2 * 100
    return (
        float(np.percentile(sharpes, tail)),
        float(np.percentile(sharpes, 100 - tail)),
        float(np.percentile(cagrs, tail)),
        float(np.percentile(cagrs, 100 - tail)),
    )


def compute_performance_metrics(
    equity_curve: pd.Series,
    trades: list[SimulatedTrade],
    benchmark_returns: pd.Series | None = None,
    risk_free_rate_annual: float = 0.0,
) -> PerformanceMetrics:
    equity_curve = equity_curve.sort_index()
    # N equity points give N-1 returns; the first point has no prior day, so it is
    # dropped rather than padded with a 0% return that would dilute mean and volatility.
    daily_returns = equity_curve.pct_change().iloc[1:].fillna(0.0)
    if daily_returns.empty:
        daily_returns = pd.Series([0.0], index=equity_curve.index[:1])
    rf_daily = risk_free_rate_annual / TRADING_DAYS_PER_YEAR

    total_return_pct = (equity_curve.iloc[-1] / equity_curve.iloc[0] - 1) * 100
    n_years = max((len(equity_curve) - 1) / TRADING_DAYS_PER_YEAR, 1e-9)
    cagr_pct = ((equity_curve.iloc[-1] / equity_curve.iloc[0]) ** (1 / n_years) - 1) * 100
    volatility_pct = daily_returns.std(ddof=0) * np.sqrt(TRADING_DAYS_PER_YEAR) * 100

    excess_returns = daily_returns - rf_daily
    sharpe_ratio = _safe_div(excess_returns.mean(), excess_returns.std(ddof=0)) * np.sqrt(TRADING_DAYS_PER_YEAR)

    # Downside deviation: root-mean-square of shortfalls below the risk-free target, taken
    # over every period (periods above target count as zero shortfall).
    downside_deviation = float(np.sqrt(np.mean(np.square(np.minimum(excess_returns, 0.0)))))
    sortino_ratio = _safe_div(excess_returns.mean(), downside_deviation) * np.sqrt(TRADING_DAYS_PER_YEAR)

    drawdown = _max_drawdown_series(equity_curve)
    max_drawdown_pct = drawdown.min() * 100
    calmar_ratio = _safe_div(cagr_pct, abs(max_drawdown_pct))

    gains = daily_returns[daily_returns > 0].sum()
    losses = -daily_returns[daily_returns < 0].sum()
    omega_ratio = min(_safe_div(gains, losses, default=_OMEGA_CAP), _OMEGA_CAP)

    ulcer_index = float(np.sqrt(np.mean(np.square(drawdown * 100))))

    var_95_pct = float(np.percentile(daily_returns, 5)) * 100
    tail = daily_returns[daily_returns <= np.percentile(daily_returns, 5)]
    cvar_95_pct = float(tail.mean()) * 100 if not tail.empty else var_95_pct

    recovery_days = _recovery_days(equity_curve, drawdown)

    num_trades = len(trades)
    winning = [t for t in trades if t.pnl > 0]
    losing = [t for t in trades if t.pnl <= 0]
    win_rate_pct = _safe_div(len(winning), num_trades) * 100
    gross_profit = sum(t.pnl for t in winning)
    gross_loss = abs(sum(t.pnl for t in losing))
    profit_factor = _safe_div(gross_profit, gross_loss, default=gross_profit if gross_profit > 0 else 0.0)
    expectancy = _safe_div(sum(t.pnl for t in trades), num_trades)

    alpha, beta = 0.0, 0.0
    if benchmark_returns is not None and len(benchmark_returns) > 1:
        aligned = pd.concat([daily_returns, benchmark_returns], axis=1, join="inner").dropna()
        if len(aligned) > 1 and aligned.iloc[:, 1].var() > 0:
            cov_matrix = np.cov(aligned.iloc[:, 0], aligned.iloc[:, 1])
            beta = float(cov_matrix[0, 1] / cov_matrix[1, 1])
            # Jensen's alpha: excess return over the risk-free rate not explained by beta.
            strategy_excess = aligned.iloc[:, 0].mean() - rf_daily
            benchmark_excess = aligned.iloc[:, 1].mean() - rf_daily
            alpha = float((strategy_excess - beta * benchmark_excess) * TRADING_DAYS_PER_YEAR)

    sharpe_ci_low, sharpe_ci_high, cagr_ci_low, cagr_ci_high = compute_bootstrap_confidence_intervals(
        daily_returns, rf_daily=rf_daily
    )

    equity_curve_payload = [
        {"date": idx.isoformat() if hasattr(idx, "isoformat") else str(idx), "equity": float(val)}
        for idx, val in equity_curve.items()
    ]
    drawdown_curve_payload = [
        {"date": idx.isoformat() if hasattr(idx, "isoformat") else str(idx), "drawdown_pct": float(val * 100)}
        for idx, val in drawdown.items()
    ]
    daily_returns_payload = [
        {"date": idx.isoformat() if hasattr(idx, "isoformat") else str(idx), "return_pct": float(val * 100)}
        for idx, val in daily_returns.items()
    ]

    monthly = equity_curve.resample("ME").last()
    monthly_returns_series = monthly.pct_change().fillna(
        (monthly.iloc[0] / equity_curve.iloc[0]) - 1 if len(monthly) else 0
    )
    monthly_returns_payload = [
        {"year": idx.year, "month": idx.month, "return_pct": float(val * 100)}
        for idx, val in monthly_returns_series.items()
    ]

    return PerformanceMetrics(
        total_return_pct=float(total_return_pct),
        cagr_pct=float(cagr_pct),
        volatility_pct=float(volatility_pct),
        sharpe_ratio=float(sharpe_ratio),
        sortino_ratio=float(sortino_ratio),
        calmar_ratio=float(calmar_ratio),
        omega_ratio=float(omega_ratio),
        max_drawdown_pct=float(max_drawdown_pct),
        ulcer_index=ulcer_index,
        var_95_pct=var_95_pct,
        cvar_95_pct=cvar_95_pct,
        max_consecutive_losses=_max_consecutive_losses(trades),
        recovery_days=recovery_days,
        num_trades=num_trades,
        win_rate_pct=float(win_rate_pct),
        profit_factor=float(profit_factor),
        expectancy=float(expectancy),
        alpha=alpha,
        beta=beta,
        sharpe_ratio_ci_low=sharpe_ci_low,
        sharpe_ratio_ci_high=sharpe_ci_high,
        cagr_pct_ci_low=cagr_ci_low,
        cagr_pct_ci_high=cagr_ci_high,
        equity_curve=equity_curve_payload,
        drawdown_curve=drawdown_curve_payload,
        monthly_returns=monthly_returns_payload,
        daily_returns=daily_returns_payload,
    )
