#!/usr/bin/env python3
"""Seeds a demo account with Indian market data (NSE large-caps + benchmark indices),
sector watchlists, and a few completed backtests - so the app is immediately
explorable without waiting on (or being rate-limited by) a live NSE/Yahoo download.

Usage:
    cd backend && source .venv/Scripts/activate
    python ../scripts/seed_demo_data.py

Requires the backend to already be running (see README "Local development").
"""
import io
import os
import sys
import time

import httpx
import numpy as np
import pandas as pd

BASE_URL = os.environ.get("QUANTFORGE_API_URL", "http://localhost:8000/api/v1")
DEMO_EMAIL = "demo@quantforge.io"
DEMO_USERNAME = "demo_researcher"
DEMO_PASSWORD = "DemoPass123"

# 20 NSE large-caps with sector/industry/market cap (INR crore, approximate) — a
# realistic constituent slice of the NIFTY 50, not a random symbol swap.
STOCKS = {
    "RELIANCE": {
        "seed": 1,
        "price": 2900.0,
        "sector": "Energy",
        "industry": "Oil & Gas Refining & Marketing",
        "cap": 1_900_000.0,
    },
    "TCS": {"seed": 2, "price": 3800.0, "sector": "IT", "industry": "IT Services & Consulting", "cap": 1_400_000.0},
    "INFY": {"seed": 3, "price": 1800.0, "sector": "IT", "industry": "IT Services & Consulting", "cap": 750_000.0},
    "HDFCBANK": {
        "seed": 4,
        "price": 1650.0,
        "sector": "Banking",
        "industry": "Private Sector Bank",
        "cap": 1_250_000.0,
    },
    "ICICIBANK": {"seed": 5, "price": 1200.0, "sector": "Banking", "industry": "Private Sector Bank", "cap": 850_000.0},
    "BHARTIARTL": {"seed": 6, "price": 1300.0, "sector": "Telecom", "industry": "Telecom Services", "cap": 750_000.0},
    "ITC": {"seed": 7, "price": 460.0, "sector": "FMCG", "industry": "Diversified FMCG", "cap": 570_000.0},
    "LT": {
        "seed": 8,
        "price": 3600.0,
        "sector": "Infrastructure",
        "industry": "Engineering & Construction",
        "cap": 500_000.0,
    },
    "MARUTI": {"seed": 9, "price": 12500.0, "sector": "Auto", "industry": "Passenger Vehicles", "cap": 380_000.0},
    "AXISBANK": {"seed": 10, "price": 1150.0, "sector": "Banking", "industry": "Private Sector Bank", "cap": 360_000.0},
    "SBIN": {"seed": 11, "price": 820.0, "sector": "PSU", "industry": "Public Sector Bank", "cap": 730_000.0},
    "ADANIENT": {
        "seed": 12,
        "price": 3000.0,
        "sector": "Diversified",
        "industry": "Diversified Conglomerate",
        "cap": 340_000.0,
    },
    "BAJFINANCE": {"seed": 13, "price": 7000.0, "sector": "Financial Services", "industry": "NBFC", "cap": 430_000.0},
    "ASIANPAINT": {"seed": 14, "price": 2900.0, "sector": "Consumer", "industry": "Paints", "cap": 275_000.0},
    "TATAMOTORS": {
        "seed": 15,
        "price": 950.0,
        "sector": "Auto",
        "industry": "Commercial & Passenger Vehicles",
        "cap": 330_000.0,
    },
    "ULTRACEMCO": {
        "seed": 16,
        "price": 11000.0,
        "sector": "Cement",
        "industry": "Cement & Construction Materials",
        "cap": 320_000.0,
    },
    "TITAN": {"seed": 17, "price": 3400.0, "sector": "Consumer", "industry": "Jewellery & Watches", "cap": 300_000.0},
    "WIPRO": {"seed": 18, "price": 550.0, "sector": "IT", "industry": "IT Services & Consulting", "cap": 230_000.0},
    "TECHM": {"seed": 19, "price": 1650.0, "sector": "IT", "industry": "IT Services & Consulting", "cap": 140_000.0},
    "SUNPHARMA": {"seed": 20, "price": 1750.0, "sector": "Pharma", "industry": "Pharmaceuticals", "cap": 420_000.0},
}

INDICES = {
    "NIFTY50": {"seed": 101, "price": 24500.0},
    "BANKNIFTY": {"seed": 102, "price": 52000.0},
    "FINNIFTY": {"seed": 103, "price": 23500.0},
    "SENSEX": {"seed": 104, "price": 80500.0},
    "MIDCAP100": {"seed": 105, "price": 57000.0},
    "NIFTYNEXT50": {"seed": 106, "price": 72000.0},
}

