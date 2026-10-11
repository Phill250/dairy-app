import enum
import uuid
from sqlalchemy import Boolean, Column, String, Enum, DateTime, Integer, Text, func
from app.core.types import GUID
from app.core.database import Base


class UserRole(str, enum.Enum):
    farmer = "farmer"
    admin = "admin"


class UserModel(Base):
    __tablename__ = "users"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4, index=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    role = Column(Enum(UserRole), nullable=False, default=UserRole.farmer)
    current_refresh_token_hash = Column(String, nullable=True)

    failed_login_attempts = Column(Integer, nullable=False, default=0)
    locked_until = Column(DateTime(timezone=True), nullable=True)
    password_reset_token_hash = Column(String, nullable=True)
    password_reset_expires_at = Column(DateTime(timezone=True), nullable=True)
    totp_secret_encrypted = Column(String, nullable=True)
    totp_enabled = Column(Boolean, nullable=False, server_default="false", default=False)
    totp_last_step = Column(Integer, nullable=True)       # blocks code replay
    recovery_code_hashes = Column(Text, nullable=True)    # JSON list of SHA-256 hashes

    created_at = Column(DateTime(timezone=True), server_default=func.now())