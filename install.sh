#!/bin/sh
# Video Transcriber installer. POSIX sh — no bashisms — so it runs with
# plain `sh` on systems that don't have bash installed at all.
#
# Usage:
#   curl -fsSL https://raw.githubusercontent.com/EmaSleal/video-transcriber/main/install.sh | sh
#
# Installs video-transcriber as a global command via pipx (no manual git
# clone needed — pipx clones the repo internally). Re-running this script
# (e.g. to update, or to switch profiles) is safe.
set -eu

REPO_URL="https://github.com/EmaSleal/video-transcriber.git"
REF="main"

# `curl ... | sh` makes stdin the piped script source itself, not the
# keyboard — a plain `read` at that point silently consumes bytes of the
# script's own remaining source instead of waiting for the user, which is
# why the prompt below would be skipped entirely. Reading from /dev/tty
# (the real controlling terminal) sidesteps that. Falls back to an empty
# reply — caller applies its own default — when there's truly no terminal
# available at all (CI, no tty).
prompt_read() {
    printf "%s" "$1"
    if [ -t 0 ]; then
        read -r REPLY || REPLY=""
    elif { read -r REPLY < /dev/tty; } 2>/dev/null; then
        :
    else
        REPLY=""
    fi
}

echo "═══════════════════════════════════════"
echo "  Video Transcriber — instalador"
echo "═══════════════════════════════════════"
echo

# ── python3 ──────────────────────────────────────────────────────────────
if ! command -v python3 >/dev/null 2>&1; then
    echo "Error: python3 no está instalado. Instalalo y volvé a correr este script." >&2
    exit 1
fi

PY_VERSION="$(python3 -c 'import sys; print(f"{sys.version_info[0]}.{sys.version_info[1]}")')"
PY_MAJOR="${PY_VERSION%%.*}"
PY_MINOR="${PY_VERSION##*.}"
if [ "$PY_MAJOR" -lt 3 ] || { [ "$PY_MAJOR" -eq 3 ] && [ "$PY_MINOR" -lt 10 ]; }; then
    echo "Error: se requiere Python >= 3.10 (encontrado $PY_VERSION)." >&2
    exit 1
fi

# ── ffmpeg ───────────────────────────────────────────────────────────────
# imageio-ffmpeg trae un binario portable, así que esto no bloquea nada —
# solo avisa, por si el usuario prefiere el de su sistema (más rápido de
# arrancar, sin descarga la primera vez).
if ! command -v ffmpeg >/dev/null 2>&1; then
    echo "Nota: no se encontró ffmpeg en el PATH — imageio-ffmpeg instala"
    echo "un binario portable automáticamente, así que no es necesario,"
    echo "pero instalar el de tu sistema evita la descarga inicial."
    echo
fi

# ── pipx ─────────────────────────────────────────────────────────────────
if ! command -v pipx >/dev/null 2>&1; then
    echo "pipx no está instalado — instalando con pip..."
    python3 -m pip install --user pipx
    python3 -m pipx ensurepath
    echo
    echo "pipx se instaló. Puede que necesites abrir una terminal nueva"
    echo "(o correr 'source ~/.bashrc' / equivalente de tu shell) para que"
    echo "'pipx' quede en el PATH. Volvé a correr este script después de eso."
    exit 0
fi

# ── perfil de instalación ────────────────────────────────────────────────
echo "¿Querés el extra de dedup semántico de categorías (RAG, vía"
echo "chromadb + OpenAI embeddings)? Sin esto, la app cae al juez LLM o"
echo "al match exacto por nombre — funciona igual, solo menos preciso."
prompt_read "Instalar RAG? [y/N]: "
EXTRAS=""
case "$REPLY" in
    [Yy]*) EXTRAS="rag" ;;
esac

# ── instalación ──────────────────────────────────────────────────────────
if [ -n "$EXTRAS" ]; then
    SPEC="video-transcriber[$EXTRAS] @ git+${REPO_URL}@${REF}"
else
    SPEC="video-transcriber @ git+${REPO_URL}@${REF}"
fi

echo
echo "Instalando ($REF): $SPEC"
# uninstall-then-install rather than `pipx install --force` — pipx's
# uv-backed venv creation refuses to clear a venv from a prior session on
# some setups, so --force fails outright there. Uninstalling a package
# that isn't installed yet (first run) exits nonzero — expected, ignored.
# Also doubles as the update path: re-running this script pulls main again.
pipx uninstall video-transcriber >/dev/null 2>&1 || true
INSTALL_OK=1
if ! pipx install "$SPEC"; then
    INSTALL_OK=0
    # Some setup (AV/backup software on Windows most commonly, but the
    # lock can happen elsewhere too) can leave a half-deleted venv that
    # makes the install above fail even though the uninstall reported
    # success. Clean it by hand and retry once — same fix a human would do.
    VENVS_DIR="$(pipx environment --value PIPX_LOCAL_VENVS 2>/dev/null || true)"
    if [ -n "$VENVS_DIR" ]; then
        echo "La instalación falló — puede haber quedado un venv viejo trabado. Lo limpio y reintento una vez..."
        rm -rf "$VENVS_DIR/video-transcriber"
        if pipx install "$SPEC"; then
            INSTALL_OK=1
        fi
    fi
fi
if [ "$INSTALL_OK" -ne 1 ]; then
    echo "Error: no se pudo instalar video-transcriber." >&2
    exit 1
fi

echo
echo "✓ Listo. Corré 'video-transcriber' para arrancar."
echo "  Creá un .env en el directorio desde donde lo corras (o exportá"
echo "  variables de entorno) con LLM_BACKEND y la API key que corresponda"
echo "  — mirá example.env en el repo como referencia:"
echo "  https://github.com/EmaSleal/video-transcriber/blob/main/example.env"
echo
echo "Para actualizar a la última versión, volvé a correr este instalador."
