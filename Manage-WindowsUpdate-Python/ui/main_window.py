# ui/main_window.py

import tkinter as tk
from tkinter import ttk
from concurrent.futures import ThreadPoolExecutor

from ui.pc_panel import PCPanel
from ui.kb_panel import KBPanel
from ui.log_panel import LogPanel
from ui.toolbar import Toolbar

from settings import (
APP_NAME,
APP_VERSION,
MAX_WORKERS
)


class MainWindow(tk.Tk):

    def __init__(self, credentials):

        super().__init__()

        self.credentials = credentials

        self.title(
            f"{APP_NAME} {APP_VERSION}"
        )

        self.geometry(
            "1600x900"
        )

        self.minsize(
            1300,
            750
        )

        self.executor = (
            ThreadPoolExecutor(
                max_workers=MAX_WORKERS
            )
        )

        self.pc_jobs = []

        self._build_ui()

        def _build_ui(self):

            self.toolbar = Toolbar(
                self
            )

        self.toolbar.pack(
            fill="x"
        )

        body = ttk.PanedWindow(
            self,
            orient="horizontal"
        )

        body.pack(
            fill="both",
            expand=True
        )

        left = ttk.Frame(body)

        right = ttk.Frame(body)

        body.add(
            left,
            weight=2
        )

        body.add(
            right,
            weight=1
        )

        self.pc_panel = (
            PCPanel(
                left,
                self
            )
        )

        self.pc_panel.pack(
            fill="both",
            expand=True
        )

        self.kb_panel = (
            KBPanel(
                right,
                self
            )
        )

        self.kb_panel.pack(
            fill="both",
            expand=True
        )

        self.log_panel = (
            LogPanel(
                self
            )
        )

        self.log_panel.pack(
            fill="x"
        )

        def run(self):

            self.mainloop()
