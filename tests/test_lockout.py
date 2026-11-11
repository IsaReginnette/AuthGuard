from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from uuid import uuid4

from fastapi.testclient import TestClient

from app import lockout
from app.database import SessionLocal
from app.main import app
from app.models import LoginLockout, User, UserSession

client = TestClient(app)


def cleanup(email: str):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        if user:
            db.query(UserSession).filter(UserSession.user_id == user.id).delete()
            db.delete(user)
        db.query(LoginLockout).filter(LoginLockout.email_key == lockout.email_key(email)).delete()
        db.commit()
    finally:
        db.close()


def test_three_failures_block_even_correct_password_until_ten_minutes_pass(monkeypatch):
    email = f"{uuid4().hex}@authguard.com"
    password = "SenhaSegura123"
    assert client.post("/register", json={"email": email, "password": password}).status_code == 201
    now = datetime(2026, 11, 11, 16, 0, 0)
    monkeypatch.setattr(lockout, "utcnow", lambda: now)
    try:
        for attempt in range(1, 4):
            response = client.post("/login", json={"email": email, "password": "incorreta"})
            assert response.status_code == (429 if attempt == 3 else 401)
            db = SessionLocal()
            try:
                state = db.get(LoginLockout, lockout.email_key(email))
                assert state.failed_attempts == attempt
                assert state.locked_until == (now + timedelta(minutes=10) if attempt == 3 else None)
            finally:
                db.close()

        for delta in (timedelta(0), timedelta(minutes=9, seconds=59)):
            monkeypatch.setattr(lockout, "utcnow", lambda delta=delta: now + delta)
            blocked = client.post("/login", json={"email": email, "password": password})
            assert blocked.status_code == 429
            assert "senha" not in blocked.text.lower()

        monkeypatch.setattr(lockout, "utcnow", lambda: now + timedelta(minutes=10))
        unlocked = client.post("/login", json={"email": email, "password": password})
        assert unlocked.status_code == 200
        db = SessionLocal()
        try:
            assert db.get(LoginLockout, lockout.email_key(email)) is None
        finally:
            db.close()
    finally:
        cleanup(email)


def test_successful_login_resets_consecutive_failures():
    email = f"{uuid4().hex}@authguard.com"
    password = "SenhaSegura123"
    assert client.post("/register", json={"email": email, "password": password}).status_code == 201
    try:
        for _ in range(2):
            assert client.post("/login", json={"email": email, "password": "errada"}).status_code == 401
        assert client.post("/login", json={"email": email, "password": password}).status_code == 200
        for _ in range(2):
            assert client.post("/login", json={"email": email, "password": "errada"}).status_code == 401
        assert client.post("/login", json={"email": email, "password": password}).status_code == 200
    finally:
        cleanup(email)


def test_unregistered_address_is_throttled_too_without_user_enumeration():
    email = f"{uuid4().hex}@authguard.com"
    try:
        statuses = [client.post("/login", json={"email": email, "password": "errada"}).status_code
                    for _ in range(4)]
        assert statuses == [401, 401, 429, 429]
    finally:
        cleanup(email)


def test_expired_lock_starts_new_failure_count(monkeypatch):
    email = f"{uuid4().hex}@authguard.com"
    now = datetime(2026, 11, 11, 16, 0, 0)
    monkeypatch.setattr(lockout, "utcnow", lambda: now)
    try:
        for _ in range(3):
            client.post("/login", json={"email": email, "password": "errada"})
        monkeypatch.setattr(lockout, "utcnow", lambda: now + timedelta(minutes=11))
        assert client.post("/login", json={"email": email, "password": "errada"}).status_code == 401
        db = SessionLocal()
        try:
            state = db.get(LoginLockout, lockout.email_key(email))
            assert state.failed_attempts == 1
            assert state.locked_until is None
        finally:
            db.close()
    finally:
        cleanup(email)


def test_simultaneous_password_failures_are_counted_atomically():
    """Três falhas concorrentes devem produzir um único bloqueio sem perda de incrementos."""
    email = f"{uuid4().hex}@authguard.com"
    password = "SenhaSegura123"
    assert client.post("/register", json={"email": email, "password": password}).status_code == 201

    def wrong_login(_):
        # Um cliente por worker evita compartilhar estado de transporte entre threads.
        with TestClient(app) as worker_client:
            return worker_client.post(
                "/login", json={"email": email, "password": "senha-errada"}
            ).status_code

    try:
        with ThreadPoolExecutor(max_workers=3) as executor:
            statuses = list(executor.map(wrong_login, range(3)))

        assert sorted(statuses) == [401, 401, 429]
        db = SessionLocal()
        try:
            state = db.get(LoginLockout, lockout.email_key(email))
            assert state is not None
            assert state.failed_attempts == 3
            assert state.locked_until is not None
        finally:
            db.close()

        assert client.post(
            "/login", json={"email": email, "password": password}
        ).status_code == 429
    finally:
        cleanup(email)
