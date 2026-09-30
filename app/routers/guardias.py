"""Guardias médicas: consulta, asignación por rondas y registro de quién la realiza."""
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.db import auditar, db, notificar, nuevo_id
from app.schemas import AsignarGuardiaIn, Error, Franja, Guardia, GuardiaPatch
from app.security import requiere_rol, usuario_actual
from app.services.guardias import hueco, seleccionar

router = APIRouter(prefix="/guardias", tags=["Guardias"])
supervision = requiere_rol("supervision")


def _ausente(usuario_id: str, fecha: date, franja: str) -> bool:
    return any(a["usuario_id"] == usuario_id and a["fecha"] == fecha.isoformat()
               and (a["dia_completo"] or franja in a["franjas"])
               for a in db["ausencias"].values())


@router.get("", response_model=list[Guardia], summary="Consultar guardias",
            responses={401: {"model": Error}})
def listar(fecha: date | None = Query(None, description="Filtrar por fecha (AAAA-MM-DD)"),
           franja: Franja | None = Query(None),
           _: dict = Depends(usuario_actual)):
    return [g for g in db["guardias"].values()
            if (fecha is None or g["fecha"] == fecha.isoformat()) and (franja is None or g["franja"] == franja)]


@router.post("/asignar", response_model=list[Guardia], status_code=status.HTTP_201_CREATED,
             summary="Asignar guardias por rondas",
             responses={403: {"model": Error}, 409: {"model": Error, "description": "Ya asignadas o sin candidatos"}})
def asignar(datos: AsignarGuardiaIn, usuario: dict = Depends(supervision)):
    """Ejecuta el algoritmo por rondas para un hueco concreto (fecha + franja).

    Es POST porque **no es idempotente**: lanza un proceso que crea guardias nuevas y cuyo
    resultado puede variar (sorteo en caso de empate).
    """
    clave = hueco(datos.fecha, datos.franja)
    if any(g["fecha"] == datos.fecha.isoformat() and g["franja"] == datos.franja for g in db["guardias"].values()):
        raise HTTPException(status.HTTP_409_CONFLICT, "Ese hueco ya tiene guardias asignadas")
    candidatos = [u["id"] for u in db["usuarios"].values()
                  if u["estado"] == "activo" and clave in u["disponibilidad"]
                  and not _ausente(u["id"], datos.fecha, datos.franja)]
    if not candidatos:
        raise HTTPException(status.HTTP_409_CONFLICT, f"No hay profesionales disponibles para {clave}")
    contadores = db["contadores"].setdefault(clave, {})
    creadas = []
    for profesional in seleccionar(candidatos, contadores, datos.plazas):
        guardia = {"id": nuevo_id("g"), "fecha": datos.fecha.isoformat(), "franja": datos.franja, "hueco": clave,
                   "asignado_a": profesional, "realizada_por": None, "estado": "asignada"}
        db["guardias"][guardia["id"]] = guardia
        notificar(profesional, f"Se te ha asignado la guardia {clave} del {guardia['fecha']}")
        creadas.append(guardia)
    auditar(usuario["id"], "asignar_guardias", f"{clave} {datos.fecha}: {[g['asignado_a'] for g in creadas]}")
    return creadas


@router.patch("/{guardia_id}", response_model=Guardia, summary="Registrar quién realiza la guardia",
              responses={404: {"model": Error}, 409: {"model": Error}, 422: {"model": Error}})
def registrar_realizacion(guardia_id: str, datos: GuardiaPatch, usuario: dict = Depends(supervision)):
    """Actualización PARCIAL de la guardia: solo cambia `realizada_por` (y su estado).

    Suma 1 al contador de quien la REALIZA en ese hueco, que puede no coincidir con el asignado.
    """
    guardia = db["guardias"].get(guardia_id)
    if guardia is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Guardia no encontrada")
    if guardia["estado"] == "realizada":
        raise HTTPException(status.HTTP_409_CONFLICT, "La guardia ya estaba registrada como realizada")
    profesional = db["usuarios"].get(datos.realizada_por)
    if profesional is None or profesional["estado"] != "activo":
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Profesional no válido")
    guardia.update(realizada_por=datos.realizada_por, estado="realizada")
    contadores = db["contadores"].setdefault(guardia["hueco"], {})
    contadores[datos.realizada_por] = contadores.get(datos.realizada_por, 0) + 1
    auditar(usuario["id"], "registrar_guardia", f"{guardia_id} realizada por {datos.realizada_por}")
    return guardia
