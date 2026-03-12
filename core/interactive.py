"""
Interface terminal interactive avec sélection cliquable.
Utilise questionary pour les menus et rich pour l'affichage.
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

import questionary
from questionary import Style
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from models.repo import RepoInfo, RepoStatus


logger = logging.getLogger(__name__)

# Style PowerShell-like
console = Console()

CUSTOM_STYLE = Style([
    ("qmark", "fg:cyan bold"),
    ("question", "fg:white bold"),
    ("answer", "fg:green bold"),
    ("pointer", "fg:cyan bold"),
    ("highlighted", "fg:cyan bold"),
    ("selected", "fg:green"),
    ("separator", "fg:gray"),
    ("instruction", "fg:gray italic"),
])


class InteractiveUI:
    """Interface utilisateur interactive pour le workflow Git."""

    def __init__(self):
        self.console = console

    def clear_screen(self) -> None:
        """Efface l'écran."""
        self.console.clear()

    def print_header(self) -> None:
        """Affiche l'en-tête du programme."""
        now = datetime.now().strftime("%H:%M - %d/%m/%Y")
        
        header = Text()
        header.append("🔍 Git Workflow Manager", style="bold cyan")
        header.append(f"  │  {now}", style="dim")
        
        self.console.print(Panel(
            header,
            border_style="cyan",
            padding=(0, 2)
        ))
        self.console.print()

    def print_section(self, title: str, icon: str = "📁") -> None:
        """Affiche un titre de section."""
        self.console.print(f"\n{icon} [bold white]{title}[/bold white]")
        self.console.print("─" * 50, style="dim")

    def print_success(self, message: str) -> None:
        """Affiche un message de succès."""
        self.console.print(f"[green]✓[/green] {message}")

    def print_error(self, message: str) -> None:
        """Affiche un message d'erreur."""
        self.console.print(f"[red]✗[/red] {message}")

    def print_warning(self, message: str) -> None:
        """Affiche un avertissement."""
        self.console.print(f"[yellow]![/yellow] {message}")

    def print_info(self, message: str) -> None:
        """Affiche une information."""
        self.console.print(f"[dim]>[/dim] {message}")

    def display_new_repos(self, repos: list[Path]) -> None:
        """Affiche les nouveaux repos détectés."""
        if not repos:
            return
        
        self.print_section("Nouveaux repos détectés", "🆕")
        
        for repo in repos:
            self.console.print(f"  [cyan]•[/cyan] {repo.name}")
            self.console.print(f"    [dim]{repo}[/dim]")

    def display_repos_status(self, repos: list[RepoInfo]) -> None:
        """Affiche le statut de tous les repos."""
        self.print_section("État des repositories", "📊")
        
        table = Table(show_header=True, header_style="bold cyan", box=None)
        table.add_column("Repo", style="white")
        table.add_column("Branche", style="dim")
        table.add_column("Statut", justify="center")
        table.add_column("Changements", justify="right")
        
        for repo in repos:
            # Icône statut
            status_display = {
                RepoStatus.CLEAN: "[green]✓ Clean[/green]",
                RepoStatus.MODIFIED: "[yellow]● Modifié[/yellow]",
                RepoStatus.UNTRACKED: "[blue]+ Untracked[/blue]",
                RepoStatus.ERROR: "[red]✗ Erreur[/red]",
                RepoStatus.NEW: "[cyan]★ Nouveau[/cyan]"
            }.get(repo.status, "?")
            
            # Changements
            if repo.status == RepoStatus.CLEAN:
                changes = "[dim]-[/dim]"
            elif repo.status == RepoStatus.ERROR:
                changes = f"[dim]{repo.error_message[:20]}[/dim]"
            else:
                changes = f"[green]+{repo.total_additions}[/green] [red]-{repo.total_deletions}[/red] ({repo.file_count})"
            
            table.add_row(
                repo.name,
                repo.branch,
                status_display,
                changes
            )
        
        self.console.print(table)

    def select_new_repos_to_track(self, repos: list[Path]) -> list[Path]:
        """
        Sélection interactive des nouveaux repos à suivre.
        
        Returns:
            Liste des repos sélectionnés
        """
        if not repos:
            return []
        
        self.console.print()
        
        choices = [
            questionary.Choice(
                title=f"{repo.name} ({repo})",
                value=repo,
                checked=True  # Pré-sélectionné
            )
            for repo in repos
        ]
        
        selected = questionary.checkbox(
            "Sélectionnez les repos à ajouter au suivi:",
            choices=choices,
            style=CUSTOM_STYLE,
            instruction="(ESPACE: sélectionner, ENTER: valider)"
        ).ask()
        
        return selected or []

    def select_repos_to_push(self, repos: list[RepoInfo]) -> list[RepoInfo]:
        """
        Sélection interactive des repos à commit/push.
        
        Returns:
            Liste des repos sélectionnés
        """
        # Filtrer les repos avec changements
        actionable = [r for r in repos if r.is_actionable]
        
        if not actionable:
            self.print_info("Aucun repo avec des modifications.")
            return []
        
        self.console.print()
        
        choices = [
            questionary.Choice(
                title=self._format_repo_choice(repo),
                value=repo,
                checked=False
            )
            for repo in actionable
        ]
        
        selected = questionary.checkbox(
            "Sélectionnez les repos à commit/push:",
            choices=choices,
            style=CUSTOM_STYLE,
            instruction="(ESPACE: sélectionner, ENTER: valider)"
        ).ask()
        
        return selected or []

    def _format_repo_choice(self, repo: RepoInfo) -> str:
        """Formate l'affichage d'un repo pour la sélection."""
        stats = f"+{repo.total_additions} -{repo.total_deletions}"
        files = f"({repo.file_count} fichiers)"
        
        # Padding pour alignement
        name = repo.name.ljust(25)
        stats = stats.ljust(12)
        
        return f"{name} {stats} {files}"

    def select_readme_generation(self, repos: list[RepoInfo]) -> list[RepoInfo]:
        """
        Sélection des repos pour lesquels générer un README.
        
        Returns:
            Liste des repos sélectionnés
        """
        if not repos:
            return []
        
        self.console.print()
        
        choices = [
            questionary.Choice(
                title=f"{repo.name} {'[README existant]' if (repo.path / 'README.md').exists() else '[Pas de README]'}",
                value=repo,
                checked=not (repo.path / "README.md").exists()
            )
            for repo in repos
        ]
        
        selected = questionary.checkbox(
            "Générer/mettre à jour le README pour:",
            choices=choices,
            style=CUSTOM_STYLE,
            instruction="(ESPACE: sélectionner, ENTER: valider)"
        ).ask()
        
        return selected or []

    def confirm_action(self, message: str) -> bool:
        """Demande de confirmation simple."""
        return questionary.confirm(
            message,
            style=CUSTOM_STYLE,
            default=True
        ).ask()

    def display_operation_result(
        self,
        repo_name: str,
        result: dict
    ) -> None:
        """Affiche le résultat d'une opération commit/push."""
        self.console.print()
        self.console.print(f"[bold]{repo_name}[/bold]")
        
        if result.get("readme_generated"):
            self.print_success("README généré")
        
        if result.get("staged"):
            self.print_success("Fichiers stagés")
        
        if result.get("committed"):
            msg = result.get("commit_message", "")
            self.print_success(f"Commit: {msg[:50]}...")
        
        if result.get("pushed"):
            self.print_success("Push effectué")
        elif result.get("error"):
            self.print_error(result["error"])

    def display_summary(
        self,
        total: int,
        success: int,
        failed: int
    ) -> None:
        """Affiche le résumé final."""
        self.console.print()
        
        summary = Panel(
            f"[bold]Terminé[/bold]\n\n"
            f"  Total: {total}\n"
            f"  [green]Réussis: {success}[/green]\n"
            f"  [red]Échecs: {failed}[/red]",
            title="📋 Résumé",
            border_style="cyan",
            padding=(1, 2)
        )
        
        self.console.print(summary)

    def show_spinner(self, message: str):
        """Retourne un contexte de spinner."""
        return self.console.status(f"[cyan]{message}[/cyan]", spinner="dots")

    def ask_continue(self) -> bool:
        """Demande si l'utilisateur veut continuer."""
        return questionary.confirm(
            "Continuer avec ces sélections?",
            style=CUSTOM_STYLE,
            default=True
        ).ask()

    def goodbye(self) -> None:
        """Message de fin."""
        self.console.print()
        self.console.print("[dim]─" * 50 + "[/dim]")
        self.console.print("[cyan]À demain ![/cyan] 👋")
        self.console.print()