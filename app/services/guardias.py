"""Algoritmo de asignación de guardias por rondas.

Reglas (equivalentes a las de la memoria técnica del proyecto):
1. En cada hueco horario puede haber más de un profesional asignado (plazas).
2. Se mantiene, para cada profesional y cada hueco concreto, un contador de guardias REALIZADAS.
3. Se elige a quien tiene el contador más bajo; si hay empate, la elección es aleatoria.
4. La comparación se hace solo entre los profesionales disponibles en ese hueco.
5. Si el asignado no puede asistir, otro profesional la realiza y es SU contador el que sube.
   Así, en rondas siguientes, el asignado original vuelve a tener prioridad.
"""
import random
from datetime import date

from app.db import DIAS


def hueco(fecha: date, franja: str) -> str:
    """Convierte fecha + franja en la clave del hueco horario, p. ej. 'lunes-noche'."""
    return f"{DIAS[fecha.weekday()]}-{franja}"


def seleccionar(candidatos: list[str], contadores: dict[str, int], plazas: int,
                rng: random.Random | None = None) -> list[str]:
    """Devuelve los profesionales asignados para cubrir las plazas del hueco.

    Función pura (sin acceso a datos) para poder probarla fácilmente con pytest.
    """
    rng = rng or random.Random()
    disponibles = list(candidatos)
    elegidos: list[str] = []
    for _ in range(min(plazas, len(disponibles))):
        minimo = min(contadores.get(p, 0) for p in disponibles)
        empatados = [p for p in disponibles if contadores.get(p, 0) == minimo]
        elegido = rng.choice(empatados)
        elegidos.append(elegido)
        disponibles.remove(elegido)
    return elegidos
