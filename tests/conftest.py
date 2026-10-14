"""
Test configuration: stub out heavy third-party dependencies that are not
installed in the CI/test environment (openai, anthropic, chromadb, textual,
whisper, etc.) so that unit tests can import modules without installing
the full production stack.
"""

import sys
from unittest.mock import MagicMock

import pytest


def _mock_module(name: str, **attrs) -> MagicMock:
    m = MagicMock()
    for k, v in attrs.items():
        setattr(m, k, v)
    sys.modules[name] = m
    return m


# ── openai ────────────────────────────────────────────────────────────────────
if "openai" not in sys.modules:
    _mock_module("openai")
    _mock_module("openai.AsyncOpenAI")

# ── anthropic ─────────────────────────────────────────────────────────────────
if "anthropic" not in sys.modules:
    _mock_module("anthropic")

# ── chromadb ──────────────────────────────────────────────────────────────────
if "chromadb" not in sys.modules:
    _mock_module("chromadb")

# ── whisper (openai-whisper, used by src/video/pipeline.py) ───────────────────
if "whisper" not in sys.modules:
    _mock_module("whisper")

# ── textual ───────────────────────────────────────────────────────────────────
for _name in [
    "textual",
    "textual.app",
    "textual.widgets",
    "textual.containers",
    "textual.screen",
    "textual.reactive",
    "textual.binding",
    "textual.message",
    "textual.css",
    "textual.css.query",
]:
    if _name not in sys.modules:
        _mock_module(_name)

# ── dotenv ────────────────────────────────────────────────────────────────────
if "dotenv" not in sys.modules:
    _mock_module("dotenv")
    _mock_module("python_dotenv")


# ── i18n: shared language fixtures ──────────────────────────────────────────
# Pin the active src.i18n language for a test body, restore after.

@pytest.fixture
def english():
    import src.i18n as i18n
    original = i18n.get_language()
    i18n.set_language("en")
    yield
    i18n.set_language(original)


@pytest.fixture
def spanish():
    import src.i18n as i18n
    original = i18n.get_language()
    i18n.set_language("es")
    yield
    i18n.set_language(original)
