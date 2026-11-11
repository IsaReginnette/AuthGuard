
from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app
from app.database import SessionLocal
from app.models import User
from app.security import verify_password

client = TestClient(app)


def test_register_user_with_secure_password():
    email = f"{uuid4().hex}@authguard.com"
    password = "SenhaSegura123"

    response = client.post(
        "/register",
        json={"email": email, "password": password}
    )

    assert response.status_code == 201
    assert response.json()["email"] == email
    assert "password" not in response.json()
    assert "hashed_password" not in response.json()

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()

        assert user is not None
        assert user.hashed_password != password
        assert verify_password(password, user.hashed_password)
    finally:
        if user:
            db.delete(user)
            db.commit()
        db.close()


def test_register_rejects_short_password():
    response = client.post(
        "/register",
        json={
            "email": f"{uuid4().hex}@authguard.com",
            "password": "1234567"
        }
    )

    assert response.status_code == 422


def test_register_rejects_invalid_email():
    response = client.post(
        "/register",
        json={
            "email": "email-invalido",
            "password": "SenhaSegura123"
        }
    )

    assert response.status_code == 422
