from __future__ import annotations

import argparse
import signal
import sys
from difflib import get_close_matches
from pathlib import Path
from typing import List, Optional

from extract_recipe.history import (
    filter_by_project,
    group_by_session,
    list_projects,
    load_history,
)
from extract_recipe.formatter import (
    format_all_json,
    format_json,
    format_markdown,
    format_project_list,
)


def _match_projects(
    target: str, all_paths: List[str], exact: bool
) -> List[str]:
    """Find projects matching the target specifier.

    With exact=True, matches projects whose path ends with /target
    (i.e. the final component(s) match exactly).
    With exact=False, matches by substring (case-insensitive).
    """
    # Full path match always wins
    if target in all_paths:
        return [target]
    if exact:
        suffix = "/" + target
        return [p for p in all_paths if p.endswith(suffix) or p == target]
    else:
        return [p for p in all_paths if target.lower() in p.lower()]


def _fuzzy_suggest(target: str, all_paths: List[str]) -> List[str]:
    """Suggest projects using fuzzy matching against path suffixes.

    Compares the target against the last N path components of each project,
    where N is the number of components in the target. This handles typos
    and transpositions in project names.
    """
    n_parts = target.count("/") + 1
    suffix_to_paths: dict[str, List[str]] = {}
    for p in all_paths:
        parts = p.split("/")
        suffix = "/".join(parts[-n_parts:])
        suffix_to_paths.setdefault(suffix, []).append(p)
    close = get_close_matches(target, suffix_to_paths.keys(), n=5, cutoff=0.5)
    result: List[str] = []
    for s in close:
        result.extend(suffix_to_paths[s])
    return result



def main() -> None:
    # Exit quietly on broken pipe (e.g. piping to head)
    signal.signal(signal.SIGPIPE, signal.SIG_DFL)

    parser = argparse.ArgumentParser(
        prog="extract-recipe",
        description="Extract prompt recipes from Claude Code history",
        epilog=(
            "examples:\n"
            "  extract-recipe --list                  list all projects\n"
            "  extract-recipe myproject               match by substring\n"
            "  extract-recipe -e comparison           exact final component (not comparison2)\n"
            "  extract-recipe -a                      extract all projects\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "project",
        nargs="?",
        help="Project path, substring, or path suffix to match. "
        "Use / to disambiguate: 'foo/bar' matches only projects "
        "whose path ends with that suffix",
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
        "-a", "--all",
        action="store_true",
        dest="all_projects",
        help="Extract recipes for all projects",
    )
    parser.add_argument(
        "-e", "--exact",
        action="store_true",
        help="Match by exact final path component(s) instead of substring "
        "(e.g. -e comparison matches .../comparison but not .../comparison2)",
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

    if args.all_projects:
        all_paths = sorted(set(e.project for e in entries))
        if args.output_format == "json":
            projects_sessions = [
                (p, group_by_session(filter_by_project(entries, p)))
                for p in all_paths
            ]
            output = format_all_json(projects_sessions, paste_cache_dir)
        else:
            parts = []
            for p in all_paths:
                sessions = group_by_session(filter_by_project(entries, p))
                parts.append(format_markdown(p, sessions, paste_cache_dir))
            output = "\n".join(parts)
        _write_output(output, args.o)
        return

    if args.project is None:
        parser.error("please provide a project path, -a, or --list")

    # Resolve project specifier
    all_paths = sorted(set(e.project for e in entries))
    matches = _match_projects(args.project, all_paths, args.exact)

    if len(matches) == 1:
        project = matches[0]
    elif len(matches) > 1:
        print(
            f"Multiple projects match '{args.project}', "
            "please specify the path or an identifying substring:",
            file=sys.stderr,
        )
        for p in matches:
            print(f"  {p}", file=sys.stderr)
        sys.exit(1)
    else:
        suggestions = _fuzzy_suggest(args.project, all_paths)
        if suggestions:
            print(
                f"No projects match '{args.project}'. "
                "Similar projects:",
                file=sys.stderr,
            )
            for p in suggestions:
                print(f"  {p}", file=sys.stderr)
        else:
            print(
                f"No projects match '{args.project}'. "
                "Run extract-recipe --list to see available projects.",
                file=sys.stderr,
            )
        sys.exit(1)

    filtered = filter_by_project(entries, project)
    sessions = group_by_session(filtered)

    if args.output_format == "json":
        output = format_json(project, sessions, paste_cache_dir)
    else:
        output = format_markdown(project, sessions, paste_cache_dir)

    _write_output(output, args.o)


def _write_output(output: str, filepath: str) -> None:
    if filepath:
        Path(filepath).write_text(output, encoding="utf-8")
        print(f"Written to {filepath}", file=sys.stderr)
    else:
        print(output)


if __name__ == "__main__":
    main()
