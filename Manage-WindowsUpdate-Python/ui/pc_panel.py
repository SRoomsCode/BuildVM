# ui/pc_panel.py

import tkinter as tk

from tkinter import ttk
from tkinter import messagebox

from models import JobState


class PCPanel(ttk.Frame):

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

        self.pc_map = {}

        self._build_ui(
            self.tree.bind(
                "<<TreeviewSelect>>",
                self._on_selection_change
            )
        )

    # ---------------------------------------------------------
    # UI
    # ---------------------------------------------------------

    def _on_selection_change(
        self,
        event
    ):

        if not self.app:
            return

        jobs = self.get_selected_jobs()

        if jobs:

            self.app.on_pc_selected(
                jobs[0]
            )

    def _build_ui(self):

        title = ttk.Label(
            self,
            text="Postes Windows",
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

        tree_frame = ttk.Frame(
            self
        )

        tree_frame.pack(
            fill="both",
            expand=True
        )

        columns = (

            "hostname",
            "ip",
            "state",
            "progress",
            "kb",
            "reboot",
            "message"
        )

        self.tree = ttk.Treeview(

            tree_frame,

            columns=columns,
			
            show="headings",

            selectmode="extended"
        )

        self.tree.heading(
            "hostname",
            text="Poste"
        )

        self.tree.heading(
            "ip",
            text="Adresse IP"
        )

        self.tree.heading(
            "state",
            text="État"
        )

        self.tree.heading(
            "progress",
            text="Progression"
        )

        self.tree.heading(
            "kb",
            text="KB active"
        )

        self.tree.heading(
            "reboot",
            text="Reboot"
        )

        self.tree.heading(
            "message",
            text="Message"
        )

        self.tree.column(
            "hostname",
            width=160
        )

        self.tree.column(
            "ip",
            width=120
        )

        self.tree.column(
            "state",
            width=120
        )

        self.tree.column(
            "progress",
            width=100
        )

        self.tree.column(
            "kb",
            width=150
        )

        self.tree.column(
            "reboot",
            width=80
        )

        self.tree.column(
            "message",
            width=400
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

        self.tree.tag_configure(
            "success",
            background="#d5ffe0"
        )

        self.tree.tag_configure(
            "warning",
            background="#fff2cc"
        )

        self.tree.tag_configure(
            "failed",
            background="#ffd6d6"
        )

        self.tree.tag_configure(
            "running",
            background="#ddeeff"
        )

        self.tree.tag_configure(
            "cancelled",
            background="#dddddd"
        )

        buttons = ttk.Frame(
            self
        )

        buttons.pack(
            fill="x",
            pady=5
        )

        ttk.Button(

            buttons,

            text="Ajouter",

            command=
            self.add_computer_dialog

        ).pack(
            side="left",
            padx=2
        )

        ttk.Button(

            buttons,

            text="Supprimer",

            command=
            self.remove_selected

        ).pack(
            side="left",
            padx=2
        )

        ttk.Button(

            buttons,

            text="Annuler tâche",

            command=
            self.cancel_selected_jobs

        ).pack(
            side="left",
            padx=2
        )

    # ---------------------------------------------------------
    # AJOUT
    # ---------------------------------------------------------

    def add_pc_job(
        self,
        pc_job
    ):

        iid = self.tree.insert(

            "",

            "end",

            values=(

                pc_job.hostname,

                pc_job.ip_address,

                pc_job.state.value,

                "0 %",

                "",

                "NON",

                ""
            )
        )

        self.pc_map[iid] = pc_job

    def add_many(
        self,
        jobs
    ):

        for job in jobs:

            self.add_pc_job(
                job
            )

    # ---------------------------------------------------------
    # SUPPRESSION
    # ---------------------------------------------------------

    def remove_selected(self):

        selected = (
            self.tree.selection()
        )

        if not selected:
            return

        for iid in selected:

            self.tree.delete(
                iid
            )

            self.pc_map.pop(
                iid,
                None
            )

    # ---------------------------------------------------------
    # MISE A JOUR
    # ---------------------------------------------------------

    def refresh(self):

        for iid, job in (
            self.pc_map.items()
        ):

            self.tree.item(

                iid,

                values=(

                    job.hostname,

                    job.ip_address,

                    job.state.value,

                    f"{job.progress} %",

                    job.current_kb,

                    (
                        "OUI"
                        if job.reboot_required
                        else "NON"
                    ),

                    job.last_message
                ),

                tags=(
                    self._get_tag(job)
                )
            )

    # ---------------------------------------------------------
    # TAGS
    # ---------------------------------------------------------

    def _get_tag(
        self,
        job
    ):

        if job.state == JobState.SUCCESS:
            return "success"

        if job.state == JobState.WARNING:
            return "warning"

        if job.state == JobState.FAILED:
            return "failed"

        if job.state == JobState.RUNNING:
            return "running"

        if job.state == JobState.CANCELLED:
            return "cancelled"

        return ""

    # ---------------------------------------------------------
    # SELECTION
    # ---------------------------------------------------------

    def get_selected_jobs(
        self
    ):

        jobs = []

        for iid in (
            self.tree.selection()
        ):

            if iid in self.pc_map:

                jobs.append(
                    self.pc_map[iid]
                )

        return jobs

    def select_all(
        self
    ):

        self.tree.selection_set(
            self.tree.get_children()
        )

    def unselect_all(
        self
    ):

        self.tree.selection_remove(
            self.tree.selection()
        )

    # ---------------------------------------------------------
    # ANNULATION
    # ---------------------------------------------------------

    def cancel_selected_jobs(
        self
    ):

        jobs = (
            self.get_selected_jobs()
        )

        if not jobs:
            return

        result = (
            messagebox.askyesno(

                "Confirmation",

                (
                    "Annuler les tâches "
                    "sélectionnées ?"
                )
            )
        )

        if not result:
            return

        for job in jobs:

            job.cancel()

    # ---------------------------------------------------------
    # AJOUT MANUEL
    # ---------------------------------------------------------

    def add_computer_dialog(
        self
    ):

        dialog = tk.Toplevel(
            self
        )

        dialog.title(
            "Ajouter un poste"
        )

        dialog.geometry(
            "350x150"
        )

        ttk.Label(
            dialog,
            text="Nom du poste"
        ).pack(
            pady=5
        )

        hostname = tk.StringVar()

        ttk.Entry(

            dialog,

            textvariable=
            hostname

        ).pack(
            fill="x",
            padx=10
        )

        ttk.Label(
            dialog,
            text="Adresse IP"
        ).pack(
            pady=5
        )

        ip_address = tk.StringVar()

        ttk.Entry(

            dialog,

            textvariable=
            ip_address

        ).pack(
            fill="x",
            padx=10
        )

        def add():

            host = (
                hostname.get()
                .strip()
            )

            if not host:
                return

            from models import PCJob

            job = PCJob(

                hostname=host,

                ip_address=
                ip_address.get()
                .strip()
            )

            self.add_pc_job(
                job
            )

            dialog.destroy()

        ttk.Button(

            dialog,

            text="Ajouter",

            command=add

        ).pack(
            pady=10
        )