# ui/toolbar.py

import tkinter as tk

from tkinter import ttk
from tkinter import filedialog
from tkinter import messagebox


class Toolbar(ttk.Frame):

    def __init__(
        self,
        parent,
        app=None,
        *args,
        **kwargs
    ):

        super().__init__(
            parent,
            padding=5,
            *args,
            **kwargs
        )

        self.app = app

        self._build_ui()

# -----------------------------------------------------
# UI
# -----------------------------------------------------

def _build_ui(self):

    self.columnconfigure(
        20,
        weight=1
    )

    self.btn_import_csv = ttk.Button(
        self,
        text="📂 Import CSV",
        command=self.import_csv
    )

    self.btn_import_csv.grid(
        row=0,
        column=0,
        padx=2,
        pady=2
    )

    self.btn_export_csv = ttk.Button(
        self,
        text="💾 Export CSV",
        command=self.export_inventory
    )

    self.btn_export_csv.grid(
        row=0,
        column=1,
        padx=2,
        pady=2
    )

    ttk.Separator(
        self,
        orient="vertical"
        ).grid(
        row=0,
        column=2,
        sticky="ns",
        padx=10
    )

    self.btn_scan_updates = ttk.Button(
        self,
        text="🔍 Rechercher MAJ",
        command=self.scan_updates
    )

    self.btn_scan_updates.grid(
        row=0,
        column=3,
        padx=2
    )

    self.btn_install = ttk.Button(
        self,
        text="⬇ Installer KB",
        command=self.install_updates
    )

    self.btn_install.grid(
        row=0,
        column=4,
        padx=2
    )

    ttk.Separator(
        self,
        orient="vertical"
        ).grid(
        row=0,
        column=5,
        sticky="ns",
        padx=10
    )

    self.btn_check_reboot = ttk.Button(
        self,
        text="🔄 Vérifier reboot",
        command=self.check_reboot
    )

    self.btn_check_reboot.grid(
        row=0,
        column=6,
        padx=2
    )

    self.btn_reboot = ttk.Button(
        self,
        text="⚡ Redémarrer",
        command=self.reboot_selected
    )

    self.btn_reboot.grid(
        row=0,
        column=7,
        padx=2
    )

    ttk.Separator(
        self,
        orient="vertical"
    ).grid(
        row=0,
        column=8,
        sticky="ns",
        padx=10
    )

    self.btn_generate_reports = ttk.Button(
        self,
        text="📊 Rapport",
        command=self.generate_report
    )

    self.btn_generate_reports.grid(
        row=0,
        column=9,
        padx=2
    )

    ttk.Separator(
        self,
        orient="vertical"
    ).grid(
        row=0,
        column=10,
        sticky="ns",
        padx=10
    )

    self.btn_select_all = ttk.Button(
        self,
        text="☑ Sélectionner tout",
        command=self.select_all_pcs
    )

    self.btn_select_all.grid(
        row=0,
        column=11,
        padx=2
    )

    self.btn_unselect_all = ttk.Button(
        self,
        text="☐ Désélectionner",
        command=self.unselect_all_pcs
    )

    self.btn_unselect_all.grid(
        row=0,
        column=12,
        padx=2
    )

    ttk.Separator(
        self,
        orient="vertical"
        ).grid(
        row=0,
        column=13,
        sticky="ns",
        padx=10
    )

    self.btn_refresh = ttk.Button(
        self,
        text="🔄 Actualiser",
        command=self.refresh_view
    )

    self.btn_refresh.grid(
        row=0,
        column=14,
        padx=2
    )

    self.status_var = tk.StringVar(
        value="Prêt"
    )

    status_label = ttk.Label(
        self,
        textvariable=self.status_var
    )

    status_label.grid(
        row=0,
        column=21,
        sticky="e",
        padx=10
    )

# -----------------------------------------------------
# STATUS
# -----------------------------------------------------

    def set_status(
        self,
        text
    ):

        self.status_var.set(
            text
        )

# -----------------------------------------------------
# ACTIONS
# -----------------------------------------------------

def import_csv(self):

    if not self.app:
        return

    file_path = (
        filedialog.askopenfilename(
            title="Importer CSV",

            filetypes=[
                (
                    "CSV",
                    "*.csv"
                )
            ]
        )
    )

    if not file_path:
        return

    self.app.import_csv(
        file_path
    )

def export_inventory(self):

    if not self.app:
        return

    file_path = (
        filedialog.asksaveasfilename(

        title="Exporter",

        defaultextension=".csv",

            filetypes=[
                (
                    "CSV",
                    "*.csv"
                )
            ]
        )
    )

    if not file_path:
        return

    self.app.export_inventory(
        file_path
    )

def scan_updates(self):

    if self.app:

        self.app.scan_updates()

def install_updates(self):

    if self.app:

        self.app.install_updates()

def check_reboot(self):

    if self.app:

        self.app.check_reboot()

def reboot_selected(self):

    if not self.app:
        return

    result = messagebox.askyesno(

    "Confirmation",

        (
            "Redémarrer "
            "les postes sélectionnés ?"
        )
    )

    if result:

        self.app.reboot_selected()

def generate_report(self):

    if self.app:

        self.app.generate_reports()

def select_all_pcs(self):

    if self.app:

        self.app.select_all_computers()

def unselect_all_pcs(self):

    if self.app:

        self.app.unselect_all_computers()

def refresh_view(self):

    if self.app:

        self.app.refresh_ui()

# -----------------------------------------------------
# ACTIVATION
# -----------------------------------------------------

def enable_all(self):

    widgets = [

        self.btn_import_csv,
        self.btn_export_csv,
        self.btn_scan_updates,
        self.btn_install,
        self.btn_check_reboot,
        self.btn_reboot,
        self.btn_generate_reports,
        self.btn_select_all,
        self.btn_unselect_all,
        self.btn_refresh
    ]

    for widget in widgets:

        widget.configure(
            state="normal"
        )

def disable_all(self):

    widgets = [

        self.btn_import_csv,
        self.btn_export_csv,
        self.btn_scan_updates,
        self.btn_install,
        self.btn_check_reboot,
        self.btn_reboot,
        self.btn_generate_reports,
        self.btn_select_all,
        self.btn_unselect_all,
        self.btn_refresh
    ]

    for widget in widgets:

        widget.configure(
            state="disabled"
        )
