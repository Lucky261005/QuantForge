"""Phase 5: security regression tests (input validation, PII in logs, headers) and
coverage for access-control and rate-limit boundaries. Every test runs against the
conftest client's fresh temporary database."""

from datetime import timedelta

import pytest

from tests.utils import synthetic_csv

LIST_ENDPOINTS = [
    "/api/v1/assets",
    "/api/v1/backtests",
    "/api/v1/notes",
    "/api/v1/strategies",
    "/api/v1/portfolio/transactions",
]


def _user(client, n: int) -> dict:
    email = f"user{n}@example.com"
    client.post("/api/v1/auth/register", json={"email": email, "username": f"user{n}", "password": "password123"})
    token = client.post("/api/v1/auth/login", json={"email": email, "password": "password123"}).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _reset_token(email: str, expires: timedelta | None = None) -> str:
    import app.api.deps as deps
    from app.core import security
    from app.models.user import User
    from app.services.auth_service import AuthService

    with deps.SessionLocal() as db:
        if expires is None:
            return AuthService(db).request_password_reset(email)
        user = db.query(User).filter_by(email=email).one()
        return security.create_purpose_token(
            user.id, "password_reset", expires, {"pwv": security.password_fingerprint(user.hashed_password)}
        )


# ---------- confirmed defects ----------


def test_password_reset_enforces_the_same_length_rule_as_registration(client):
    _user(client, 1)
    token = _reset_token("user1@example.com")
    r = client.post("/api/v1/auth/reset-password", json={"token": token, "new_password": "a"})
    assert r.status_code == 422
    # The rejected attempt must not have consumed or changed anything: the old password still works.
    r = client.post("/api/v1/auth/login", json={"email": "user1@example.com", "password": "password123"})
    assert r.status_code == 200


@pytest.mark.parametrize("query", ["page_size=0", "page_size=-5", "page_size=201", "page=0", "page=-1"])
@pytest.mark.parametrize("endpoint", LIST_ENDPOINTS)
def test_list_endpoints_reject_out_of_range_pagination(client, auth_headers, endpoint, query):
    # page_size=0 used to crash with ZeroDivisionError (500); negative sizes returned every row.
    r = client.get(f"{endpoint}?{query}", headers=auth_headers)
    assert r.status_code == 422


@pytest.mark.parametrize("endpoint", LIST_ENDPOINTS)
def test_list_endpoints_accept_the_largest_page_the_ui_requests(client, auth_headers, endpoint):
    assert client.get(f"{endpoint}?page=1&page_size=200", headers=auth_headers).status_code == 200


def test_upload_rejects_symbols_longer_than_the_column(client, auth_headers):
    files = {"file": ("x.csv", synthetic_csv(1, n=5), "text/csv")}
    r = client.post(f"/api/v1/assets/upload?symbol={'X' * 21}", files=files, headers=auth_headers)
    assert r.status_code == 422


def test_registration_does_not_log_the_email_address(client, capsys):
    capsys.readouterr()
    client.post(
        "/api/v1/auth/register", json={"email": "private@example.com", "username": "private", "password": "password123"}
    )
    out = capsys.readouterr()
    assert "private@example.com" not in out.out + out.err


def test_api_responses_carry_baseline_security_headers(client):
    r = client.get("/api/v1/health")
    assert r.headers.get("x-content-type-options") == "nosniff"
    assert r.headers.get("x-frame-options") == "DENY"
    assert r.headers.get("referrer-policy") == "no-referrer"


# ---------- boundary coverage (behaviour verified correct; previously untested) ----------


def test_expired_reset_token_is_rejected(client):
    _user(client, 1)
    token = _reset_token("user1@example.com", expires=timedelta(seconds=-1))
    r = client.post("/api/v1/auth/reset-password", json={"token": token, "new_password": "NewPassword456"})
    assert r.status_code == 401


def test_forgot_password_answers_identically_for_known_and_unknown_emails(client):
    _user(client, 1)
    known = client.post("/api/v1/auth/forgot-password", json={"email": "user1@example.com"})
    unknown = client.post("/api/v1/auth/forgot-password", json={"email": "nobody@example.com"})
    assert (known.status_code, known.json()) == (unknown.status_code, unknown.json())


def test_user_cannot_read_change_or_delete_another_users_notes_and_strategies(client):
    owner, other = _user(client, 1), _user(client, 2)
    note = client.post("/api/v1/notes", json={"title": "private", "content": "c"}, headers=owner).json()["id"]
    strategy = client.post(
        "/api/v1/strategies", json={"name": "s", "strategy_type": "buy_and_hold", "parameters": {}}, headers=owner
    ).json()["id"]

    for path, body in [
        (f"/api/v1/notes/{note}", {"title": "x", "content": "y"}),
        (f"/api/v1/strategies/{strategy}", {"name": "x"}),
    ]:
        assert client.get(path, headers=other).status_code == 403
        assert client.put(path, json=body, headers=other).status_code == 403
        assert client.delete(path, headers=other).status_code == 403
        assert client.get(path, headers=owner).status_code == 200  # untouched for the owner

    assert note not in [n["id"] for n in client.get("/api/v1/notes", headers=other).json()["items"]]


def test_user_cannot_see_or_delete_another_users_backtest(client):
    owner, other = _user(client, 1), _user(client, 2)
    client.post(
        "/api/v1/assets/upload?symbol=ACME", files={"file": ("a.csv", synthetic_csv(1), "text/csv")}, headers=owner
    )
    strategy = client.post(
        "/api/v1/strategies", json={"name": "s", "strategy_type": "buy_and_hold", "parameters": {}}, headers=owner
    ).json()["id"]
    backtest = client.post(
        "/api/v1/backtests",
        json={"strategy_id": strategy, "symbols": ["ACME"], "start_date": "2022-01-03", "end_date": "2022-12-30"},
        headers=owner,
    ).json()["id"]

    for suffix in ["", "/status", "/metrics", "/equity", "/trades"]:
        assert client.get(f"/api/v1/backtests/{backtest}{suffix}", headers=other).status_code == 403, suffix
    assert client.delete(f"/api/v1/backtests/{backtest}", headers=other).status_code == 403
    assert (
        client.post("/api/v1/analytics/compare", json={"backtest_ids": [backtest, backtest]}, headers=other).status_code
        == 403
    )
    assert client.get(f"/api/v1/backtests/{backtest}", headers=owner).status_code == 200


def test_login_is_rate_limited(client):
    from app.api.v1.endpoints import auth

    _user(client, 1)
    auth.limiter.enabled = True
    auth.limiter.reset()
    try:
        codes = [
            client.post(
                "/api/v1/auth/login", json={"email": "user1@example.com", "password": "wrong-password"}
            ).status_code
            for _ in range(11)
        ]
    finally:
        auth.limiter.reset()
        auth.limiter.enabled = False
    assert codes[:10] == [401] * 10
    assert codes[10] == 429
