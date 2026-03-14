"""
Git Workflow Manager - Orchestrateur principal.
Point d'entrée du programme.
"""

import argparse
import logging
import sys
from datetime import datetime
from pathlib import Path

import yaml
from dotenv import load_dotenv

from core.scanner import RepoScanner
from core.monitor import GitMonitor
from core.git_operations import GitOperations
from core.interactive import InteractiveUI
from llm.base import get_provider
from core.notifier import send_windows_notification, write_summary_log, format_notification_message


# Chargement variables d'environnement
load_dotenv()


def setup_logging(config: dict) -> None:
    """Configure le logging."""
    log_config = config.get("logging", {})
    log_level = getattr(logging, log_config.get("level", "INFO"))
    log_file = log_config.get("file", "data/logs/workflow.log")
    
    # Créer le dossier logs si nécessaire
    Path(log_file).parent.mkdir(parents=True, exist_ok=True)
    
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.FileHandler(log_file, encoding="utf-8"),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Réduire verbosité des libs externes
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("anthropic").setLevel(logging.WARNING)


def load_config(config_path: str = "config.yaml") -> dict:
    """Charge la configuration."""
    path = Path(config_path)
    
    if not path.exists():
        raise FileNotFoundError(f"Fichier config introuvable: {config_path}")
    
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def main():
    """Point d'entrée principal."""
    
    # Arguments CLI
    parser = argparse.ArgumentParser(description="Git Workflow Manager")
    parser.add_argument(
        "--auto", 
        action="store_true", 
        help="Mode automatique (non-interactif)"
    )
    args = parser.parse_args()
    auto_mode = args.auto
    
    # Chargement config
    try:
        config = load_config()
    except FileNotFoundError as e:
        print(f"❌ Erreur: {e}")
        sys.exit(1)
    
    setup_logging(config)
    logger = logging.getLogger(__name__)
    logger.info(f"Démarrage Git Workflow Manager (auto={auto_mode})")
    
    # Initialisation des composants
    ui = InteractiveUI()
    scanner = RepoScanner(config)
    monitor = GitMonitor(config)
    
    try:
        llm_provider = get_provider(config.get("llm", {}))
        if not llm_provider.is_available():
            ui.print_warning(f"LLM ({llm_provider.name}) non disponible - README/commits par défaut")
    except Exception as e:
        logger.warning(f"Erreur init LLM: {e}")
        llm_provider = None
    
    git_ops = GitOperations(config, llm_provider) if llm_provider else None
    
    # Interface
    if not auto_mode:
        ui.clear_screen()
    ui.print_header()
    
    # ═══════════════════════════════════════════════════════════════
    # ÉTAPE 1 : Scan des nouveaux repos
    # ═══════════════════════════════════════════════════════════════
    
    ui.print_section("Scan du répertoire", "🔍")
    
    with ui.show_spinner("Recherche des repositories..."):
        new_repos = scanner.find_new_repos()
        tracked_repos = scanner.find_tracked_repos()
    
    ui.print_info(f"{len(tracked_repos)} repos suivis")
    ui.print_info(f"{len(new_repos)} nouveaux repos détectés")
    
    # Gestion des nouveaux repos
    if new_repos:
        ui.display_new_repos(new_repos)
        
        if auto_mode:
            # Mode auto : ajouter tous les nouveaux repos
            selected_new = new_repos
            for repo_path in selected_new:
                scanner.add_to_tracking(repo_path)
                tracked_repos.append(repo_path)
                ui.print_success(f"Ajouté (auto): {repo_path.name}")
        else:
            selected_new = ui.select_new_repos_to_track(new_repos)
            
            for repo_path in selected_new:
                scanner.add_to_tracking(repo_path)
                tracked_repos.append(repo_path)
                ui.print_success(f"Ajouté: {repo_path.name}")
            
            # Ignorer les non-sélectionnés
            ignored = set(new_repos) - set(selected_new)
            for repo_path in ignored:
                scanner.ignore_repo(repo_path)
    
    # ═══════════════════════════════════════════════════════════════
    # ÉTAPE 2 : Analyse des repos suivis
    # ═══════════════════════════════════════════════════════════════
    
    if not tracked_repos:
        ui.print_warning("Aucun repo à analyser.")
        ui.goodbye()
        return
    
    ui.print_section("Analyse des modifications", "📊")
    
    with ui.show_spinner("Analyse en cours..."):
        repos_info = monitor.analyze_multiple(tracked_repos)
    
    # Mise à jour last_seen
    for repo_info in repos_info:
        scanner.update_last_seen(repo_info.path)
    
    ui.display_repos_status(repos_info)
    
    # ═══════════════════════════════════════════════════════════════
    # ÉTAPE 3 : Sélection des repos à push
    # ═══════════════════════════════════════════════════════════════
    
    if auto_mode:
        # Mode auto : pusher tous les repos modifiés
        repos_to_push = [r for r in repos_info if r.is_actionable]
        if repos_to_push:
            ui.print_info(f"Mode auto: {len(repos_to_push)} repo(s) à traiter")
    else:
        repos_to_push = ui.select_repos_to_push(repos_info)
    
    if not repos_to_push:
        ui.print_info("Aucun repo sélectionné pour push.")
        ui.goodbye()
        return
    
    # ═══════════════════════════════════════════════════════════════
    # ÉTAPE 4 : Sélection README
    # ═══════════════════════════════════════════════════════════════
    
    repos_for_readme = []
    if git_ops and config.get("readme", {}).get("auto_generate", True):
        if auto_mode:
            # Mode auto : générer README seulement si absent
            repos_for_readme = [
                r for r in repos_to_push 
                if not (r.path / "README.md").exists()
            ]
            if repos_for_readme:
                ui.print_info(f"Mode auto: {len(repos_for_readme)} README à générer")
        else:
            repos_for_readme = ui.select_readme_generation(repos_to_push)
    
    # ═══════════════════════════════════════════════════════════════
    # ÉTAPE 5 : Confirmation
    # ═══════════════════════════════════════════════════════════════
    
    ui.console.print()
    ui.console.print(f"[bold]Récapitulatif:[/bold]")
    ui.console.print(f"  • {len(repos_to_push)} repo(s) à commit/push")
    ui.console.print(f"  • {len(repos_for_readme)} README à générer")
    
    if not auto_mode:
        if not ui.confirm_action("Procéder aux opérations?"):
            ui.print_info("Opération annulée.")
            ui.goodbye()
            return
    else:
        ui.print_info("Mode auto: exécution sans confirmation")
    
    # ═══════════════════════════════════════════════════════════════
    # ÉTAPE 6 : Exécution
    # ═══════════════════════════════════════════════════════════════
    
    if not git_ops:
        ui.print_error("Git operations non disponibles (LLM manquant)")
        ui.goodbye()
        return
    
    ui.print_section("Exécution des opérations", "🚀")
    
    success_count = 0
    failed_count = 0
    success_repos = []
    failed_repos = []
    
    for repo_info in repos_to_push:
        ui.console.print()
        
        with ui.show_spinner(f"Traitement de {repo_info.name}..."):
            # Préparer les données
            diff_content = monitor.get_diff_for_commit(repo_info.path)
            tree_structure = monitor.get_tree_structure(repo_info.path)
            languages = monitor.detect_languages(repo_info.path)
            
            generate_readme = repo_info in repos_for_readme
            
            # Exécuter
            result = git_ops.full_commit_push(
                repo_info=repo_info,
                diff_content=diff_content,
                generate_readme=generate_readme,
                tree_structure=tree_structure,
                languages=languages
            )
        
        ui.display_operation_result(repo_info.name, result)
        
        if result.get("pushed"):
            success_count += 1
            success_repos.append({
                "name": repo_info.name,
                "commit_msg": result.get("commit_message", "N/A")
            })
        else:
            failed_count += 1
            failed_repos.append(repo_info.name)
    
    # ═══════════════════════════════════════════════════════════════
    # RÉSUMÉ
    # ═══════════════════════════════════════════════════════════════
    
    ui.display_summary(
        total=len(repos_to_push),
        success=success_count,
        failed=failed_count
    )

    # Écrire le résumé dans les logs
    log_dir = Path(config.get("logging", {}).get("file", "data/logs/workflow.log")).parent
    write_summary_log(success_repos, failed_repos, log_dir)

    # Notification Windows (mode auto uniquement)
# Notification Windows (mode auto uniquement)
    if auto_mode and (success_repos or failed_repos):
        msg = format_notification_message(success_repos, failed_repos)
        send_windows_notification("Git Workflow", msg)

    logger.info(f"Terminé: {success_count} succès, {failed_count} échecs")
    ui.goodbye()


if __name__ == "__main__":
    main()