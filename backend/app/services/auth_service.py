"""Authentication business logic: registration, login, token refresh/rotation,
and mocked password-reset / email-verification flows.

Email delivery is mocked: instead of sending real mail, the generated token is
logged (and echoed back in the API response in non-production environments)
so the flow is fully testable without configuring an SMTP provider.
"""

from datetime import UTC, datetime, timedelta
from pathlib import Path

from sqlalchemy.orm import Session

from app.core import security
from app.core.config import settings
from app.core.logging import get_logger
from app.core.security import TokenType
from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.repositories.user import RefreshTokenRepository, UserRepository
from app.schemas.auth import TokenPair
from app.schemas.user import UserCreate
from app.services.audit_service import AuditService
from app.utils.exceptions import AlreadyExistsError, InvalidCredentialsError, NotFoundError, TokenError

logger = get_logger(__name__)


class AuthService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.users = UserRepository(db)
        self.refresh_tokens = RefreshTokenRepository(db)
        self.audit = AuditService(db)

    def register(self, payload: UserCreate) -> User:
        if self.users.get_by_email(payload.email):
            raise AlreadyExistsError("A user with this email already exists")
        if self.users.get_by_username(payload.username):
            raise AlreadyExistsError("This username is already taken")

        user = User(
            email=payload.email,
            username=payload.username,
            full_name=payload.full_name,
            hashed_password=security.hash_password(payload.password),
        )
        user = self.users.create(user)
        self.users.commit()
        self.audit.record(user_id=user.id, action="user.register", resource_type="user", resource_id=user.id)
        logger.info("user_registered", user_id=user.id)
        return user

    def authenticate(self, email: str, password: str) -> User:
        user = self.users.get_by_email(email)
        if not user or not security.verify_password(password, user.hashed_password):
            raise InvalidCredentialsError("Incorrect email or password")
        if not user.is_active:
            raise InvalidCredentialsError("This account has been deactivated")
        return user

    def issue_token_pair(self, user: User) -> TokenPair:
        access_token = security.create_access_token(user.id, user.role.value)
        refresh_token, jti, expires_at = security.create_refresh_token(user.id)
        self.refresh_tokens.create(RefreshToken(user_id=user.id, jti=jti, expires_at=expires_at))
        self.refresh_tokens.commit()
        return TokenPair(access_token=access_token, refresh_token=refresh_token)

    def login(self, email: str, password: str) -> TokenPair:
        user = self.authenticate(email, password)
        tokens = self.issue_token_pair(user)
        self.audit.record(user_id=user.id, action="user.login", resource_type="user", resource_id=user.id)
        return tokens

    def refresh_access_token(self, refresh_token: str) -> TokenPair:
        try:
            payload = security.decode_token(refresh_token)
        except security.JWTError as exc:
            raise TokenError("Invalid or expired refresh token") from exc

        if not security.is_token_type(payload, TokenType.REFRESH):
            raise TokenError("Token is not a refresh token")

        jti = payload.get("jti")
        stored = self.refresh_tokens.get_by_jti(jti) if jti else None
        if not stored or stored.revoked:
            raise TokenError("Refresh token has been revoked")
        if stored.expires_at.replace(tzinfo=UTC) < datetime.now(UTC):
            raise TokenError("Refresh token has expired")

        user = self.users.get(int(payload["sub"]))
        if not user or not user.is_active:
            raise TokenError("User no longer active")

        # Rotate: revoke the used refresh token and issue a brand new pair.
        self.refresh_tokens.revoke(stored)
        tokens = self.issue_token_pair(user)
        self.refresh_tokens.commit()
        return tokens

    def logout(self, user_id: int, refresh_token: str | None = None) -> None:
        if refresh_token:
            try:
                payload = security.decode_token(refresh_token)
                jti = payload.get("jti")
                stored = self.refresh_tokens.get_by_jti(jti) if jti else None
                if stored:
                    self.refresh_tokens.revoke(stored)
            except security.JWTError:
                pass
        else:
            self.refresh_tokens.revoke_all_for_user(user_id)
        self.refresh_tokens.commit()
        self.audit.record(user_id=user_id, action="user.logout")

    def _deliver_email(self, to: str, subject: str, body: str) -> None:
        """No email provider is configured. Outside production the message is written to
        the dev outbox (a git-ignored folder) so the flow can be completed locally; in
        production nothing is sent. Never logged: the body can carry a live token."""
        if settings.ENVIRONMENT == "production":
            return
        outbox = Path(settings.DEV_OUTBOX_DIR)
        outbox.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%f")
        (outbox / f"{stamp}.txt").write_text(f"To: {to}\nSubject: {subject}\n\n{body}", encoding="utf-8")

    def request_password_reset(self, email: str) -> str | None:
        user = self.users.get_by_email(email)
        if not user:
            # Do not leak whether the email exists.
            return None
        token = security.create_purpose_token(
            user.id,
            "password_reset",
            timedelta(minutes=30),
            extra_claims={"pwv": security.password_fingerprint(user.hashed_password)},
        )
        logger.info("password_reset_requested", user_id=user.id)
        self._deliver_email(
            to=user.email,
            subject="Reset your QuantForge password",
            body=(
                "Use this link within 30 minutes to choose a new password. It works once.\n\n"
                f"{settings.FRONTEND_URL}/reset-password?token={token}\n"
            ),
        )
        self.audit.record(user_id=user.id, action="user.password_reset_requested")
        return token if settings.ENVIRONMENT != "production" else None

    def reset_password(self, token: str, new_password: str) -> None:
        try:
            payload = security.decode_token(token)
        except security.JWTError as exc:
            raise TokenError("Invalid or expired reset token") from exc
        if payload.get("purpose") != "password_reset":
            raise TokenError("Token is not a password-reset token")

        user = self.users.get(int(payload["sub"]))
        if not user:
            raise NotFoundError("User not found")
        # The token carries a fingerprint of the password it was issued against, so once
        # the password changes (by this reset or any other way) the token is spent.
        if payload.get("pwv") != security.password_fingerprint(user.hashed_password):
            raise TokenError("Invalid or expired reset token")

        user.hashed_password = security.hash_password(new_password)
        self.refresh_tokens.revoke_all_for_user(user.id)
        self.users.commit()
        self.audit.record(user_id=user.id, action="user.password_reset_completed")

    def request_email_verification(self, user: User) -> str:
        token = security.create_purpose_token(user.id, "email_verification", timedelta(hours=24))
        logger.info("email_verification_requested", user_id=user.id)
        return token

    def verify_email(self, token: str) -> User:
        try:
            payload = security.decode_token(token)
        except security.JWTError as exc:
            raise TokenError("Invalid or expired verification token") from exc
        if payload.get("purpose") != "email_verification":
            raise TokenError("Token is not an email-verification token")

        user = self.users.get(int(payload["sub"]))
        if not user:
            raise NotFoundError("User not found")

        user.is_verified = True
        self.users.commit()
        self.audit.record(user_id=user.id, action="user.email_verified")
        return user
