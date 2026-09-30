from tests.conftest import ANA, DIRECCION, MANTENIMIENTO


def test_reserva_solapada_409(client, login):
    h = login(ANA)
    base = {"recurso_id": "sala-reuniones-1"}
    assert client.post("/api/v1/reservas", json={**base, "inicio": "2026-10-06T10:00:00",
                                                 "fin": "2026-10-06T11:00:00"}, headers=h).status_code == 201
    assert client.post("/api/v1/reservas", json={**base, "inicio": "2026-10-06T10:30:00",
                                                 "fin": "2026-10-06T12:00:00"}, headers=h).status_code == 409
    # Justo a continuación no solapa
    assert client.post("/api/v1/reservas", json={**base, "inicio": "2026-10-06T11:00:00",
                                                 "fin": "2026-10-06T12:00:00"}, headers=h).status_code == 201


def test_ticket_transiciones(client, login):
    r = client.patch("/api/v1/tickets/t1", json={"estado": "finalizado"}, headers=login(MANTENIMIENTO))
    assert r.status_code == 409                             # no se puede saltar "en_curso"
    r = client.patch("/api/v1/tickets/t1", json={"estado": "en_curso"}, headers=login(MANTENIMIENTO))
    assert r.status_code == 200
    r = client.patch("/api/v1/tickets/t1", json={"estado": "en_curso"}, headers=login(ANA))
    assert r.status_code == 403                             # solo el responsable


def test_ticket_rrss_genera_borrador(client, login):
    r = client.post("/api/v1/tickets", json={"tipo": "rrss", "titulo": "Jornada de puertas abiertas",
                                             "datos": {"actividad": "Puertas abiertas", "servicio": "Pediatría",
                                                       "descripcion": "Visita guiada para familias."}},
                    headers=login(ANA))
    assert r.status_code == 201 and "borrador_ia" in r.json()["datos"]


def test_flujo_ausencia_generica(client, login):
    h = login(ANA)
    aus = client.post("/api/v1/ausencias", json={"tipo": "generica", "fecha": "2026-10-07",
                                                  "motivo": "Consulta médica"}, headers=h).json()
    assert aus["estado"] == "pendiente_justificante"
    assert client.get(f"/api/v1/ausencias/{aus['id']}/pdf", headers=h).status_code == 409
    r = client.post(f"/api/v1/ausencias/{aus['id']}/justificante",
                    files={"archivo": ("justificante.pdf", b"%PDF-1.4", "application/pdf")}, headers=h)
    assert r.json()["estado"] == "justificada"
    pdf = client.get(f"/api/v1/ausencias/{aus['id']}/pdf", headers=h)
    assert pdf.status_code == 200 and pdf.content.startswith(b"%PDF")
    assert client.post(f"/api/v1/ausencias/{aus['id']}/firma", json={"metodo": "autofirma"},
                       headers=h).status_code == 501
    r = client.post(f"/api/v1/ausencias/{aus['id']}/firma",
                    json={"metodo": "manuscrita", "imagen_base64": "iVBORw0KGgo="}, headers=h)
    assert r.json()["estado"] == "firmada"


def test_anuncios_caducados_no_se_muestran(client, login):
    titulos = [a["titulo"] for a in client.get("/api/v1/anuncios", headers=login(ANA)).json()]
    assert "Simulacro de evacuación (caducado)" not in titulos
    assert titulos[0] == "Nuevo protocolo de triaje"        # destacado primero
    assert "Sesión clínica de Pediatría" not in titulos     # Ana es de Urgencias


def test_dashboard_solo_direccion(client, login):
    assert client.get("/api/v1/dashboard/kpis", headers=login(ANA)).status_code == 403
    r = client.get("/api/v1/dashboard/kpis", headers=login(DIRECCION))
    assert r.status_code == 200 and "guardias" in r.json()
    assert client.get("/api/v1/auditoria", headers=login(DIRECCION)).status_code == 200
