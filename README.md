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

# Extract recipe by substring (matches if unique)
extract-recipe ndthtf

# Use path components to disambiguate similar names
extract-recipe rewriting/comparison    # substring: won't match comparison2
extract-recipe -e comparison           # exact final component: won't match comparison2

# Full path always works
extract-recipe /path/to/project

# Extract all projects at once
extract-recipe -a

# Redact home paths and API keys before sharing
extract-recipe -r myproject

# Keep system-generated boilerplate (stripped by default)
extract-recipe --raw myproject

# Extract as JSON to a file
extract-recipe --format json -o recipe.json ndthtf

# Browse with rendered markdown using glow
extract-recipe ndthtf | glow -p

# Use a custom Claude config directory
extract-recipe --claude-dir /other/path --list
```

## Project Matching

The `project` argument is matched flexibly:

1. **Full path** — exact match, always works
2. **Substring** — `ndthtf` matches `.../projects/ndthtf`; if multiple projects contain the substring, all matches are listed so you can refine
3. **Path suffix** — use `/` to narrow: `rewriting/comparison` matches `.../rewriting/comparison` but not `.../rewriting/comparison2`
4. **Exact component** (`-e`) — matches only projects whose final path component(s) are exactly the argument: `-e comparison` matches `.../comparison` but not `.../comparison2`
5. **Fuzzy suggestions** — if nothing matches, similar project names are suggested (handles typos)

## Boilerplate Stripping

By default, system-generated lines injected by AI coding tools are stripped from prompts. These are not user-authored content — for example, Claude Code appends transcript file references to plan-mode prompts in `history.jsonl`.

Detection uses structural patterns (e.g. paths matching `.claude/projects/.../*.jsonl`) rather than exact English strings, so it survives rewording across tool versions. Patterns are defined in `src/extract_recipe/boilerplate.py` and can be extended for other tools (Codex, Antigravity, etc.).

Use `--raw` to preserve the verbatim recorded text. `--raw` and `--redact` are independent: `--raw --redact` keeps boilerplate but redacts sensitive content within it.

Developed against Claude Code 2.1.45.

## CLI Reference

```
extract-recipe [--claude-dir DIR] [--format {markdown,json}] [--list] [-a] [-e] [-r] [--raw] [-o FILE] [project]
```

| Flag | Description |
|------|-------------|
| `project` | Project path, substring, or path suffix to match |
| `--list` | List all projects with prompt/session counts |
| `-a, --all` | Extract recipes for all projects |
| `-e, --exact` | Match by exact final path component(s) instead of substring |
| `-r, --redact` | Redact sensitive content (home paths, API keys) from output |
| `--raw` | Preserve raw prompt text (don't strip system-generated boilerplate) |
| `--format` | Output format: `markdown` (default) or `json` |
| `-o FILE` | Write output to file instead of stdout |
| `--claude-dir` | Claude config directory (default: `~/.claude`) |
