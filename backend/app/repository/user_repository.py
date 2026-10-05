import uuid
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.user import UserModel, UserRole


class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, user: UserModel) -> UserModel:
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def update(self, user: UserModel) -> UserModel:
        self.db.commit()
        self.db.refresh(user)
        return user

    def delete(self, user: UserModel) -> None:
        self.db.delete(user)
        self.db.commit()

    def get_by_email(self, email: str) -> UserModel | None:
        return self.db.query(UserModel).filter(UserModel.email == email).first()

    def get_by_id(self, user_id: uuid.UUID) -> UserModel | None:
        return self.db.query(UserModel).filter(UserModel.id == user_id).first()

    def get_by_password_reset_hash(self, token_hash: str) -> UserModel | None:
        return self.db.query(UserModel).filter(UserModel.password_reset_token_hash == token_hash).first()

    def set_refresh_token_hash(self, user: UserModel, token_hash: str | None) -> None:
        user.current_refresh_token_hash = token_hash
        self.db.commit()

    def count_by_role(self, role: UserRole) -> int:
        return self.db.query(func.count(UserModel.id)).filter(UserModel.role == role).scalar()
    
    def list_farmers(self) -> list[UserModel]:
        return (
            self.db.query(UserModel)
            .filter(UserModel.role == UserRole.farmer)
            .order_by(UserModel.created_at.asc())
            .all()
        )