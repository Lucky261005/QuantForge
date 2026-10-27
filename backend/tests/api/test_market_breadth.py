"""Market breadth (advance/decline, 52-week highs/lows) is computed from OHLCV
already stored for every equity — no external feed. Uses recent-dated (ending
today) synthetic series, since the service only looks at the trailing ~52 weeks."""

import io

import numpy as np
import pandas as pd


def _recent_csv(seed: int, trend: str, n: int = 280) -> bytes:
    # Deterministic, strictly monotonic series — guarantees the last close is
    # unambiguously the 52-week high (uptrend) or low (downtrend), unlike a
    # random-walk-with-drift series where the very last day isn't guaranteed to
    # be the extreme even with a strong drift.
    rng = np.random.default_rng(seed)
    dates = pd.bdate_range(end=pd.Timestamp.today().normalize(), periods=n)
    step = 1.0 if trend == "up" else -1.0
    close = 1000.0 + step * np.arange(n)  # base price high enough to stay positive over n days
    df = pd.DataFrame(
        {
            "Date": dates.strftime("%Y-%m-%d"),
            "Open": close,
            "High": close * 1.005,
            "Low": close * 0.995,
            "Close": close,
            "Adj Close": close,
            "Volume": rng.integers(1_000_000, 5_000_000, n),
        }
    )
    buf = io.BytesIO()
    df.to_csv(buf, index=False)
    return buf.getvalue()


def test_market_breadth_with_no_equities_returns_zeros(client, auth_headers):
    r = client.get("/api/v1/assets/breadth", headers=auth_headers)
    assert r.status_code == 200
    assert r.json() == {
        "advancing": 0,
        "declining": 0,
        "unchanged": 0,
        "new_52w_highs": 0,
        "new_52w_lows": 0,
        "total": 0,
    }


def test_market_breadth_counts_advancers_decliners_and_52w_extremes(client, auth_headers):
    for symbol, trend in [("UPTREND", "up"), ("DOWNTREND", "down")]:
        files = {"file": (f"{symbol}.csv", _recent_csv(seed=hash(symbol) % 1000, trend=trend), "text/csv")}
        r = client.post(f"/api/v1/assets/upload?symbol={symbol}", files=files, headers=auth_headers)
        assert r.status_code == 200, r.text

    r = client.get("/api/v1/assets/breadth", headers=auth_headers)
    assert r.status_code == 200
    breadth = r.json()
    assert breadth["total"] == 2
    # A steady uptrend's last close is its own 52-week high and an up day; the
    # mirrored downtrend is a 52-week low and a down day.
    assert breadth["new_52w_highs"] >= 1
    assert breadth["new_52w_lows"] >= 1
    assert breadth["advancing"] + breadth["declining"] + breadth["unchanged"] == 2


def test_breadth_and_latest_bar_date_work_on_data_that_ended_long_ago(client, auth_headers):
    """Stored history often ends well before today (a static demo dataset); "recent"
    must mean the newest stored bars, not the calendar."""
    dates = pd.bdate_range(end="2021-06-30", periods=60)
    close = 500.0 + np.arange(60)
    df = pd.DataFrame(
        {
            "Date": dates.strftime("%Y-%m-%d"),
            "Open": close,
            "High": close + 1,
            "Low": close - 1,
            "Close": close,
            "Adj Close": close,
            "Volume": 1000,
        }
    )
    buf = io.BytesIO()
    df.to_csv(buf, index=False)
    files = {"file": ("OLDCO.csv", buf.getvalue(), "text/csv")}
    assert client.post("/api/v1/assets/upload?symbol=OLDCO", files=files, headers=auth_headers).status_code == 200

    breadth = client.get("/api/v1/assets/breadth", headers=auth_headers).json()
    assert breadth["total"] == 1
    assert breadth["advancing"] == 1
    assert breadth["new_52w_highs"] == 1

    assets = client.get("/api/v1/assets", headers=auth_headers).json()["items"]
    assert assets[0]["latest_bar_date"] == "2021-06-30"
