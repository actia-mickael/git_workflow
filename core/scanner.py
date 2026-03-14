"""
Scanner pour détecter les repositories Git dans l'arborescence.
Identifie les nouveaux repos créés dans la journée.
"""

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from models.repo import KnownRepo


logger = logging.getLogger(__name__)


class RepoScanner:
    """Scanne un répertoire pour trouver les repos Git."""

    def __init__(self, config: dict):
        # Support root_directories (liste) ou root_directory (string)
        scan_config = config["scan"]
        if "root_directories" in scan_config:
            self.root_dirs = [Path(p).expanduser() for p in scan_config["root_directories"]]
        else:
            self.root_dirs = [Path(scan_config["root_directory"]).expanduser()]
        
        self.max_depth = scan_config.get("max_depth", 3)
        self.exclude_patterns = scan_config.get("exclude_patterns", [])
        self.scan_nested_repos = scan_config.get("scan_nested_repos", False)
        self.known_repos_file = Path(config["tracking"]["known_repos_file"])
        self._known_repos: Optional[dict[str, KnownRepo]] = None

    @property
    def known_repos(self) -> dict[str, KnownRepo]:
        """Charge le cache des repos connus (lazy loading)."""
        if self._known_repos is None:
            self._known_repos = self._load_known_repos()
        return self._known_repos

    def _load_known_repos(self) -> dict[str, KnownRepo]:
        """Charge les repos connus depuis le fichier JSON."""
        if not self.known_repos_file.exists():
            return {}
        
        try:
            with open(self.known_repos_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            return {
                path: KnownRepo.from_dict(repo_data)
                for path, repo_data in data.items()
            }
        except (json.JSONDecodeError, KeyError) as e:
            logger.warning(f"Erreur lecture cache repos: {e}")
            return {}

    def _save_known_repos(self) -> None:
        """Sauvegarde le cache des repos connus."""
        self.known_repos_file.parent.mkdir(parents=True, exist_ok=True)
        
        data = {
            path: repo.to_dict()
            for path, repo in self.known_repos.items()
        }
        
        with open(self.known_repos_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def _should_exclude(self, path: Path) -> bool:
        """Vérifie si le chemin doit être exclu."""
        for pattern in self.exclude_patterns:
            if pattern in path.parts:
                return True
        return False

    def _get_git_creation_date(self, git_path: Path) -> Optional[datetime]:
        """Récupère la date de création du dossier .git."""
        try:
            stat = git_path.stat()
            return datetime.fromtimestamp(stat.st_ctime)
        except OSError:
            return None

    def _is_created_today(self, git_path: Path) -> bool:
        """Vérifie si le repo a été créé dans les dernières 24h."""
        creation_date = self._get_git_creation_date(git_path)
        if creation_date is None:
            return False
        
        cutoff = datetime.now() - timedelta(hours=24)
        return creation_date > cutoff

    def scan_all_repos(self) -> list[Path]:
        """
        Scanne récursivement pour trouver tous les repos Git.

        Returns:
            Liste des chemins vers les repos (dossier parent de .git)
        """
        repos = []

        def scan_recursive(path: Path, depth: int) -> None:
            if depth > self.max_depth:
                return

            if self._should_exclude(path):
                return

            try:
                git_dir = path / ".git"
                if git_dir.is_dir():
                    repos.append(path)
                    if not self.scan_nested_repos:
                        return  # Scanner les sous-dossiers d'un repo

                for child in path.iterdir():
                    if child.is_dir() and not child.name.startswith("."):
                        scan_recursive(child, depth + 1)

            except PermissionError:
                logger.warning(f"Permission refusée: {path}")

        for root_dir in self.root_dirs:
            if not root_dir.exists():
                logger.warning(f"Répertoire racine inexistant: {root_dir}")
                continue
            
            logger.info(f"Scan de {root_dir} (profondeur max: {self.max_depth})")
            scan_recursive(root_dir, 0)

        # Dédupliquer (au cas où des répertoires se chevauchent)
        repos = list(dict.fromkeys(repos))
        logger.info(f"{len(repos)} repos trouvés au total")

        return repos

    def find_new_repos(self) -> list[Path]:
        """
        Identifie les repos nouvellement créés (non présents dans le cache).
        
        Returns:
            Liste des chemins vers les nouveaux repos
        """
        all_repos = self.scan_all_repos()
        new_repos = []
        
        for repo_path in all_repos:
            path_str = str(repo_path)
            
            # Nouveau si absent du cache OU créé dans les 24h
            if path_str not in self.known_repos:
                new_repos.append(repo_path)
                logger.info(f"Nouveau repo détecté: {repo_path.name}")
            
        return new_repos

    def find_tracked_repos(self) -> list[Path]:
        """
        Retourne les repos connus et non ignorés.
        
        Returns:
            Liste des chemins vers les repos suivis
        """
        tracked = []
        
        for path_str, repo in self.known_repos.items():
            if repo.ignore:
                continue
            
            path = Path(path_str)
            if path.exists():
                tracked.append(path)
            else:
                logger.warning(f"Repo disparu: {path_str}")
        
        return tracked

    def add_to_tracking(self, repo_path: Path) -> None:
        """Ajoute un repo au suivi."""
        now = datetime.now().isoformat()
        path_str = str(repo_path)
        
        self.known_repos[path_str] = KnownRepo(
            path=path_str,
            added_at=now,
            last_seen=now
        )
        self._save_known_repos()
        logger.info(f"Repo ajouté au suivi: {repo_path.name}")

    def update_last_seen(self, repo_path: Path) -> None:
        """Met à jour la date de dernière vue d'un repo."""
        path_str = str(repo_path)
        
        if path_str in self.known_repos:
            self.known_repos[path_str].last_seen = datetime.now().isoformat()
            self._save_known_repos()

    def ignore_repo(self, repo_path: Path) -> None:
        """Marque un repo comme ignoré."""
        path_str = str(repo_path)
        
        if path_str in self.known_repos:
            self.known_repos[path_str].ignore = True
        else:
            now = datetime.now().isoformat()
            self.known_repos[path_str] = KnownRepo(
                path=path_str,
                added_at=now,
                last_seen=now,
                ignore=True
            )
        
        self._save_known_repos()
        logger.info(f"Repo ignoré: {repo_path.name}")