# managers/reboot_manager.py

import time
import socket

from models import JobState

from managers.logging_manager import logger
from managers.winrm_manager import (
    WinRMManager,
    WinRMCancelledError
)

from settings import (
    PING_TIMEOUT,
    ONLINE_TIMEOUT,
    OFFLINE_TIMEOUT,
    REBOOT_CHECK_INTERVAL_SECONDS
)


class RebootTimeoutError(Exception):
    pass


class MachineNeverStoppedError(Exception):
    pass


class RebootManager:

    def __init__(
        self,
        pc_job,
        credentials
    ):

        self.pc_job = pc_job

        self.credentials = credentials

        self.winrm = WinRMManager(
            hostname=pc_job.hostname,
            credentials=credentials,
            cancel_event=pc_job.cancel_event
        )

    # ---------------------------------------------------------
    # ANNULATION
    # ---------------------------------------------------------

    def check_cancel(self):

        if self.pc_job.is_cancelled():

            raise WinRMCancelledError(
                "Surveillance annulée"
            )

    # ---------------------------------------------------------
    # CONNECTIVITE
    # ---------------------------------------------------------

    def is_port_open(
        self,
        port=5985,
        timeout=PING_TIMEOUT
    ):

        try:

            sock = socket.create_connection(
                (
                    self.pc_job.hostname,
                    port
                ),
                timeout
            )

            sock.close()

            return True

        except Exception:

            return False

    # ---------------------------------------------------------
    # ATTENTE ARRET
    # ---------------------------------------------------------

    def wait_until_offline(self):

        logger.pc_info(
            self.pc_job.hostname,
            "Attente arrêt du poste"
        )

        start = time.time()

        while True:

            self.check_cancel()

            online = self.is_port_open()

            if not online:

                logger.pc_info(
                    self.pc_job.hostname,
                    "Le poste est hors ligne"
                )

                return True

            if (
                time.time() - start
            ) > OFFLINE_TIMEOUT:

                raise MachineNeverStoppedError(
                    f"{self.pc_job.hostname} "
                    f"ne s'est jamais arrêté"
                )

            time.sleep(
                REBOOT_CHECK_INTERVAL_SECONDS
            )

    # ---------------------------------------------------------
    # ATTENTE REDEMARRAGE
    # ---------------------------------------------------------

    def wait_until_online(self):

        logger.pc_info(
            self.pc_job.hostname,
            "Attente retour en ligne"
        )

        start = time.time()

        while True:

            self.check_cancel()

            online = self.is_port_open()

            if online:

                logger.pc_info(
                    self.pc_job.hostname,
                    "Port WinRM détecté"
                )

                return True

            if (
                time.time() - start
            ) > ONLINE_TIMEOUT:

                raise RebootTimeoutError(
                    f"{self.pc_job.hostname} "
                    f"timeout retour réseau"
                )

            time.sleep(
                REBOOT_CHECK_INTERVAL_SECONDS
            )

    # ---------------------------------------------------------
    # VALIDATION WINRM
    # ---------------------------------------------------------

    def wait_until_manageable(self):

        logger.pc_info(
            self.pc_job.hostname,
            "Validation WinRM"
        )

        start = time.time()

        while True:

            self.check_cancel()

            try:

                hostname = (
                    self.winrm.get_hostname()
                )

                if hostname:

                    logger.log_reboot_completed(
                        self.pc_job.hostname
                    )

                    return True

            except Exception:

                pass

            if (
                time.time() - start
            ) > ONLINE_TIMEOUT:

                raise RebootTimeoutError(
                    (
                        f"{self.pc_job.hostname} "
                        f"WinRM non disponible"
                    )
                )

            time.sleep(
                REBOOT_CHECK_INTERVAL_SECONDS
            )

    # ---------------------------------------------------------
    # REDEMARRAGE COMPLET
    # ---------------------------------------------------------

    def reboot_and_wait(self):

        self.pc_job.state = (
            JobState.RUNNING
        )

        self.pc_job.last_message = (
            "Redémarrage en cours"
        )

        try:

            logger.log_reboot_started(
                self.pc_job.hostname
            )

            self.winrm.reboot()

            self.pc_job.progress = 10

            self.wait_until_offline()

            self.pc_job.progress = 40

            self.wait_until_online()

            self.pc_job.progress = 75

            self.wait_until_manageable()

            self.pc_job.progress = 100

            self.pc_job.online = True

            self.pc_job.state = (
                JobState.SUCCESS
            )

            self.pc_job.last_message = (
                "Poste à nouveau disponible"
            )

            return True

        except WinRMCancelledError:

            self.pc_job.state = (
                JobState.CANCELLED
            )

            self.pc_job.last_message = (
                "Surveillance annulée"
            )

            logger.log_cancel_completed(
                self.pc_job.hostname
            )

            return False

        except Exception as exc:

            self.pc_job.state = (
                JobState.FAILED
            )

            self.pc_job.last_message = (
                str(exc)
            )

            logger.pc_error(
                self.pc_job.hostname,
                str(exc)
            )

            return False

    # ---------------------------------------------------------
    # REDÉMARRAGE SANS SURVEILLANCE
    # ---------------------------------------------------------

    def reboot_only(self):

        try:

            self.winrm.reboot()

            return True

        except Exception as exc:

            logger.pc_error(
                self.pc_job.hostname,
                str(exc)
            )

            return False

    # ---------------------------------------------------------
    # VERIFICATION ETAT MACHINE
    # ---------------------------------------------------------

    def verify_online_status(self):

        online = self.is_port_open()

        self.pc_job.online = online

        return online

    # ---------------------------------------------------------
    # VERIFICATION REBOOT PENDING
    # ---------------------------------------------------------

    def check_reboot_required(self):

        try:

            reboot_required = (
                self.winrm.reboot_pending()
            )

            self.pc_job.reboot_required = (
                reboot_required
            )

            return reboot_required

        except Exception as exc:

            logger.pc_error(
                self.pc_job.hostname,
                str(exc)
            )

            return False