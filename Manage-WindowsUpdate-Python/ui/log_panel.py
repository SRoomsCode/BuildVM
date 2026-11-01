# ui/log_panel.py

import queue
import tkinter as tk

from tkinter import ttk
from tkinter import filedialog
from tkinter import messagebox


class LogPanel(ttk.LabelFrame):

    MAX_LINES = 5000

    def __init__(
        self,
        parent,
        *args,
        **kwargs
    ):

        super().__init__(
        parent,
        text="Journal d'événements",
        padding=5,
        *args,
        **kwargs
        )

        self.log_queue = queue.Queue()

        self.auto_scroll = tk.BooleanVar(
        value=True
        )

        self.filter_info = tk.BooleanVar(
        value=True
        )

        self.filter_warning = tk.BooleanVar(
        value=True
        )

        self.filter_error = tk.BooleanVar(
        value=True
        )

        self._build_ui()

        self.after(
        250,
        self._process_queue
        )

# ---------------------------------------------------------
# UI
# ---------------------------------------------------------

    def _build_ui(self):

        toolbar = ttk.Frame(
            self
        )

        toolbar.pack(
            fill="x",
            pady=(0, 5)
        )

        ttk.Checkbutton(

            toolbar,

            text="INFO",

            variable=
            self.filter_info

        ).pack(
            side="left",
            padx=2
        )

        ttk.Checkbutton(

            toolbar,

            text="WARNING",

            variable=
            self.filter_warning

        ).pack(
            side="left",
            padx=2
        )

        ttk.Checkbutton(

            toolbar,

            text="ERROR",

            variable=
            self.filter_error

        ).pack(
            side="left",
            padx=2
        )

        ttk.Separator(
            toolbar,
            orient="vertical"
        ).pack(
            side="left",
            fill="y",
            padx=10
        )

        ttk.Checkbutton(

            toolbar,

            text="Auto-scroll",

            variable=
            self.auto_scroll

        ).pack(
            side="left"
        )

        ttk.Button(

            toolbar,

            text="Effacer",

            command=
            self.clear

        ).pack(
            side="right",
            padx=2
        )

        ttk.Button(

            toolbar,

            text="Exporter",

            command=
            self.export_logs

        ).pack(
            side="right",
            padx=2
        )

        log_frame = ttk.Frame(
            self
        )

        log_frame.pack(
            fill="both",
            expand=True
        )

        self.text = tk.Text(

            log_frame,

            wrap="none",
            height=12,
            state="disabled",
            font=(
                "Consolas",
            9
            )
        )

        vsb = ttk.Scrollbar(
            log_frame,
            orient="vertical",
            command=self.text.yview
        )

        hsb = ttk.Scrollbar(
            log_frame,
            orient="horizontal",
            command=self.text.xview
        )

        self.text.configure(
            yscrollcommand=vsb.set,
            xscrollcommand=hsb.set
        )

        self.text.grid(
            row=0,
            column=0,
            sticky="nsew"
        )

        vsb.grid(
            row=0,
            column=1,
            sticky="ns"
        )

        hsb.grid(
            row=1,
            column=0,
            sticky="ew"
        )

        log_frame.rowconfigure(
            0,
            weight=1
        )

        log_frame.columnconfigure(
            0,
            weight=1
        )

        self.text.tag_configure(
            "INFO",
            foreground="#000000"
        )

        self.text.tag_configure(
            "WARNING",
            foreground="#cc8800"
        )

        self.text.tag_configure(
            "ERROR",
            foreground="#cc0000"
        )

# ---------------------------------------------------------
# AJOUT MESSAGE
# ---------------------------------------------------------

    def write_info(
        self,
        message
    ):

        self.log_queue.put(
        (
            "INFO",
            message
        )
        )

    def write_warning(
        self,
        message
    ):

        self.log_queue.put(
            (
                "WARNING",
                message
            )
        )

    def write_error(
        self,
        message
    ):

        self.log_queue.put(
            (
                "ERROR",
                message
            )
        )

# ---------------------------------------------------------
# QUEUE
# ---------------------------------------------------------

    def _process_queue(self):

        try:

            while True:

                level, message = (
                self.log_queue
                .get_nowait()
            )

                self._append(
                    level,
                    message
                )

        except queue.Empty:

            pass

        self.after(
        250,
        self._process_queue
        )

# ---------------------------------------------------------
# RENDU
# ---------------------------------------------------------

    def _append(
        self,
        level,
        message
    ):

        if (
            level == "INFO"
            and not self.filter_info.get()
        ):
            return

        if (
            level == "WARNING"
            and not self.filter_warning.get()
        ):
            return

        if (
            level == "ERROR"
            and not self.filter_error.get()
        ):
            return

        self.text.configure(
            state="normal"
        )

        line = (
            f"[{level}] "
            f"{message}\n"
        )

        self.text.insert(
            "end",
            line,
            level
        )

        lines = int(
            self.text.index(
            "end-1c"
            ).split(".")[0]
        )

        if lines > self.MAX_LINES:

            self.text.delete(
                "1.0",
                "100.0"
            )

        if self.auto_scroll.get():

            self.text.see(
                "end"
            )

        self.text.configure(
            state="disabled"
        )

# ---------------------------------------------------------
# NETTOYAGE
# ---------------------------------------------------------

    def clear(self):

        self.text.configure(
            state="normal"
        )

        self.text.delete(
            "1.0",
            "end"
        )

        self.text.configure(
            state="disabled"
        )

# ---------------------------------------------------------
# EXPORT
# ---------------------------------------------------------

    def export_logs(self):

        filename = (
        filedialog.asksaveasfilename(

            title="Exporter les logs",
            defaultextension=".txt",
            filetypes=[
                    (
                        "Texte",
                        "*.txt"
                    )
                ]
            )
        )

        if not filename:
            return

        try:
            content = self.text.get(
                "1.0",
                "end"
            )

            with open(
                filename,
                "w",
                encoding="utf-8"
            ) as file:

                file.write(
                content
            )

            messagebox.showinfo(
                "Export",
                "Export terminé"
            )

        except Exception as exc:

            messagebox.showerror(

        "Erreur",

        str(exec)
        )

# ---------------------------------------------------------
# INTERFACE COMPATIBLE LOGGER
# ---------------------------------------------------------

    def info(
        self,
        message
    ):

        self.write_info(
        message
    )

    def warning(
        self,
        message
    ):

        self.write_warning(
        message
    )

    def error(
        self,
        message
    ):

        self.write_error(
        message
    )
