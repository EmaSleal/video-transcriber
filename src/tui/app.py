"""
TUI de Video Transcriber.

Tabs:
  [1] Video      — procesar URL de YouTube, historial de sesiones
  [2] Categorías — CRUD de taxonomía

Este módulo es solo el shell de la app (VideoTranscriberApp) y el
entrypoint. Cada tab vive en su propio módulo bajo tabs/ — ver ahí por la
lógica de cada pantalla.
"""

import logging
import os

from dotenv import load_dotenv
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.widgets import Footer, Header, TabbedContent, TabPane

from src.db.database import init_db
from src.i18n import t
from src.tui.messages import CategoriesChanged
from src.tui.tabs.categories import CategoriesTab
from src.tui.tabs.video import VideoTab

load_dotenv()

_log_file = os.getenv("VT_LOG")
if _log_file:
    _fh = logging.FileHandler(_log_file, mode="a")
    _fh.setLevel(logging.DEBUG)
    _fh.setFormatter(
        logging.Formatter("%(asctime)s [%(name)s] %(levelname)s %(message)s")
    )
    logging.getLogger().addHandler(_fh)
    logging.getLogger().setLevel(logging.DEBUG)


class VideoTranscriberApp(App):
    CSS = """
    Screen { background: #0f172a; }
    Header { background: #1e293b; color: #f8fafc; }
    Footer { background: #1e293b; color: #64748b; }
    TabbedContent { height: 1fr; }
    TabPane { padding: 1 2; }
    Input { margin-bottom: 1; }
    Label { color: #94a3b8; margin-bottom: 0; }
    Button { margin-right: 1; }
    DataTable { height: 15; border: solid #334155; background: #1e293b; }
    #cat-layout { height: 1fr; }
    #cat-list-panel { width: 50%; padding-right: 2; }
    #cat-form-panel { width: 50%; border-left: solid #334155; padding-left: 2; }
    ProgressBar { margin: 1 0; }
    #video-status { margin-bottom: 1; }
    #lbl-sessions { margin-bottom: 1; }
    #suggestions-list { height: 8; border: solid #334155; background: #1e293b; }
    #suggestion-feedback { margin-top: 1; }
    #tab-video Horizontal { height: auto; }
    #tab-video Horizontal Input { width: 1fr; }
    Select { margin-bottom: 1; }
    """

    BINDINGS = [
        Binding("ctrl+q", "quit", t("app.quit_binding")),
        Binding("1", "switch_tab('tab-video')", "Video"),
        Binding("2", "switch_tab('tab-categories')", t("app.categories_binding")),
    ]

    TITLE = t("app.title")

    def compose(self) -> ComposeResult:
        yield Header()
        with TabbedContent():
            yield VideoTab()
            yield CategoriesTab()
        yield Footer()

    def action_switch_tab(self, tab_id: str) -> None:
        self.query_one(TabbedContent).active = tab_id

    def on_categories_changed(self, event: CategoriesChanged) -> None:
        self.query_one(CategoriesTab)._refresh()

    def on_tabbed_content_tab_activated(
        self, event: TabbedContent.TabActivated
    ) -> None:
        # TabbedContent mounts all TabPanes once at startup, so on_mount()
        # never fires again on tab switch — Categorías opts in via a
        # refresh_data() method since it can go stale from Video's
        # suggestion-add flow.
        refresh = getattr(event.pane, "refresh_data", None)
        if refresh is not None:
            refresh()


def main():
    init_db()
    VideoTranscriberApp().run()


if __name__ == "__main__":
    main()