SECTOR_WATCHLISTS = {
    "Banking": ["HDFCBANK", "ICICIBANK", "AXISBANK", "SBIN"],
    "IT": ["TCS", "INFY", "WIPRO", "TECHM"],
    "Auto": ["MARUTI", "TATAMOTORS"],
    "Pharma": ["SUNPHARMA"],
    "FMCG": ["ITC"],
    "Energy": ["RELIANCE"],
    "PSU": ["SBIN"],
}


def synthetic_csv(seed: int, start_price: float, n: int = 1260) -> bytes:
    """Defaults to ~5 years of business days (252/year * 5) — matches the
    'backtested across 5 years of historical market data' resume claim with data
    that's actually demonstrable in the running demo, not just supported in theory."""
    rng = np.random.default_rng(seed)
    dates = pd.bdate_range(end=pd.Timestamp.today().normalize(), periods=n)
    returns = rng.normal(0.0005, 0.012, n)
    close = start_price * np.cumprod(1 + returns)
    open_ = close * (1 + rng.normal(0, 0.002, n))
    high = np.maximum(open_, close) * (1 + np.abs(rng.normal(0, 0.004, n)))
    low = np.minimum(open_, close) * (1 - np.abs(rng.normal(0, 0.004, n)))
    volume = rng.integers(1_000_000, 8_000_000, n)

    df = pd.DataFrame(
        {
            "Date": dates.strftime("%Y-%m-%d"),
            "Open": open_,
            "High": high,
            "Low": low,
            "Close": close,
            "Adj Close": close,
            "Volume": volume,
        }
    )
    buf = io.BytesIO()
    df.to_csv(buf, index=False)
    return buf.getvalue()


