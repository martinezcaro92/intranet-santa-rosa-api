"""Ausencias del personal: registro, justificante, documento PDF y firma.

Máquina de estados:
    genérica:              pendiente_justificante -> justificada -> firmada
    administrativa/externa: registrada -> firmada
"""
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import Response

from app.db import auditar, db, notificar, nuevo_id
from app.schemas import Ausencia, AusenciaIn, Error, FirmaIn
from app.security import usuario_actual
from app.services.pdf import generar_pdf

router = APIRouter(prefix="/ausencias", tags=["Ausencias"])


def _propia(ausencia_id: str, usuario: dict) -> dict:
    ausencia = db["ausencias"].get(ausencia_id)
    if ausencia is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Ausencia no encontrada")
    if ausencia["usuario_id"] != usuario["id"] and not {"admin", "direccion"} & set(usuario["roles"]):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Solo puedes gestionar tus propias ausencias")
    return ausencia


@router.post("", response_model=Ausencia, status_code=status.HTTP_201_CREATED, summary="Registrar una ausencia",
             responses={401: {"model": Error}})
def crear(datos: AusenciaIn, usuario: dict = Depends(usuario_actual)):
    ausencia = {"id": nuevo_id("aus"), "usuario_id": usuario["id"],
                "estado": "pendiente_justificante" if datos.tipo == "generica" else "registrada",
                "justificante": None, "documento_generado": False, "firma": None,
                **datos.model_dump(mode="json")}
    db["ausencias"][ausencia["id"]] = ausencia
    notificar("supervision", f"Nueva ausencia de {usuario['nombre']} el {ausencia['fecha']}")
    auditar(usuario["id"], "crear_ausencia", ausencia["id"])
    return ausencia


@router.post("/{ausencia_id}/justificante", response_model=Ausencia, summary="Adjuntar justificante",
             responses={404: {"model": Error}, 409: {"model": Error}})
async def justificar(ausencia_id: str, archivo: UploadFile = File(..., description="PDF o imagen del justificante"),
                     usuario: dict = Depends(usuario_actual)):
    """Solo aplica a las ausencias de tipo *genérica*. El fichero no se guarda en esta demo."""
    ausencia = _propia(ausencia_id, usuario)
    if ausencia["estado"] != "pendiente_justificante":
        raise HTTPException(status.HTTP_409_CONFLICT, "Esta ausencia no admite justificante en su estado actual")
    await archivo.read()
    ausencia.update(justificante=archivo.filename, estado="justificada")
    auditar(usuario["id"], "adjuntar_justificante", ausencia_id)
    return ausencia


@router.get("/{ausencia_id}/pdf", summary="Descargar el documento PDF de la ausencia",
            response_class=Response,
            responses={200: {"content": {"application/pdf": {}}, "description": "Documento PDF"},
                       404: {"model": Error}, 409: {"model": Error}})
def documento(ausencia_id: str, usuario: dict = Depends(usuario_actual)):
    """Genera el PDF autocompletando los datos personales del perfil (en el proyecto: cuenta de Google)."""
    ausencia = _propia(ausencia_id, usuario)
    if ausencia["estado"] == "pendiente_justificante":
        raise HTTPException(status.HTTP_409_CONFLICT, "Falta adjuntar el justificante")
    titular = db["usuarios"][ausencia["usuario_id"]]
    horario = "Día completo" if ausencia["dia_completo"] else ", ".join(ausencia["franjas"])
    pdf = generar_pdf("Centro Médico Santa Rosa de Lima · Comunicación de ausencia", [
        f"Profesional: {titular['nombre']} ({titular['email']})",
        f"Servicio: {titular['servicio']}",
        f"Tipo de ausencia: {ausencia['tipo']}",
        f"Fecha: {ausencia['fecha']}   Horario: {horario}",
        f"Motivo: {ausencia['motivo'] or '-'}",
        f"Justificante: {ausencia['justificante'] or 'No aplica'}",
        f"Estado: {ausencia['estado']}",
        "",
        "Firma: ______________________________",
    ])
    ausencia["documento_generado"] = True
    auditar(usuario["id"], "generar_pdf_ausencia", ausencia_id)
    return Response(pdf, media_type="application/pdf",
                    headers={"Content-Disposition": f'inline; filename="ausencia-{ausencia_id}.pdf"'})


@router.post("/{ausencia_id}/firma", response_model=Ausencia, summary="Firmar el documento",
             responses={404: {"model": Error}, 409: {"model": Error}, 422: {"model": Error},
                        501: {"model": Error, "description": "AutoFirma no disponible en la demo"}})
def firmar(ausencia_id: str, datos: FirmaIn, usuario: dict = Depends(usuario_actual)):
    """Firma manuscrita (imagen capturada en pantalla) o electrónica con AutoFirma (mejor esfuerzo)."""
    ausencia = _propia(ausencia_id, usuario)
    if not ausencia["documento_generado"]:
        raise HTTPException(status.HTTP_409_CONFLICT, "Genera primero el PDF (GET /ausencias/{id}/pdf)")
    if ausencia["estado"] == "firmada":
        raise HTTPException(status.HTTP_409_CONFLICT, "El documento ya está firmado")
    if datos.metodo == "autofirma":
        raise HTTPException(status.HTTP_501_NOT_IMPLEMENTED, "AutoFirma requiere certificado y la aplicación local")
    if not datos.imagen_base64:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "La firma manuscrita requiere imagen_base64")
    ausencia.update(firma="manuscrita", estado="firmada")
    auditar(usuario["id"], "firmar_ausencia", ausencia_id)
    return ausencia
