"""
Modèles de données pour la gestion des repositories Git.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional


class RepoStatus(Enum):
    """État d'un repository."""
    CLEAN = "clean"
    MODIFIED = "modified"
    UNTRACKED = "untracked"
    NEW = "new"
    ERROR = "error"


@dataclass
class FileChange:
    """Représente un fichier modifié."""
    path: str
    status: str          # M=modified, A=added, D=deleted, ?=untracked
    additions: int = 0
    deletions: int = 0

    @property
    def status_icon(self) -> str:
        icons = {
            "M": "📝",
            "A": "➕",
            "D": "🗑️",
            "?": "❓",
            "R": "📛"
        }
        return icons.get(self.status, "•")


@dataclass
class RepoInfo:
    """Informations complètes sur un repository."""
    path: Path
    name: str
    status: RepoStatus = RepoStatus.CLEAN
    branch: str = "main"
    remote_url: Optional[str] = None
    has_remote: bool = False
    changes: list[FileChange] = field(default_factory=list)
    total_additions: int = 0
    total_deletions: int = 0
    last_commit_date: Optional[datetime] = None
    last_commit_message: Optional[str] = None
    created_at: Optional[datetime] = None  # Date création .git
    error_message: Optional[str] = None

    @property
    def file_count(self) -> int:
        return len(self.changes)

    @property
    def summary(self) -> str:
        """Résumé une ligne pour l'affichage."""
        if self.status == RepoStatus.ERROR:
            return f"❌ Erreur: {self.error_message}"
        if self.status == RepoStatus.CLEAN:
            return "✅ Aucune modification"
        return f"+{self.total_additions} -{self.total_deletions} ({self.file_count} fichiers)"

    @property
    def is_actionable(self) -> bool:
        """Indique si le repo nécessite une action."""
        return self.status in (RepoStatus.MODIFIED, RepoStatus.UNTRACKED)


@dataclass
class KnownRepo:
    """Repository enregistré dans le cache."""
    path: str
    added_at: str        # ISO format
    last_seen: str       # ISO format
    auto_push: bool = False
    ignore: bool = False

    def to_dict(self) -> dict:
        return {
            "path": self.path,
            "added_at": self.added_at,
            "last_seen": self.last_seen,
            "auto_push": self.auto_push,
            "ignore": self.ignore
        }

    @classmethod
    def from_dict(cls, data: dict) -> "KnownRepo":
        return cls(
            path=data["path"],
            added_at=data["added_at"],
            last_seen=data["last_seen"],
            auto_push=data.get("auto_push", False),
            ignore=data.get("ignore", False)
        )