 # Git Workflow

A Python-based tool to automate and monitor Git workflows.

## Description

Git Workflow is an automated system for managing and monitoring Git repositories. It combines advanced Git operations with AI capabilities (Claude or Mistral 7B, which needs to be installed locally under Ollama) to optimize development workflows, track changes, and provide intelligent insights on your projects.

## Features

- 🔍 **Automatic Scanner** for Git repositories
- 📊 **Real-time Monitoring** of changes
- 🤖 **AI Integration** with Claude for code analysis
- 📝 **Detailed Logging** of operations
- 🎯 **Interactive Mode** for manual management
- 📋 **Tracking of known repositories** with data persistence

## Installation

1. **Clone the repository**
```bash
git clone <repository-url>
cd git_workflow
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Configuration**

    - **Environment Variables**
        - Set up environment variables according to your AI provider (Claude or Ollama).
    - **Configuration file**
        - Modify the `config.yaml` file to set up your Git workflow preferences.

## Usage

- **Run the main script**
```bash
python main.py
```

## Structure

The project has the following structure:

```bash
git_workflow/
├── core/
│   ├── git_operations.py
│   ├── interactive.py
│   ├── monitor.py
│   └── scanner.py
├── data/
│   ├── logs/
│   │   └── workflow.log
│   └── known_repos.json
├── llm/
│   ├── base.py
│   ├── claude_provider.py
│   └── ollama_provider.py
├── models/
│   └── repo.py
├── .env
├── .gitignore
├── README.md
├── config.yaml
├── install&setup.md
├── main.py
├── requirements.txt
└── setup_cron.py
```

## Main Files

- `.env`
- `.gitignore`
- `config.yaml`
- `install&setup.md`
- `main.py`
- `README.md`
- `requirements.txt`
- `setup_cron.py`
- `core/git_operations.py`
- `core/interactive.py`
- `core/monitor.py`
- `core/scanner.py`
- `data/known_repos.json`
- `llm/base.py`
- `llm/claude_provider.py`
- `llm/ollama_provider.py`
- `models/repo.py`
- `data/logs/workflow.log`

For more information about installation, usage, and configuration, please refer to the `install&setup.md` file.