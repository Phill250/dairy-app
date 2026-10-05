from datetime import datetime, timedelta, timezone

import pytest

from app.repository.user_repository import UserRepository


@pytest.fixture()
def sent_emails(monkeypatch):
    """Capture reset emails instead of sending them. Each entry is (email, raw_token)."""
    captured = []
    monkeypatch.setattr(
        "app.routers.auth.send_password_reset_email",
        lambda email, token: captured.append((email, token)),
    )
    return captured


def register(client, email, password="OldPassword123"):
    resp = client.post("/auth/register", json={
        "first_name": "Reset", "last_name": "Tester", "email": email, "password": password,
    })
    assert resp.status_code == 201


def login(client, email, password):
    return client.post("/auth/login", data={"username": email, "password": password})


def request_reset(client, email):
    return client.post("/auth/forgot-password", json={"email": email})


class TestPasswordResetFlow:
    def test_full_flow_changes_the_password(self, client, sent_emails):
        register(client, "reset1@example.com")
        assert request_reset(client, "reset1@example.com").status_code == 202
        assert len(sent_emails) == 1
        _, token = sent_emails[0]

        resp = client.post("/auth/reset-password", json={"token": token, "new_password": "NewPassword456"})
        assert resp.status_code == 200
        assert login(client, "reset1@example.com", "NewPassword456").status_code == 200
        assert login(client, "reset1@example.com", "OldPassword123").status_code == 401

    def test_token_cannot_be_used_twice(self, client, sent_emails):
        register(client, "reset2@example.com")
        request_reset(client, "reset2@example.com")
        _, token = sent_emails[0]

        first = client.post("/auth/reset-password", json={"token": token, "new_password": "NewPassword456"})
        second = client.post("/auth/reset-password", json={"token": token, "new_password": "AnotherPass789"})
        assert first.status_code == 200
        assert second.status_code == 400

    def test_expired_token_is_rejected(self, client, db_session, sent_emails):
        register(client, "reset3@example.com")
        request_reset(client, "reset3@example.com")
        _, token = sent_emails[0]

        user = UserRepository(db_session).get_by_email("reset3@example.com")
        user.password_reset_expires_at = datetime.now(timezone.utc) - timedelta(minutes=1)
        db_session.commit()

        resp = client.post("/auth/reset-password", json={"token": token, "new_password": "NewPassword456"})
        assert resp.status_code == 400

    def test_garbage_token_is_rejected(self, client):
        resp = client.post("/auth/reset-password", json={"token": "not-a-real-token", "new_password": "NewPassword456"})
        assert resp.status_code == 400

    def test_reset_signs_out_existing_sessions(self, client, sent_emails):
        register(client, "reset4@example.com")
        old_refresh = login(client, "reset4@example.com", "OldPassword123").json()["refresh_token"]

        request_reset(client, "reset4@example.com")
        _, token = sent_emails[0]
        client.post("/auth/reset-password", json={"token": token, "new_password": "NewPassword456"})

        assert client.post("/auth/refresh", json={"refresh_token": old_refresh}).status_code == 401

    def test_weak_new_password_is_rejected(self, client, sent_emails):
        register(client, "reset5@example.com")
        request_reset(client, "reset5@example.com")
        _, token = sent_emails[0]
        resp = client.post("/auth/reset-password", json={"token": token, "new_password": "short"})
        assert resp.status_code == 422


class TestForgotPasswordDoesNotLeak:
    def test_unknown_email_sends_nothing_but_looks_identical(self, client, sent_emails):
        register(client, "reset6@example.com")
        known = request_reset(client, "reset6@example.com")
        unknown = request_reset(client, "nobody@example.com")

        assert known.status_code == unknown.status_code == 202
        assert known.json() == unknown.json()
        assert len(sent_emails) == 1  # only the real account got an email


class TestResend:
    def test_second_request_within_cooldown_sends_no_second_email(self, client, sent_emails):
        register(client, "resend1@example.com")
        first = request_reset(client, "resend1@example.com")
        second = request_reset(client, "resend1@example.com")

        assert first.status_code == second.status_code == 202
        assert first.json() == second.json()
        assert len(sent_emails) == 1

    def test_resend_after_cooldown_sends_a_new_link_and_retires_the_old_one(
        self, client, db_session, sent_emails
    ):
        from app.core.config import settings

        register(client, "resend2@example.com")
        request_reset(client, "resend2@example.com")
        _, old_token = sent_emails[0]

        # Pretend the first link was issued two minutes ago
        user = UserRepository(db_session).get_by_email("resend2@example.com")
        user.password_reset_expires_at = datetime.now(timezone.utc) + timedelta(
            minutes=settings.password_reset_token_expire_minutes - 2
        )
        db_session.commit()

        request_reset(client, "resend2@example.com")
        assert len(sent_emails) == 2
        _, new_token = sent_emails[1]
        assert new_token != old_token

        old = client.post("/auth/reset-password", json={"token": old_token, "new_password": "NewPassword456"})
        new = client.post("/auth/reset-password", json={"token": new_token, "new_password": "NewPassword456"})
        assert old.status_code == 400
        assert new.status_code == 200


