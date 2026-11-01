# main.py

import sys
import traceback
import tkinter as tk

from tkinter import messagebox

from settings import (
    APP_NAME,
    APP_VERSION
)

from ui.login_dialog import LoginDialog
from ui.main_window import MainWindow

from managers.logging_manager import logger


def global_exception_handler(
    exc_type,
    exc_value,
    exc_traceback
):
    """
    Gestionnaire global des exceptions.
    """

    error_text = "".join(

        traceback.format_exception(

            exc_type,

            exc_value,

            exc_traceback
        )
    )

    logger.error(
        error_text
    )

    try:

        messagebox.showerror(

            "Erreur critique",

            (
                "Une erreur non gérée "
                "s'est produite.\n\n"
                "Consultez les logs "
                "pour plus d'informations."
            )
        )

    except Exception:
        pass


def main():

    sys.excepthook = (
        global_exception_handler
    )

    logger.startup()

    root = tk.Tk()

    root.withdraw()

    success, credentials, remember = (
        LoginDialog.show(
            root
        )
    )

    if not success:

        logger.info(
            "Connexion annulée"
        )

        root.destroy()

        logger.shutdown()

        return

    logger.info(

        f"Utilisateur connecté : "

        f"{credentials.full_username}"
    )

    root.destroy()

    app = MainWindow(
        credentials
    )

    def on_close():

        try:

            logger.info(
                "Arrêt demandé"
            )

            if hasattr(
                app,
                "executor"
            ):

                app.executor.shutdown(
                    wait=False,
                    cancel_futures=True
                )

        except Exception as exc:

            logger.error(
                str(exc)
            )

        finally:

            logger.shutdown()

            app.destroy()

    app.protocol(
        "WM_DELETE_WINDOW",
        on_close
    )

    app.mainloop()


if __name__ == "__main__":

    try:

        main()

    except KeyboardInterrupt:

        logger.info(
            "Interruption clavier"
        )

        logger.shutdown()

    except Exception as exc:

        logger.exception(
            exc
        )

        raise