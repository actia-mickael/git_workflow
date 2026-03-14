 # Git Workflow

A comprehensive and intelligent Python-based tool for automating and monitoring Git workflows.

## Description

Git Workflow is an automated system for managing and monitoring Git repositories. It combines advanced Git operations with AI capabilities (Claude or Mistral 7B, which needs to be installed locally under Ollama) to optimize development workflows, track changes, and provide intelligent insights on your projects.

This tool offers the following features:

- Advanced Git operations
- AI capabilities for intelligent insights
- Repository monitoring
- Logging and notifications

## Installation

1. Clone the repository:

```bash
git clone https://github.com/your-username/git_workflow.git
```

2. Navigate to the project directory:

```bash
cd git_workflow
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Configure the environment:

```bash
cp .env.example .env
# Edit .env file as needed
```

5. Set up the project:

```bash
./setup.sh
```

## Usage

To start the Git Workflow, run the main script:

```bash
python main.py
```

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
│   │   ├── cron.log
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

`.env`: Project environment variables

`.gitignore`: File to ignore specific files for Git

`config.yaml`: Configuration file for the project

`install&setup.md`: Guide for installation and setup of the project

`main.py`: Main script for running the Git Workflow

`README.md`: This documentation

`requirements.txt`: List of required Python packages

`setup_cron.py`: Script for setting up a cron job for the Git Workflow

`core/git_operations.py`: Script for advanced Git operations

`core/interactive.py`: Interactive Git operations

`core/monitor.py`: Repository monitoring functions

`core/notifier.py`: Notification functions

`core/scanner.py`: AI-powered repository scanning functions

`data/known_repos.json`: List of known repositories

`data/logs/cron.log`: Cron job logs

`data/logs/workflow.log`: Workflow logs

`llm/base.py`: Base class for AI providers

`llm/claude_provider.py`: Claude AI provider

`llm/ollama_provider.py`: Ollama AI provider

`models/repo.py`: Repository model class

---

**Note:** This tool utilizes the following languages: JSON, Markdown, Python, and YAML.

**Additional Note:** The AI capabilities (Claude or Mistral 7B) need to be installed locally under Ollama.