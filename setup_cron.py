"""
Configure le cron pour lancer git_workflow automatiquement.
Lit l'heure depuis config.yaml.
"""

import subprocess
import sys
from pathlib import Path

import yaml


def load_config() -> dict:
    """Charge la configuration."""
    config_path = Path(__file__).parent / "config.yaml"
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def get_current_crontab() -> str:
    """Récupère le crontab actuel."""
    try:
        result = subprocess.run(
            ["crontab", "-l"],
            capture_output=True,
            text=True
        )
        return result.stdout if result.returncode == 0 else ""
    except Exception:
        return ""


def setup_cron():
    """Configure le cron depuis config.yaml."""
    
    config = load_config()
    schedule = config.get("schedule", {})
    
    if not schedule.get("enabled", False):
        print("❌ Cron désactivé dans config.yaml (schedule.enabled: false)")
        return
    
    time_str = schedule.get("time", "18:00")
    
    try:
        hour, minute = time_str.split(":")
        hour = int(hour)
        minute = int(minute)
    except ValueError:
        print(f"❌ Format d'heure invalide: {time_str} (attendu: HH:MM)")
        return
    
    # Chemins
    project_dir = Path(__file__).parent.resolve()
    venv_python = project_dir / ".venv" / "bin" / "python"
    main_script = project_dir / "main.py"
    log_file = project_dir / "data" / "logs" / "cron.log"
    
    # Commande cron
    cron_command = (
        f"{minute} {hour} * * * "
        f"cd {project_dir} && "
        f"{venv_python} {main_script} --auto "
        f">> {log_file} 2>&1"
    )
    
    # Marqueur pour identifier notre entrée
    marker = "# git_workflow auto-schedule"
    cron_line = f"{cron_command} {marker}"
    
    # Récupérer crontab actuel
    current_crontab = get_current_crontab()
    
    # Supprimer ancienne entrée si présente
    lines = [
        line for line in current_crontab.splitlines()
        if marker not in line
    ]
    
    # Ajouter nouvelle entrée
    lines.append(cron_line)
    new_crontab = "\n".join(lines) + "\n"
    
    # Installer nouveau crontab
    process = subprocess.Popen(
        ["crontab", "-"],
        stdin=subprocess.PIPE,
        text=True
    )
    process.communicate(input=new_crontab)
    
    if process.returncode == 0:
        print(f"✅ Cron configuré: {hour:02d}:{minute:02d} chaque jour")
        print(f"   Logs: {log_file}")
    else:
        print("❌ Erreur lors de la configuration du cron")


def remove_cron():
    """Supprime l'entrée cron."""
    marker = "# git_workflow auto-schedule"
    current_crontab = get_current_crontab()
    
    lines = [
        line for line in current_crontab.splitlines()
        if marker not in line
    ]
    
    new_crontab = "\n".join(lines) + "\n" if lines else ""
    
    process = subprocess.Popen(
        ["crontab", "-"],
        stdin=subprocess.PIPE,
        text=True
    )
    process.communicate(input=new_crontab)
    
    print("✅ Cron supprimé")


def show_status():
    """Affiche le statut du cron."""
    marker = "# git_workflow auto-schedule"
    current_crontab = get_current_crontab()
    
    for line in current_crontab.splitlines():
        if marker in line:
            print(f"✅ Cron actif: {line.split(marker)[0].strip()}")
            return
    
    print("❌ Aucun cron configuré")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == "remove":
            remove_cron()
        elif cmd == "status":
            show_status()
        else:
            print("Usage: python setup_cron.py [remove|status]")
    else:
        setup_cron()