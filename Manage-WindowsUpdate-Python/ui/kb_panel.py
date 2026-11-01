# ui/kb_panel.py

import tkinter as tk

from tkinter import ttk

from models import KBState


class KBPanel(ttk.Frame):

    def __init__(
        self,
        parent,
        app,
        *args,
        **kwargs
    ):

        super().__init__(
            parent,
            *args,
            **kwargs
        )

        self.app = app

        self.current_job = None

        self._build_ui()

    # ---------------------------------------------------------
    # UI
    # ---------------------------------------------------------

    def _build_ui(self):

        title = ttk.Label(

            self,

            text="Mises à jour Windows",

            font=(
                "Segoe UI",
                11,
                "bold"
            )
        )

        title.pack(
            anchor="w",
            padx=5,
            pady=5
        )

        control_frame = ttk.Frame(
            self
        )

        control_frame.pack(
            fill="x",
            padx=5,
            pady=(0, 5)
        )

        ttk.Button(

            control_frame,

            text="☑ Tout sélectionner",

            command=
            self.select_all

        ).pack(
            side="left",
            padx=2
        )

        ttk.Button(

            control_frame,

            text="☐ Tout désélectionner",

            command=
            self.unselect_all

        ).pack(
            side="left",
            padx=2
        )

        ttk.Button(

            control_frame,

            text="🔄 Actualiser",

            command=
            self.refresh

        ).pack(
            side="left",
            padx=2
        )

        tree_frame = ttk.Frame(
            self
        )

        tree_frame.pack(
            fill="both",
            expand=True
        )

        self.tree = ttk.Treeview(

            tree_frame,

            columns=(

                "selected",

                "kb",

                "title",

                "state",

                "progress",

                "error"
            ),

            show="headings"
        )

        self.tree.heading(
            "selected",
            text="Sel."
        )

        self.tree.heading(
            "kb",
            text="KB"
        )

        self.tree.heading(
            "title",
            text="Description"
        )

        self.tree.heading(
            "state",
            text="État"
        )

        self.tree.heading(
            "progress",
            text="%"
        )

        self.tree.heading(
            "error",
            text="Erreur"
        )

        self.tree.column(
            "selected",
            width=60,
            anchor="center"
        )

        self.tree.column(
            "kb",
            width=110
        )

        self.tree.column(
            "title",
            width=350
        )

        self.tree.column(
            "state",
            width=120
        )

        self.tree.column(
            "progress",
            width=70,
            anchor="center"
        )

        self.tree.column(
            "error",
            width=300
        )

        scrollbar = ttk.Scrollbar(
            tree_frame,
            orient="vertical",
            command=self.tree.yview
        )

        self.tree.configure(
            yscrollcommand=
            scrollbar.set
        )

        self.tree.pack(
            side="left",
            fill="both",
            expand=True
        )

        scrollbar.pack(
            side="right",
            fill="y"
        )

        self.tree.bind(
            "<Double-Button-1>",
            self.toggle_selected
        )

        self.tree.tag_configure(
            "success",
            background="#d5ffe0"
        )

        self.tree.tag_configure(
            "installing",
            background="#ddeeff"
        )

        self.tree.tag_configure(
            "failed",
            background="#ffd6d6"
        )

        self.tree.tag_configure(
            "pending",
            background="#ffffff"
        )

        self.tree.tag_configure(
            "cancelled",
            background="#dddddd"
        )

    # ---------------------------------------------------------
    # CHANGEMENT DE MACHINE
    # ---------------------------------------------------------

    def load_job(
        self,
        pc_job
    ):

        self.current_job = pc_job

        self.refresh()

    # ---------------------------------------------------------
    # RAFRAICHISSEMENT
    # ---------------------------------------------------------

    def refresh(self):

        self.tree.delete(
            *self.tree.get_children()
        )

        if not self.current_job:
            return

        for kb in self.current_job.updates:

            selected_text = (
                "☑"
                if kb.selected
                else "☐"
            )

            self.tree.insert(

                "",

                "end",

                values=(

                    selected_text,

                    kb.kb_id,

                    kb.title,

                    kb.state.value,

                    kb.progress,

                    kb.error_message
                ),

                tags=(
                    self._kb_tag(kb)
                )
            )

    # ---------------------------------------------------------
    # SELECTION
    # ---------------------------------------------------------

    def toggle_selected(
        self,
        event
    ):

        if not self.current_job:
            return

        item = self.tree.focus()

        if not item:
            return

        index = (
            self.tree.index(item)
        )

        if index >= len(
            self.current_job.updates
        ):
            return

        kb = (
            self.current_job
            .updates[index]
        )

        kb.selected = (
            not kb.selected
        )

        self.refresh()

    def select_all(self):

        if not self.current_job:
            return

        for kb in (
            self.current_job.updates
        ):

            kb.selected = True

        self.refresh()

    def unselect_all(self):

        if not self.current_job:
            return

        for kb in (
            self.current_job.updates
        ):

            kb.selected = False

        self.refresh()

    # ---------------------------------------------------------
    # TAG COULEUR
    # ---------------------------------------------------------

    def _kb_tag(
        self,
        kb
    ):

        if kb.state == KBState.SUCCESS:
            return "success"

        if kb.state == KBState.INSTALLING:
            return "installing"

        if kb.state == KBState.FAILED:
            return "failed"

        if kb.state == KBState.CANCELLED:
            return "cancelled"

        return "pending"

    # ---------------------------------------------------------
    # UTILITAIRES
    # ---------------------------------------------------------

    def get_selected_kbs(
        self
    ):

        if not self.current_job:
            return []

        return [

            kb

            for kb

            in self.current_job.updates

            if kb.selected
        ]

    def selected_count(
        self
    ):

        return len(
            self.get_selected_kbs()
        )

    def total_count(
        self
    ):

        if not self.current_job:
            return 0

        return len(
            self.current_job.updates
        )

    def clear(self):

        self.current_job = None

        self.tree.delete(
            *self.tree.get_children()
        )