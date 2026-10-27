"""Portfolio optimizer: turns a matrix of daily asset returns into allocation
weights under one of five standard research objectives. Long-only, fully
invested (weights sum to 1, each in [0, 1]) via SLSQP — the standard
constrained-QP approach for this class of problem.
"""

from dataclasses import dataclass
from enum import StrEnum

import numpy as np
import pandas as pd
from scipy.optimize import minimize

TRADING_DAYS_PER_YEAR = 252


class OptimizationMethod(StrEnum):
    EQUAL_WEIGHT = "equal_weight"
    MEAN_VARIANCE = "mean_variance"
    RISK_PARITY = "risk_parity"
    MAX_SHARPE = "max_sharpe"
    MIN_VOLATILITY = "min_volatility"


@dataclass
class OptimizationResult:
    method: OptimizationMethod
    weights: dict[str, float]
    expected_return_pct: float
    expected_volatility_pct: float
    sharpe_ratio: float


def _bounds_and_constraints(n: int) -> tuple[tuple, tuple, np.ndarray]:
    bounds = tuple((0.0, 1.0) for _ in range(n))
    constraints = ({"type": "eq", "fun": lambda w: np.sum(w) - 1.0},)
    x0 = np.repeat(1.0 / n, n)
    return bounds, constraints, x0


def _minimize_volatility(cov_matrix: np.ndarray, n: int) -> np.ndarray:
    bounds, constraints, x0 = _bounds_and_constraints(n)
    result = minimize(lambda w: w @ cov_matrix @ w, x0, method="SLSQP", bounds=bounds, constraints=constraints)
    return result.x if result.success else x0


def _maximize_sharpe(mean_returns: np.ndarray, cov_matrix: np.ndarray, n: int, risk_free_rate: float) -> np.ndarray:
    bounds, constraints, x0 = _bounds_and_constraints(n)

    def neg_sharpe(w: np.ndarray) -> float:
        ret = w @ mean_returns
        vol = np.sqrt(w @ cov_matrix @ w)
        return -(ret - risk_free_rate) / vol if vol > 1e-12 else 0.0

    result = minimize(neg_sharpe, x0, method="SLSQP", bounds=bounds, constraints=constraints)
    return result.x if result.success else x0


def _risk_parity(cov_matrix: np.ndarray, n: int) -> np.ndarray:
    bounds, constraints, x0 = _bounds_and_constraints(n)

    def objective(w: np.ndarray) -> float:
        portfolio_vol = np.sqrt(w @ cov_matrix @ w)
        if portfolio_vol < 1e-12:
            return 0.0
        marginal_contrib = cov_matrix @ w
        risk_contrib = w * marginal_contrib / portfolio_vol
        return float(np.sum((risk_contrib - risk_contrib.mean()) ** 2))

    result = minimize(objective, x0, method="SLSQP", bounds=bounds, constraints=constraints)
    return result.x if result.success else x0


def _mean_variance(mean_returns: np.ndarray, cov_matrix: np.ndarray, n: int, risk_aversion: float = 1.0) -> np.ndarray:
    bounds, constraints, x0 = _bounds_and_constraints(n)

    def objective(w: np.ndarray) -> float:
        return -(w @ mean_returns - risk_aversion * (w @ cov_matrix @ w))

    result = minimize(objective, x0, method="SLSQP", bounds=bounds, constraints=constraints)
    return result.x if result.success else x0


def optimize_portfolio(
    returns: pd.DataFrame, method: OptimizationMethod, risk_free_rate: float = 0.0
) -> OptimizationResult:
    """`returns` must be a DataFrame of daily simple returns, one column per symbol,
    aligned on date. At least ~30 rows are recommended for a stable covariance estimate."""
    symbols = list(returns.columns)
    n = len(symbols)
    if n == 0:
        raise ValueError("Cannot optimize an empty asset universe")

    mean_returns = returns.mean().to_numpy() * TRADING_DAYS_PER_YEAR
    cov_matrix = returns.cov().to_numpy() * TRADING_DAYS_PER_YEAR

    if method == OptimizationMethod.EQUAL_WEIGHT:
        weights = np.repeat(1.0 / n, n)
    elif method == OptimizationMethod.MIN_VOLATILITY:
        weights = _minimize_volatility(cov_matrix, n)
    elif method == OptimizationMethod.MAX_SHARPE:
        weights = _maximize_sharpe(mean_returns, cov_matrix, n, risk_free_rate)
    elif method == OptimizationMethod.RISK_PARITY:
        weights = _risk_parity(cov_matrix, n)
    elif method == OptimizationMethod.MEAN_VARIANCE:
        weights = _mean_variance(mean_returns, cov_matrix, n)
    else:
        raise ValueError(f"Unknown optimization method: {method}")

    weights = np.clip(weights, 0, 1)
    weights = weights / weights.sum()

    port_return = float(weights @ mean_returns)
    port_vol = float(np.sqrt(weights @ cov_matrix @ weights))
    sharpe = (port_return - risk_free_rate) / port_vol if port_vol > 1e-12 else 0.0

    return OptimizationResult(
        method=method,
        weights={symbol: float(w) for symbol, w in zip(symbols, weights, strict=True)},
        expected_return_pct=port_return * 100,
        expected_volatility_pct=port_vol * 100,
        sharpe_ratio=sharpe,
    )
