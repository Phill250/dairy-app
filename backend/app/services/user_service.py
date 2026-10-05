from fastapi import HTTPException, status

from app.repository.user_repository import UserRepository
from app.models.user import UserModel
from app.schemas.user import UserUpdate
from app.core.security import verify_password, hash_password


class UserService:
    def __init__(self, repository: UserRepository):
        self.repository = repository

    def update_self(self, current_user: UserModel, update_in: UserUpdate) -> UserModel:
        wants_sensitive_change = update_in.email is not None or update_in.new_password is not None

        if wants_sensitive_change:
            if not update_in.current_password:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Current password is required to change email or password",
                )
            if not verify_password(update_in.current_password, current_user.hashed_password):
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect password")

        if update_in.first_name is not None:
            current_user.first_name = update_in.first_name
        if update_in.last_name is not None:
            current_user.last_name = update_in.last_name

        if update_in.email is not None and update_in.email != current_user.email:
            existing = self.repository.get_by_email(update_in.email)
            if existing is not None:
                raise HTTPException(status_code=400, detail="Could not update with the provided details")
            current_user.email = update_in.email

        if update_in.new_password is not None:
          
            current_user.hashed_password = hash_password(update_in.new_password)
            current_user.current_refresh_token_hash = None

        return self.repository.update(current_user)

    def delete_self(self, current_user: UserModel, password: str) -> None:
        if not verify_password(password, current_user.hashed_password):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect password")
        self.repository.delete(current_user)