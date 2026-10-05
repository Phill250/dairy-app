import json
import smtplib
import urllib.error
import urllib.request
from email.message import EmailMessage

from app.core.config import settings
from app.core.logging_config import security_logger

BREVO_API_URL = "https://api.brevo.com/v3/smtp/email"


def _compose(raw_token: str) -> tuple[str, str, str]:
    link = f"{settings.frontend_url}/reset-password?token={raw_token}"
    subject = "Reset your Smart Dairy Manager password"
    body = (
        "We received a request to reset your password.\n\n"
        f"Open this link to choose a new one (valid for {settings.password_reset_token_expire_minutes} minutes):\n"
        f"{link}\n\n"
        "If you didn't ask for this, you can ignore this email."
    )
    return link, subject, body


def _send_via_brevo(to_email: str, subject: str, body: str) -> None:
    if not settings.email_from:
        security_logger.error("EMAIL_FROM is not set; password reset email was NOT sent")
        return
    payload = json.dumps({
        "sender": {"name": "Smart Dairy Manager", "email": settings.email_from},
        "to": [{"email": to_email}],
        "subject": subject,
        "textContent": body,
    }).encode("utf-8")
    request = urllib.request.Request(
        BREVO_API_URL,
        data=payload,
        method="POST",
        headers={
            "api-key": settings.brevo_api_key,
            "content-type": "application/json",
            "accept": "application/json",
        },
    )
    with urllib.request.urlopen(request, timeout=10) as response:
        response.read()


def _send_via_smtp(to_email: str, subject: str, body: str) -> None:
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = settings.smtp_from or settings.smtp_user
    msg["To"] = to_email
    msg.set_content(body)
    with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=10) as server:
        server.starttls()
        if settings.smtp_user:
            server.login(settings.smtp_user, settings.smtp_password)
        server.send_message(msg)


def send_password_reset_email(to_email: str, raw_token: str) -> None:
    link, subject, body = _compose(raw_token)

    try:
        if settings.brevo_api_key:
            _send_via_brevo(to_email, subject, body)
        elif settings.smtp_host:
            _send_via_smtp(to_email, subject, body)
        elif settings.environment == "production":
            # Never write a live reset token to disk in production
            security_logger.error("No email provider configured; password reset email was NOT sent")
        else:
            security_logger.info(f"[DEV ONLY] Password reset link for {to_email}: {link}")
    except urllib.error.HTTPError as exc:
        security_logger.error(f"Email provider rejected the password reset email (HTTP {exc.code})")
    except Exception as exc:
        # Never surface this to the caller: that would reveal whether the account exists
        security_logger.error(f"Failed to send password reset email: {exc}")