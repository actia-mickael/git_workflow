"""
Interface abstraite pour les providers LLM.
Permet de changer de provider sans modifier le reste du code.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Optional


class LLMProviderType(Enum):
    """Types de providers supportés."""
    CLAUDE = "claude"
    OLLAMA = "ollama"


@dataclass
class LLMResponse:
    """Réponse standardisée d'un provider LLM."""
    content: str
    success: bool
    tokens_used: Optional[int] = None
    error_message: Optional[str] = None


@dataclass 
class RepoContext:
    """Contexte d'un repo pour la génération de contenu."""
    name: str
    path: str
    files: list[str]
    tree_structure: str
    languages: list[str]
    description: Optional[str] = None
    existing_readme: Optional[str] = None


@dataclass
class ChangeSummary:
    """Résumé des changements pour génération commit message."""
    files_modified: list[str]
    files_added: list[str]
    files_deleted: list[str]
    diff_content: str
    repo_name: str


class LLMProvider(ABC):
    """Interface abstraite pour tous les providers LLM."""

    @abstractmethod
    def generate_readme(self, context: RepoContext) -> LLMResponse:
        """
        Génère un README basé sur le contexte du repo.
        
        Args:
            context: Informations sur le repository
            
        Returns:
            LLMResponse avec le contenu du README
        """
        pass

    @abstractmethod
    def generate_commit_message(self, changes: ChangeSummary) -> LLMResponse:
        """
        Génère un message de commit basé sur les changements.
        
        Args:
            changes: Résumé des modifications
            
        Returns:
            LLMResponse avec le message de commit (conventional commits)
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """
        Vérifie si le provider est disponible et configuré.
        
        Returns:
            True si le provider peut être utilisé
        """
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Nom du provider pour les logs."""
        pass


def get_provider(config: dict) -> LLMProvider:
    """
    Factory pour instancier le bon provider selon la config.
    
    Args:
        config: Section 'llm' du fichier config.yaml
        
    Returns:
        Instance du provider configuré
        
    Raises:
        ValueError: Si le provider n'est pas supporté
    """
    provider_type = config.get("provider", "claude")
    
    if provider_type == "claude":
        from llm.claude_provider import ClaudeProvider
        return ClaudeProvider(config.get("claude", {}))
    
    elif provider_type == "ollama":
        from llm.ollama_provider import OllamaProvider
        return OllamaProvider(config.get("ollama", {}))
    
    else:
        raise ValueError(f"Provider LLM non supporté: {provider_type}")