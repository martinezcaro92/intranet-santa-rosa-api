"""Tablón de anuncios segmentado por servicio."""
from datetime import datetime

from fastapi import APIRouter, Depends, status

from app.db import auditar, db, notificar, nuevo_id
from app.schemas import Anuncio, AnuncioIn, Error
from app.security import requiere_rol, usuario_actual

router = APIRouter(prefix="/anuncios", tags=["Anuncios"])


@router.get("", response_model=list[Anuncio], summary="Ver el tablón de anuncios",
            responses={401: {"model": Error}})
def listar(usuario: dict = Depends(usuario_actual)):
    """Devuelve los anuncios generales y los del servicio del usuario.

    Los anuncios caducados no se muestran (borrado lógico). Los destacados aparecen primero.
    """
    ahora = datetime.now()
    visibles = [a for a in db["anuncios"].values()
                if (a["servicio"] in (None, usuario["servicio"]))
                and (a["caduca"] is None or datetime.fromisoformat(str(a["caduca"])) > ahora)]
    visibles.sort(key=lambda a: str(a["publicado"]), reverse=True)  # más recientes primero
    visibles.sort(key=lambda a: not a["destacado"])                 # destacados arriba
    return visibles


@router.post("", response_model=Anuncio, status_code=status.HTTP_201_CREATED, summary="Publicar un anuncio",
             responses={401: {"model": Error}, 403: {"model": Error}})
def crear(datos: AnuncioIn, usuario: dict = Depends(requiere_rol("direccion", "supervision"))):
    anuncio = {"id": nuevo_id("a"), "autor_id": usuario["id"], "publicado": datetime.now().isoformat(timespec="seconds"),
               **datos.model_dump(mode="json")}
    db["anuncios"][anuncio["id"]] = anuncio
    if anuncio["destacado"]:
        notificar(anuncio["servicio"] or "todos", f"Anuncio destacado: {anuncio['titulo']}")
    auditar(usuario["id"], "crear_anuncio", anuncio["id"])
    return anuncio
