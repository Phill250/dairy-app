import os

os.environ["DATABASE_URL"] = "sqlite:///./test.db"

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.core.database import Base, engine, SessionLocal
from app.models import user, cow, log  # noqa: F401 — registers tables on Base.metadata


@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
    if os.path.exists("test.db"):
        os.remove("test.db")


@pytest.fixture(scope="session", autouse=True)
def disable_rate_limiting():
    """
    slowapi's default in-memory storage keys limits by client IP, and
    TestClient reports every request as coming from the same fake address
    ("testclient"). That means all tests share ONE rate-limit bucket
    regardless of which test they're in, so login attempts in later tests
    get silently 429'd by earlier tests' quota. None of the current tests
    are actually testing rate limiting itself, so disabling it entirely
    for the test session avoids this cross-test interference at its root,
    rather than fighting to reset internal counters between tests.
    """
    app.state.limiter.enabled = False
    yield
    app.state.limiter.enabled = True


@pytest.fixture()
def db_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def client():
    with TestClient(app) as c:
        yield c
        
@pytest.fixture(autouse=True)
def never_send_real_email(monkeypatch):
    from app.core.config import settings
    monkeypatch.setattr(settings, "brevo_api_key", "")
    monkeypatch.setattr(settings, "smtp_host", "")