"""
Implémentation du provider Ollama (local).
"""

import logging
from typing import Optional

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from llm.base import LLMProvider, LLMResponse, RepoContext, ChangeSummary


logger = logging.getLogger(__name__)


class OllamaProvider(LLMProvider):
    """Provider utilisant Ollama en local."""

    def __init__(self, config: dict):
        self.model = config.get("model", "mistral:7b")
        self.base_url = config.get("base_url", "http://localhost:11434")
        self.timeout = config.get("timeout", 120)

    @property
    def name(self) -> str:
        return f"Ollama ({self.model})"

    def is_available(self) -> bool:
        """Vérifie si Ollama est accessible."""
        try:
            response = httpx.get(
                f"{self.base_url}/api/tags",
                timeout=5
            )
            return response.status_code == 200
        except Exception:
            return False

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    def _call_api(self, prompt: str) -> LLMResponse:
        """Appel API Ollama avec retry automatique."""
        try:
            response = httpx.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.7,
                        "num_predict": 2048
                    }
                },
                timeout=self.timeout
            )
            
            if response.status_code != 200:
                return LLMResponse(
                    content="",
                    success=False,
                    error_message=f"HTTP {response.status_code}"
                )
            
            data = response.json()
            content = data.get("response", "")
            
            logger.info(f"Ollama: réponse générée ({len(content)} chars)")
            
            return LLMResponse(
                content=content,
                success=True,
                tokens_used=None  # Ollama ne retourne pas le count
            )
            
        except httpx.TimeoutException:
            logger.error("Timeout Ollama")
            return LLMResponse(
                content="",
                success=False,
                error_message="Timeout"
            )
        except Exception as e:
            logger.error(f"Erreur Ollama: {e}")
            return LLMResponse(
                content="",
                success=False,
                error_message=str(e)
            )

    def generate_readme(self, context: RepoContext) -> LLMResponse:
        """Génère un README pour le repository."""
        
        prompt = f"""Tu es un expert en documentation technique.
Génère un README.md professionnel, clair et concis.
Utilise le format Markdown standard.
Inclus: titre, description, installation, usage, structure si pertinent.
Réponds UNIQUEMENT avec le contenu Markdown, sans commentaires.

Génère un README.md pour ce repository:

Nom: {context.name}
Chemin: {context.path}
Langages détectés: {', '.join(context.languages) if context.languages else 'Non détecté'}

Structure du projet:
{context.tree_structure}

Fichiers principaux:
{chr(10).join(context.files[:20])}
{'... et ' + str(len(context.files) - 20) + ' autres fichiers' if len(context.files) > 20 else ''}
"""

        if context.existing_readme:
            prompt += f"""

README existant (à améliorer):
{context.existing_readme[:1000]}
"""

        return self._call_api(prompt)

    def generate_commit_message(self, changes: ChangeSummary) -> LLMResponse:
        """Génère un message de commit conventionnel."""
        
        files_summary = []
        if changes.files_added:
            files_summary.append(f"Ajoutés: {', '.join(changes.files_added[:5])}")
        if changes.files_modified:
            files_summary.append(f"Modifiés: {', '.join(changes.files_modified[:5])}")
        if changes.files_deleted:
            files_summary.append(f"Supprimés: {', '.join(changes.files_deleted[:5])}")

        prompt = f"""Tu es un expert Git.
Génère un message de commit au format Conventional Commits.
Format: type(scope): description courte

Types: feat, fix, docs, style, refactor, test, chore
Scope: optionnel, partie du code concernée
Description: impératif, minuscule, max 72 caractères

Réponds UNIQUEMENT avec le message de commit, rien d'autre.

Génère un commit message pour ces changements:

Repository: {changes.repo_name}

Fichiers:
{chr(10).join(files_summary)}

Diff (extrait):
{changes.diff_content[:2000]}
"""

        return self._call_api(prompt)