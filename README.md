# Git Workflow

Un outil Python pour automatiser et monitorer les workflows Git avec intelligence artificielle intégrée.

## Description

Git Workflow est un système de gestion et de surveillance automatisé pour les dépôts Git. Il combine des opérations Git avancées avec des capacités d'IA (Claude) pour optimiser les flux de travail de développement, surveiller les changements et fournir des insights intelligents sur vos projets.

## Fonctionnalités

- 🔍 **Scanner automatique** de dépôts Git
- 📊 **Monitoring en temps réel** des changements
- 🤖 **Intégration IA** avec Claude pour l'analyse de code
- 📝 **Logging détaillé** des opérations
- 🎯 **Mode interactif** pour la gestion manuelle
- 📋 **Suivi des dépôts connus** avec persistence des données

## Installation

1. **Cloner le repository**
```bash
git clone <repository-url>
cd git_workflow
```

2. **Installer les dépendances**
```bash
pip install -r requirements.txt
```

3. **Configuration**
```bash
# Copier et configurer le fichier d'environnement
cp .env.example .env

# Éditer config.yaml selon vos besoins
```

4. **Configuration des variables d'environnement**
Créer un fichier `.env` avec:
```env
CLAUDE_API_KEY=your_claude_api_key_here
```

Consulter `install&setup.md` pour des instructions détaillées.

## Usage

### Lancement principal
```bash
python main.py
```

### Mode interactif
```bash
python -c "from core.interactive import run_interactive; run_interactive()"
```

### Surveillance des dépôts
```bash
python -c "from core.monitor import start_monitoring; start_monitoring()"
```

## Structure du projet

```
git_workflow/
├── core/                    # Modules principaux
│   ├── git_operations.py    # Opérations Git
│   ├── interactive.py       # Interface interactive
│   ├── monitor.py          # Surveillance des dépôts
│   └── scanner.py          # Scanner de dépôts
├── data/                   # Données et logs
│   ├── logs/              # Fichiers de log
│   └── known_repos.json  # Base de données des dépôts
├── llm/                   # Intégration IA
│   ├── base.py           # Interface de base
│   └── claude_provider.py # Provider Claude
├── models/               # Modèles de données
│   └── repo.py          # Modèle Repository
├── config.yaml          # Configuration principale
└── main.py              # Point d'entrée
```

## Configuration

Le fichier `config.yaml` permet de personnaliser:
- Paramètres de surveillance
- Configuration des providers IA
- Paramètres de logging
- Chemins des dépôts à surveiller

## Prérequis

- Python 3.8+
- Git installé sur le système
- Clé API Claude (optionnel)
- Accès en lecture/écriture aux dépôts Git

## Contributions

Les contributions sont les bienvenues ! Veuillez consulter les guidelines de contribution avant de soumettre une pull request.

## Licence

Ce projet est sous licence [MIT](LICENSE).