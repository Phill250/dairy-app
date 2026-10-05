from fastapi import APIRouter, BackgroundTasks, Depends, Request
from app.services.email_service import send_password_reset_email
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.limiter import limiter
from app.core.dependencies import require_role
from app.repository.user_repository import UserRepository
from app.services.auth_service import AuthService
from app.schemas.user import (
    FarmerRegister, AdminRegister, UserRead, Token, RefreshRequest,
    PasswordResetRequest, PasswordResetConfirm,
)
from app.models.user import UserModel, UserRole

router = APIRouter(prefix="/auth", tags=["auth"])


def get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    return AuthService(UserRepository(db))


@router.post("/register", response_model=UserRead, status_code=201)
@limiter.limit("10/hour")
def register_farmer(
    request: Request, user_in: FarmerRegister, service: AuthService = Depends(get_auth_service)
):
    return service.register_farmer(user_in)


@router.post("/register-admin", response_model=UserRead, status_code=201)
@limiter.limit("5/hour")
def register_admin(
    request: Request,
    user_in: AdminRegister,
    service: AuthService = Depends(get_auth_service),
    _current_user: UserModel = Depends(require_role(UserRole.admin)),
):
    return service.register_admin(user_in)


@router.post("/login", response_model=Token)
@limiter.limit("5/minute")
def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    service: AuthService = Depends(get_auth_service),
):
    return service.authenticate_and_issue_tokens(form_data.username, form_data.password)


@router.post("/refresh", response_model=Token)
@limiter.limit("20/minute")
def refresh(request: Request, payload: RefreshRequest, service: AuthService = Depends(get_auth_service)):
    return service.refresh_access_token(payload.refresh_token)


@router.post("/logout", status_code=204)
def logout(payload: RefreshRequest, service: AuthService = Depends(get_auth_service)):
    service.logout(payload.refresh_token)


@router.post("/forgot-password", status_code=202)
@limiter.limit("10/hour")
def forgot_password(
    request: Request,
    payload: PasswordResetRequest,
    background_tasks: BackgroundTasks,
    service: AuthService = Depends(get_auth_service),
):
    result = service.request_password_reset(payload.email)
    if result is not None:
        email, raw_token = result
        background_tasks.add_task(send_password_reset_email, email, raw_token)
    # Identical response whether or not the email exists
    return {"detail": "If that email is registered, a password reset link has been sent."}


@router.post("/reset-password", status_code=200)
@limiter.limit("5/hour")
def reset_password(
    request: Request, payload: PasswordResetConfirm, service: AuthService = Depends(get_auth_service)
):
    service.reset_password(payload.token, payload.new_password)
    return {"detail": "Password has been reset. Please log in with your new password."}