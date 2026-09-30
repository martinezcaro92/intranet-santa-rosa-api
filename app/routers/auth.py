"""Autenticación: login con Google (OAuth), renovación de token y perfil del usuario."""
from fastapi import APIRouter, Depends, HTTPException, status

from app import config
from app.db import auditar, db, nuevo_id
from app.schemas import AccessToken, Error, LoginGoogle, RefreshIn, Tokens, Usuario
from app.security import crear_token, decodificar, usuario_actual

router = APIRouter(prefix="/auth", tags=["Autenticación"])


@router.post("/google", response_model=Tokens, summary="Iniciar sesión con Google (OAuth)",
             responses={403: {"model": Error, "description": "Usuario pendiente de confirmación"},
                        501: {"model": Error, "description": "Verificación real de Google no configurada"}})
def login_google(datos: LoginGoogle):
    """Valida el token de Google y devuelve los tokens JWT de la intranet.

    **Modo demostración (DEMO_MODE=true):** en `id_token` se escribe directamente el email
    de un usuario de ejemplo. Si el email no existe, se da de alta en estado *pendiente*
    y debe aprobarlo un administrador (`PATCH /usuarios/{id}`).
    """
    if not config.DEMO_MODE:
        raise HTTPException(status.HTTP_501_NOT_IMPLEMENTED,
                            "Verificación real no configurada: usa google-auth para validar el id_token")
    email = datos.id_token.strip().lower()
    usuario = next((u for u in db["usuarios"].values() if u["email"] == email), None)
    if usuario is None:
        nuevo = {"id": nuevo_id("u"), "nombre": email.split("@")[0], "email": email, "servicio": "Sin asignar",
                 "roles": ["personal"], "estado": "pendiente", "disponibilidad": []}
        db["usuarios"][nuevo["id"]] = nuevo
        auditar(nuevo["id"], "alta_oauth", email)
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Alta registrada: pendiente de confirmación por un administrador")
    if usuario["estado"] != "activo":
        raise HTTPException(status.HTTP_403_FORBIDDEN, f"Usuario en estado '{usuario['estado']}'")
    auditar(usuario["id"], "login")
    return Tokens(access_token=crear_token(usuario["id"], "access"),
                  refresh_token=crear_token(usuario["id"], "refresh"))


@router.post("/refresh", response_model=AccessToken, summary="Renovar el access token",
             responses={401: {"model": Error}})
def refrescar(datos: RefreshIn):
    usuario_id = decodificar(datos.refresh_token, "refresh")
    return AccessToken(access_token=crear_token(usuario_id, "access"))


@router.get("/me", response_model=Usuario, summary="Datos del usuario autenticado",
            responses={401: {"model": Error}})
def perfil(usuario: dict = Depends(usuario_actual)):
    return usuario
