"""
Live Brevo check. Skipped by default, so normal test runs and CI never send real email.

Run it deliberately, from backend/:
    RUN_LIVE_EMAIL_TEST=1 LIVE_TEST_RECIPIENT=you@example.com pytest tests/test_brevo_live.py -v
"""
import os
import urllib.error

import pytest

LIVE = os.getenv("RUN_LIVE_EMAIL_TEST") == "1"
RECIPIENT = os.getenv("LIVE_TEST_RECIPIENT", "")


@pytest.mark.skipif(not LIVE, reason="set RUN_LIVE_EMAIL_TEST=1 to send a real email")
def test_brevo_accepts_a_real_message(monkeypatch):
    from app.core.config import Settings
    from app.services import email_service

    assert RECIPIENT, "set LIVE_TEST_RECIPIENT to an inbox you can open"

    # conftest blanks the key for every test, so read the real values from .env
    real = Settings()
    assert real.brevo_api_key, "BREVO_API_KEY is not set in backend/.env"
    assert real.email_from, "EMAIL_FROM is not set in backend/.env"

    monkeypatch.setattr(email_service.settings, "brevo_api_key", real.brevo_api_key)
    monkeypatch.setattr(email_service.settings, "email_from", real.email_from)

    # Call the low-level sender directly. The public function swallows errors on purpose,
    # so a bad key would still look like a pass.
    try:
        email_service._send_via_brevo(
            RECIPIENT,
            "Smart Dairy Manager: live email test",
            "If you can read this, Brevo accepted the message from your backend.",
        )
    except urllib.error.HTTPError as exc:
        pytest.fail(f"Brevo rejected the request: HTTP {exc.code}: {exc.read().decode(errors='replace')}")