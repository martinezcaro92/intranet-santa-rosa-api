"""Entidad genérica de solicitudes ("ticket"): mantenimiento, suministros y publicaciones RRSS.

Un único modelo reutilizable con: tipo, solicitante, responsable, estado y datos flexibles.
Transiciones válidas de estado: pendiente -> en_curso -> finalizado.
"""
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.db import RESPONSABLE_TICKET, auditar, db, notificar, nuevo_id
from app.schemas import Error, EstadoTicket, Ticket, TicketIn, TicketPatch, TipoTicket
from app.security import usuario_actual

router = APIRouter(prefix="/tickets", tags=["Tickets"])

TRANSICIONES = {"pendiente": {"en_curso"}, "en_curso": {"finalizado"}, "finalizado": set()}


def _borrador_rrss(datos: dict) -> str:
    """SIMULA la llamada al modelo de IA generativa que redacta el borrador de la publicación."""
    return (f"📢 {datos.get('actividad', 'Nueva actividad')} · {datos.get('servicio', 'Centro Médico')}\n"
            f"{datos.get('descripcion', '')}\n#SantaRosaDeLima #Salud")


def _puede_ver(ticket: dict, usuario: dict) -> bool:
    return ("admin" in usuario["roles"] or ticket["solicitante_id"] == usuario["id"]
            or ticket["responsable_rol"] in usuario["roles"])


@router.get("", response_model=list[Ticket], summary="Listar tickets", responses={401: {"model": Error}})
def listar(tipo: TipoTicket | None = Query(None), estado: EstadoTicket | None = Query(None),
           usuario: dict = Depends(usuario_actual)):
    """Cada usuario ve los tickets que ha creado y los de los tipos de los que es responsable."""
    return [t for t in db["tickets"].values()
            if _puede_ver(t, usuario) and (tipo is None or t["tipo"] == tipo)
            and (estado is None or t["estado"] == estado)]


@router.post("", response_model=Ticket, status_code=status.HTTP_201_CREATED, summary="Crear un ticket",
             responses={401: {"model": Error}})
def crear(datos: TicketIn, usuario: dict = Depends(usuario_actual)):
    ticket = {"id": nuevo_id("t"), "solicitante_id": usuario["id"], "responsable_rol": RESPONSABLE_TICKET[datos.tipo],
              "estado": "pendiente", "creado": datetime.now().isoformat(timespec="seconds"), "historial": [],
              **datos.model_dump()}
    if datos.tipo == "rrss":
        ticket["datos"]["borrador_ia"] = _borrador_rrss(ticket["datos"])
    db["tickets"][ticket["id"]] = ticket
    notificar(ticket["responsable_rol"], f"Nuevo ticket de {datos.tipo}: {datos.titulo}")
    auditar(usuario["id"], "crear_ticket", ticket["id"])
    return ticket


@router.patch("/{ticket_id}", response_model=Ticket, summary="Cambiar el estado de un ticket",
              responses={403: {"model": Error}, 404: {"model": Error}, 409: {"model": Error}})
def cambiar_estado(ticket_id: str, datos: TicketPatch, usuario: dict = Depends(usuario_actual)):
    """Actualización PARCIAL: solo cambia el estado. Lo hace el responsable del tipo de ticket."""
    ticket = db["tickets"].get(ticket_id)
    if ticket is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Ticket no encontrado")
    if ticket["responsable_rol"] not in usuario["roles"] and "admin" not in usuario["roles"]:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Solo el responsable puede cambiar el estado")
    if datos.estado not in TRANSICIONES[ticket["estado"]]:
        raise HTTPException(status.HTTP_409_CONFLICT,
                            f"Transición no permitida: {ticket['estado']} -> {datos.estado}")
    ticket["historial"].append({"de": ticket["estado"], "a": datos.estado, "por": usuario["id"],
                                "fecha": datetime.now().isoformat(timespec="seconds")})
    ticket["estado"] = datos.estado
    notificar(ticket["solicitante_id"], f"Tu ticket '{ticket['titulo']}' está ahora: {datos.estado}")
    auditar(usuario["id"], "cambiar_estado_ticket", f"{ticket_id} -> {datos.estado}")
    return ticket
