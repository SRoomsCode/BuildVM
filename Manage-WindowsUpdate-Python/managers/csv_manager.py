# managers/csv_manager.py

import csv

from pathlib import Path

from models import PCJob

from managers.logging_manager import logger

from settings import (
    SUPPORTED_CSV_SEPARATORS,
    CSV_REQUIRED_COLUMNS,
    CSV_OPTIONAL_COLUMNS
)


class CSVFormatError(Exception):
    pass


class CSVManager:

    def __init__(self):
        pass

    # ---------------------------------------------------------
    # DETECTION SEPARATEUR
    # ---------------------------------------------------------

    def detect_delimiter(
        self,
        file_path
    ):

        with open(
            file_path,
            "r",
            encoding="utf-8-sig"
        ) as file:

            sample = file.read(2048)

        candidates = [
            ";",
            ",",
            "\t"
        ]

        best_delimiter = ";"
        best_score = 0

        for delimiter in candidates:

            score = sample.count(
                delimiter
            )

            if score > best_score:

                best_score = score

                best_delimiter = delimiter

        return best_delimiter

    # ---------------------------------------------------------
    # VALIDATION
    # ---------------------------------------------------------

    def validate_columns(
        self,
        headers
    ):

        headers = [

            col.strip()

            for col

            in headers

        ]

        for required in CSV_REQUIRED_COLUMNS:

            if required not in headers:

                raise CSVFormatError(
                    f"Colonne obligatoire absente : "
                    f"{required}"
                )

    # ---------------------------------------------------------
    # IMPORT
    # ---------------------------------------------------------

    def import_computers(
        self,
        file_path
    ):

        file_path = Path(
            file_path
        )

        if not file_path.exists():

            raise FileNotFoundError(
                str(file_path)
            )

        delimiter = (
            self.detect_delimiter(
                file_path
            )
        )

        logger.info(
            f"Import CSV : {file_path}"
        )

        logger.info(
            f"Séparateur détecté : "
            f"{delimiter}"
        )

        computers = []

        existing = set()

        with open(
            file_path,
            "r",
            encoding="utf-8-sig"
        ) as file:

            reader = csv.DictReader(
                file,
                delimiter=delimiter
            )

            self.validate_columns(
                reader.fieldnames
            )

            for row in reader:

                hostname = (
                    row.get("Nom", "")
                    .strip()
                )

                ip_address = (
                    row.get("IP", "")
                    .strip()
                )

                if not hostname:
                    continue

                key = hostname.lower()

                if key in existing:

                    logger.warning(
                        f"Doublon ignoré : "
                        f"{hostname}"
                    )

                    continue

                existing.add(
                    key
                )

                pc_job = PCJob(

                    hostname=
                    hostname,

                    ip_address=
                    ip_address
                )

                computers.append(
                    pc_job
                )

        logger.info(
            f"{len(computers)} "
            f"poste(s) importé(s)"
        )

        return computers

    # ---------------------------------------------------------
    # EXPORT PC
    # ---------------------------------------------------------

    def export_computers(
        self,
        pc_jobs,
        file_path
    ):

        with open(
            file_path,
            "w",
            newline="",
            encoding="utf-8-sig"
        ) as file:

            writer = csv.writer(
                file,
                delimiter=";"
            )

            writer.writerow([
                "Nom",
                "IP",
                "Etat",
                "Progression",
                "Redemarrage"
            ])

            for job in pc_jobs:

                writer.writerow([

                    job.hostname,

                    job.ip_address,

                    job.state.value,

                    job.progress,

                    (
                        "OUI"
                        if job.reboot_required
                        else "NON"
                    )
                ])

        logger.info(
            f"Export PC : "
            f"{file_path}"
        )

        return file_path

    # ---------------------------------------------------------
    # EXEMPLE
    # ---------------------------------------------------------

    def generate_template(
        self,
        file_path
    ):

        with open(
            file_path,
            "w",
            newline="",
            encoding="utf-8-sig"
        ) as file:

            writer = csv.writer(
                file,
                delimiter=";"
            )

            writer.writerow([
                "Nom",
                "IP"
            ])

            writer.writerow([
                "PC-001",
                "192.168.1.10"
            ])

            writer.writerow([
                "PC-002",
                "192.168.1.11"
            ])

            writer.writerow([
                "PC-003",
                "192.168.1.12"
            ])

        logger.info(
            f"Modèle CSV créé : "
            f"{file_path}"
        )

        return file_path

    # ---------------------------------------------------------
    # FUSION
    # ---------------------------------------------------------

    def merge_computers(
        self,
        current_jobs,
        imported_jobs
    ):

        existing = {

            job.hostname.lower()

            for job

            in current_jobs
        }

        added = 0

        for job in imported_jobs:

            key = (
                job.hostname
                .lower()
            )

            if key in existing:
                continue

            current_jobs.append(
                job
            )

            existing.add(
                key
            )

            added += 1

        logger.info(
            f"{added} nouveau(x) "
            f"poste(s) ajouté(s)"
        )

        return added

    # ---------------------------------------------------------
    # VALIDATEUR SIMPLE
    # ---------------------------------------------------------

    def is_valid_file(
        self,
        file_path
    ):

        try:

            self.import_computers(
                file_path
            )

            return True

        except Exception:

            return False