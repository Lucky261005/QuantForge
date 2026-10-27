"""Market data is shared by every user: normal users may only add bars, admins may
also overwrite, and CSV uploads are size-capped."""

import io

import pandas as pd

from app.core.config import settings


def _csv(close: float, n: int = 5) -> bytes:
    dates = pd.bdate_range("2024-01-01", periods=n)
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
    return buf.getvalue()


def _upload(client, headers, close: float, n: int = 5):
    files = {"file": ("ACME.csv", _csv(close, n), "text/csv")}
    return client.post("/api/v1/assets/upload?symbol=ACME", files=files, headers=headers)


def _closes(client, headers) -> list[float]:
    r = client.get("/api/v1/assets/ACME/data?start_date=2024-01-01&end_date=2024-12-31", headers=headers)
    assert r.status_code == 200, r.text
    return [bar["close"] for bar in r.json()["bars"]]


def _admin_headers(client) -> dict:
    from app.api import deps
    from app.models.user import User, UserRole

    client.post(
        "/api/v1/auth/register",
        json={"email": "admin@example.com", "username": "admin", "password": "password123"},
    )
    with deps.SessionLocal() as db:
        user = db.query(User).filter_by(email="admin@example.com").one()
        user.role = UserRole.ADMIN
        db.commit()
    r = client.post("/api/v1/auth/login", json={"email": "admin@example.com", "password": "password123"})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def test_user_upload_adds_new_bars_but_never_overwrites_existing(client, auth_headers):
    assert _upload(client, auth_headers, close=100.0).json()["bars_written"] == 5

    # Same 5 dates with a different price, plus 2 new dates.
    r = _upload(client, auth_headers, close=999.0, n=7)
    assert r.status_code == 200, r.text
    assert r.json()["bars_written"] == 2

    assert _closes(client, auth_headers) == [100.0] * 5 + [999.0] * 2


def test_admin_upload_overwrites_existing_bars(client, auth_headers):
    _upload(client, auth_headers, close=100.0)
    admin = _admin_headers(client)

    r = _upload(client, admin, close=250.0)
    assert r.status_code == 200, r.text
    assert r.json()["bars_written"] == 5
    assert _closes(client, auth_headers) == [250.0] * 5


def test_user_upload_cannot_replace_asset_metadata(client, auth_headers):
    files = {"file": ("ACME.csv", _csv(100.0), "text/csv")}
    client.post("/api/v1/assets/upload?symbol=ACME&sector=Energy", files=files, headers=auth_headers)
    files = {"file": ("ACME.csv", _csv(100.0), "text/csv")}
    r = client.post("/api/v1/assets/upload?symbol=ACME&sector=Banking", files=files, headers=auth_headers)
    assert r.json()["asset"]["sector"] == "Energy"


def test_oversized_upload_is_rejected_and_writes_nothing(client, auth_headers, monkeypatch):
    monkeypatch.setattr(settings, "MAX_CSV_UPLOAD_BYTES", 100)
    r = _upload(client, auth_headers, close=100.0)
    assert r.status_code == 413
    r = client.get("/api/v1/assets/ACME/data?start_date=2024-01-01&end_date=2024-12-31", headers=auth_headers)
    assert r.status_code == 404 or r.json()["bars"] == []


def test_synthetic_upload_is_flagged_on_the_asset(client, auth_headers):
    files = {"file": ("DEMO.csv", _csv(100.0), "text/csv")}
    client.post("/api/v1/assets/upload?symbol=DEMO&synthetic=true", files=files, headers=auth_headers)
    _upload(client, auth_headers, close=100.0)  # ACME: a normal CSV upload

    flags = {a["symbol"]: a["is_synthetic"] for a in client.get("/api/v1/assets", headers=auth_headers).json()["items"]}
    assert flags == {"DEMO": True, "ACME": False}
