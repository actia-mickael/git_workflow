# 1. Créer le dossier
mkdir -p ~/git-workflow
cd ~/git-workflow

# 2. Créer l'environnement virtuel
python -m venv .venv
source .venv/bin/activate  # Linux/WSL

# 3. Installer les dépendances
pip install -r requirements.txt

# 4. Créer le fichier .env
echo "ANTHROPIC_API_KEY=sk-ant-xxxxx" > .env

# 5. Créer les dossiers
mkdir -p core llm models data/logs
touch core/__init__.py llm/__init__.py models/__init__.py

# 6. Lancer
python main.py




# CRON

# Éditer crontab
crontab -e

# Ajouter
0 18 * * * cd ~/git-workflow && /home/mmo/git-workflow/.venv/bin/python main.py >> data/logs/cron.log 2>&1