def main() -> None:
    client = httpx.Client(base_url=BASE_URL, timeout=30)

    print(f"==> Registering demo user ({DEMO_EMAIL})")
    r = client.post(
        "/auth/register",
        json={
            "email": DEMO_EMAIL,
            "username": DEMO_USERNAME,
            "password": DEMO_PASSWORD,
            "full_name": "Demo Researcher",
        },
    )
    if r.status_code not in (201, 409):
        print(f"Registration failed unexpectedly: {r.status_code} {r.text}", file=sys.stderr)
        sys.exit(1)
    print("    (already existed, continuing)" if r.status_code == 409 else "    created")

    r = client.post("/auth/login", json={"email": DEMO_EMAIL, "password": DEMO_PASSWORD})
    r.raise_for_status()
    access_token = r.json()["access_token"]
    client.headers["Authorization"] = f"Bearer {access_token}"

    # /assets/upload is rate-limited (RATE_LIMIT_DATA_DOWNLOAD, 20/minute by default) to
    # protect the real download path from abuse — with 26 symbols to seed here, a brief
    # pace-limiting sleep keeps this script under that limit instead of tripping it.
    upload_pause_seconds = 3.5

    print("==> Uploading synthetic OHLCV data (20 NSE large-caps)")
    for symbol, meta in STOCKS.items():
        csv_bytes = synthetic_csv(meta["seed"], meta["price"])
        r = client.post(
            "/assets/upload",
            params={
                "symbol": symbol,
                "asset_type": "equity",
                "exchange": "NSE",
                "sector": meta["sector"],
                "industry": meta["industry"],
                "market_cap_cr": meta["cap"],
                "synthetic": True,  # generated prices: the app labels them as synthetic demo data
            },
            files={"file": (f"{symbol}.csv", csv_bytes, "text/csv")},
        )
        r.raise_for_status()
        print(f"    {symbol}: {r.json()['bars_written']} bars ({meta['sector']})")
        time.sleep(upload_pause_seconds)

    print("==> Uploading synthetic index series (NIFTY50, BANKNIFTY, FINNIFTY, SENSEX, MIDCAP100, NIFTYNEXT50)")
    for symbol, meta in INDICES.items():
        csv_bytes = synthetic_csv(meta["seed"], meta["price"])
        r = client.post(
            "/assets/upload",
            params={
                "symbol": symbol,
                "asset_type": "index",
                "exchange": "NSE" if symbol != "SENSEX" else "BSE",
                "synthetic": True,  # generated prices: the app labels them as synthetic demo data
            },
            files={"file": (f"{symbol}.csv", csv_bytes, "text/csv")},
        )
        r.raise_for_status()
        print(f"    {symbol}: {r.json()['bars_written']} bars")
        time.sleep(upload_pause_seconds)

    print("==> Creating sector watchlists")
    all_watchlists = {"NIFTY 50": list(STOCKS.keys()), **SECTOR_WATCHLISTS}
    for name, symbols in all_watchlists.items():
        r = client.post("/watchlists", json={"name": name})
        r.raise_for_status()
        watchlist_id = r.json()["id"]
        for symbol in symbols:
            item_r = client.post(f"/watchlists/{watchlist_id}/items", json={"symbol": symbol})
            item_r.raise_for_status()
        print(f"    {name}: {len(symbols)} symbols")

    print("==> Creating strategies")
    strategies = [
        {
            "name": "Golden Cross - 50/200",
            "strategy_type": "ma_cross",
            "parameters": {"fast_window": 50, "slow_window": 200},
        },
        {
            "name": "EMA Crossover - 9/21",
            "strategy_type": "ema_crossover",
            "parameters": {"fast_window": 9, "slow_window": 21},
        },
        {"name": "SuperTrend - 10/3", "strategy_type": "supertrend", "parameters": {"window": 10, "multiplier": 3.0}},
        {"name": "RSI Reversal - Classic", "strategy_type": "rsi_mean_reversion", "parameters": {}},
        {"name": "NIFTY Momentum", "strategy_type": "momentum", "parameters": {"lookback": 90}},
        {"name": "Aroon Trend", "strategy_type": "aroon_trend", "parameters": {}},
        {"name": "Parabolic SAR Trend", "strategy_type": "parabolic_sar_trend", "parameters": {}},
        {"name": "CCI Trend", "strategy_type": "cci_trend", "parameters": {}},
        {"name": "Passive Benchmark", "strategy_type": "buy_and_hold", "parameters": {}},
    ]
    strategy_ids = {}
    for payload in strategies:
        r = client.post("/strategies", json=payload)
        r.raise_for_status()
        strategy_ids[payload["name"]] = r.json()["id"]
        print(f"    {payload['name']} -> id {r.json()['id']}")

    print("==> Running backtests (5-year window)")
    start_date = (pd.Timestamp.today() - pd.Timedelta(days=365 * 5 + 14)).strftime("%Y-%m-%d")
    end_date = pd.Timestamp.today().strftime("%Y-%m-%d")

    runs = [
        ("Golden Cross - 50/200", "RELIANCE", {}),
        ("EMA Crossover - 9/21", "TCS", {}),
        ("SuperTrend - 10/3", "HDFCBANK", {"charge_model": "indian_equity_delivery", "brokerage_pct": 0.0003}),
        ("RSI Reversal - Classic", "INFY", {}),
        ("NIFTY Momentum", "NIFTY50", {}),
        ("Aroon Trend", "MARUTI", {}),
        ("Parabolic SAR Trend", "TATAMOTORS", {}),
        ("CCI Trend", "SUNPHARMA", {}),
    ]
    backtest_ids = []
    for strategy_name, symbol, extra in runs:
        payload = {
            "strategy_id": strategy_ids[strategy_name],
            "name": f"{strategy_name} - {symbol}",
            "symbols": [symbol],
            "start_date": start_date,
            "end_date": end_date,
            "benchmark_symbol": "NIFTY50",
            **extra,
        }
        r = client.post("/backtests", json=payload)
        r.raise_for_status()
        backtest_id = r.json()["id"]
        backtest_ids.append(backtest_id)
        print(f"    started backtest {backtest_id} ({strategy_name} on {symbol})")

    print("==> Waiting for backtests to complete...")
    for backtest_id in backtest_ids:
        for _ in range(30):
            status = client.get(f"/backtests/{backtest_id}/status").json()
            if status["status"] in ("completed", "failed"):
                break
            time.sleep(1)
        print(f"    backtest {backtest_id}: {status['status']}")
        if status["status"] == "completed":
            metrics = client.get(f"/backtests/{backtest_id}/metrics").json()
            print(
                f"        total_return={metrics['total_return_pct']:.2f}%  "
                f"sharpe={metrics['sharpe_ratio']:.2f}  max_dd={metrics['max_drawdown_pct']:.2f}%"
            )

    print("\nDone. Log in at the frontend with:")
    print(f"    email:    {DEMO_EMAIL}")
    print(f"    password: {DEMO_PASSWORD}")


if __name__ == "__main__":
    main()
