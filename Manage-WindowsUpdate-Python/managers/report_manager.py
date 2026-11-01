# managers/report_manager.py

import csv

from pathlib import Path
from datetime import datetime
from collections import defaultdict

from managers.logging_manager import logger

from settings import (
    REPORT_DIR,
    CSV_REPORT_TEMPLATE,
    HTML_REPORT_TEMPLATE,
    REPORT_HEADERS
)


class ReportManager:

    def __init__(self):

        self.created_reports = []

    # ---------------------------------------------------------
    # FICHIERS
    # ---------------------------------------------------------

    def _current_timestamp(self):

        return datetime.now().strftime(
            "%Y%m%d_%H%M%S"
        )

    def _csv_path(self):

        filename = CSV_REPORT_TEMPLATE.format(
            date=self._current_timestamp()
        )

        return REPORT_DIR / filename

    def _html_path(self):

        filename = HTML_REPORT_TEMPLATE.format(
            date=self._current_timestamp()
        )

        return REPORT_DIR / filename

    # ---------------------------------------------------------
    # CSV
    # ---------------------------------------------------------

    def export_csv(
        self,
        report_entries
    ):

        csv_file = self._csv_path()

        with open(
            csv_file,
            "w",
            newline="",
            encoding="utf-8-sig"
        ) as file:

            writer = csv.writer(
                file,
                delimiter=";"
            )

            writer.writerow(
                REPORT_HEADERS
            )

            for entry in report_entries:

                writer.writerow([

                    entry.hostname,

                    entry.kb_id,

                    entry.status,

                    "OUI"
                    if entry.reboot_required
                    else "NON",

                    entry.duration_seconds,

                    entry.error_message
                ])

        logger.log_report_generated(
            csv_file
        )

        self.created_reports.append(
            csv_file
        )

        return csv_file

    # ---------------------------------------------------------
    # HTML
    # ---------------------------------------------------------

    def export_html(
        self,
        report_entries
    ):

        html_file = self._html_path()

        stats = self.generate_statistics(
            report_entries
        )

        html_content = self._build_html(
            report_entries,
            stats
        )

        with open(
            html_file,
            "w",
            encoding="utf-8"
        ) as file:

            file.write(
                html_content
            )

        logger.log_report_generated(
            html_file
        )

        self.created_reports.append(
            html_file
        )

        return html_file

    # ---------------------------------------------------------
    # STATISTIQUES
    # ---------------------------------------------------------

    def generate_statistics(
        self,
        report_entries
    ):

        total = len(
            report_entries
        )

        success = len([

            entry

            for entry in report_entries

            if entry.status == "SUCCESS"

        ])

        failed = len([

            entry

            for entry in report_entries

            if entry.status == "FAILED"

        ])

        reboot_required = len([

            entry

            for entry in report_entries

            if entry.reboot_required

        ])

        total_duration = round(

            sum(

                entry.duration_seconds

                for entry

                in report_entries

            ),

            2
        )

        return {

            "total": total,

            "success": success,

            "failed": failed,

            "reboot_required":
                reboot_required,

            "duration":
                total_duration
        }

    # ---------------------------------------------------------
    # REGROUPEMENT PAR PC
    # ---------------------------------------------------------

    def group_by_host(
        self,
        report_entries
    ):

        grouped = defaultdict(
            list
        )

        for entry in report_entries:

            grouped[
                entry.hostname
            ].append(
                entry
            )

        return grouped

    # ---------------------------------------------------------
    # HTML
    # ---------------------------------------------------------

    def _build_html(
        self,
        report_entries,
        stats
    ):

        grouped = self.group_by_host(
            report_entries
        )

        html = f"""
<!DOCTYPE html>
<html>
<head>

<meta charset="utf-8">

<title>
Rapport Windows Update
</title>

<style>

body {{

    font-family: Arial;
    margin: 30px;
}}

table {{

    width: 100%;
    border-collapse: collapse;
}}

th, td {{

    border: 1px solid #cccccc;
    padding: 8px;
}}

th {{

    background-color: #f0f0f0;
}}

.success {{

    background-color: #d5ffe0;
}}

.failed {{

    background-color: #ffd6d6;
}}

.warning {{

    background-color: #fff2cc;
}}

</style>

</head>

<body>

<h1>
Rapport Windows Update
</h1>

<p>
Date :
{datetime.now()}
</p>

<h2>
Statistiques globales
</h2>

<ul>

<li>
Total KB :
{stats['total']}
</li>

<li>
Succès :
{stats['success']}
</li>

<li>
Échecs :
{stats['failed']}
</li>

<li>
Redémarrage requis :
{stats['reboot_required']}
</li>

<li>
Temps total :
{stats['duration']} s
</li>

</ul>

"""

        for hostname, entries in grouped.items():

            html += f"""

<h2>
{hostname}
</h2>

<table>

<tr>

<th>KB</th>

<th>Statut</th>

<th>Durée</th>

<th>Redémarrage</th>

<th>Erreur</th>

</tr>

"""

            for entry in entries:

                css_class = (
                    "success"
                    if entry.status == "SUCCESS"
                    else "failed"
                )

                html += f"""

<tr class="{css_class}">

<td>
{entry.kb_id}
</td>

<td>
{entry.status}
</td>

<td>
{entry.duration_seconds}
</td>

<td>
{
'OUI'
if entry.reboot_required
else 'NON'
}
</td>

<td>
{entry.error_message}
</td>

</tr>

"""

            html += "</table>"

        html += """

</body>
</html>

"""

        return html

    # ---------------------------------------------------------
    # EXPORT COMPLET
    # ---------------------------------------------------------

    def export_all(
        self,
        report_entries
    ):

        csv_file = self.export_csv(
            report_entries
        )

        html_file = self.export_html(
            report_entries
        )

        return {

            "csv": csv_file,

            "html": html_file
        }

    # ---------------------------------------------------------
    # HISTORIQUE
    # ---------------------------------------------------------

    def get_created_reports(self):

        return self.created_reports.copy()