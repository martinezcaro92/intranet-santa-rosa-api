"""Gestión de usuarios y roles (solo administración)."""
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.db import ROLES_VALIDOS, auditar, db
from app.schemas import EstadoUsuario, Error, RolesIn, Usuario, UsuarioPatch
from app.security import requiere_rol

router = APIRouter(prefix="/usuarios", tags=["Usuarios"])
solo_admin = requiere_rol("admin")


def _buscar(usuario_id: str) -> dict:
    usuario = db["usuarios"].get(usuario_id)
    if usuario is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Usuario no encontrado")
    return usuario


@router.get("", response_model=list[Usuario], summary="Listar usuarios",
            responses={401: {"model": Error}, 403: {"model": Error}})
def listar(estado: EstadoUsuario | None = Query(None, description="Filtrar por estado"),
           _: dict = Depends(solo_admin)):
    return [u for u in db["usuarios"].values() if estado is None or u["estado"] == estado]


@router.patch("/{usuario_id}", response_model=Usuario, summary="Modificar parcialmente un usuario",
              responses={404: {"model": Error}, 403: {"model": Error}})
def modificar(usuario_id: str, cambios: UsuarioPatch, admin: dict = Depends(solo_admin)):
    """Actualización PARCIAL: solo se modifican los campos enviados.

    Uso típico: aprobar un alta pendiente enviando `{"estado": "activo"}`.
    """
    usuario = _buscar(usuario_id)
    datos = cambios.model_dump(exclude_unset=True)
    usuario.update(datos)
    auditar(admin["id"], "modificar_usuario", f"{usuario_id}: {datos}")
    return usuario


@router.put("/{usuario_id}/roles", response_model=Usuario, summary="Sustituir los roles de un usuario",
            responses={404: {"model": Error}, 422: {"model": Error}})
def asignar_roles(usuario_id: str, datos: RolesIn, admin: dict = Depends(solo_admin)):
    """Sustitución COMPLETA de la lista de roles (por eso es PUT y no PATCH)."""
    usuario = _buscar(usuario_id)
    invalidos = set(datos.roles) - ROLES_VALIDOS
    if invalidos:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, f"Roles no válidos: {sorted(invalidos)}")
    usuario["roles"] = sorted(set(datos.roles) | {"personal"})
    auditar(admin["id"], "asignar_roles", f"{usuario_id}: {usuario['roles']}")
    return usuario
