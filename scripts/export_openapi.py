"""Genera el sitio estático de documentación a partir del código de FastAPI.

Uso:
    python scripts/export_openapi.py            # genera la carpeta site/
    python scripts/export_openapi.py public     # genera la carpeta public/ (GitLab Pages)

Variables de entorno opcionales:
    PUBLIC_API_URL  URL de la API desplegada (p. ej. https://mi-api.onrender.com).
                    Si se indica, aparece como primer servidor en "Try it out".
"""
import json
import os
import shutil
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from app.main import app  # noqa: E402

destino = RAIZ / (sys.argv[1] if len(sys.argv) > 1 else "site")
destino.mkdir(exist_ok=True)

esquema = app.openapi()

# Servidores contra los que se ejecuta "Try it out" desde la página publicada
servidores = [{"url": "http://127.0.0.1:8000", "description": "Servidor local (uvicorn app.main:app)"}]
url_publica = os.getenv("PUBLIC_API_URL", "").strip().rstrip("/")
if url_publica:
    servidores.insert(0, {"url": url_publica, "description": "API desplegada"})
esquema["servers"] = servidores

(destino / "openapi.json").write_text(json.dumps(esquema, ensure_ascii=False, indent=2), encoding="utf-8")

# Contrato escrito a mano (API First), para poder compararlo con el generado
for yaml in (RAIZ / "docs").glob("*.yaml"):
    shutil.copy(yaml, destino / yaml.name)

# Página de Swagger UI
if destino.name != "site":
    shutil.copy(RAIZ / "site" / "index.html", destino / "index.html")

print(f"Documentación generada en {destino.relative_to(RAIZ)}/ "
      f"({len(esquema['paths'])} rutas, servidores: {[s['url'] for s in servidores]})")
