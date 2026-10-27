"""Auth API + AuthService coverage — password reset, email verification, refresh
rotation/revocation, and the httpOnly-cookie option were previously the least
tested surface in the codebase (auth_service.py sat at 42% coverage) despite
being the most security-sensitive module."""

import pytest

from app.services.auth_service import AuthService
from app.utils.exceptions import TokenError


def _get_db_session():
    """Auth flows that mock email delivery (password reset, email verification)
    never return the token over HTTP — it's only ever logged, by design (see
    AuthService's module docstring). Reaching it in a test means going through the
    service directly, against the same session the `client` fixture monkeypatched."""
    import app.api.deps as deps_module

    return deps_module.SessionLocal()


def test_register_rejects_duplicate_email(client):
    payload = {"email": "dup@example.com", "username": "dupuser", "password": "password123"}
    r1 = client.post("/api/v1/auth/register", json=payload)
    assert r1.status_code == 201

    r2 = client.post("/api/v1/auth/register", json={**payload, "username": "differentuser"})
    assert r2.status_code == 409


def test_register_rejects_duplicate_username(client):
    payload = {"email": "userone@example.com", "username": "sharedname", "password": "password123"}
    client.post("/api/v1/auth/register", json=payload)

    r = client.post(
        "/api/v1/auth/register",
        json={"email": "usertwo@example.com", "username": "sharedname", "password": "password123"},
    )
    assert r.status_code == 409


def test_login_rejects_wrong_password(client):
    client.post(
        "/api/v1/auth/register",
        json={"email": "wrongpw@example.com", "username": "wrongpw", "password": "correct-password"},
    )
    r = client.post("/api/v1/auth/login", json={"email": "wrongpw@example.com", "password": "incorrect"})
    assert r.status_code == 401


def test_login_rejects_unknown_email(client):
    r = client.post("/api/v1/auth/login", json={"email": "nobody@example.com", "password": "whatever123"})
    assert r.status_code == 401


def test_me_requires_authentication(client):
    r = client.get("/api/v1/auth/me")
    assert r.status_code == 401


