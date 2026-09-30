"""Reserva de salas y equipos con detección de solapamientos."""
from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.db import auditar, db, nuevo_id
from app.schemas import Error, Reserva, ReservaIn
from app.security import usuario_actual

router = APIRouter(prefix="/reservas", tags=["Reservas"])


def _dt(valor) -> datetime:
    return valor if isinstance(valor, datetime) else datetime.fromisoformat(valor)


@router.get("", response_model=list[Reserva], summary="Consultar reservas", responses={401: {"model": Error}})
def listar(recurso_id: str | None = Query(None, examples=["sala-reuniones-1"]),
           fecha: date | None = Query(None), _: dict = Depends(usuario_actual)):
    return [r for r in db["reservas"].values()
            if (recurso_id is None or r["recurso_id"] == recurso_id)
            and (fecha is None or _dt(r["inicio"]).date() == fecha)]


@router.post("", response_model=Reserva, status_code=status.HTTP_201_CREATED, summary="Reservar sala o equipo",
             responses={404: {"model": Error}, 409: {"model": Error, "description": "Solapamiento con otra reserva"},
                        422: {"model": Error}})
def crear(datos: ReservaIn, usuario: dict = Depends(usuario_actual)):
    if datos.recurso_id not in db["recursos"]:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Recurso no encontrado. Disponibles: {list(db['recursos'])}")
    if datos.fin <= datos.inicio:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "La hora de fin debe ser posterior a la de inicio")
    for r in db["reservas"].values():
        # Dos intervalos se solapan si cada uno empieza antes de que termine el otro
        if r["recurso_id"] == datos.recurso_id and datos.inicio < _dt(r["fin"]) and _dt(r["inicio"]) < datos.fin:
            raise HTTPException(status.HTTP_409_CONFLICT, f"Solapa con la reserva {r['id']} ({r['inicio']} - {r['fin']})")
    reserva = {"id": nuevo_id("r"), "usuario_id": usuario["id"], **datos.model_dump(mode="json")}
    db["reservas"][reserva["id"]] = reserva
    auditar(usuario["id"], "crear_reserva", reserva["id"])
    return reserva
