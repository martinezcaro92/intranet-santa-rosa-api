from tests.conftest import ANA, DIRECCION


def test_login_devuelve_tokens(client):
    r = client.post("/api/v1/auth/google", json={"id_token": ANA})
    assert r.status_code == 200
    assert {"access_token", "refresh_token"} <= r.json().keys()


def test_usuario_pendiente_no_puede_entrar(client):
    r = client.post("/api/v1/auth/google", json={"id_token": "elena.torres@santarosadelima.es"})
    assert r.status_code == 403


def test_email_desconocido_queda_pendiente(client, login):
    r = client.post("/api/v1/auth/google", json={"id_token": "nuevo@gmail.com"})
    assert r.status_code == 403
    pendientes = client.get("/api/v1/usuarios?estado=pendiente", headers=login(DIRECCION)).json()
    assert any(u["email"] == "nuevo@gmail.com" for u in pendientes)


def test_sin_token_401(client):
    assert client.get("/api/v1/auth/me").status_code == 401


def test_me_y_refresh(client):
    tokens = client.post("/api/v1/auth/google", json={"id_token": ANA}).json()
    r = client.post("/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert r.status_code == 200
    me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {r.json()['access_token']}"})
    assert me.json()["email"] == ANA


def test_refresh_no_sirve_como_access(client):
    tokens = client.post("/api/v1/auth/google", json={"id_token": ANA}).json()
    r = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {tokens['refresh_token']}"})
    assert r.status_code == 401


def test_rol_insuficiente_403(client, login):
    assert client.get("/api/v1/usuarios", headers=login(ANA)).status_code == 403


def test_admin_aprueba_usuario_pendiente(client, login):
    r = client.patch("/api/v1/usuarios/u9", json={"estado": "activo"}, headers=login(DIRECCION))
    assert r.status_code == 200 and r.json()["estado"] == "activo"
    assert client.post("/api/v1/auth/google", json={"id_token": "elena.torres@santarosadelima.es"}).status_code == 200
