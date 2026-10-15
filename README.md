# Video Transcriber

[![CI](https://github.com/EmaSleal/video-transcriber/actions/workflows/ci.yml/badge.svg)](https://github.com/EmaSleal/video-transcriber/actions/workflows/ci.yml)

TUI (Textual) para bajar un video de YouTube, transcribirlo, clasificar
los segmentos por categoría y generar un reporte HTML navegable.

Extraído de [call-copilot](https://github.com/EmaSleal/call-copilot), donde
vivía como una segunda feature dentro de un copiloto de llamadas en vivo —
dos productos distintos que solo compartían base de datos y pantalla. Acá
tiene su propia base de datos (`categories`/`video_sessions`/`segments`),
sin acoplamiento con call-copilot.

## Arquitectura

```
URL de YouTube ──► yt-dlp (audio+video) ──► Whisper (transcripción) ──►
  clasificador LLM (por categoría) ──► SQLite ──► reporte HTML
```

- **`src/video/pipeline.py`** — orquesta todo el flujo, pensado para correr
  vía `run_in_executor` así no bloquea la TUI mientras procesa.
- **`src/video/classifier.py`** — clasificación batch de segmentos,
  sugerencia de categorías nuevas a partir de segmentos "Otro", juez de
  duplicados y agrupamiento de categorías bajo un padre común. Backend LLM
  intercambiable (`LLM_BACKEND=ollama|gpt|claude`).
- **`src/processing/category_dedup.py`** — dedup híbrido de categorías
  sugeridas: match exacto por nombre → embeddings (si hay
  `OPENAI_API_KEY`) → juez LLM como fallback. Nunca bloquea: cualquier
  falla resuelve a "categoría nueva", nunca rompe el flujo.
- **`src/rag/`** — stores Chroma-backed opcionales (dedup semántico de
  categorías, búsqueda semántica de segmentos). La app funciona igual sin
  `chromadb` instalado — cae a substring/LLM-judge.

## Instalación

Sin clonar el repo — instala como comando global vía [pipx](https://pipx.pypa.io)
(el script clona internamente):

```bash
curl -fsSL https://raw.githubusercontent.com/EmaSleal/video-transcriber/main/install.sh | sh
```

Config y datos quedan en `~/.video-transcriber/`, no en el directorio
desde donde lo corras. Volvé a correr el instalador para actualizar a la
última versión de `main` — todavía no hay releases etiquetados.

También instalable directo con el extra `rag` de `pyproject.toml`:

```bash
pipx install "video-transcriber[rag] @ git+https://github.com/EmaSleal/video-transcriber.git@main"
```

### Setup (desde el repo, para desarrollo)

```bash
git clone https://github.com/EmaSleal/video-transcriber.git
cd video-transcriber
cp example.env .env   # completá LLM_BACKEND y la API key que corresponda
./run.sh               # crea/activa el venv, instala deps, arranca la TUI
```

`LLM_BACKEND=ollama` (default) no necesita API key — requiere tener
[Ollama](https://ollama.com) corriendo local con un modelo pulleado
(`ollama pull qwen3:4b`).

## Uso

Tab **Video**: pegá una URL de YouTube y apretá "Procesar". El progreso se
muestra en vivo; al terminar, la sesión aparece en la tabla de abajo.
Seleccionarla (Enter) abre un modal con opciones: abrir el reporte HTML,
exportarlo como `.zip` portable, analizar los segmentos "Otro" en busca de
categorías nuevas, reprocesar, o borrar.

Tab **Categorías**: CRUD de la taxonomía — un nivel de subcategorías
(`└─`), color por categoría.

## Base de datos

SQLite en `data/app.db` (dev checkout) o `~/.video-transcriber/data/app.db`
(instalado fuera de un checkout de git). Cuatro tablas: `categories`,
`video_sessions`, `segments`, `audit_log`.

## Qué quedó deliberadamente afuera de este primer corte

Al extraer esto de call-copilot, se dejaron afuera a propósito (no son
parte del flujo núcleo "transcribir → clasificar → reporte"):

- **Servidor MCP** — call-copilot exponía `start_video_processing` vía MCP
  para que un cliente externo (Claude Desktop) disparara el procesamiento.
  No se portó; `src/db/video_sessions.py::try_start_processing_session`
  (el claim atómico que evita dos jobs concurrentes) sigue acá por si se
  retoma más adelante.
- **Reclasificación masiva cross-sesión** (`CategoryReclassifyModal` en
  call-copilot) — herramienta manual para mover todos los segmentos de una
  categoría, en cualquier sesión, de una sola vez. Útil pero no esencial;
  la reclasificación de "Otro" por sesión (la que sí se portó) cubre el
  caso de uso principal.
- **Panel de Configuración en caliente** — call-copilot permitía cambiar
  `LLM_BACKEND`/API keys desde la TUI sin reiniciar. Acá es más simple:
  se edita `.env` y se reinicia.
