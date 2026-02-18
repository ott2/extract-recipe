# extract-recipe

Extract the sequence of prompts ("recipes") used to build artifacts with Claude Code.

Reads prompt history from `~/.claude/history.jsonl` and resolves pasted content references from `~/.claude/paste-cache/`.

## Installation

Requires Python 3.9+. No external dependencies.

```bash
cd /Users/as456/projects/claudecode/recipe-extraction

# Create and activate a virtual environment
/usr/bin/python3 -m venv .venv
source .venv/bin/activate

# Upgrade pip (required — the system pip 21.x cannot do editable installs
# from pyproject.toml-only projects)
pip install --upgrade pip

# Install in editable mode
pip install -e .
```

## Usage

```bash
# List all projects with prompt and session counts
extract-recipe --list

# Extract recipe as markdown (to stdout)
extract-recipe /path/to/project

# Extract as JSON to a file
extract-recipe --format json -o recipe.json /path/to/project

# Use a custom Claude config directory
extract-recipe --claude-dir /other/path --list
```

## CLI Reference

```
extract-recipe [--claude-dir DIR] [--format {markdown,json}] [--list] [-o FILE] [project]
```

| Flag | Description |
|------|-------------|
| `project` | Project path to extract recipe for |
| `--list` | List all projects with prompt/session counts |
| `--format` | Output format: `markdown` (default) or `json` |
| `-o FILE` | Write output to file instead of stdout |
| `--claude-dir` | Claude config directory (default: `~/.claude`) |
