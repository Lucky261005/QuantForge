import numpy as np
import pandas as pd
import pytest

from app.backtesting.optimizer import OptimizationMethod, optimize_portfolio


@pytest.fixture
def returns_df() -> pd.DataFrame:
    rng = np.random.default_rng(7)
    n = 500
    dates = pd.bdate_range("2022-01-03", periods=n)
    # AAA: higher return/higher vol, BBB: lower return/lower vol, CCC: middling, correlated with AAA
    aaa = rng.normal(0.0012, 0.02, n)
    bbb = rng.normal(0.0004, 0.008, n)
    ccc = 0.6 * aaa + rng.normal(0.0006, 0.01, n)
    return pd.DataFrame({"AAA": aaa, "BBB": bbb, "CCC": ccc}, index=dates)


def test_weights_sum_to_one_for_every_method(returns_df):
    for method in OptimizationMethod:
        result = optimize_portfolio(returns_df, method)
        assert sum(result.weights.values()) == pytest.approx(1.0, abs=1e-4)
        assert all(w >= -1e-6 for w in result.weights.values())


def test_equal_weight_splits_evenly(returns_df):
    result = optimize_portfolio(returns_df, OptimizationMethod.EQUAL_WEIGHT)
    for w in result.weights.values():
        assert w == pytest.approx(1 / 3, abs=1e-6)


def test_min_volatility_favors_lower_vol_asset(returns_df):
    result = optimize_portfolio(returns_df, OptimizationMethod.MIN_VOLATILITY)
    assert result.weights["BBB"] > result.weights["AAA"]


def test_max_sharpe_produces_better_or_equal_sharpe_than_equal_weight(returns_df):
    eq = optimize_portfolio(returns_df, OptimizationMethod.EQUAL_WEIGHT)
    ms = optimize_portfolio(returns_df, OptimizationMethod.MAX_SHARPE)
    assert ms.sharpe_ratio >= eq.sharpe_ratio - 1e-6


def test_risk_parity_gives_less_weight_to_high_vol_asset_than_equal_weight(returns_df):
    result = optimize_portfolio(returns_df, OptimizationMethod.RISK_PARITY)
    assert result.weights["AAA"] < 1 / 3


def test_single_asset_universe_gets_full_weight():
    dates = pd.bdate_range("2023-01-02", periods=100)
    returns = pd.DataFrame({"ONLY": np.random.default_rng(1).normal(0.001, 0.01, 100)}, index=dates)
    result = optimize_portfolio(returns, OptimizationMethod.MAX_SHARPE)
    assert result.weights["ONLY"] == pytest.approx(1.0)


def test_empty_universe_raises():
    with pytest.raises(ValueError):
        optimize_portfolio(pd.DataFrame(), OptimizationMethod.EQUAL_WEIGHT)
