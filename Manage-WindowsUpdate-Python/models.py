# models.py

from dataclasses import dataclass, field
from enum import Enum
from threading import Event
from typing import List


class JobState(Enum):
    WAITING = "En attente"
    RUNNING = "En cours"
    SUCCESS = "Terminé"
    WARNING = "Avertissement"
    FAILED = "Erreur"
    CANCELLED = "Annulé"


class KBState(Enum):
    PENDING = "En attente"
    DOWNLOADING = "Téléchargement"
    INSTALLING = "Installation"
    SUCCESS = "Installée"
    FAILED = "Erreur"
    CANCELLED = "Annulée"


@dataclass
class Credentials:
    username: str
    password: str
    domain: str = ""

    @property
    def full_username(self) -> str:
        if self.domain:
            return f"{self.domain}\\{self.username}"
        return self.username