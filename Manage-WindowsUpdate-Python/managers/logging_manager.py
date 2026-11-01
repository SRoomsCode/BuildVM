# managers/logging_manager.py

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from threading import Lock
from datetime import datetime

from settings import (
    LOG_DIR,
    LOG_FILE,
    LOG_LEVEL,
    LOG_FORMAT,
    LOG_DATE_FORMAT
)


class LoggingManager:

    _instance = None
    _lock = Lock()

    @classmethod
    def get_instance(cls):

        with cls._lock:

            if cls._instance is None:

                cls._instance = cls()

            return cls._instance

    def __init__(self):

        self.logger = logging.getLogger(
            "WindowsUpdateManager"
        )

        self.logger.setLevel(
            getattr(logging, LOG_LEVEL.upper())
        )

        self.logger.propagate = False

        self._configure_logger()

    def _configure_logger(self):

        if self.logger.handlers:
            return

        formatter = logging.Formatter(
            LOG_FORMAT,
            datefmt=LOG_DATE_FORMAT
        )

        file_handler = RotatingFileHandler(
            LOG_FILE,
            maxBytes=5 * 1024 * 1024,
            backupCount=10,
            encoding="utf-8"
        )

        file_handler.setFormatter(
            formatter
        )

        console_handler = logging.StreamHandler()

        console_handler.setFormatter(
            formatter
        )

        self.logger.addHandler(
            file_handler
        )

        self.logger.addHandler(
            console_handler
        )

    def info(self, message):

        self.logger.info(
            message
        )

    def warning(self, message):

        self.logger.warning(
            message
        )

    def error(self, message):

        self.logger.error(
            message
        )

    def exception(self, exception_obj):

        self.logger.exception(
            str(exception_obj)
        )

    def debug(self, message):

        self.logger.debug(
            message
        )

    # ------------------------------------------------------------------
    # LOGS PAR POSTE
    # ------------------------------------------------------------------

    def pc_info(
        self,
        hostname,
        message
    ):

        self.info(
            f"[{hostname}] {message}"
        )

    def pc_warning(
        self,
        hostname,
        message
    ):

        self.warning(
            f"[{hostname}] {message}"
        )

    def pc_error(
        self,
        hostname,
        message
    ):

        self.error(
            f"[{hostname}] {message}"
        )

    # ------------------------------------------------------------------
    # ETAPES WINDOWS UPDATE
    # ------------------------------------------------------------------

    def log_update_scan(
        self,
        hostname
    ):

        self.pc_info(
            hostname,
            "Recherche des mises à jour"
        )

    def log_update_found(
        self,
        hostname,
        count
    ):

        self.pc_info(
            hostname,
            f"{count} mise(s) à jour trouvée(s)"
        )

    def log_install_start(
        self,
        hostname,
        kb
    ):

        self.pc_info(
            hostname,
            f"Installation {kb}"
        )

    def log_install_success(
        self,
        hostname,
        kb
    ):

        self.pc_info(
            hostname,
            f"{kb} installée"
        )

    def log_install_failed(
        self,
        hostname,
        kb,
        error
    ):

        self.pc_error(
            hostname,
            f"Echec {kb} | {error}"
        )

    def log_reboot_required(
        self,
        hostname
    ):

        self.pc_warning(
            hostname,
            "Redémarrage requis"
        )

    def log_reboot_started(
        self,
        hostname
    ):

        self.pc_info(
            hostname,
            "Redémarrage lancé"
        )

    def log_reboot_completed(
        self,
        hostname
    ):

        self.pc_info(
            hostname,
            "Poste de nouveau disponible"
        )

    # ------------------------------------------------------------------
    # WINRM
    # ------------------------------------------------------------------

    def log_winrm_connection(
        self,
        hostname
    ):

        self.pc_info(
            hostname,
            "Connexion WinRM"
        )

    def log_winrm_connected(
        self,
        hostname
    ):

        self.pc_info(
            hostname,
            "Connexion WinRM établie"
        )

    def log_winrm_timeout(
        self,
        hostname
    ):

        self.pc_error(
            hostname,
            "Timeout WinRM"
        )

    def log_winrm_auth_failed(
        self,
        hostname
    ):

        self.pc_error(
            hostname,
            "Authentification WinRM refusée"
        )

    # ------------------------------------------------------------------
    # ANNULATION
    # ------------------------------------------------------------------

    def log_cancel_requested(
        self,
        hostname
    ):

        self.pc_warning(
            hostname,
            "Annulation demandée"
        )

    def log_cancel_completed(
        self,
        hostname
    ):

        self.pc_warning(
            hostname,
            "Traitement annulé"
        )

    # ------------------------------------------------------------------
    # RAPPORTS
    # ------------------------------------------------------------------

    def log_report_generated(
        self,
        report_file
    ):

        self.info(
            f"Rapport généré : {report_file}"
        )

    # ------------------------------------------------------------------
    # SESSION
    # ------------------------------------------------------------------

    def startup(self):

        self.info(
            "=" * 80
        )

        self.info(
            "DEMARRAGE WINDOWS UPDATE MANAGER"
        )

        self.info(
            datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            )
        )

        self.info(
            "=" * 80
        )

    def shutdown(self):

        self.info(
            "=" * 80
        )

        self.info(
            "ARRET WINDOWS UPDATE MANAGER"
        )

        self.info(
            "=" * 80
        )

    def add_handler(
    self,
    handler
    ):

        self.logger.addHandler(
            handler
        )

logger = LoggingManager.get_instance()