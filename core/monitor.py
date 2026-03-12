"""
Moniteur Git pour analyser l'état des repositories.
Collecte les status, diff et informations de chaque repo.
"""

import logging
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Optional

from models.repo import RepoInfo, RepoStatus, FileChange


logger = logging.getLogger(__name__)


class GitMonitor:
    """Analyse l'état des repositories Git."""

    def __init__(self, config: dict):
        self.default_branch = config.get("git", {}).get("default_branch", "main")

    def _run_git(self, repo_path: Path, *args) -> tuple[bool, str]:
        """
        Exécute une commande git dans le repo.
        
        Returns:
            (success, output)
        """
        try:
            result = subprocess.run(
                ["git", *args],
                cwd=repo_path,
                capture_output=True,
                text=True,
                timeout=30
            )
            return result.returncode == 0, result.stdout.strip()
        except subprocess.TimeoutExpired:
            logger.warning(f"Timeout git {args[0]} dans {repo_path}")
            return False, "Timeout"
        except Exception as e:
            return False, str(e)

    def _get_current_branch(self, repo_path: Path) -> str:
        """Récupère la branche courante."""
        success, output = self._run_git(repo_path, "branch", "--show-current")
        return output if success and output else self.default_branch

    def _get_remote_url(self, repo_path: Path) -> Optional[str]:
        """Récupère l'URL du remote origin."""
        success, output = self._run_git(repo_path, "remote", "get-url", "origin")
        return output if success else None

    def _has_remote(self, repo_path: Path) -> bool:
        """Vérifie si un remote est configuré."""
        success, output = self._run_git(repo_path, "remote")
        return success and bool(output.strip())

    def _get_last_commit(self, repo_path: Path) -> tuple[Optional[datetime], Optional[str]]:
        """Récupère la date et le message du dernier commit."""
        success, output = self._run_git(
            repo_path, "log", "-1", "--format=%aI|%s"
        )
        
        if not success or not output:
            return None, None
        
        try:
            date_str, message = output.split("|", 1)
            commit_date = datetime.fromisoformat(date_str)
            return commit_date, message
        except ValueError:
            return None, None

    def _parse_status(self, repo_path: Path) -> list[FileChange]:
        """Parse git status --porcelain pour extraire les changements."""
        success, output = self._run_git(repo_path, "status", "--porcelain")
        
        if not success or not output:
            return []
        
        changes = []
        for line in output.splitlines():
            if len(line) < 3:
                continue
            
            status = line[0:2].strip()
            if not status:
                status = line[1]  # Untracked files
            
            file_path = line[3:]
            
            changes.append(FileChange(
                path=file_path,
                status=status[0] if status else "?"
            ))
        
        return changes

    def _get_diff_stats(self, repo_path: Path) -> tuple[int, int]:
        """Récupère les stats de diff (additions, deletions)."""
        success, output = self._run_git(
            repo_path, "diff", "--stat", "--cached", "HEAD"
        )
        
        if not success:
            # Essayer sans --cached pour les fichiers non stagés
            success, output = self._run_git(repo_path, "diff", "--stat")
        
        if not success or not output:
            return 0, 0
        
        # Dernière ligne format: "X files changed, Y insertions(+), Z deletions(-)"
        lines = output.strip().splitlines()
        if not lines:
            return 0, 0
        
        last_line = lines[-1]
        additions = 0
        deletions = 0
        
        if "insertion" in last_line:
            try:
                part = last_line.split("insertion")[0].split(",")[-1]
                additions = int(part.strip().split()[0])
            except (ValueError, IndexError):
                pass
        
        if "deletion" in last_line:
            try:
                part = last_line.split("deletion")[0].split(",")[-1]
                deletions = int(part.strip().split()[0])
            except (ValueError, IndexError):
                pass
        
        return additions, deletions

    def _get_diff_content(self, repo_path: Path) -> str:
        """Récupère le contenu du diff."""
        # Diff staged
        success, staged = self._run_git(repo_path, "diff", "--cached")
        
        # Diff unstaged
        success2, unstaged = self._run_git(repo_path, "diff")
        
        diff_parts = []
        if staged:
            diff_parts.append(staged)
        if unstaged:
            diff_parts.append(unstaged)
        
        return "\n".join(diff_parts)

    def analyze_repo(self, repo_path: Path) -> RepoInfo:
        """
        Analyse complète d'un repository.
        
        Args:
            repo_path: Chemin vers le repo
            
        Returns:
            RepoInfo avec toutes les informations
        """
        logger.debug(f"Analyse de {repo_path.name}")
        
        # Vérification de base
        git_dir = repo_path / ".git"
        if not git_dir.exists():
            return RepoInfo(
                path=repo_path,
                name=repo_path.name,
                status=RepoStatus.ERROR,
                error_message="Pas un repository Git"
            )
        
        try:
            # Collecte des informations
            branch = self._get_current_branch(repo_path)
            remote_url = self._get_remote_url(repo_path)
            has_remote = self._has_remote(repo_path)
            last_commit_date, last_commit_msg = self._get_last_commit(repo_path)
            changes = self._parse_status(repo_path)
            additions, deletions = self._get_diff_stats(repo_path)
            
            # Détermination du statut
            if not changes:
                status = RepoStatus.CLEAN
            elif any(c.status == "?" for c in changes):
                status = RepoStatus.UNTRACKED
            else:
                status = RepoStatus.MODIFIED
            
            return RepoInfo(
                path=repo_path,
                name=repo_path.name,
                status=status,
                branch=branch,
                remote_url=remote_url,
                has_remote=has_remote,
                changes=changes,
                total_additions=additions,
                total_deletions=deletions,
                last_commit_date=last_commit_date,
                last_commit_message=last_commit_msg
            )
            
        except Exception as e:
            logger.error(f"Erreur analyse {repo_path}: {e}")
            return RepoInfo(
                path=repo_path,
                name=repo_path.name,
                status=RepoStatus.ERROR,
                error_message=str(e)
            )

    def analyze_multiple(self, repo_paths: list[Path]) -> list[RepoInfo]:
        """Analyse plusieurs repos."""
        return [self.analyze_repo(path) for path in repo_paths]

    def get_diff_for_commit(self, repo_path: Path) -> str:
        """Récupère le diff pour génération du commit message."""
        return self._get_diff_content(repo_path)

    def get_tree_structure(self, repo_path: Path, max_depth: int = 2) -> str:
        """Génère une représentation arborescente du projet."""
        lines = []
        
        def walk(path: Path, prefix: str, depth: int):
            if depth > max_depth:
                return
            
            entries = sorted(path.iterdir(), key=lambda p: (p.is_file(), p.name))
            
            # Filtrer les dossiers à ignorer
            ignore = {".git", "__pycache__", "node_modules", ".venv", "venv"}
            entries = [e for e in entries if e.name not in ignore]
            
            for i, entry in enumerate(entries[:15]):  # Limite à 15 entrées
                is_last = i == len(entries) - 1 or i == 14
                connector = "└── " if is_last else "├── "
                lines.append(f"{prefix}{connector}{entry.name}")
                
                if entry.is_dir() and depth < max_depth:
                    extension = "    " if is_last else "│   "
                    walk(entry, prefix + extension, depth + 1)
            
            if len(entries) > 15:
                lines.append(f"{prefix}└── ... ({len(entries) - 15} autres)")
        
        lines.append(repo_path.name + "/")
        walk(repo_path, "", 0)
        
        return "\n".join(lines)

    def detect_languages(self, repo_path: Path) -> list[str]:
        """Détecte les langages utilisés dans le projet."""
        extensions_map = {
            ".py": "Python",
            ".js": "JavaScript",
            ".ts": "TypeScript",
            ".jsx": "React",
            ".tsx": "React TypeScript",
            ".java": "Java",
            ".rs": "Rust",
            ".go": "Go",
            ".rb": "Ruby",
            ".php": "PHP",
            ".cs": "C#",
            ".cpp": "C++",
            ".c": "C",
            ".html": "HTML",
            ".css": "CSS",
            ".scss": "SCSS",
            ".yaml": "YAML",
            ".yml": "YAML",
            ".json": "JSON",
            ".md": "Markdown",
            ".sh": "Shell",
            ".sql": "SQL"
        }
        
        found = set()
        ignore = {".git", "__pycache__", "node_modules", ".venv", "venv"}
        
        for path in repo_path.rglob("*"):
            if any(part in ignore for part in path.parts):
                continue
            if path.is_file():
                ext = path.suffix.lower()
                if ext in extensions_map:
                    found.add(extensions_map[ext])
        
        return sorted(found)