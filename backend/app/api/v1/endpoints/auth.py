from fastapi import APIRouter, Request, Response
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.api.deps import CurrentUser, DbSession
from app.core.config import settings
from app.schemas.auth import (
    ForgotPasswordRequest,
    LoginRequest,
    RefreshRequest,
    ResetPasswordRequest,
    TokenPair,
    VerifyEmailRequest,
)
from app.schemas.common import Message
from app.schemas.user import UserCreate, UserRead
from app.services.auth_service import AuthService
from app.utils.exceptions import TokenError

router = APIRouter(prefix="/auth", tags=["auth"])
limiter = Limiter(key_func=get_remote_address)

REFRESH_COOKIE_NAME = "refresh_token"
REFRESH_COOKIE_PATH = f"{settings.API_V1_PREFIX}/auth"


def _set_refresh_cookie(response: Response, refresh_token: str) -> None:
    if not settings.AUTH_COOKIE_ENABLED:
        return
    response.set_cookie(
        key=REFRESH_COOKIE_NAME,
        value=refresh_token,
        httponly=True,
        secure=settings.AUTH_COOKIE_SECURE,
        samesite="lax",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400,
        path=REFRESH_COOKIE_PATH,
    )


@router.post("/register", response_model=UserRead, status_code=201)
@limiter.limit(settings.RATE_LIMIT_AUTH)
def register(request: Request, payload: UserCreate, db: DbSession) -> UserRead:
    user = AuthService(db).register(payload)
    return UserRead.model_validate(user)


@router.post("/login", response_model=TokenPair)
@limiter.limit(settings.RATE_LIMIT_AUTH)
def login(request: Request, response: Response, payload: LoginRequest, db: DbSession) -> TokenPair:
    tokens = AuthService(db).login(payload.email, payload.password)
    _set_refresh_cookie(response, tokens.refresh_token)
    return tokens


@router.post("/refresh", response_model=TokenPair)
def refresh(request: Request, response: Response, payload: RefreshRequest, db: DbSession) -> TokenPair:
    # Bearer-token clients send the refresh token in the body; a cookie-auth client
    # (AUTH_COOKIE_ENABLED) can omit it and rely on the httpOnly cookie instead.
    refresh_token = payload.refresh_token or request.cookies.get(REFRESH_COOKIE_NAME)
    if not refresh_token:
        raise TokenError("No refresh token provided (body or cookie)")
    tokens = AuthService(db).refresh_access_token(refresh_token)
    _set_refresh_cookie(response, tokens.refresh_token)
    return tokens


@router.post("/logout", response_model=Message)
def logout(request: Request, response: Response, payload: RefreshRequest, user: CurrentUser, db: DbSession) -> Message:
    refresh_token = payload.refresh_token or request.cookies.get(REFRESH_COOKIE_NAME)
    AuthService(db).logout(user.id, refresh_token)
    if settings.AUTH_COOKIE_ENABLED:
        response.delete_cookie(key=REFRESH_COOKIE_NAME, path=REFRESH_COOKIE_PATH)
    return Message(message="Logged out successfully")


@router.get("/me", response_model=UserRead)
def me(user: CurrentUser) -> UserRead:
    return UserRead.model_validate(user)


@router.post("/forgot-password", response_model=Message)
@limiter.limit(settings.RATE_LIMIT_AUTH)
def forgot_password(request: Request, payload: ForgotPasswordRequest, db: DbSession) -> Message:
    # Mocked email delivery — see AuthService.request_password_reset docstring.
    AuthService(db).request_password_reset(payload.email)
    return Message(message="If that email exists, a password reset link has been sent")


@router.post("/reset-password", response_model=Message)
def reset_password(payload: ResetPasswordRequest, db: DbSession) -> Message:
    AuthService(db).reset_password(payload.token, payload.new_password)
    return Message(message="Password has been reset successfully")


@router.post("/send-verification", response_model=Message)
def send_verification(user: CurrentUser, db: DbSession) -> Message:
    AuthService(db).request_email_verification(user)
    return Message(message="Verification email sent (mocked — check server logs)")


@router.post("/verify-email", response_model=Message)
def verify_email(payload: VerifyEmailRequest, db: DbSession) -> Message:
    AuthService(db).verify_email(payload.token)
    return Message(message="Email verified successfully")
