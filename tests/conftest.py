import pytest
from fastapi.testclient import TestClient

from app.db import reset
from app.main import app


@pytest.fixture(autouse=True)
def datos_limpios():
    """Cada test empieza con los datos de ejemplo originales."""
    reset()
    yield


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def login(client):
    """Devuelve una función que inicia sesión y devuelve las cabeceras de autorización."""
    def _login(email: str) -> dict:
        r = client.post("/api/v1/auth/google", json={"id_token": email})
        assert r.status_code == 200, r.text
        return {"Authorization": f"Bearer {r.json()['access_token']}"}
    return _login


DIRECCION = "laura.martinez@santarosadelima.es"
SUPERVISION = "carlos.ruiz@santarosadelima.es"
ANA = "ana.garcia@santarosadelima.es"
MANTENIMIENTO = "pedro.gomez@santarosadelima.es"
