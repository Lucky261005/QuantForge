import numpy as np
import pandas as pd
import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client(tmp_path, monkeypatch):
    """A TestClient wired to an isolated, per-test SQLite database — used by any
    test that exercises the API rather than calling services/repositories directly."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    db_path = tmp_path / "test.db"
    engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
    test_session_local = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    from app.db.base import Base

    Base.metadata.create_all(bind=engine)

    # `get_db` (request-scoped sessions) lives in app.api.deps; the Celery-fallback
    # path in run_backtest_task imports SessionLocal fresh from app.db.session each
    # call, so both need to point at this test's isolated engine.
    import app.api.deps as deps_module
    import app.db.session as session_module

    monkeypatch.setattr(deps_module, "SessionLocal", test_session_local)
    monkeypatch.setattr(session_module, "SessionLocal", test_session_local)

    from app.api.v1.endpoints import assets, auth, backtests, portfolio, strategies

    # Rate limits exist to protect production from abuse — they're not something any
    # test should be subject to. slowapi's @limiter.limit(...) checks the `enabled`
    # flag on whichever Limiter instance decorated that specific route — each
    # endpoint module (auth, assets, backtests, strategies, portfolio) constructs
    # its own Limiter, so app.state.limiter.enabled alone does NOT disable them;
    # every module-level limiter has to be turned off individually. Without this,
    # tests that legitimately call an endpoint many times (e.g. registering/logging
    # in repeatedly across a large auth test file) fail on a shared counter that has
    # nothing to do with what they're actually testing.
    # Emails go to the dev outbox outside production; keep each test's mail in its own folder.
    from app.core.config import settings
    from app.main import app

    monkeypatch.setattr(settings, "DEV_OUTBOX_DIR", str(tmp_path / "outbox"))

    # The cache is a process-wide singleton; give every test its own empty in-memory
    # one so cached OHLCV from an earlier test's database can't leak into this one.
    from app.core import cache as cache_module

    fresh_cache = object.__new__(cache_module.CacheClient)
    fresh_cache._client = cache_module._InMemoryFallback()
    monkeypatch.setattr(cache_module, "_cache_instance", fresh_cache)

    for module in (auth, assets, backtests, strategies, portfolio):
        module.limiter.enabled = False
    app.state.limiter.enabled = False

    return TestClient(app)


@pytest.fixture
def auth_headers(client):
    client.post(
        "/api/v1/auth/register",
        json={"email": "researcher@example.com", "username": "researcher", "password": "password123"},
    )
    r = client.post("/api/v1/auth/login", json={"email": "researcher@example.com", "password": "password123"})
    token = r.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def ohlcv_df() -> pd.DataFrame:
    """250 trading days of synthetic-but-plausible OHLCV data, seeded for determinism."""
    rng = np.random.default_rng(42)
    n = 250
    dates = pd.bdate_range("2023-01-02", periods=n)
    returns = rng.normal(loc=0.0004, scale=0.012, size=n)
    close = 100 * np.cumprod(1 + returns)
    open_ = close * (1 + rng.normal(0, 0.002, n))
    high = np.maximum(open_, close) * (1 + np.abs(rng.normal(0, 0.004, n)))
    low = np.minimum(open_, close) * (1 - np.abs(rng.normal(0, 0.004, n)))
    volume = rng.integers(1_000_000, 10_000_000, n).astype(float)

    return pd.DataFrame(
        {"open": open_, "high": high, "low": low, "close": close, "adj_close": close, "volume": volume},
        index=dates,
    )
