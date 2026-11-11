from uuid import uuid4

from fastapi.testclient import TestClient

from app.database import SessionLocal
from app.main import app
from app.models import User, UserSession

client = TestClient(app)


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
            db.query(User).filter(User.email == email).delete()
            db.commit()
        finally:
            db.close()


def test_invalid_or_expired_session_is_rejected(monkeypatch):
    assert client.get("/me").status_code == 401
    assert client.get("/me", headers={"Authorization": "Bearer token-invalido"}).status_code == 401
