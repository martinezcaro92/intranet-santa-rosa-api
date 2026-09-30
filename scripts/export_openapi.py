"""Atajo equivalente a:  python -m app.documentacion"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.documentacion import RAIZ, generar  # noqa: E402

print(f"Generado {generar().relative_to(RAIZ)}. Haz commit y push para publicarlo en GitHub Pages.")
