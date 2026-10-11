import time
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pyotp
from jose import jwt

from app.core import security
from app.core.config import settings
from app.core.security import hash_password
from app.models.user import UserModel, UserRole
from app.services import totp_service


PASSWORD = "CorrectPass123"


# ---------- helpers ----------
def make_admin(db, email):
    admin = UserModel(first_name="Ada", last_name="Min", email=email,
                      hashed_password=hash_password(PASSWORD), role=UserRole.admin)
    db.add(admin)
    db.commit()
    db.refresh(admin)
    return admin


def login(client, email, password=PASSWORD):
    return client.post("/auth/login", data={"username": email, "password": password})


def bearer(resp):
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


def enrol(client, email):
    """Returns (totp, recovery_codes) for an admin who is now enrolled."""
    headers = bearer(login(client, email))
    setup = client.post("/auth/2fa/setup", headers=headers).json()
    totp = pyotp.TOTP(setup["secret"])
    r = client.post("/auth/2fa/enable", json={"code": totp.now()}, headers=headers)
    assert r.status_code == 200
    return totp, r.json()["recovery_codes"]


def next_code(totp):
    """A code from the next 30s window: valid now, and newer than the one used to enrol."""
    return totp.at(int(time.time()) + 30)


def verify(client, mfa_token, code):
    return client.post("/auth/login/verify-2fa", json={"mfa_token": mfa_token, "code": code})


def register_farmer(client, email):
    client.post("/auth/register", json={"first_name": "Test", "last_name": "User",
                                        "email": email, "password": PASSWORD})
    return login(client, email)


# ---------- unit tests for the helper module ----------
class TestTotpServiceUnit:
    def test_recovery_codes_are_single_use(self):
        user = SimpleNamespace(recovery_code_hashes=None)
        codes = totp_service.generate_recovery_codes(user)
        assert len(codes) == 8
        assert totp_service.consume_recovery_code(user, codes[0]) is True
        assert totp_service.consume_recovery_code(user, codes[0]) is False

    def test_recovery_codes_are_stored_hashed(self):
        user = SimpleNamespace(recovery_code_hashes=None)
        codes = totp_service.generate_recovery_codes(user)
        assert all(c not in user.recovery_code_hashes for c in codes)

    def test_secret_round_trips_through_encryption(self):
        secret = totp_service.new_secret()
        token = totp_service.encrypt(secret)
        assert token != secret
        assert totp_service.decrypt(token) == secret


# ---------- enrolment ----------
class TestEnrolment:
    def test_admin_can_enrol_and_gets_eight_recovery_codes(self, client, db_session):
        make_admin(db_session, "enrol1@example.com")
        _totp, codes = enrol(client, "enrol1@example.com")
        assert len(codes) == 8

    def test_secret_is_encrypted_at_rest(self, client, db_session):
        admin = make_admin(db_session, "enrol2@example.com")
        headers = bearer(login(client, "enrol2@example.com"))
        secret = client.post("/auth/2fa/setup", headers=headers).json()["secret"]
        db_session.refresh(admin)
        assert admin.totp_secret_encrypted != secret
        assert totp_service.decrypt(admin.totp_secret_encrypted) == secret

    def test_wrong_code_does_not_enable_2fa(self, client, db_session):
        make_admin(db_session, "enrol3@example.com")
        headers = bearer(login(client, "enrol3@example.com"))
        client.post("/auth/2fa/setup", headers=headers)
        assert client.post("/auth/2fa/enable", json={"code": "000000"}, headers=headers).status_code == 400
        assert "access_token" in login(client, "enrol3@example.com").json()   # still plain login

    def test_farmer_cannot_start_setup(self, client):
        headers = bearer(register_farmer(client, "farmer-2fa@example.com"))
        assert client.post("/auth/2fa/setup", headers=headers).status_code == 403


