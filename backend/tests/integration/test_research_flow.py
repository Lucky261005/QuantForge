"""End-to-end integration test for the core research loop: register -> upload data
-> create strategy -> run backtest -> read metrics/equity/trades -> compare -> optimize.

Uses a temp SQLite file (not :memory:, since TestClient may use a different connection)
and CSV upload as the data path, since it needs no network access.
"""

import pytest

from tests.utils import synthetic_csv as _synthetic_csv


def test_full_research_loop(client, auth_headers):
    # 1. Upload OHLCV data for the traded asset and the benchmark.
    for symbol, seed in [("AAPL", 1), ("SPY", 2)]:
        files = {"file": (f"{symbol}.csv", _synthetic_csv(seed), "text/csv")}
        r = client.post(f"/api/v1/assets/upload?symbol={symbol}", files=files, headers=auth_headers)
        assert r.status_code == 200, r.text
        assert r.json()["bars_written"] == 300

    # 2. Strategy catalog should list all 21 built-ins.
    r = client.get("/api/v1/strategies/catalog")
    assert r.status_code == 200
    catalog_keys = {entry["key"] for entry in r.json()}
    assert "ma_cross" in catalog_keys
    assert len(catalog_keys) == 21

    # 3. Create a strategy.
    r = client.post(
        "/api/v1/strategies",
        json={"name": "My MA Cross", "strategy_type": "ma_cross", "parameters": {"fast_window": 10, "slow_window": 30}},
        headers=auth_headers,
    )
    assert r.status_code == 201, r.text
    strategy_id = r.json()["id"]
    assert r.json()["parameters"]["fast_window"] == 10

    # 4. Run a backtest.
    r = client.post(
        "/api/v1/backtests",
        json={
            "strategy_id": strategy_id,
            "symbols": ["AAPL"],
            "start_date": "2022-01-03",
            "end_date": "2023-03-01",
            "initial_capital": 100_000,
            "benchmark_symbol": "SPY",
        },
        headers=auth_headers,
    )
    assert r.status_code == 201, r.text
    backtest_id = r.json()["id"]

    # Since no Celery broker is running in tests, dispatch_backtest falls back to
    # synchronous execution, so the backtest should already be done.
    r = client.get(f"/api/v1/backtests/{backtest_id}/status", headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["status"] == "completed", r.json()

    # 5. Metrics, equity curve, and trades should all be populated.
    r = client.get(f"/api/v1/backtests/{backtest_id}/metrics", headers=auth_headers)
    assert r.status_code == 200
    metrics = r.json()
    assert "sharpe_ratio" in metrics
    assert "max_drawdown_pct" in metrics

    r = client.get(f"/api/v1/backtests/{backtest_id}/equity", headers=auth_headers)
    assert r.status_code == 200
    assert len(r.json()["equity_curve"]) > 0

    r = client.get(f"/api/v1/backtests/{backtest_id}/trades", headers=auth_headers)
    assert r.status_code == 200

    # 5b. Cost sensitivity — returns 5.5% overall (0/0.5/1/1.5/2x cost multipliers)
    r = client.get(f"/api/v1/backtests/{backtest_id}/cost-sensitivity", headers=auth_headers)
    assert r.status_code == 200
    sensitivity = r.json()
    assert len(sensitivity) == 5
    assert sensitivity[0]["cost_multiplier"] == 0.0
    # Zero-cost should never do worse than 2x-cost on the same signals.
    assert sensitivity[0]["total_return_pct"] >= sensitivity[-1]["total_return_pct"]

    # 5c. Walk-forward validation — same fixed params, split into windows.
    r = client.get(f"/api/v1/backtests/{backtest_id}/walk-forward?n_windows=3", headers=auth_headers)
    assert r.status_code == 200
    windows = r.json()
    assert len(windows) == 3
    assert windows[0]["window"] == 1

    # 6. A second strategy/backtest for comparison.
    r = client.post(
        "/api/v1/strategies",
        json={"name": "Passive Benchmark", "strategy_type": "buy_and_hold", "parameters": {}},
        headers=auth_headers,
    )
    strategy2_id = r.json()["id"]
    r = client.post(
        "/api/v1/backtests",
        json={
            "strategy_id": strategy2_id,
            "symbols": ["AAPL"],
            "start_date": "2022-01-03",
            "end_date": "2023-03-01",
            "benchmark_symbol": "SPY",
        },
        headers=auth_headers,
    )
    backtest2_id = r.json()["id"]
    assert client.get(f"/api/v1/backtests/{backtest2_id}/status", headers=auth_headers).json()["status"] == "completed"

    # 7. Compare the two backtests.
    r = client.post(
        "/api/v1/analytics/compare", json={"backtest_ids": [backtest_id, backtest2_id]}, headers=auth_headers
    )
    assert r.status_code == 200, r.text
    compare = r.json()
    assert len(compare["entries"]) == 2
    assert "correlation_matrix" in compare

    # 8. Portfolio optimizer across the two uploaded symbols.
    r = client.post(
        "/api/v1/analytics/optimize-portfolio",
        json={"symbols": ["AAPL", "SPY"], "start_date": "2022-01-03", "end_date": "2023-03-01", "method": "max_sharpe"},
        headers=auth_headers,
    )
    assert r.status_code == 200, r.text
    weights = r.json()["weights"]
    assert pytest.approx(sum(weights.values()), abs=1e-3) == 1.0


def test_backtest_rejects_strategy_owned_by_another_user(client, auth_headers):
    client.post(
        "/api/v1/auth/register",
        json={"email": "other@example.com", "username": "otheruser", "password": "password123"},
    )
    r = client.post("/api/v1/auth/login", json={"email": "other@example.com", "password": "password123"})
    other_headers = {"Authorization": f"Bearer {r.json()['access_token']}"}

    r = client.post(
        "/api/v1/strategies",
        json={"name": "Private", "strategy_type": "buy_and_hold", "parameters": {}},
        headers=auth_headers,
    )
    strategy_id = r.json()["id"]

    r = client.post(
        "/api/v1/backtests",
        json={"strategy_id": strategy_id, "symbols": ["AAPL"], "start_date": "2022-01-01", "end_date": "2022-06-01"},
        headers=other_headers,
    )
    assert r.status_code == 403
