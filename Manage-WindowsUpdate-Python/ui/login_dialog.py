# ui/login_dialog.py

import tkinter as tk

from tkinter import ttk
from tkinter import messagebox

from models import Credentials


class LoginDialog(tk.Toplevel):

    def __init__(
        self,
        parent
    ):

        super().__init__(parent)

        self.parent = parent

        self.credentials = None

        self.result = False

        self.title(
            "Connexion WinRM"
        )

        self.resizable(
            False,
            False
        )

        self.geometry(
            "420x260"
        )

        self.transient(
            parent
        )

        self.grab_set()

        self.protocol(
            "WM_DELETE_WINDOW",
            self.on_cancel
        )

        self._build_ui()

        self.wait_visibility()

        self.focus_force()

    # ---------------------------------------------------------
    # UI
    # ---------------------------------------------------------

    def _build_ui(self):

        container = ttk.Frame(
            self,
            padding=20
        )

        container.pack(
            fill="both",
            expand=True
        )

        title = ttk.Label(
            container,
            text="Authentification WinRM",
            font=(
                "Segoe UI",
                12,
                "bold"
            )
        )

        title.pack(
            pady=(0, 15)
        )

        # Domaine

        ttk.Label(
            container,
            text="Domaine"
        ).pack(
            anchor="w"
        )

        self.domain_var = tk.StringVar()

        self.domain_entry = ttk.Entry(
            container,
            textvariable=self.domain_var
        )

        self.domain_entry.pack(
            fill="x",
            pady=(0, 10)
        )

        # Utilisateur

        ttk.Label(
            container,
            text="Utilisateur"
        ).pack(
            anchor="w"
        )

        self.username_var = (
            tk.StringVar()
        )

        self.username_entry = (
            ttk.Entry(

                container,

                textvariable=
                self.username_var
            )
        )

        self.username_entry.pack(
            fill="x",
            pady=(0, 10)
        )

        # Mot de passe

        ttk.Label(
            container,
            text="Mot de passe"
        ).pack(
            anchor="w"
        )

        self.password_var = (
            tk.StringVar()
        )

        self.password_entry = (
            ttk.Entry(

                container,

                textvariable=
                self.password_var,

                show="●"
            )
        )

        self.password_entry.pack(
            fill="x",
            pady=(0, 10)
        )

        # Mémorisation

        self.remember_var = (
            tk.BooleanVar(
                value=False
            )
        )

        remember_check = (
            ttk.Checkbutton(

                container,

                text=
                "Mémoriser la session",

                variable=
                self.remember_var
            )
        )

        remember_check.pack(
            anchor="w",
            pady=(5, 15)
        )

        # Boutons

        button_frame = (
            ttk.Frame(
                container
            )
        )

        button_frame.pack(
            fill="x"
        )

        ttk.Button(

            button_frame,

            text="Connexion",

            command=
            self.on_login

        ).pack(

            side="left",

            expand=True,

            fill="x",

            padx=(0, 5)
        )

        ttk.Button(

            button_frame,

            text="Annuler",

            command=
            self.on_cancel

        ).pack(

            side="left",

            expand=True,

            fill="x",

            padx=(5, 0)
        )

        self.username_entry.focus()

    # ---------------------------------------------------------
    # VALIDATION
    # ---------------------------------------------------------

    def validate(self):

        username = (

            self.username_var

            .get()

            .strip()
        )

        password = (

            self.password_var

            .get()

            .strip()
        )

        if not username:

            messagebox.showerror(

                "Erreur",

                "Utilisateur requis"

            )

            return False

        if not password:

            messagebox.showerror(

                "Erreur",

                "Mot de passe requis"

            )

            return False

        return True

    # ---------------------------------------------------------
    # LOGIN
    # ---------------------------------------------------------

    def on_login(self):

        if not self.validate():

            return

        self.credentials = (
            Credentials(

                username=
                self.username_var
                .get()
                .strip(),

                password=
                self.password_var
                .get(),

                domain=
                self.domain_var
                .get()
                .strip()
            )
        )

        self.result = True

        self.destroy()

    # ---------------------------------------------------------
    # CANCEL
    # ---------------------------------------------------------

    def on_cancel(self):

        self.result = False

        self.credentials = None

        self.destroy()

    # ---------------------------------------------------------
    # RESULTAT
    # ---------------------------------------------------------

    @classmethod
    def show(
        cls,
        parent
    ):

        dialog = cls(
            parent
        )

        parent.wait_window(
            dialog
        )

        return (

            dialog.result,

            dialog.credentials,

            dialog.remember_var.get()
        )