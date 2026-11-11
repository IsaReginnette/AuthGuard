from datetime import timedelta
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app import session_auth
from app.database import SessionLocal
from app.main import app
from app.models import LoginAttempt, User, UserSession

client = TestClient(app)


def test_invalid_login_email_is_rejected_before_database_query(monkeypatch):
    def fail_if_query_runs(*args, **kwargs):
        raise AssertionError("Consulta ao banco não deveria ocorrer para e-mail inválido.")

    monkeypatch.setattr(Session, "query", fail_if_query_runs)

    for email in ("", "email-invalido"):
        response = client.post(
            "/login",
            json={"email": email, "password": "SenhaSegura123"},
        )
        assert response.status_code == 422


def test_valid_login_creates_usable_bearer_session():
    email = f"{uuid4().hex}@authguard.com"
    password = "SenhaSegura123"
    registered = client.post("/register", json={"email": email, "password": password})
    assert registered.status_code == 201

    try:
        result = client.post("/login", json={"email": email, "password": password})
        assert result.status_code == 200
        data = result.json()
        assert data["token_type"] == "bearer"
        assert data["expires_in"] == 3600
        assert len(data["access_token"]) >= 32
        assert "password" not in data and "hashed_password" not in data
        assert password not in str(data)

        profile = client.get("/me", headers={"Authorization": f"Bearer {data['access_token']}"})
        assert profile.status_code == 200
        assert profile.json() == registered.json()
        assert "password" not in profile.json()

        session = SessionLocal()
        try:
            saved = session.query(UserSession).filter(UserSession.user_id == registered.json()["id"]).one()
            assert saved.token_hash != data["access_token"]
        finally:
            session.close()
    finally:
        db = SessionLocal()
        try:
            db.query(UserSession).filter(UserSession.user_id == registered.json()["id"]).delete()
            db.query(LoginAttempt).filter(LoginAttempt.email == email).delete()
            db.query(User).filter(User.email == email).delete()
            db.commit()
        finally:
            db.close()


def test_invalid_credentials_are_rejected_without_revealing_user_existence():
    registered_email = f"{uuid4().hex}@authguard.com"
    unknown_email = f"{uuid4().hex}@authguard.com"
    password = "SenhaSegura123"
    registered = client.post(
        "/register",
        json={"email": registered_email, "password": password},
    )
    assert registered.status_code == 201

    try:
        wrong_password = client.post(
            "/login",
            json={"email": registered_email, "password": "SenhaErrada123"},
        )
        unknown_user = client.post(
            "/login",
            json={"email": unknown_email, "password": "SenhaErrada123"},
        )

        # O comportamento observável é idêntico nos dois cenários.
        assert wrong_password.status_code == unknown_user.status_code == 401
        assert wrong_password.json() == unknown_user.json() == {
            "detail": "Credenciais inválidas."
        }
        assert wrong_password.headers["www-authenticate"] == "Bearer"
        assert unknown_user.headers["www-authenticate"] == "Bearer"
    finally:
        db = SessionLocal()
        try:
            db.query(LoginAttempt).filter(
                LoginAttempt.email.in_([registered_email, unknown_email])
            ).delete(synchronize_session=False)
            db.query(User).filter(User.email == registered_email).delete()
            db.commit()
        finally:
            db.close()


def test_invalid_session_is_rejected():
    assert client.get("/me").status_code == 401
    assert client.get("/me", headers={"Authorization": "Bearer token-invalido"}).status_code == 401


def test_expired_session_is_rejected(monkeypatch):
    email = f"{uuid4().hex}@authguard.com"
    password = "SenhaSegura123"
    registered = client.post("/register", json={"email": email, "password": password})
    assert registered.status_code == 201
    user_id = registered.json()["id"]

    try:
        response = client.post("/login", json={"email": email, "password": password})
        assert response.status_code == 200
        headers = {"Authorization": f"Bearer {response.json()['access_token']}"}
        assert client.get("/me", headers=headers).status_code == 200

        db = SessionLocal()
        try:
            saved = db.query(UserSession).filter(UserSession.user_id == user_id).one()
            expired_at = saved.expires_at
        finally:
            db.close()

        monkeypatch.setattr(session_auth, "utcnow", lambda: expired_at + timedelta(seconds=1))
        assert client.get("/me", headers=headers).status_code == 401
    finally:
        db = SessionLocal()
        try:
            db.query(UserSession).filter(UserSession.user_id == user_id).delete()
            db.query(LoginAttempt).filter(LoginAttempt.email == email).delete()
            db.query(User).filter(User.email == email).delete()
            db.commit()
        finally:
            db.close()
