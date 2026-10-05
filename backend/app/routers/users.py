from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.repository.user_repository import UserRepository
from app.services.user_service import UserService
from app.schemas.user import UserRead, UserUpdate, AccountDeleteRequest
from app.models.user import UserModel

router = APIRouter(prefix="/api/users", tags=["users"])


def get_user_service(db: Session = Depends(get_db)) -> UserService:
    return UserService(UserRepository(db))


@router.get("/me", response_model=UserRead)
def read_own_profile(current_user: UserModel = Depends(get_current_user)):
    return current_user


@router.patch("/me", response_model=UserRead)
def update_own_profile(
    update_in: UserUpdate,
    service: UserService = Depends(get_user_service),
    current_user: UserModel = Depends(get_current_user),
):
    return service.update_self(current_user, update_in)


@router.delete("/me", status_code=204)
def delete_own_account(
    payload: AccountDeleteRequest,
    service: UserService = Depends(get_user_service),
    current_user: UserModel = Depends(get_current_user),
):
    service.delete_self(current_user, payload.password)