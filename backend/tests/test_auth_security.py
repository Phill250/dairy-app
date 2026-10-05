from app.repository.user_repository import UserRepository
from app.services.auth_service import AuthService


def register_farmer(client, email="farmer1@example.com", password="CorrectPass123"):
    return client.post("/auth/register", json={
        "first_name": "Test", "last_name": "Farmer", "email": email, "password": password,
    })


def login(client, email, password):
    return client.post("/auth/login", data={"username": email, "password": password})


class TestAccountLockout:
    def test_locks_after_max_failed_attempts(self, client, db_session):
        register_farmer(client, email="lockout@example.com", password="CorrectPass123")

        auth_service = AuthService(UserRepository(db_session))
        for _ in range(5):
            try:
                auth_service.authenticate_and_issue_tokens("lockout@example.com", "WrongPassword")
            except Exception:
                pass

        resp = login(client, "lockout@example.com", "CorrectPass123")
        assert resp.status_code == 423

    def test_successful_login_resets_counter(self, client, db_session):
        register_farmer(client, email="resetcounter@example.com", password="CorrectPass123")

        auth_service = AuthService(UserRepository(db_session))
        for _ in range(3):
            try:
                auth_service.authenticate_and_issue_tokens("resetcounter@example.com", "WrongPassword")
            except Exception:
                pass

        resp = login(client, "resetcounter@example.com", "CorrectPass123")
        assert resp.status_code == 200


class TestJWTValidation:
    def test_rejects_garbage_token(self, client):
        resp = client.get("/api/users/me", headers={"Authorization": "Bearer not-a-real-token"})
        assert resp.status_code == 401

    def test_rejects_missing_token(self, client):
        resp = client.get("/api/users/me")
        assert resp.status_code == 401

    def test_valid_token_works(self, client):
        register_farmer(client, email="validtoken@example.com", password="CorrectPass123")
        tokens = login(client, "validtoken@example.com", "CorrectPass123").json()
        resp = client.get("/api/users/me", headers={"Authorization": f"Bearer {tokens['access_token']}"})
        assert resp.status_code == 200
        assert resp.json()["email"] == "validtoken@example.com"


class TestPasswordResetDoesNotLeakAccountExistence:
    def test_same_response_for_unknown_email(self, client):
        resp = client.post("/auth/forgot-password", json={"email": "doesnotexist@example.com"})
        assert resp.status_code == 202
        assert "sent" in resp.json()["detail"].lower()

    def test_same_response_for_known_email(self, client):
        register_farmer(client, email="knownemail@example.com")
        resp = client.post("/auth/forgot-password", json={"email": "knownemail@example.com"})
        assert resp.status_code == 202
        assert "sent" in resp.json()["detail"].lower()
        
