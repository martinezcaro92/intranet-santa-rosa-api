"""Comprueba que la documentación publicada (docs/openapi.json) coincide con el código."""
import json

from app.documentacion import FICHERO, esquema_publico


def test_openapi_publicado_esta_actualizado():
    assert FICHERO.exists(), "Falta docs/openapi.json. Ejecuta: python -m app.documentacion"
    publicado = json.loads(FICHERO.read_text(encoding="utf-8"))
    actual = esquema_publico()
    publicado.pop("servers", None)
    actual.pop("servers", None)
    assert publicado == actual, (
        "docs/openapi.json está desactualizado respecto al código. "
        "Ejecuta: python -m app.documentacion  y haz commit del fichero."
    )
