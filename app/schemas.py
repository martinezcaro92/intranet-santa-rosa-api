"""Esquemas de datos (Pydantic) de peticiones y respuestas.

Son el equivalente en código de la sección `components/schemas` del fichero OpenAPI.
"""
from datetime import date, datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

Franja = Literal["manana", "tarde", "noche"]
EstadoUsuario = Literal["activo", "pendiente", "inactivo"]
TipoTicket = Literal["mantenimiento", "suministros", "rrss"]
EstadoTicket = Literal["pendiente", "en_curso", "finalizado"]
TipoAusencia = Literal["generica", "administrativa", "actividad_externa"]


# ---------- Autenticación ----------
class LoginGoogle(BaseModel):
    id_token: str = Field(..., description="Token de Google. En DEMO_MODE, escribe el email del usuario.",
                          examples=["ana.garcia@santarosadelima.es"])


class RefreshIn(BaseModel):
    refresh_token: str


class Tokens(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class AccessToken(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ---------- Usuarios ----------
class Usuario(BaseModel):
    id: str
    nombre: str
    email: str
    servicio: str
    roles: list[str]
    estado: EstadoUsuario
    disponibilidad: list[str] = Field(default_factory=list, description="Huecos de guardia, p. ej. 'lunes-noche'")


class UsuarioPatch(BaseModel):
    estado: EstadoUsuario | None = None
    servicio: str | None = None


class RolesIn(BaseModel):
    roles: list[str] = Field(..., examples=[["personal", "supervision"]])


# ---------- Anuncios ----------
class AnuncioIn(BaseModel):
    titulo: str = Field(..., min_length=3)
    cuerpo: str
    servicio: str | None = Field(None, description="None = anuncio general para todo el centro")
    destacado: bool = False
    caduca: datetime | None = None


class Anuncio(AnuncioIn):
    id: str
    autor_id: str
    publicado: datetime


# ---------- Guardias ----------
class AsignarGuardiaIn(BaseModel):
    fecha: date = Field(..., examples=["2026-10-05"])
    franja: Franja = Field(..., examples=["noche"])
    plazas: int = Field(1, ge=1, le=5, description="Número de profesionales necesarios en ese hueco")


class GuardiaPatch(BaseModel):
    realizada_por: str = Field(..., description="Id del profesional que finalmente cubre la guardia",
                               examples=["u4"])


class Guardia(BaseModel):
    id: str
    fecha: date
    franja: Franja
    hueco: str = Field(..., description="Día de la semana + franja, p. ej. 'lunes-noche'")
    asignado_a: str = Field(..., description="Profesional al que le corresponde por ronda")
    realizada_por: str | None = Field(None, description="Profesional que finalmente la realiza")
    estado: Literal["asignada", "realizada"]


# ---------- Ausencias ----------
class AusenciaIn(BaseModel):
    tipo: TipoAusencia
    fecha: date
    dia_completo: bool = True
    franjas: list[Franja] = Field(default_factory=list, description="Solo si no es día completo")
    motivo: str | None = None


class Ausencia(AusenciaIn):
    id: str
    usuario_id: str
    estado: Literal["pendiente_justificante", "registrada", "justificada", "firmada"]
    justificante: str | None = None
    documento_generado: bool = False
    firma: str | None = None


class FirmaIn(BaseModel):
    metodo: Literal["manuscrita", "autofirma"]
    imagen_base64: str | None = Field(None, description="Imagen PNG de la firma capturada en pantalla")


# ---------- Tickets ----------
class TicketIn(BaseModel):
    tipo: TipoTicket
    titulo: str = Field(..., min_length=3)
    datos: dict[str, Any] = Field(default_factory=dict,
                                  description="Campos específicos del tipo de ticket (campo flexible)")


class TicketPatch(BaseModel):
    estado: EstadoTicket


class Ticket(TicketIn):
    id: str
    solicitante_id: str
    responsable_rol: str
    estado: EstadoTicket
    creado: datetime
    historial: list[dict[str, Any]] = Field(default_factory=list)


# ---------- Reservas ----------
class ReservaIn(BaseModel):
    recurso_id: str = Field(..., examples=["sala-reuniones-1"])
    inicio: datetime = Field(..., examples=["2026-10-06T10:00:00"])
    fin: datetime = Field(..., examples=["2026-10-06T11:00:00"])
    motivo: str | None = None


class Reserva(ReservaIn):
    id: str
    usuario_id: str


# ---------- Errores ----------
class Error(BaseModel):
    detail: str
