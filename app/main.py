"""Punto de entrada de la API de la intranet del Centro Médico Santa Rosa de Lima.

Ejecutar:  uvicorn app.main:app --reload
Documentación interactiva:  http://127.0.0.1:8000/docs
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from app import config
from app.routers import anuncios, auth, ausencias, direccion, guardias, reservas, tickets, usuarios

DESCRIPCION = """
API de ejemplo de la **intranet de gestión** del Centro Médico Santa Rosa de Lima.

Proyecto didáctico del Proyecto Intermodular (DAW): muestra cómo definir e implementar
los endpoints de una intranet con **FastAPI**, **JWT** y control de permisos por **roles**.

**Cómo probarla:** ejecuta `POST /api/v1/auth/google` con el email de un usuario de ejemplo
(p. ej. `laura.martinez@santarosadelima.es`), copia el `access_token`, pulsa **Authorize**
y pégalo. Los datos se guardan en memoria y se reinician al reiniciar el servidor.
"""

TAGS = [
    {"name": "Autenticación", "description": "Login con Google (OAuth) y tokens JWT"},
    {"name": "Usuarios", "description": "Altas, estados y roles (administración)"},
    {"name": "Anuncios", "description": "Tablón de anuncios por servicio"},
    {"name": "Guardias", "description": "Asignación de guardias por rondas"},
    {"name": "Ausencias", "description": "Ausencias, justificante, PDF y firma"},
    {"name": "Tickets", "description": "Mantenimiento, suministros y publicaciones RRSS"},
    {"name": "Reservas", "description": "Salas y equipos sin solapamientos"},
    {"name": "Dirección", "description": "Indicadores y auditoría"},
]

app = FastAPI(title="Intranet · Centro Médico Santa Rosa de Lima", version="1.0.0",
              description=DESCRIPCION, openapi_tags=TAGS)

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

for modulo in (auth, usuarios, anuncios, guardias, ausencias, tickets, reservas, direccion):
    app.include_router(modulo.router, prefix=config.API_PREFIX)


@app.get("/", include_in_schema=False)
def inicio():
    return RedirectResponse("/docs")
