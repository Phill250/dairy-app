"""
One-time bootstrap: creates the FIRST admin account directly in the
database, bypassing the API (no admin token can exist yet to authorize
creating one via the normal endpoint).

Run manually, once, with server/terminal access only:
    python -m scripts.create_first_admin
"""
import getpass
import sys

from app.core.database import SessionLocal
from app.models.user import UserModel, UserRole
from app.core.security import hash_password


def main():
    db = SessionLocal()
    try:
        existing = db.query(UserModel).filter(UserModel.role == UserRole.admin).first()
        if existing:
            print(f"An admin already exists ({existing.email}). Aborting — "
                  f"use /auth/register-admin with that account's token instead.")
            sys.exit(1)

        print("Creating the first admin account.")
        first_name = input("First name: ").strip()
        last_name = input("Last name: ").strip()
        email = input("Email: ").strip()
        password = getpass.getpass("Password (input hidden): ")
        confirm = getpass.getpass("Confirm password: ")

        if password != confirm:
            print("Passwords did not match. Aborting.")
            sys.exit(1)
        if len(password) < 8:
            print("Password must be at least 8 characters. Aborting.")
            sys.exit(1)
        if not first_name or not last_name:
            print("First and last name are required. Aborting.")
            sys.exit(1)

        if db.query(UserModel).filter(UserModel.email == email).first():
            print(f"A user with email {email} already exists. Aborting.")
            sys.exit(1)

        admin = UserModel(
            first_name=first_name,
            last_name=last_name,
            email=email,
            hashed_password=hash_password(password),
            role=UserRole.admin,
        )
        db.add(admin)
        db.commit()
        db.refresh(admin)
        print(f"Created admin #{admin.id} ({admin.email}). They can now log in via POST /auth/login.")
    finally:
        db.close()


if __name__ == "__main__":
    main()