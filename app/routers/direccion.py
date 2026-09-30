"""Dashboard de dirección y registro de auditoría (acceso restringido al rol 'direccion')."""
from collections import Counter

from fastapi import APIRouter, Depends, Query

from app.db import db
from app.schemas import Error
from app.security import requiere_rol

router = APIRouter(tags=["Dirección"])
direccion = requiere_rol("direccion")


@router.get("/dashboard/kpis", summary="Indicadores para la dirección",
            responses={401: {"model": Error}, 403: {"model": Error}})
def kpis(_: dict = Depends(direccion)):
    guardias = list(db["guardias"].values())
    realizadas = [g for g in guardias if g["estado"] == "realizada"]
    rrss = [t for t in db["tickets"].values() if t["tipo"] == "rrss"]
    return {
        "usuarios_por_estado": Counter(u["estado"] for u in db["usuarios"].values()),
        "guardias": {
            "asignadas": len(guardias),
            "realizadas": len(realizadas),
            "cubiertas_por_otro_profesional": sum(g["realizada_por"] != g["asignado_a"] for g in realizadas),
            "contadores_por_hueco": db["contadores"],
        },
        "ausencias_por_tipo": Counter(a["tipo"] for a in db["ausencias"].values()),
        "tickets_por_tipo_y_estado": Counter(f"{t['tipo']}:{t['estado']}" for t in db["tickets"].values()),
        "rrss_porcentaje_publicado": round(100 * sum(t["estado"] == "finalizado" for t in rrss) / len(rrss), 1) if rrss else 0,
        "reservas_totales": len(db["reservas"]),
        "notificaciones_enviadas": len(db["notificaciones"]),
    }


@router.get("/auditoria", summary="Consultar el registro de auditoría",
            responses={401: {"model": Error}, 403: {"model": Error}})
def auditoria(usuario_id: str | None = Query(None), limit: int = Query(50, ge=1, le=500),
              _: dict = Depends(direccion)):
    registros = [r for r in db["auditoria"] if usuario_id is None or r["usuario_id"] == usuario_id]
    return list(reversed(registros))[:limit]