def test_as_utc_handles_naive_and_offset_datetimes():
    from app.services.auth_service import _as_utc

    naive = datetime(2026, 1, 1, 12, 0)
    assert _as_utc(naive) == datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)

    nairobi = datetime(2026, 1, 1, 15, 0, tzinfo=timezone(timedelta(hours=3)))
    assert _as_utc(nairobi) == datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)


class TestEmailService:
    def test_no_provider_in_development_does_not_raise(self, monkeypatch):
        from app.services import email_service
        monkeypatch.setattr(email_service.settings, "environment", "development")
        email_service.send_password_reset_email("a@example.com", "tok")

    def test_brevo_path_posts_the_reset_link_over_https(self, monkeypatch):
        import json
        from app.services import email_service
        calls = []

        class FakeResponse:
            def __enter__(self): return self
            def __exit__(self, *args): return False
            def read(self): return b"{}"

        def fake_urlopen(req, timeout=None):
            calls.append(req)
            return FakeResponse()

        monkeypatch.setattr(email_service.urllib.request, "urlopen", fake_urlopen)
        monkeypatch.setattr(email_service.settings, "brevo_api_key", "test-key")
        monkeypatch.setattr(email_service.settings, "email_from", "noreply@example.com")
        monkeypatch.setattr(email_service.settings, "frontend_url", "https://app.example.com")

        email_service.send_password_reset_email("farmer@example.com", "abc123")

        assert len(calls) == 1
        req = calls[0]
        assert req.full_url == "https://api.brevo.com/v3/smtp/email"
        assert req.get_header("Api-key") == "test-key"
        payload = json.loads(req.data)
        assert payload["to"] == [{"email": "farmer@example.com"}]
        assert "https://app.example.com/reset-password?token=abc123" in payload["textContent"]

    def test_brevo_rejection_is_swallowed(self, monkeypatch):
        import urllib.error
        from app.services import email_service

        def rejecting_urlopen(req, timeout=None):
            raise urllib.error.HTTPError(req.full_url, 401, "Unauthorized", {}, None)

        monkeypatch.setattr(email_service.urllib.request, "urlopen", rejecting_urlopen)
        monkeypatch.setattr(email_service.settings, "brevo_api_key", "bad-key")
        monkeypatch.setattr(email_service.settings, "email_from", "noreply@example.com")
        email_service.send_password_reset_email("a@example.com", "tok")  # must not raise

    def test_smtp_path_builds_a_message_containing_the_link(self, monkeypatch):
        from app.services import email_service
        sent = []

        class FakeSMTP:
            def __init__(self, host, port, timeout=None): pass
            def __enter__(self): return self
            def __exit__(self, *args): return False
            def starttls(self): pass
            def login(self, user, password): pass
            def send_message(self, msg): sent.append(msg)

        monkeypatch.setattr(email_service.smtplib, "SMTP", FakeSMTP)
        monkeypatch.setattr(email_service.settings, "smtp_host", "smtp.example.com")
        monkeypatch.setattr(email_service.settings, "smtp_user", "user")
        monkeypatch.setattr(email_service.settings, "smtp_password", "pw")
        monkeypatch.setattr(email_service.settings, "smtp_from", "noreply@example.com")
        monkeypatch.setattr(email_service.settings, "frontend_url", "https://app.example.com")

        email_service.send_password_reset_email("farmer@example.com", "abc123")

        assert len(sent) == 1
        assert sent[0]["To"] == "farmer@example.com"
        assert "https://app.example.com/reset-password?token=abc123" in sent[0].get_content()

    def test_smtp_failure_is_swallowed(self, monkeypatch):
        from app.services import email_service

        class BrokenSMTP:
            def __init__(self, *args, **kwargs):
                raise OSError("connection refused")

        monkeypatch.setattr(email_service.smtplib, "SMTP", BrokenSMTP)
        monkeypatch.setattr(email_service.settings, "smtp_host", "smtp.example.com")
        email_service.send_password_reset_email("a@example.com", "tok")  # must not raise
