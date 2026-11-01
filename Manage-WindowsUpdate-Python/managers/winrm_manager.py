# managers/winrm_manager.py

import time
import socket
import winrm

#---------------------------------------------------------
# pip install pywinrm
# pip install requests
#---------------------------------------------------------

from requests.exceptions import ConnectionError
from requests.exceptions import ReadTimeout

from managers.logging_manager import logger

from settings import (
    WINRM_PORT_HTTP,
    WINRM_TRANSPORT,
    WINRM_SERVER_CERT_VALIDATION,
    MAX_RECONNECT_ATTEMPTS,
    RECONNECT_DELAY_SECONDS,
    CHECK_UPDATES_OPERATION_TIMEOUT,
    CHECK_UPDATES_READ_TIMEOUT,
    INSTALL_OPERATION_TIMEOUT,
    INSTALL_READ_TIMEOUT,
    REBOOT_OPERATION_TIMEOUT,
    REBOOT_READ_TIMEOUT
)


class WinRMConnectionError(Exception):
    pass


class WinRMAuthenticationError(Exception):
    pass


class WinRMTimeoutError(Exception):
    pass


class WinRMCancelledError(Exception):
    pass


class WinRMManager:

    def __init__(
        self,
        hostname,
        credentials,
        cancel_event=None
    ):

        self.hostname = hostname

        self.credentials = credentials

        self.cancel_event = cancel_event

        self.protocol = None

    # ---------------------------------------------------------
    # ANNULATION
    # ---------------------------------------------------------

    def check_cancel(self):

        if self.cancel_event and self.cancel_event.is_set():

            logger.log_cancel_requested(
                self.hostname
            )

            raise WinRMCancelledError(
                f"{self.hostname} : opération annulée"
            )

    # ---------------------------------------------------------
    # CONNECTIVITE
    # ---------------------------------------------------------

    def is_port_open(
        self,
        port=WINRM_PORT_HTTP,
        timeout=5
    ):

        try:

            sock = socket.create_connection(
                (self.hostname, port),
                timeout
            )

            sock.close()

            return True

        except Exception:

            return False

    def ping_winrm(self):

        self.check_cancel()

        return self.is_port_open()

    # ---------------------------------------------------------
    # CONNEXION
    # ---------------------------------------------------------

    def connect(
        self,
        operation_timeout=60,
        read_timeout=120
    ):

        self.check_cancel()

        logger.log_winrm_connection(
            self.hostname
        )

        try:

            protocol = winrm.Protocol(
                endpoint=(
                    f"http://{self.hostname}:"
                    f"{WINRM_PORT_HTTP}/wsman"
                ),

                transport=WINRM_TRANSPORT,

                username=(
                    self.credentials.full_username
                ),

                password=(
                    self.credentials.password
                ),

                server_cert_validation=(
                    WINRM_SERVER_CERT_VALIDATION
                ),

                operation_timeout_sec=(
                    operation_timeout
                ),

                read_timeout_sec=(
                    read_timeout
                )
            )

            self.protocol = protocol

            logger.log_winrm_connected(
                self.hostname
            )

            return True

        except Exception as exc:

            logger.pc_error(
                self.hostname,
                str(exc)
            )

            raise WinRMConnectionError(
                str(exc)
            )

    # ---------------------------------------------------------
    # EXECUTION POWERSHELL
    # ---------------------------------------------------------

    def execute_ps(
        self,
        script,
        operation_timeout=60,
        read_timeout=120,
        retries=MAX_RECONNECT_ATTEMPTS
    ):

        for attempt in range(
            1,
            retries + 1
        ):

            self.check_cancel()

            try:

                self.connect(
                    operation_timeout,
                    read_timeout
                )

                shell_id = (
                    self.protocol.open_shell()
                )

                command_id = (
                    self.protocol.run_command(
                        shell_id,
                        "powershell.exe",
                        [
                            "-NoProfile",
                            "-ExecutionPolicy",
                            "Bypass",
                            "-Command",
                            script
                        ]
                    )
                )

                stdout, stderr, status = (
                    self.protocol.get_command_output(
                        shell_id,
                        command_id
                    )
                )

                self.protocol.cleanup_command(
                    shell_id,
                    command_id
                )

                self.protocol.close_shell(
                    shell_id
                )

                return {

                    "status_code": status,

                    "stdout": stdout.decode(
                        errors="ignore"
                    ),

                    "stderr": stderr.decode(
                        errors="ignore"
                    )
                }

            except ReadTimeout:

                logger.log_winrm_timeout(
                    self.hostname
                )

                if attempt < retries:

                    time.sleep(
                        RECONNECT_DELAY_SECONDS
                    )

                    continue

                raise WinRMTimeoutError(
                    (
                        f"{self.hostname} "
                        f"timeout après "
                        f"{retries} tentatives"
                    )
                )

            except ConnectionError:

                if attempt < retries:

                    time.sleep(
                        RECONNECT_DELAY_SECONDS
                    )

                    continue

                raise WinRMConnectionError(
                    (
                        f"{self.hostname} "
                        f"injoignable"
                    )
                )

            except Exception as exc:

                raise exc

    # ---------------------------------------------------------
    # COMMANDES STANDARDS
    # ---------------------------------------------------------

    def get_hostname(self):

        result = self.execute_ps(
            "hostname"
        )

        return result["stdout"].strip()

    def reboot(self):

        logger.log_reboot_started(
            self.hostname
        )

        return self.execute_ps(
            "Restart-Computer -Force",
            operation_timeout=
            REBOOT_OPERATION_TIMEOUT,

            read_timeout=
            REBOOT_READ_TIMEOUT
        )

    def get_installed_hotfixes(self):

        command = """
        Get-HotFix |
        Select-Object HotFixID
        """

        return self.execute_ps(
            command
        )

    def module_available(
        self,
        module_name
    ):

        command = (
            f"Get-Module "
            f"-ListAvailable "
            f"{module_name}"
        )

        result = self.execute_ps(
            command
        )

        return bool(
            result["stdout"].strip()
        )

    # ---------------------------------------------------------
    # WINDOWS UPDATE
    # ---------------------------------------------------------

    def get_windows_updates(self):

        command = """
        Import-Module PSWindowsUpdate

        Get-WindowsUpdate | Select-Object KB,Title | ConvertTo-Json -Depth 3
        """

        logger.log_update_scan(
            self.hostname
        )

        return self.execute_ps(

            command,

            operation_timeout=
            CHECK_UPDATES_OPERATION_TIMEOUT,

            read_timeout=
            CHECK_UPDATES_READ_TIMEOUT
        )

    def install_kb(
        self,
        kb_id
    ):

        logger.log_install_start(
            self.hostname,
            kb_id
        )

        command = f"""
        Import-Module PSWindowsUpdate

        Install-WindowsUpdate `
            -KBArticleID {kb_id} `
            -AcceptAll `
            -IgnoreReboot `
            -Confirm:$false
        """

        return self.execute_ps(

            command,

            operation_timeout=
            INSTALL_OPERATION_TIMEOUT,

            read_timeout=
            INSTALL_READ_TIMEOUT
        )

    # ---------------------------------------------------------
    # REBOOT PENDING
    # ---------------------------------------------------------

    def reboot_pending(self):

        command = r"""
        $pending = $false

        if(Test-Path
        'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\WindowsUpdate\Auto Update\RebootRequired')
        {
            $pending = $true
        }

        if(Test-Path
        'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Component Based Servicing\RebootPending')
        {
            $pending = $true
        }

        $pending
        """

        result = self.execute_ps(
            command
        )

        output = (
            result["stdout"]
            .strip()
            .lower()
        )

        return output == "true"