from __future__ import annotations

import argparse
import sys
from difflib import get_close_matches
from pathlib import Path
from typing import List

from extract_recipe.history import (
    filter_by_project,
    group_by_session,
    list_projects,
    load_history,
)
from extract_recipe.formatter import format_json, format_markdown, format_project_list


def _find_similar_projects(target: str, all_paths: List[str]) -> List[str]:
    """Find project paths similar to target for suggestions."""
    # Try difflib close matches
    matches = get_close_matches(target, all_paths, n=5, cutoff=0.4)
    if matches:
        return matches
    # Fallback: substring match on the last path component
    target_name = Path(target).name.lower()
    return [p for p in all_paths if target_name in p.lower()][:5]


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="extract-recipe",
        description="Extract prompt recipes from Claude Code history",
    )
    parser.add_argument(
        "project",
        nargs="?",
        help="Project path to extract recipe for",
    )
    parser.add_argument(
        "--claude-dir",
        type=Path,
        default=Path.home() / ".claude",
        help="Path to Claude config directory (default: ~/.claude)",
    )
    parser.add_argument(
        "--format",
        choices=["markdown", "json"],
        default="markdown",
        dest="output_format",
        help="Output format (default: markdown)",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List all projects with prompt/session counts",
    )
    parser.add_argument(
        "-o",
        metavar="FILE",
        help="Write output to file instead of stdout",
    )

    args = parser.parse_args()

    # Load history
    try:
        entries = load_history(args.claude_dir)
    except FileNotFoundError:
        print(
            f"Error: History file not found at {args.claude_dir / 'history.jsonl'}",
            file=sys.stderr,
        )
        sys.exit(1)

    paste_cache_dir = args.claude_dir / "paste-cache"

    if args.list:
        projects = list_projects(entries)
        output = format_project_list(projects)
        _write_output(output, args.o)
        return

    if args.project is None:
        parser.error("please provide a project path or use --list")

    # Filter by project
    filtered = filter_by_project(entries, args.project)
    if not filtered:
        all_paths = sorted(set(e.project for e in entries))
        similar = _find_similar_projects(args.project, all_paths)
        print(
            f"Error: No prompts found for project: {args.project}",
            file=sys.stderr,
        )
        if similar:
            print("\nDid you mean one of these?", file=sys.stderr)
            for p in similar:
                print(f"  {p}", file=sys.stderr)
        sys.exit(1)

    sessions = group_by_session(filtered)

    if args.output_format == "json":
        output = format_json(args.project, sessions, paste_cache_dir)
    else:
        output = format_markdown(args.project, sessions, paste_cache_dir)

    _write_output(output, args.o)


def _write_output(output: str, filepath: str) -> None:
    if filepath:
        Path(filepath).write_text(output, encoding="utf-8")
        print(f"Written to {filepath}", file=sys.stderr)
    else:
        print(output)


if __name__ == "__main__":
    main()
