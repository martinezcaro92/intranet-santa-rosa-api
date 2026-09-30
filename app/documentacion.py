"""Generación de la documentación pública de la API (carpeta docs/ para GitHub Pages).

Uso (desde la raíz del proyecto):
    python -m app.documentacion

Genera docs/openapi.json a partir del código de FastAPI. Después hay que hacer
commit y push del fichero para que GitHub Pages lo publique.

Variable de entorno opcional:
    PUBLIC_API_URL  URL de la API desplegada; aparece como primer servidor en "Try it out".
"""
import json
import os
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
FICHERO = RAIZ / "docs" / "openapi.json"


def esquema_publico() -> dict:
    """Esquema OpenAPI de la aplicación con los servidores para 'Try it out'."""
    from app.main import app

    app.openapi_schema = None          # fuerza a regenerarlo desde el código actual
    esquema = app.openapi()
    servidores = [{"url": "http://127.0.0.1:8000", "description": "Servidor local (python -m uvicorn app.main:app)"}]
    url_publica = os.getenv("PUBLIC_API_URL", "").strip().rstrip("/")
    if url_publica:
        servidores.insert(0, {"url": url_publica, "description": "API desplegada"})
    return {**esquema, "servers": servidores}


def generar() -> Path:
    FICHERO.write_text(json.dumps(esquema_publico(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return FICHERO


if __name__ == "__main__":
    ruta = generar()
    print(f"Generado {ruta.relative_to(RAIZ)}. Haz commit y push para publicarlo en GitHub Pages.")
