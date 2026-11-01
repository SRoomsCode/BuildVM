# managers/update_manager.py

import json
import re
import time
from datetime import datetime

from models import (
    JobState,
    KBState,
    UpdateKB,
    ReportEntry
)

from managers.logging_manager import logger
from managers.winrm_manager import (
    WinRMManager,
    WinRMCancelledError
)

from settings import (
    INSTALLATION_WATCHDOG_TIMEOUT,
    KB_STATE_REFRESH_SECONDS,
    PROGRESS_SCANNING,
    PROGRESS_INSTALLING,
    PROGRESS_REBOOT_CHECK,
    PROGRESS_COMPLETE
)


class UpdateManager:

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

        self.report_entries = []

    # ----------------------------------------------------
    # UTILS
    # ----------------------------------------------------

    def check_cancel(self):

        if self.pc_job.is_cancelled():
            raise WinRMCancelledError()

    def update_job_progress(
        self,
        value,
        message=""
    ):

        self.pc_job.progress = value

        if message:
            self.pc_job.last_message = message

    # ----------------------------------------------------
    # DISCOVERY
    # ----------------------------------------------------

    def discover_updates(self):

        logger.log_update_scan(
            self.pc_job.hostname
        )

        self.pc_job.state = JobState.RUNNING

        self.update_job_progress(
            PROGRESS_SCANNING,
            "Recherche des mises à jour"
        )

        result = self.winrm.get_windows_updates()
        
        updates = self._parse_updates(            
            updates = json.loads(
                result["stdout"]
            )
        )

        self.pc_job.updates.clear()

        self.pc_job.updates.extend(
            updates
        )

        self.pc_job.total_count = (
            len(updates)
        )

        logger.log_update_found(
            self.pc_job.hostname,
            len(updates)
        )

        return updates

    # ----------------------------------------------------
    # INSTALLATION
    # ----------------------------------------------------

    def install_selected_updates(self):

        selected = [

            kb

            for kb in self.pc_job.updates

            if kb.selected

        ]

        if not selected:

            return

        self.pc_job.state = (
            JobState.RUNNING
        )

        self.pc_job.total_count = (
            len(selected)
        )

        start_time = time.time()

        completed = 0

        for kb in selected:

            self.check_cancel()

            self.pc_job.current_kb = (
                kb.kb_id
            )

            kb.state = (
                KBState.INSTALLING
            )

            kb.progress = 10

            install_begin = time.time()

            try:

                logger.log_install_start(
                    self.pc_job.hostname,
                    kb.kb_id
                )

                self.update_job_progress(
                    PROGRESS_INSTALLING,
                    f"Installation {kb.kb_id}"
                )

                watchdog_start = (
                    time.time()
                )

                result = (
                    self.winrm.install_kb(
                        kb.kb_id
                    )
                )

                elapsed = (
                    time.time()
                    - watchdog_start
                )

                if elapsed > (
                    INSTALLATION_WATCHDOG_TIMEOUT
                ):
                    raise TimeoutError(
                        f"Installation timeout {kb.kb_id}"
                    )

                if result["status_code"] != 0:

                    raise Exception(
                        result["stderr"]
                    )

                kb.state = (
                    KBState.SUCCESS
                )

                kb.progress = 100

                completed += 1

                self.pc_job.installed_count = (
                    completed
                )

                self._update_global_progress(
                    completed,
                    len(selected)
                )

                logger.log_install_success(
                    self.pc_job.hostname,
                    kb.kb_id
                )

                self.report_entries.append(

                    ReportEntry(

                        hostname=self.pc_job.hostname,

                        kb_id=kb.kb_id,

                        status="SUCCESS",

                        reboot_required=False,

                        duration_seconds=
                        round(
                            time.time()
                            - install_begin,
                            2
                        )
                    )
                )

            except Exception as exc:

                kb.state = (
                    KBState.FAILED
                )

                kb.error_message = (
                    str(exc)
                )

                logger.log_install_failed(
                    self.pc_job.hostname,
                    kb.kb_id,
                    str(exc)
                )

                self.report_entries.append(

                    ReportEntry(

                        hostname=self.pc_job.hostname,

                        kb_id=kb.kb_id,

                        status="FAILED",

                        reboot_required=False,

                        duration_seconds=
                        round(
                            time.time()
                            - install_begin,
                            2
                        ),

                        error_message=
                        str(exc)
                    )
                )

        if self.pc_job.is_cancelled():

            self.pc_job.state = (
                JobState.CANCELLED
            )

        else:

            self._check_reboot_state()

        total_duration = (
            time.time() - start_time
        )

        logger.pc_info(
            self.pc_job.hostname,
            (
                f"Traitement terminé "
                f"({round(total_duration,2)} sec)"
            )
        )

    # ----------------------------------------------------
    # REBOOT STATE
    # ----------------------------------------------------

    def _check_reboot_state(self):

        self.update_job_progress(
            PROGRESS_REBOOT_CHECK,
            "Vérification redémarrage"
        )

        reboot_required = (
            self.winrm.reboot_pending()
        )

        self.pc_job.reboot_required = (
            reboot_required
        )

        if reboot_required:

            logger.log_reboot_required(
                self.pc_job.hostname
            )

            self.pc_job.state = (
                JobState.WARNING
            )

        else:

            self.pc_job.state = (
                JobState.SUCCESS
            )

        self.update_job_progress(
            PROGRESS_COMPLETE
        )

    # ----------------------------------------------------
    # PROGRESSION
    # ----------------------------------------------------

    def _update_global_progress(
        self,
        completed,
        total
    ):

        if total == 0:
            percent = 0

        else:
            percent = int(
                (completed / total)
                * 100
            )

        self.pc_job.progress = percent

    # ----------------------------------------------------
    # PARSING WINDOWS UPDATE
    # ----------------------------------------------------

    def _parse_updates(
        self,
        raw_output
    ):

        updates = []

        lines = (
            raw_output
            .splitlines()
        )

        kb_regex = (
            r"(KB\d+)"
        )

        for line in lines:

            kb_match = re.search(
                kb_regex,
                line,
                re.IGNORECASE
            )

            if not kb_match:
                continue

            kb_id = (
                kb_match.group(1)
                .upper()
            )

            title = (
                line.strip()
            )

            updates.append(

                UpdateKB(

                    kb_id=kb_id,

                    title=title,

                    selected=False
                )
            )

        return updates

    # ----------------------------------------------------
    # ANNULATION
    # ----------------------------------------------------

    def cancel(self):

        self.pc_job.cancel()

        self.pc_job.state = (
            JobState.CANCELLED
        )

        logger.log_cancel_completed(
            self.pc_job.hostname
        )

    # ----------------------------------------------------
    # STATISTIQUES
    # ----------------------------------------------------

    def get_statistics(self):

        success = len([

            kb

            for kb in self.pc_job.updates

            if kb.state == KBState.SUCCESS

        ])

        failed = len([

            kb

            for kb in self.pc_job.updates

            if kb.state == KBState.FAILED

        ])

        pending = len([

            kb

            for kb in self.pc_job.updates

            if kb.state == KBState.PENDING

        ])

        return {

            "total":
                len(
                    self.pc_job.updates
                ),

            "success":
                success,

            "failed":
                failed,

            "pending":
                pending,

            "progress":
                self.pc_job.progress
        }

    # ----------------------------------------------------
    # EXPORT RAPPORT
    # ----------------------------------------------------

    def get_report_entries(self):

        return self.report_entries