"""Shared FastAPI dependencies: DB session, current user, RBAC guards."""

from collections.abc import Generator
from typing import Annotated

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core import security
from app.core.security import TokenType
from app.db.session import SessionLocal
from app.models.user import User, UserRole
from app.repositories.user import UserRepository
from app.utils.exceptions import PermissionDeniedError, TokenError

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


DbSession = Annotated[Session, Depends(get_db)]


def get_current_user(
    db: DbSession,
    token: Annotated[str | None, Depends(oauth2_scheme)],
) -> User:
    if not token:
        raise TokenError("Not authenticated")
    try:
        payload = security.decode_token(token)
    except security.JWTError as exc:
        raise TokenError("Invalid or expired access token") from exc

    if not security.is_token_type(payload, TokenType.ACCESS) or payload.get("purpose"):
        raise TokenError("Token is not a valid access token")

    user = UserRepository(db).get(int(payload["sub"]))
    if not user or not user.is_active:
        raise TokenError("User not found or inactive")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def require_admin(user: CurrentUser) -> User:
    if user.role != UserRole.ADMIN:
        raise PermissionDeniedError("This action requires administrator privileges")
    return user


AdminUser = Annotated[User, Depends(require_admin)]
