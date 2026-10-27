from fastapi import APIRouter

from app.api.deps import CurrentUser, DbSession
from app.core.security import hash_password, verify_password
from app.repositories.user import UserRepository
from app.schemas.common import Message
from app.schemas.user import PasswordChange, UserRead, UserUpdate
from app.utils.exceptions import AlreadyExistsError, InvalidCredentialsError

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserRead)
def get_profile(user: CurrentUser) -> UserRead:
    return UserRead.model_validate(user)


@router.put("/me", response_model=UserRead)
def update_profile(payload: UserUpdate, user: CurrentUser, db: DbSession) -> UserRead:
    repo = UserRepository(db)
    if payload.username and payload.username != user.username:
        if repo.get_by_username(payload.username):
            raise AlreadyExistsError("This username is already taken")
        user.username = payload.username
    if payload.full_name is not None:
        user.full_name = payload.full_name
    repo.commit()
    return UserRead.model_validate(user)


@router.post("/me/change-password", response_model=Message)
def change_password(payload: PasswordChange, user: CurrentUser, db: DbSession) -> Message:
    if not verify_password(payload.current_password, user.hashed_password):
        raise InvalidCredentialsError("Current password is incorrect")
    user.hashed_password = hash_password(payload.new_password)
    db.commit()
    return Message(message="Password updated successfully")
