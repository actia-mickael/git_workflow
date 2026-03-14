 # Git Workflow

A Python-based tool for automating and monitoring Git workflows.

## Description

Git Workflow is an automated system for managing and monitoring Git repositories. It combines advanced Git operations with AI capabilities (Claude or Mistral 7B, which needs to be installed locally under Ollama) to optimize development workflows, track changes, and provide intelligent insights on your projects.

## Structure

```
git_workflow
├── core
│   ├── git_operations.py
│   ├── interactive.py
│   ├── monitor.py
│   └── scanner.py
├── data
│   ├── logs
│   │   └── workflow.log
│   └── known_repos.json
├── llm
│   ├── base.py
│   ├── claude_provider.py
│   └── ollama_provider.py
├── models
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

## Principal Files

`.env`

`.gitignore`

`config.yaml`

`install&setup.md`

`main.py`

`README.md`

`requirements.txt`

`setup_cron.py`

`core/git_operations.py`

`core/interactive.py`

`core/monitor.py`

`core/scanner.py`

`data/known_repos.json`

`llm/base.py`

`llm/claude_provider.py`

`llm/ollama_provider.py`

`models/repo.py`

`data/logs/workflow.log`

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
        - Set up environment variables according to your AI provider.

Refer to the `install&setup.md` file for more detailed instructions.