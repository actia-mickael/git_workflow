"""
Opérations Git : staging, commit, push, génération README.
"""

import logging
import subprocess
from pathlib import Path
from typing import Optional

from models.repo import RepoInfo
from llm.base import LLMProvider, RepoContext, ChangeSummary


logger = logging.getLogger(__name__)


class GitOperations:
    """Gère les opérations Git sur les repositories."""

    def __init__(self, config: dict, llm_provider: LLMProvider):
        self.config = config
        self.llm = llm_provider
        self.commit_style = config.get("git", {}).get("commit_style", "conventional")
        self.auto_push = config.get("git", {}).get("auto_push", False)

    def _run_git(self, repo_path: Path, *args) -> tuple[bool, str]:
        """Exécute une commande git."""
        try:
            result = subprocess.run(
                ["git", *args],
                cwd=repo_path,
                capture_output=True,
                text=True,
                timeout=60
            )
            if result.returncode != 0:
                logger.warning(f"Git error: {result.stderr}")
            return result.returncode == 0, result.stdout.strip() or result.stderr.strip()
        except subprocess.TimeoutExpired:
            return False, "Timeout"
        except Exception as e:
            return False, str(e)

    def stage_all(self, repo_path: Path) -> bool:
        """Stage tous les fichiers modifiés."""
        success, output = self._run_git(repo_path, "add", "-A")
        if success:
            logger.info(f"Fichiers stagés: {repo_path.name}")
        return success

    def stage_files(self, repo_path: Path, files: list[str]) -> bool:
        """Stage des fichiers spécifiques."""
        success, output = self._run_git(repo_path, "add", *files)
        return success

    def commit(self, repo_path: Path, message: str) -> bool:
        """Crée un commit avec le message donné."""
        success, output = self._run_git(repo_path, "commit", "-m", message)
        if success:
            logger.info(f"Commit créé: {repo_path.name}")
        else:
            logger.error(f"Échec commit {repo_path.name}: {output}")
        return success

    def push(self, repo_path: Path, branch: Optional[str] = None) -> bool:
        """Push vers le remote."""
        args = ["push"]
        if branch:
            args.extend(["origin", branch])
        
        success, output = self._run_git(repo_path, *args)
        if success:
            logger.info(f"Push réussi: {repo_path.name}")
        else:
            logger.error(f"Échec push {repo_path.name}: {output}")
        return success

    def set_upstream_and_push(self, repo_path: Path, branch: str) -> bool:
        """Configure l'upstream et push."""
        success, output = self._run_git(
            repo_path, "push", "-u", "origin", branch
        )
        return success

    def generate_commit_message(
        self,
        repo_info: RepoInfo,
        diff_content: str
    ) -> Optional[str]:
        """Génère un message de commit via LLM."""
        
        if not self.llm.is_available():
            logger.warning("LLM non disponible, message par défaut")
            return self._default_commit_message(repo_info)
        
        changes = ChangeSummary(
            repo_name=repo_info.name,
            files_modified=[c.path for c in repo_info.changes if c.status == "M"],
            files_added=[c.path for c in repo_info.changes if c.status in ("A", "?")],
            files_deleted=[c.path for c in repo_info.changes if c.status == "D"],
            diff_content=diff_content[:3000]  # Limite pour les tokens
        )
        
        response = self.llm.generate_commit_message(changes)
        
        if response.success:
            return response.content.strip()
        else:
            logger.warning(f"Erreur LLM: {response.error_message}")
            return self._default_commit_message(repo_info)

    def _default_commit_message(self, repo_info: RepoInfo) -> str:
        """Message de commit par défaut si LLM indisponible."""
        file_count = len(repo_info.changes)
        return f"chore: update {file_count} file(s)"

    def generate_readme(
        self,
        repo_path: Path,
        tree_structure: str,
        languages: list[str]
    ) -> Optional[str]:
        """Génère un README via LLM."""
        
        if not self.llm.is_available():
            logger.warning("LLM non disponible pour README")
            return None
        
        # Liste des fichiers
        files = []
        ignore = {".git", "__pycache__", "node_modules", ".venv"}
        for f in repo_path.rglob("*"):
            if f.is_file() and not any(p in f.parts for p in ignore):
                files.append(str(f.relative_to(repo_path)))
        
        # README existant ?
        existing_readme = None
        readme_path = repo_path / "README.md"
        if readme_path.exists():
            try:
                existing_readme = readme_path.read_text(encoding="utf-8")
            except Exception:
                pass
        
        context = RepoContext(
            name=repo_path.name,
            path=str(repo_path),
            files=files,
            tree_structure=tree_structure,
            languages=languages,
            existing_readme=existing_readme
        )
        
        response = self.llm.generate_readme(context)
        
        if response.success:
            return response.content
        else:
            logger.error(f"Erreur génération README: {response.error_message}")
            return None

    def write_readme(self, repo_path: Path, content: str) -> bool:
        """Écrit le README.md dans le repo."""
        readme_path = repo_path / "README.md"
        
        try:
            readme_path.write_text(content, encoding="utf-8")
            logger.info(f"README créé: {repo_path.name}")
            return True
        except Exception as e:
            logger.error(f"Erreur écriture README: {e}")
            return False

    def full_commit_push(
        self,
        repo_info: RepoInfo,
        diff_content: str,
        generate_readme: bool = False,
        tree_structure: str = "",
        languages: list[str] = None
    ) -> dict:
        """
        Workflow complet : README (opt) → stage → commit → push.
        
        Returns:
            dict avec le statut de chaque étape
        """
        result = {
            "readme_generated": False,
            "staged": False,
            "committed": False,
            "pushed": False,
            "commit_message": None,
            "error": None
        }
        
        repo_path = repo_info.path
        
        try:
            # Étape 1: README si demandé
            if generate_readme:
                readme_content = self.generate_readme(
                    repo_path, tree_structure, languages or []
                )
                if readme_content:
                    self.write_readme(repo_path, readme_content)
                    result["readme_generated"] = True
            
            # Étape 2: Stage
            if not self.stage_all(repo_path):
                result["error"] = "Échec staging"
                return result
            result["staged"] = True
            
            # Étape 3: Commit message
            commit_msg = self.generate_commit_message(repo_info, diff_content)
            result["commit_message"] = commit_msg
            
            # Étape 4: Commit
            if not self.commit(repo_path, commit_msg):
                result["error"] = "Échec commit"
                return result
            result["committed"] = True
            
            # Étape 5: Push
            if not repo_info.has_remote:
                logger.warning(f"Pas de remote configuré: {repo_info.name}")
                result["error"] = "Pas de remote"
                return result
            
            if not self.push(repo_path, repo_info.branch):
                # Tenter avec upstream
                if not self.set_upstream_and_push(repo_path, repo_info.branch):
                    result["error"] = "Échec push"
                    return result
            
            result["pushed"] = True
            
        except Exception as e:
            result["error"] = str(e)
            logger.error(f"Erreur workflow {repo_info.name}: {e}")
        
        return result