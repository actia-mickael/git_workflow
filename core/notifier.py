"""
Notifications Windows depuis WSL.
"""

import subprocess
import logging
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


def send_windows_notification(title: str, message: str) -> bool:
    """Envoie une notification toast Windows depuis WSL."""
    try:
        # Escape les guillemets pour PowerShell
        message = message.replace('"', '`"').replace("'", "`'")
        title = title.replace('"', '`"').replace("'", "`'")
        
        ps_script = f'''
        [Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
        [Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom.XmlDocument, ContentType = WindowsRuntime] | Out-Null
        
        $template = @"
        <toast>
            <visual>
                <binding template="ToastText02">
                    <text id="1">{title}</text>
                    <text id="2">{message}</text>
                </binding>
            </visual>
        </toast>
"@
        
        $xml = New-Object Windows.Data.Xml.Dom.XmlDocument
        $xml.LoadXml($template)
        $toast = [Windows.UI.Notifications.ToastNotification]::new($xml)
        [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier("Git Workflow").Show($toast)
        '''
        
        subprocess.run(
            ["powershell.exe", "-Command", ps_script],
            capture_output=True,
            timeout=10
        )
        logger.info("Notification Windows envoyée")
        return True
        
    except Exception as e:
        logger.warning(f"Échec notification Windows: {e}")
        return False


def write_summary_log(success_repos: list, failed_repos: list, log_dir: Path) -> Path:
    """Écrit un résumé dans un fichier log dédié."""
    log_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    summary_file = log_dir / f"summary_{timestamp}.log"
    
    with open(summary_file, "w", encoding="utf-8") as f:
        f.write(f"═══ Git Workflow - Résumé du {datetime.now().strftime('%d/%m/%Y %H:%M')} ═══\n\n")
        
        f.write(f"✅ Réussis: {len(success_repos)}\n")
        for repo in success_repos:
            f.write(f"   • {repo}\n")
        
        if failed_repos:
            f.write(f"\n❌ Échecs: {len(failed_repos)}\n")
            for repo in failed_repos:
                f.write(f"   • {repo}\n")
        
        f.write(f"\n{'─' * 40}\n")
    
    # Mettre à jour le fichier "latest"
    latest_file = log_dir / "latest_summary.txt"
    with open(latest_file, "w", encoding="utf-8") as f:
        f.write(f"Dernière exécution: {datetime.now().strftime('%d/%m/%Y %H:%M')}\n")
        f.write(f"Repos pushés: {len(success_repos)}\n")
        if success_repos:
            for repo in success_repos:
                f.write(f"  ✓ {repo}\n")
        else:
            f.write("  (aucun)\n")
        if failed_repos:
            f.write(f"Échecs: {len(failed_repos)}\n")
            for repo in failed_repos:
                f.write(f"  ✗ {repo}\n")
    
    logger.info(f"Résumé écrit: {summary_file}")
    return summary_file
