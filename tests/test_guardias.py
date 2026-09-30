import random

from app.services.guardias import seleccionar
from tests.conftest import SUPERVISION

LUNES = "2026-10-05"  # es lunes


def test_elige_al_de_menor_contador():
    assert seleccionar(["A", "B"], {"A": 3, "B": 5}, 1) == ["A"]


def test_empate_se_decide_por_sorteo():
    resultados = {seleccionar(["A", "B"], {"A": 6, "B": 6}, 1, random.Random(s))[0] for s in range(30)}
    assert resultados == {"A", "B"}


def test_varias_plazas_sin_repetir():
    elegidos = seleccionar(["A", "B", "C"], {"A": 1, "B": 0, "C": 2}, 2)
    assert elegidos == ["B", "A"]


def test_ejemplo_memoria_tecnica():
    """A (3) no puede asistir, la cubre B (5 -> 6). A tiene prioridad hasta llegar a 6."""
    contadores = {"A": 3, "B": 5}
    contadores["B"] += 1                        # B realiza la guardia de A
    for esperado in [4, 5, 6]:                  # A cubre las siguientes rondas
        assert seleccionar(["A", "B"], contadores, 1) == ["A"]
        contadores["A"] += 1
        assert contadores["A"] == esperado
    assert contadores["A"] == contadores["B"] == 6   # vuelven a empatar: decide el sorteo


def test_flujo_api_asignar_y_registrar(client, login):
    h = login(SUPERVISION)
    r = client.post("/api/v1/guardias/asignar", json={"fecha": LUNES, "franja": "noche", "plazas": 1}, headers=h)
    assert r.status_code == 201
    guardia = r.json()[0]
    assert guardia["asignado_a"] == "u3"        # Ana tiene el contador más bajo (3)
    # Ana no puede asistir: la realiza Javier (u4)
    r = client.patch(f"/api/v1/guardias/{guardia['id']}", json={"realizada_por": "u4"}, headers=h)
    assert r.status_code == 200 and r.json()["estado"] == "realizada"
    # Repetir la asignación del mismo hueco da conflicto
    r = client.post("/api/v1/guardias/asignar", json={"fecha": LUNES, "franja": "noche"}, headers=h)
    assert r.status_code == 409


def test_ausente_no_es_candidato(client, login):
    ana = login("ana.garcia@santarosadelima.es")
    client.post("/api/v1/ausencias", json={"tipo": "administrativa", "fecha": LUNES}, headers=ana)
    r = client.post("/api/v1/guardias/asignar", json={"fecha": LUNES, "franja": "noche"}, headers=login(SUPERVISION))
    assert r.json()[0]["asignado_a"] != "u3"
