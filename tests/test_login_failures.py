from uuid import uuid4

from fastapi.testclient import TestClient

from app.database import SessionLocal
from app.main import app
from app.models import User, UserSession

client = TestClient(app)


def test_wrong_password_and_unknown_email_return_identical_generic_errors():
    email = f"{uuid4().hex}@authguard.com"
    password = "SenhaSegura123"
    registered = client.post("/register", json={"email": email, "password": password})
    assert registered.status_code == 201

    try:
        invalid_password = client.post(
            "/login", json={"email": email, "password": "senha-errada"}
        )
        unknown_email = client.post(
            "/login", json={"email": f"{uuid4().hex}@authguard.com", "password": "senha-errada"}
        )
        assert invalid_password.status_code == unknown_email.status_code == 401
        assert invalid_password.json() == unknown_email.json() == {"detail": "Credenciais inválidas."}
        assert invalid_password.headers["www-authenticate"] == "Bearer"
        assert unknown_email.headers["www-authenticate"] == "Bearer"
        for response in (invalid_password, unknown_email):
            assert "senha-errada" not in response.text
            assert "hashed_password" not in response.text
            assert "traceback" not in response.text.lower()
    finally:
        db = SessionLocal()
        try:
            db.query(UserSession).filter(UserSession.user_id == registered.json()["id"]).delete()
            db.query(User).filter(User.email == email).delete()
            db.commit()
        finally:
            db.close()
