"""Almacén de datos EN MEMORIA con datos de ejemplo.

En el proyecto real este módulo se sustituye por el acceso a MongoDB (colecciones)
y Redis (caché, sesiones y colas). Los datos se reinician cada vez que se arranca
el servidor.
"""
from copy import deepcopy
from datetime import datetime, timedelta

ROLES_VALIDOS = {"personal", "admin", "direccion", "supervision", "mantenimiento", "suministros", "rrss"}

# Rol responsable de cada tipo de ticket (entidad genérica de solicitudes)
RESPONSABLE_TICKET = {"mantenimiento": "mantenimiento", "suministros": "suministros", "rrss": "rrss"}

DIAS = ["lunes", "martes", "miercoles", "jueves", "viernes", "sabado", "domingo"]

_ahora = datetime.now().replace(minute=0, second=0, microsecond=0)

_SEED = {
    "usuarios": {
        "u1": {"id": "u1", "nombre": "Laura Martínez Ros", "email": "laura.martinez@santarosadelima.es",
               "servicio": "Dirección", "roles": ["personal", "admin", "direccion"], "estado": "activo",
               "disponibilidad": []},
        "u2": {"id": "u2", "nombre": "Carlos Ruiz Pérez", "email": "carlos.ruiz@santarosadelima.es",
               "servicio": "Supervisión", "roles": ["personal", "supervision"], "estado": "activo",
               "disponibilidad": ["lunes-tarde", "miercoles-tarde"]},
        "u3": {"id": "u3", "nombre": "Ana García López", "email": "ana.garcia@santarosadelima.es",
               "servicio": "Urgencias", "roles": ["personal"], "estado": "activo",
               "disponibilidad": [f"{d}-noche" for d in DIAS] + ["lunes-manana", "martes-manana"]},
        "u4": {"id": "u4", "nombre": "Javier López Sáez", "email": "javier.lopez@santarosadelima.es",
               "servicio": "Urgencias", "roles": ["personal"], "estado": "activo",
               "disponibilidad": [f"{d}-noche" for d in DIAS] + ["lunes-manana"]},
        "u5": {"id": "u5", "nombre": "Marta Sánchez Gil", "email": "marta.sanchez@santarosadelima.es",
               "servicio": "Pediatría", "roles": ["personal"], "estado": "activo",
               "disponibilidad": [f"{d}-noche" for d in DIAS] + ["martes-manana"]},
        "u6": {"id": "u6", "nombre": "Pedro Gómez Vera", "email": "pedro.gomez@santarosadelima.es",
               "servicio": "Mantenimiento", "roles": ["personal", "mantenimiento"], "estado": "activo",
               "disponibilidad": []},
        "u7": {"id": "u7", "nombre": "Lucía Fernández Mora", "email": "lucia.fernandez@santarosadelima.es",
               "servicio": "Administración", "roles": ["personal", "suministros"], "estado": "activo",
               "disponibilidad": []},
        "u8": {"id": "u8", "nombre": "Sergio Navarro Cano", "email": "sergio.navarro@santarosadelima.es",
               "servicio": "Comunicación", "roles": ["personal", "rrss"], "estado": "activo",
               "disponibilidad": []},
        "u9": {"id": "u9", "nombre": "Elena Torres Ibáñez", "email": "elena.torres@santarosadelima.es",
               "servicio": "Pediatría", "roles": ["personal"], "estado": "pendiente",
               "disponibilidad": []},
    },
    # Contador de guardias REALIZADAS por hueco horario y profesional.
    # Reproduce el ejemplo de la memoria técnica: A (u3) tiene 3 y B (u4) tiene 5.
    "contadores": {f"{d}-noche": {"u3": 3, "u4": 5, "u5": 4} for d in DIAS},
    "anuncios": {
        "a1": {"id": "a1", "titulo": "Nuevo protocolo de triaje",
               "cuerpo": "A partir del lunes se aplica el protocolo de triaje actualizado.",
               "autor_id": "u1", "servicio": None, "destacado": True,
               "publicado": (_ahora - timedelta(days=1)).isoformat(), "caduca": None},
        "a2": {"id": "a2", "titulo": "Sesión clínica de Pediatría",
               "cuerpo": "Jueves a las 14:00 en el aula de formación.",
               "autor_id": "u2", "servicio": "Pediatría", "destacado": False,
               "publicado": (_ahora - timedelta(hours=5)).isoformat(),
               "caduca": (_ahora + timedelta(days=7)).isoformat()},
        "a3": {"id": "a3", "titulo": "Simulacro de evacuación (caducado)",
               "cuerpo": "Este anuncio está caducado y no debe mostrarse (borrado lógico).",
               "autor_id": "u1", "servicio": None, "destacado": False,
               "publicado": (_ahora - timedelta(days=30)).isoformat(),
               "caduca": (_ahora - timedelta(days=20)).isoformat()},
    },
    "guardias": {},
    "ausencias": {},
    "tickets": {
        "t1": {"id": "t1", "tipo": "mantenimiento", "titulo": "Monitor averiado en box 3",
               "solicitante_id": "u3", "responsable_rol": "mantenimiento", "estado": "pendiente",
               "datos": {"dispositivo": "Monitor de constantes", "ubicacion": "Urgencias · Box 3"},
               "creado": (_ahora - timedelta(hours=3)).isoformat(), "historial": []},
    },
    "recursos": {
        "sala-reuniones-1": {"id": "sala-reuniones-1", "nombre": "Sala de reuniones 1", "tipo": "espacio"},
        "aula-formacion": {"id": "aula-formacion", "nombre": "Aula de formación", "tipo": "espacio"},
        "ecografo-portatil": {"id": "ecografo-portatil", "nombre": "Ecógrafo portátil", "tipo": "equipo"},
        "proyector-1": {"id": "proyector-1", "nombre": "Proyector 1", "tipo": "equipo"},
    },
    "reservas": {},
    "auditoria": [],
    "notificaciones": [],
}

db: dict = deepcopy(_SEED)
_secuencia = {"n": 100}


def reset() -> None:
    """Restaura los datos de ejemplo (se usa en los tests)."""
    db.clear()
    db.update(deepcopy(_SEED))
    _secuencia["n"] = 100


def nuevo_id(prefijo: str) -> str:
    _secuencia["n"] += 1
    return f"{prefijo}{_secuencia['n']}"


def auditar(usuario_id: str | None, accion: str, detalle: str = "") -> None:
    """Registro de auditoría: usuario, acción y fecha/hora de toda acción relevante."""
    db["auditoria"].append({"fecha": datetime.now().isoformat(timespec="seconds"),
                            "usuario_id": usuario_id, "accion": accion, "detalle": detalle})


def notificar(destino: str, mensaje: str) -> None:
    """Notificación SIMULADA. En el proyecto real: Web Push (pywebpush) y email (fastapi-mail)."""
    db["notificaciones"].append({"fecha": datetime.now().isoformat(timespec="seconds"),
                                 "destino": destino, "mensaje": mensaje})
