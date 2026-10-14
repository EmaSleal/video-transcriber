"""
Traducción ES/EN en tiempo de ejecución para el TUI.

Fuente de verdad del idioma activo: el singleton a nivel de módulo definido
acá, inicializado una sola vez al importar desde
src.core.config_defaults.language().
"""

from src.core.config_defaults import language as _default_language
from src.i18n.en import EN_STRINGS
from src.i18n.es import ES_STRINGS

_TABLES: dict[str, dict[str, str]] = {"es": ES_STRINGS, "en": EN_STRINGS}
_DEFAULT_LANGUAGE = "es"

_current_language: str = _default_language()


def get_language() -> str:
    """Idioma activo actual ('es' o 'en')."""
    return _current_language


def set_language(language: str) -> None:
    """Actualiza el idioma activo en memoria. No persiste a .env."""
    global _current_language
    _current_language = language


def t(key: str, /, **kwargs) -> str:
    """
    Traduce `key` al idioma activo.

    `key` es solo posicional a propósito: evita que un kwarg nombrado
    "key" colisione con el parámetro.

    Si la key falta en la tabla activa, cae a la tabla default ('es'); si
    tampoco está ahí, devuelve la key cruda — nunca rompe la UI por un typo
    de traducción.
    """
    template = _TABLES[_current_language].get(key)
    if template is None:
        template = _TABLES[_DEFAULT_LANGUAGE].get(key, key)
    return template.format(**kwargs) if kwargs else template
