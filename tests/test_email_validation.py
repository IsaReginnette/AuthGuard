from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app

client = TestClient(app)


@pytest.mark.parametrize("route", ["/register", "/login"])
@pytest.mark.parametrize("email", ["", "sem-arroba", "invalido@", "@example.com"])
def test_invalid_email_is_rejected_before_any_database_query(route, email):
    """Nem a consulta de usuário pode ocorrer com e-mail inválido."""
    with patch.object(Session, "query", side_effect=AssertionError("consulta SQL indevida")) as query:
        response = client.post(route, json={"email": email, "password": "SenhaSegura123"})
    assert response.status_code == 422
    assert query.call_count == 0
