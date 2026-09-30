"""Autenticación con JWT (access / refresh) y control de permisos mediante Depends()."""
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app import config
from app.db import db

bearer = HTTPBearer(auto_error=False, scheme_name="bearerAuth",
                    description="Pega aquí el access_token obtenido en POST /auth/google")


def crear_token(usuario_id: str, tipo: str) -> str:
    """Genera un JWT de tipo 'access' (corta duración) o 'refresh' (larga duración)."""
    ahora = datetime.now(timezone.utc)
    duracion = (timedelta(minutes=config.ACCESS_TOKEN_MINUTES) if tipo == "access"
                else timedelta(days=config.REFRESH_TOKEN_DAYS))
    payload = {"sub": usuario_id, "tipo": tipo, "iat": ahora, "exp": ahora + duracion}
    return jwt.encode(payload, config.SECRET_KEY, algorithm=config.ALGORITHM)


def decodificar(token: str, tipo_esperado: str) -> str:
    """Valida el token y devuelve el id del usuario (claim 'sub')."""
    try:
        payload = jwt.decode(token, config.SECRET_KEY, algorithms=[config.ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token caducado")
    except jwt.InvalidTokenError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token no válido")
    if payload.get("tipo") != tipo_esperado:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, f"Se esperaba un token de tipo '{tipo_esperado}'")
    return payload["sub"]


def usuario_actual(cred: HTTPAuthorizationCredentials | None = Depends(bearer)) -> dict:
    """Dependencia base: exige un access token válido de un usuario activo."""
    if cred is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "No autenticado",
                            headers={"WWW-Authenticate": "Bearer"})
    usuario = db["usuarios"].get(decodificar(cred.credentials, "access"))
    if usuario is None or usuario["estado"] != "activo":
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Usuario no válido o no activo")
    return usuario


def requiere_rol(*roles: str):
    """Fábrica de dependencias: exige al menos uno de los roles indicados (admin siempre pasa)."""
    def comprobar(usuario: dict = Depends(usuario_actual)) -> dict:
        if "admin" in usuario["roles"] or set(roles) & set(usuario["roles"]):
            return usuario
        raise HTTPException(status.HTTP_403_FORBIDDEN,
                            f"Se requiere uno de estos roles: {', '.join(roles)}")
    return comprobar
