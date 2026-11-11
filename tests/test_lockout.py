from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from uuid import uuid4

from fastapi.testclient import TestClient

from app import lockout
from app.database import SessionLocal
from app.main import app
from app.models import LoginAttempt, User, UserSession

client = TestClient(app)


def test_account_is_locked_for_ten_minutes_after_three_failed_attempts(monkeypatch):
    email = f"{uuid4().hex}@authguard.com"
    password = "SenhaSegura123"
    registered = client.post("/register", json={"email": email, "password": password})
    assert registered.status_code == 201
    user_id = registered.json()["id"]

    now = datetime(2030, 1, 1, 12, 0, 0)
    monkeypatch.setattr(lockout, "utcnow", lambda: now)

    try:
        for _ in range(3):
            response = client.post(
                "/login",
                json={"email": email, "password": "SenhaIncorreta123"},
            )
            assert response.status_code == 401

        blocked = client.post("/login", json={"email": email, "password": password})
        assert blocked.status_code == 429
        assert blocked.headers["retry-after"] == "600"

        monkeypatch.setattr(lockout, "utcnow", lambda: now + timedelta(minutes=9, seconds=59))
        still_blocked = client.post("/login", json={"email": email, "password": password})
        assert still_blocked.status_code == 429

        monkeypatch.setattr(lockout, "utcnow", lambda: now + timedelta(minutes=10, seconds=1))
        unlocked = client.post("/login", json={"email": email, "password": password})
        assert unlocked.status_code == 200

        db = SessionLocal()
        try:
            assert db.query(LoginAttempt).filter(LoginAttempt.email == email).first() is None
        finally:
            db.close()
    finally:
        db = SessionLocal()
        try:
            db.query(UserSession).filter(UserSession.user_id == user_id).delete()
            db.query(LoginAttempt).filter(LoginAttempt.email == email).delete()
            db.query(User).filter(User.email == email).delete()
            db.commit()
        finally:
            db.close()


def test_three_concurrent_failures_are_counted_atomically():
    email = f"{uuid4().hex}@authguard.com"

    def record_failure():
        db = SessionLocal()
        try:
            lockout.register_failed_attempt(db, email)
        finally:
            db.close()

    try:
        with ThreadPoolExecutor(max_workers=3) as executor:
            list(executor.map(lambda _: record_failure(), range(3)))

        db = SessionLocal()
        try:
            attempt = db.query(LoginAttempt).filter(LoginAttempt.email == email).one()
            assert attempt.failed_attempts == 3
            assert attempt.locked_until is not None
            assert attempt.locked_until >= lockout.utcnow() + timedelta(minutes=9)
        finally:
            db.close()
    finally:
        db = SessionLocal()
        try:
            db.query(LoginAttempt).filter(LoginAttempt.email == email).delete()
            db.commit()
        finally:
            db.close()