def test_me_returns_current_user(client, auth_headers):
    r = client.get("/api/v1/auth/me", headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["email"] == "researcher@example.com"


def test_refresh_rotates_token_and_invalidates_the_old_one(client):
    client.post(
        "/api/v1/auth/register",
        json={"email": "rotate@example.com", "username": "rotateuser", "password": "password123"},
    )
    login = client.post("/api/v1/auth/login", json={"email": "rotate@example.com", "password": "password123"})
    old_refresh = login.json()["refresh_token"]

    r1 = client.post("/api/v1/auth/refresh", json={"refresh_token": old_refresh})
    assert r1.status_code == 200
    new_refresh = r1.json()["refresh_token"]
    assert new_refresh != old_refresh

    # The rotated-out token must no longer work — this is what makes rotation meaningful.
    r2 = client.post("/api/v1/auth/refresh", json={"refresh_token": old_refresh})
    assert r2.status_code == 401

    # The new token from rotation must work.
    r3 = client.post("/api/v1/auth/refresh", json={"refresh_token": new_refresh})
    assert r3.status_code == 200


def test_refresh_rejects_garbage_token(client):
    r = client.post("/api/v1/auth/refresh", json={"refresh_token": "not-a-real-jwt"})
    assert r.status_code == 401


def test_refresh_rejects_an_access_token_used_as_refresh(client, auth_headers):
    access_token = auth_headers["Authorization"].split(" ")[1]
    r = client.post("/api/v1/auth/refresh", json={"refresh_token": access_token})
    assert r.status_code == 401


def test_refresh_with_no_token_anywhere_is_rejected(client):
    r = client.post("/api/v1/auth/refresh", json={})
    assert r.status_code == 401


def test_logout_revokes_the_specific_refresh_token(client):
    client.post(
        "/api/v1/auth/register",
        json={"email": "logout@example.com", "username": "logoutuser", "password": "password123"},
    )
    login = client.post("/api/v1/auth/login", json={"email": "logout@example.com", "password": "password123"})
    tokens = login.json()
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    r = client.post("/api/v1/auth/logout", json={"refresh_token": tokens["refresh_token"]}, headers=headers)
    assert r.status_code == 200

    r2 = client.post("/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert r2.status_code == 401


def test_logout_without_a_token_revokes_every_session_for_the_user(client):
    client.post(
        "/api/v1/auth/register",
        json={"email": "multisession@example.com", "username": "multisession", "password": "password123"},
    )
    login1 = client.post("/api/v1/auth/login", json={"email": "multisession@example.com", "password": "password123"})
    login2 = client.post("/api/v1/auth/login", json={"email": "multisession@example.com", "password": "password123"})
    headers = {"Authorization": f"Bearer {login1.json()['access_token']}"}

    r = client.post("/api/v1/auth/logout", json={}, headers=headers)
    assert r.status_code == 200

    # Both sessions' refresh tokens should now be revoked, not just the one used to log out.
    assert (
        client.post("/api/v1/auth/refresh", json={"refresh_token": login1.json()["refresh_token"]}).status_code == 401
    )
    assert (
        client.post("/api/v1/auth/refresh", json={"refresh_token": login2.json()["refresh_token"]}).status_code == 401
    )


def test_full_password_reset_flow_and_old_password_stops_working(client):
    client.post(
        "/api/v1/auth/register",
        json={"email": "resetflow@example.com", "username": "resetflowuser", "password": "OldPassword123"},
    )
    client.post("/api/v1/auth/forgot-password", json={"email": "resetflow@example.com"})

    db = _get_db_session()
    try:
        reset_token = AuthService(db).request_password_reset("resetflow@example.com")
    finally:
        db.close()
    assert reset_token is not None

    r = client.post("/api/v1/auth/reset-password", json={"token": reset_token, "new_password": "NewPassword456"})
    assert r.status_code == 200

    old_login = client.post("/api/v1/auth/login", json={"email": "resetflow@example.com", "password": "OldPassword123"})
    assert old_login.status_code == 401

    new_login = client.post("/api/v1/auth/login", json={"email": "resetflow@example.com", "password": "NewPassword456"})
    assert new_login.status_code == 200


def test_password_reset_revokes_existing_sessions(client):
    """Resetting a password must invalidate any refresh tokens issued before the reset —
    otherwise a stolen refresh token would survive a password change indefinitely.

    Takes the (unused directly) `client` fixture purely to get the per-test isolated
    database wired up via its monkeypatch — without it, `_get_db_session()` would
    resolve to the real dev database instead of a throwaway per-test one."""
    db = _get_db_session()
    try:
        service = AuthService(db)
        from app.schemas.user import UserCreate

        user = service.register(UserCreate(email="postreset@example.com", username="postreset", password="Password123"))
        tokens = service.issue_token_pair(user)

        reset_token = service.request_password_reset("postreset@example.com")
        service.reset_password(reset_token, "BrandNewPassword456")

        with pytest.raises(TokenError):
            service.refresh_access_token(tokens.refresh_token)
    finally:
        db.close()


def test_reset_password_rejects_garbage_token(client):
    r = client.post("/api/v1/auth/reset-password", json={"token": "garbage", "new_password": "Whatever123"})
    assert r.status_code == 401


def test_full_email_verification_flow(client, auth_headers):
    r = client.get("/api/v1/auth/me", headers=auth_headers)
    assert r.json()["is_verified"] is False

    client.post("/api/v1/auth/send-verification", headers=auth_headers)

    db = _get_db_session()
    try:
        user = AuthService(db).users.get_by_email("researcher@example.com")
        verify_token = AuthService(db).request_email_verification(user)
    finally:
        db.close()

    r = client.post("/api/v1/auth/verify-email", json={"token": verify_token})
    assert r.status_code == 200

    r2 = client.get("/api/v1/auth/me", headers=auth_headers)
    assert r2.json()["is_verified"] is True


def test_verify_email_rejects_a_password_reset_token_used_as_verification(client):
    """Purpose-tokens must not be interchangeable — a password-reset token should
    never verify an email, even though both are signed with the same secret. Takes
    the (unused directly) `client` fixture for the same isolated-DB reason as above."""
    db = _get_db_session()
    try:
        service = AuthService(db)
        from app.schemas.user import UserCreate

        user = service.register(
            UserCreate(email="purposecheck@example.com", username="purposecheck", password="Password123")
        )
        reset_token = service.request_password_reset("purposecheck@example.com")

        with pytest.raises(TokenError):
            service.verify_email(reset_token)
        assert user.is_verified is False
    finally:
        db.close()


def test_forgot_password_does_not_leak_whether_email_exists(client):
    r = client.post("/api/v1/auth/forgot-password", json={"email": "nobody-at-all@example.com"})
    assert r.status_code == 200
    assert "sent" in r.json()["message"].lower()


def test_cookie_based_refresh_flow_when_enabled(client, monkeypatch):
    """AUTH_COOKIE_ENABLED is opt-in and off by default (verified by every other test
    in this file, which never sees a cookie) — this test turns it on and proves the
    httpOnly-cookie path works end to end without needing the token in the body."""
    from app.api.v1.endpoints import auth as auth_endpoint

    monkeypatch.setattr(auth_endpoint.settings, "AUTH_COOKIE_ENABLED", True)
    monkeypatch.setattr(auth_endpoint.settings, "AUTH_COOKIE_SECURE", False)  # TestClient uses plain http

    client.post(
        "/api/v1/auth/register",
        json={"email": "cookieflow@example.com", "username": "cookieflow", "password": "password123"},
    )
    login = client.post("/api/v1/auth/login", json={"email": "cookieflow@example.com", "password": "password123"})
    assert login.status_code == 200
    assert "refresh_token" in login.cookies

    # Omit refresh_token from the body entirely — it must come from the cookie the
    # TestClient is now carrying automatically.
    r = client.post("/api/v1/auth/refresh", json={})
    assert r.status_code == 200
    assert "refresh_token" in r.cookies  # rotated cookie reissued

    headers = {"Authorization": f"Bearer {r.json()['access_token']}"}
    logout = client.post("/api/v1/auth/logout", json={}, headers=headers)
    assert logout.status_code == 200


def _issue_reset_token(email: str) -> str:
    db = _get_db_session()
    try:
        return AuthService(db).request_password_reset(email)
    finally:
        db.close()


def test_reset_token_is_single_use(client):
    client.post(
        "/api/v1/auth/register",
        json={"email": "once@example.com", "username": "onceuser", "password": "OldPassword123"},
    )
    token = _issue_reset_token("once@example.com")

    first = client.post("/api/v1/auth/reset-password", json={"token": token, "new_password": "NewPassword456"})
    assert first.status_code == 200
    replay = client.post("/api/v1/auth/reset-password", json={"token": token, "new_password": "Hijacked789"})
    assert replay.status_code == 401

    login = client.post("/api/v1/auth/login", json={"email": "once@example.com", "password": "NewPassword456"})
    assert login.status_code == 200


def test_password_change_invalidates_outstanding_reset_token(client):
    client.post(
        "/api/v1/auth/register",
        json={"email": "change@example.com", "username": "changeuser", "password": "OldPassword123"},
    )
    token = _issue_reset_token("change@example.com")
    login = client.post("/api/v1/auth/login", json={"email": "change@example.com", "password": "OldPassword123"})
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
    r = client.post(
        "/api/v1/users/me/change-password",
        json={"current_password": "OldPassword123", "new_password": "Changed456"},
        headers=headers,
    )
    assert r.status_code == 200, r.text

    r = client.post("/api/v1/auth/reset-password", json={"token": token, "new_password": "Hijacked789"})
    assert r.status_code == 401


def test_reset_and_verification_tokens_never_reach_the_logs(client, auth_headers, capsys):
    client.post(
        "/api/v1/auth/register",
        json={"email": "quiet@example.com", "username": "quietuser", "password": "Password123"},
    )
    capsys.readouterr()
    token = _issue_reset_token("quiet@example.com")
    client.post("/api/v1/auth/send-verification", headers=auth_headers)
    out = capsys.readouterr()
    logged = out.out + out.err
    assert token not in logged
    assert "mock_email_token" not in logged


def test_forgot_password_writes_reset_link_to_dev_outbox(client):
    from pathlib import Path

    from app.core.config import settings

    client.post(
        "/api/v1/auth/register",
        json={"email": "outbox@example.com", "username": "outboxuser", "password": "OldPassword123"},
    )
    r = client.post("/api/v1/auth/forgot-password", json={"email": "outbox@example.com"})
    assert r.status_code == 200

    mails = list(Path(settings.DEV_OUTBOX_DIR).glob("*.txt"))
    assert len(mails) == 1
    body = mails[0].read_text(encoding="utf-8")
    assert "To: outbox@example.com" in body
    link = next(line for line in body.splitlines() if "/reset-password?token=" in line)
    token = link.split("token=", 1)[1]

    r = client.post("/api/v1/auth/reset-password", json={"token": token, "new_password": "NewPassword456"})
    assert r.status_code == 200


def test_forgot_password_for_unknown_email_sends_nothing(client):
    from pathlib import Path

    from app.core.config import settings

    r = client.post("/api/v1/auth/forgot-password", json={"email": "nobody@example.com"})
    assert r.status_code == 200
    assert not list(Path(settings.DEV_OUTBOX_DIR).glob("*.txt"))
