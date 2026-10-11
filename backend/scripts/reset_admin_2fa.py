"""
Emergency recovery: switches OFF two-factor authentication for one admin
account (for example after a lost phone with no recovery codes left).
Also signs that admin out everywhere.

Run manually, with server/terminal access only:
    python -m scripts.reset_admin_2fa
"""
import sys

from app.core.database import SessionLocal
from app.models.user import UserModel, UserRole


def main():
    db = SessionLocal()
    try:
        email = input("Admin email to reset 2FA for: ").strip()
        user = (
            db.query(UserModel)
            .filter(UserModel.email == email, UserModel.role == UserRole.admin)
            .first()
        )
        if user is None:
            print("No admin account with that email. Aborting.")
            sys.exit(1)
        if not user.totp_enabled and not user.totp_secret_encrypted:
            print("2FA is not set up for this account. Nothing to do.")
            return

        if input(f"Turn off 2FA for {user.email}? Type YES to confirm: ").strip() != "YES":
            print("Cancelled.")
            return

        user.totp_enabled = False
        user.totp_secret_encrypted = None
        user.totp_last_step = None
        user.recovery_code_hashes = None
        user.current_refresh_token_hash = None   # force a fresh login everywhere
        db.commit()
        print(f"2FA cleared for {user.email}. Log in with the password, then enrol again.")
    finally:
        db.close()


if __name__ == "__main__":
    main()