# ---------- login flow ----------
class TestLoginWithTwoFactor:
    def test_password_alone_returns_a_challenge_not_tokens(self, client, db_session):
        make_admin(db_session, "login1@example.com")
        enrol(client, "login1@example.com")
        body = login(client, "login1@example.com").json()
        assert body["mfa_required"] is True
        assert "access_token" not in body and "refresh_token" not in body

    def test_correct_code_issues_tokens(self, client, db_session):
        make_admin(db_session, "login2@example.com")
        totp, _ = enrol(client, "login2@example.com")
        mfa = login(client, "login2@example.com").json()["mfa_token"]
        r = verify(client, mfa, next_code(totp))
        assert r.status_code == 200
        assert "access_token" in r.json() and "refresh_token" in r.json()

    def test_wrong_code_is_rejected(self, client, db_session):
        make_admin(db_session, "login3@example.com")
        enrol(client, "login3@example.com")
        mfa = login(client, "login3@example.com").json()["mfa_token"]
        assert verify(client, mfa, "000000").status_code == 401

    def test_a_used_code_cannot_be_replayed(self, client, db_session):
        make_admin(db_session, "login4@example.com")
        totp, _ = enrol(client, "login4@example.com")
        code = next_code(totp)
        mfa = login(client, "login4@example.com").json()["mfa_token"]
        assert verify(client, mfa, code).status_code == 200
        mfa2 = login(client, "login4@example.com").json()["mfa_token"]
        assert verify(client, mfa2, code).status_code == 401

    def test_recovery_code_works_exactly_once(self, client, db_session):
        make_admin(db_session, "login5@example.com")
        _totp, codes = enrol(client, "login5@example.com")
        mfa = login(client, "login5@example.com").json()["mfa_token"]
        assert verify(client, mfa, codes[0]).status_code == 200
        mfa2 = login(client, "login5@example.com").json()["mfa_token"]
        assert verify(client, mfa2, codes[0]).status_code == 401

    def test_farmer_login_is_unchanged(self, client):
        assert "access_token" in register_farmer(client, "farmer-plain@example.com").json()


# ---------- token confusion ----------
class TestTokenConfusion:
    def test_mfa_token_cannot_be_used_as_an_access_token(self, client, db_session):
        make_admin(db_session, "tok1@example.com")
        enrol(client, "tok1@example.com")
        mfa = login(client, "tok1@example.com").json()["mfa_token"]
        r = client.post("/auth/2fa/setup", headers={"Authorization": f"Bearer {mfa}"})
        assert r.status_code == 401

    def test_access_token_cannot_complete_a_2fa_login(self, client, db_session):
        make_admin(db_session, "tok2@example.com")
        access = bearer(login(client, "tok2@example.com"))["Authorization"].split()[1]
        assert verify(client, access, "123456").status_code == 401

    def test_expired_mfa_token_is_rejected(self, client, db_session):
        admin = make_admin(db_session, "tok3@example.com")
        totp, _ = enrol(client, "tok3@example.com")
        expired = jwt.encode(
            {"sub": str(admin.id), "type": "mfa", "exp": datetime.now(timezone.utc) - timedelta(minutes=1),
             "iss": settings.jwt_issuer, "aud": settings.jwt_audience},
            security._private_key, algorithm=settings.jwt_algorithm,
        )
        assert verify(client, expired, next_code(totp)).status_code == 401


# ---------- lockout ----------
class TestLockout:
    def test_repeated_wrong_codes_lock_the_account(self, client, db_session):
        make_admin(db_session, "lock1@example.com")
        totp, _ = enrol(client, "lock1@example.com")
        mfa = login(client, "lock1@example.com").json()["mfa_token"]
        for _ in range(settings.max_failed_login_attempts):
            assert verify(client, mfa, "000000").status_code == 401
        assert verify(client, mfa, next_code(totp)).status_code == 423
        assert login(client, "lock1@example.com").status_code == 423

    def test_logging_in_again_does_not_reset_the_code_failure_counter(self, client, db_session):
        make_admin(db_session, "lock2@example.com")
        totp, _ = enrol(client, "lock2@example.com")
        mfa = login(client, "lock2@example.com").json()["mfa_token"]
        for _ in range(settings.max_failed_login_attempts - 1):
            assert verify(client, mfa, "000000").status_code == 401
        mfa = login(client, "lock2@example.com").json()["mfa_token"]   # password step again
        assert verify(client, mfa, "000000").status_code == 401         # this one reaches the limit
        assert verify(client, mfa, next_code(totp)).status_code == 423