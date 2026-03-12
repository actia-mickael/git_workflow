"""
Implémentation du provider Claude API.
"""

import os
import logging
from typing import Optional

import anthropic
from tenacity import retry, stop_after_attempt, wait_exponential

from llm.base import LLMProvider, LLMResponse, RepoContext, ChangeSummary


logger = logging.getLogger(__name__)


class ClaudeProvider(LLMProvider):
    """Provider utilisant l'API Claude d'Anthropic."""

    def __init__(self, config: dict):
        self.model = config.get("model", "claude-sonnet-4-20250514")
        self.max_tokens = config.get("max_tokens", 2048)
        self._client: Optional[anthropic.Anthropic] = None

    @property
    def client(self) -> anthropic.Anthropic:
        """Lazy initialization du client."""
        if self._client is None:
            api_key = os.getenv("ANTHROPIC_API_KEY")
            if not api_key:
                raise ValueError("ANTHROPIC_API_KEY non définie")
            self._client = anthropic.Anthropic(api_key=api_key)
        return self._client

    @property
    def name(self) -> str:
        return f"Claude ({self.model})"

    def is_available(self) -> bool:
        """Vérifie si l'API key est configurée."""
        return os.getenv("ANTHROPIC_API_KEY") is not None

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    def _call_api(self, system: str, user: str) -> LLMResponse:
        """Appel API avec retry automatique."""
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                messages=[{"role": "user", "content": user}],
                system=system
            )
            
            content = response.content[0].text
            tokens = response.usage.input_tokens + response.usage.output_tokens
            
            logger.info(f"Claude API: {tokens} tokens utilisés")
            
            return LLMResponse(
                content=content,
                success=True,
                tokens_used=tokens
            )
            
        except anthropic.APIError as e:
            logger.error(f"Erreur API Claude: {e}")
            return LLMResponse(
                content="",
                success=False,
                error_message=str(e)
            )

    def generate_readme(self, context: RepoContext) -> LLMResponse:
        """Génère un README pour le repository."""
        
        system = """Tu es un expert en documentation technique.
Génère un README.md professionnel, clair et concis.
Utilise le format Markdown standard.
Inclus: titre, description, installation, usage, structure si pertinent.
Réponds UNIQUEMENT avec le contenu Markdown, sans commentaires."""

        user = f"""Génère un README.md pour ce repository:

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
            user += f"""

README existant (à améliorer):
{context.existing_readme[:1000]}
"""

        return self._call_api(system, user)

    def generate_commit_message(self, changes: ChangeSummary) -> LLMResponse:
        """Génère un message de commit conventionnel."""
        
        system = """Tu es un expert Git.
Génère un message de commit au format Conventional Commits.
Format: type(scope): description courte

Types: feat, fix, docs, style, refactor, test, chore
Scope: optionnel, partie du code concernée
Description: impératif, minuscule, max 72 caractères

Réponds UNIQUEMENT avec le message de commit, rien d'autre."""

        files_summary = []
        if changes.files_added:
            files_summary.append(f"Ajoutés: {', '.join(changes.files_added[:5])}")
        if changes.files_modified:
            files_summary.append(f"Modifiés: {', '.join(changes.files_modified[:5])}")
        if changes.files_deleted:
            files_summary.append(f"Supprimés: {', '.join(changes.files_deleted[:5])}")

        user = f"""Génère un commit message pour ces changements:

Repository: {changes.repo_name}

Fichiers:
{chr(10).join(files_summary)}

Diff (extrait):
{changes.diff_content[:2000]}
"""

        return self._call_api(system, user)