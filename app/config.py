"""Configuración de la aplicación a partir de variables de entorno (fichero .env)."""
import os

from dotenv import load_dotenv

load_dotenv()

SECRET_KEY: str = os.getenv("SECRET_KEY", "cambia-esta-clave-antes-de-desplegar-0123456789")
ALGORITHM: str = "HS256"
ACCESS_TOKEN_MINUTES: int = int(os.getenv("ACCESS_TOKEN_MINUTES", "30"))
REFRESH_TOKEN_DAYS: int = int(os.getenv("REFRESH_TOKEN_DAYS", "7"))

# En modo demostración, el "id_token" de Google se sustituye por el email del usuario.
DEMO_MODE: bool = os.getenv("DEMO_MODE", "true").lower() == "true"

API_PREFIX: str = "/api/v1"
