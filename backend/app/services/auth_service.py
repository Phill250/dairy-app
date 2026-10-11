import uuid
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status

from app.repository.user_repository import UserRepository
from app.models.user import UserModel, UserRole
from app.schemas.user import FarmerRegister, AdminRegister
from app.core.config import settings
from app.core.logging_config import security_logger
from app.core.security import (
    hash_password, verify_password, validate_password_length,
    create_access_token, create_refresh_token, hash_token, decode_token,
    create_password_reset_token,
)
from fastapi import Request
from app.core.security import create_mfa_token
from app.services import totp_service

RESET_RESEND_COOLDOWN_SECONDS = 60


def _as_utc(dt: datetime) -> datetime:
    """SQLite returns naive datetimes (stored as UTC); Postgres returns aware ones in the
    connection's time zone. Normalise both to aware UTC so comparisons are always correct."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


class AuthService:
    def __init__(self, repository: UserRepository):
        self.repository = repository

    def register_farmer(self, user_in: FarmerRegister) -> UserModel:
        return self._register(user_in, role=UserRole.farmer)

    def register_admin(self, user_in: AdminRegister) -> UserModel:
        return self._register(user_in, role=UserRole.admin)

    def _register(self, user_in: FarmerRegister | AdminRegister, role: UserRole) -> UserModel:
        existing = self.repository.get_by_email(user_in.email)
        if existing:
            raise HTTPException(status_code=400, detail="Could not register with the provided details")

        user = UserModel(
            first_name=user_in.first_name,
            last_name=user_in.last_name,
            email=user_in.email,
            hashed_password=hash_password(user_in.password),
            role=role,
        )
        created = self.repository.create(user)
        security_logger.info(f"New {role.value} account registered: {created.email}")
        return created

    def authenticate_and_issue_tokens(self, email: str, password: str) -> dict:
        invalid_creds = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
        user = self.repository.get_by_email(email)

        if user is not None and user.locked_until is not None:
            if _as_utc(user.locked_until) > datetime.now(timezone.utc):
                security_logger.warning(f"Login attempt on locked account: {email}")
                raise HTTPException(
                    status_code=status.HTTP_423_LOCKED,
                    detail="Account temporarily locked due to repeated failed attempts. Try again later.",
                )

        if not user or not verify_password(password, user.hashed_password):
            if user is not None:
                self._register_failure(user, email)
            raise invalid_creds

        if user.totp_enabled:
            # Do NOT reset the failure counter yet: it is cleared only after the second
            # factor succeeds, so an attacker who knows the password can't reset the
            # lockout by logging in again between code guesses.
            security_logger.info(f"Password accepted, 2FA required: {email}")
            return {"mfa_required": True, "mfa_token": create_mfa_token(str(user.id))}

        user.failed_login_attempts = 0
        user.locked_until = None
        self.repository.update(user)
        security_logger.info(f"Successful login: {email}")
        return self._issue_tokens(user)

        access_token = create_access_token(subject=str(user.id), role=user.role.value)
        raw_refresh, hashed_refresh, _expires_at = create_refresh_token(subject=str(user.id))
        self.repository.set_refresh_token_hash(user, hashed_refresh)
        return {"access_token": access_token, "refresh_token": raw_refresh}

    def refresh_access_token(self, raw_refresh_token: str) -> dict:
        invalid = HTTPException(status_code=401, detail="Invalid or expired refresh token")
        try:
            payload = decode_token(raw_refresh_token)
        except Exception:
            raise invalid

        if payload.get("type") != "refresh":
            raise invalid

        try:
            user_id = uuid.UUID(payload["sub"])
        except (ValueError, KeyError):
            raise invalid

        user = self.repository.get_by_id(user_id)
        if user is None or user.current_refresh_token_hash is None:
            raise invalid

        if hash_token(raw_refresh_token) != user.current_refresh_token_hash:
            security_logger.warning(f"Reused/invalid refresh token presented for user {user_id}")
            raise invalid

        access_token = create_access_token(subject=str(user.id), role=user.role.value)
        raw_new_refresh, hashed_new_refresh, _expires_at = create_refresh_token(subject=str(user.id))
        self.repository.set_refresh_token_hash(user, hashed_new_refresh)
        return {"access_token": access_token, "refresh_token": raw_new_refresh}

    def logout(self, raw_refresh_token: str) -> None:
        try:
            payload = decode_token(raw_refresh_token)
            user_id = uuid.UUID(payload.get("sub", ""))
        except Exception:
            return

        user = self.repository.get_by_id(user_id)
        if user is not None:
            self.repository.set_refresh_token_hash(user, None)
            security_logger.info(f"User logged out: {user.email}")

    def request_password_reset(self, email: str) -> tuple[str, str] | None:
        """
        Returns (email, raw_token) if a new link should be emailed, otherwise None.
        The router gives the same response either way, so callers can't tell whether
        an account exists or whether this request was skipped by the cooldown.
        """
        user = self.repository.get_by_email(email)
        if user is None:
            security_logger.info(f"Password reset requested for unknown email: {email}")
            return None

        # Cooldown: the expiry time is issued_at + token lifetime, so issued_at can be recovered from it
        if user.password_reset_expires_at is not None:
            issued_at = _as_utc(user.password_reset_expires_at) - timedelta(
                minutes=settings.password_reset_token_expire_minutes
            )
            if datetime.now(timezone.utc) < issued_at + timedelta(seconds=RESET_RESEND_COOLDOWN_SECONDS):
                security_logger.info(f"Password reset requested again too soon for {email}; no email sent")
                return None

        raw_token, hashed_token, expires_at = create_password_reset_token()
        user.password_reset_token_hash = hashed_token
        user.password_reset_expires_at = expires_at
        self.repository.update(user)
        security_logger.info(f"Password reset requested for {email}")
        return user.email, raw_token

    def reset_password(self, raw_token: str, new_password: str) -> None:
        validate_password_length(new_password)
        token_hash = hash_token(raw_token)
        user = self.repository.get_by_password_reset_hash(token_hash)

        invalid = HTTPException(status_code=400, detail="Invalid or expired reset token")
        if user is None or user.password_reset_expires_at is None:
            raise invalid
        if _as_utc(user.password_reset_expires_at) < datetime.now(timezone.utc):
            raise invalid

        user.hashed_password = hash_password(new_password)
        user.password_reset_token_hash = None
        user.password_reset_expires_at = None
        user.current_refresh_token_hash = None  # force re-login everywhere
        user.failed_login_attempts = 0
        user.locked_until = None
        self.repository.update(user)
        security_logger.info(f"Password successfully reset for {user.email}")
    def _register_failure(self, user: UserModel, who: str) -> None:
        user.failed_login_attempts += 1
        if user.failed_login_attempts >= settings.max_failed_login_attempts:
            user.locked_until = datetime.now(timezone.utc) + timedelta(
                minutes=settings.lockout_duration_minutes
            )
            security_logger.warning(f"Account locked after {user.failed_login_attempts} failed attempts: {who}")
        else:
            security_logger.info(f"Failed login attempt for {who}")
        self.repository.update(user)

    def _issue_tokens(self, user: UserModel) -> dict:
        access_token = create_access_token(subject=str(user.id), role=user.role.value)
        raw_refresh, hashed_refresh, _ = create_refresh_token(subject=str(user.id))
        self.repository.set_refresh_token_hash(user, hashed_refresh)
        return {"access_token": access_token, "refresh_token": raw_refresh}
    def complete_2fa_login(self, mfa_token: str, code: str) -> dict:
        invalid = HTTPException(status_code=401, detail="Invalid or expired code")
        try:
            payload = decode_token(mfa_token)
            if payload.get("type") != "mfa":
                raise invalid
            user = self.repository.get_by_id(uuid.UUID(payload["sub"]))
        except HTTPException:
            raise
        except Exception:
            raise invalid
        if user is None or not user.totp_enabled:
            raise invalid

        if user.locked_until is not None and _as_utc(user.locked_until) > datetime.now(timezone.utc):
            raise HTTPException(status_code=status.HTTP_423_LOCKED,
                                detail="Account temporarily locked due to repeated failed attempts. Try again later.")

        if not (totp_service.verify_code(user, code) or totp_service.consume_recovery_code(user, code)):
            self._register_failure(user, f"{user.email} (2FA)")
            raise invalid

        user.failed_login_attempts = 0
        user.locked_until = None
        self.repository.update(user)   # also saves totp_last_step / used recovery code
        security_logger.info(f"Successful login with 2FA: {user.email}")
        return self._issue_tokens(user)

    def begin_2fa_setup(self, user: UserModel) -> dict:
        if user.totp_enabled:
            raise HTTPException(status_code=400, detail="Two-factor authentication is already enabled")
        secret = totp_service.new_secret()
        user.totp_secret_encrypted = totp_service.encrypt(secret)
        user.totp_last_step = None
        self.repository.update(user)
        security_logger.info(f"2FA setup started: {user.email}")
        return {"secret": secret, "otpauth_uri": totp_service.provisioning_uri(secret, user.email)}

    def enable_2fa(self, user: UserModel, code: str) -> list[str]:
        if user.totp_enabled or not user.totp_secret_encrypted:
            raise HTTPException(status_code=400, detail="Start 2FA setup first")
        if not totp_service.verify_code(user, code):
            raise HTTPException(status_code=400, detail="That code is not valid. Check your phone's clock and try again.")
        user.totp_enabled = True
        codes = totp_service.generate_recovery_codes(user)
        self.repository.update(user)
        security_logger.info(f"2FA enabled: {user.email}")
        return codes