from datetime import datetime, timedelta, timezone
from pathlib import Path
import hashlib
import secrets

from fastapi import HTTPException
from jose import jwt
from passlib.context import CryptContext

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

_private_key = Path(settings.jwt_private_key_path).read_text()
_public_key = Path(settings.jwt_public_key_path).read_text()


def validate_password_length(password: str) -> None:
    """
    bcrypt silently truncates anything past 72 bytes, meaning the rest of a
    longer password would have zero effect on the resulting hash. Rejecting
    it explicitly is safer than letting someone believe a 100-character
    passphrase is doing more work than it actually is.
    """
    if len(password.encode("utf-8")) > 72:
        raise HTTPException(status_code=400, detail="Password must not exceed 72 bytes")


def hash_password(password: str) -> str:
    validate_password_length(password)
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(subject: str, role: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
    payload = {
        "sub": subject, "role": role, "type": "access", "exp": expire,
        "iss": settings.jwt_issuer, "aud": settings.jwt_audience,
    }
    return jwt.encode(payload, _private_key, algorithm=settings.jwt_algorithm)


def create_refresh_token(subject: str) -> tuple[str, str, datetime]:
    expire = datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_expire_days)
    payload = {
        "sub": subject, "type": "refresh", "exp": expire, "jti": secrets.token_hex(16),
        "iss": settings.jwt_issuer, "aud": settings.jwt_audience,
    }
    raw_token = jwt.encode(payload, _private_key, algorithm=settings.jwt_algorithm)
    hashed = hash_token(raw_token)
    return raw_token, hashed, expire


def create_password_reset_token() -> tuple[str, str, datetime]:
    """
    A separate opaque random token (not a JWT) — kept simple and consistent
    with how refresh tokens are already verified: hash it, store the hash,
    compare hashes on use. No need to decode/verify signature for this one.
    """
    raw = secrets.token_urlsafe(32)
    hashed = hash_token(raw)
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.password_reset_token_expire_minutes)
    return raw, hashed, expires_at


def hash_token(raw_token: str) -> str:
    return hashlib.sha256(raw_token.encode()).hexdigest()


def decode_token(token: str) -> dict:
    """Raises JWTError if invalid/expired/wrong issuer/wrong audience — caller handles it."""
    return jwt.decode(
        token, _public_key, algorithms=[settings.jwt_algorithm],
        issuer=settings.jwt_issuer, audience=settings.jwt_audience,
    )