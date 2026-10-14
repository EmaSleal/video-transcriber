"""
Defaults de configuración leídos directo de os.environ (vía .env +
python-dotenv). A diferencia de call-copilot, este proyecto no tiene panel
de Configuración en caliente — cambiar un valor requiere editar .env y
reiniciar.

Módulo de solo lectura: cero I/O más allá de os.getenv.
"""

import os

DEFAULT_WHISPER_MODEL_VIDEO = "base"
DEFAULT_LANGUAGE = "es"

WHISPER_SIZES = ("tiny", "base", "small", "medium", "large-v3", "large-v3-turbo")


def _getenv_or_default(key: str, default: str) -> str:
    """os.getenv(key) tratando la cadena vacía como "no configurado"."""
    return os.getenv(key) or default


def whisper_model_video() -> str:
    """Tamaño de modelo Whisper para la transcripción batch de video."""
    return _getenv_or_default("WHISPER_MODEL_VIDEO", DEFAULT_WHISPER_MODEL_VIDEO)


def language() -> str:
    """Idioma activo de la UI ('es' o 'en'). Default: 'es'."""
    return _getenv_or_default("LANGUAGE", DEFAULT_LANGUAGE)
