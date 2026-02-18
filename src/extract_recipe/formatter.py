from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Tuple

from extract_recipe.history import Session
from extract_recipe.paste import resolve_pastes


def _format_timestamp(ts: int) -> str:
    """Format a millisecond timestamp as a human-readable date string."""
    dt = datetime.fromtimestamp(ts / 1000, tz=timezone.utc)
    return dt.strftime("%Y-%m-%d %H:%M:%S UTC")


def _session_label(session: Session, index: int) -> str:
    if session.session_id is None:
        return "Session (no ID)"
    return f"Session {session.session_id[:8]}"


def format_markdown(
    project: str,
    sessions: List[Session],
    paste_cache_dir: Path,
) -> str:
    """Format sessions as a markdown document."""
    lines: List[str] = []
    lines.append(f"# Recipe: {project}\n")

    prompt_num = 0
    for i, session in enumerate(sessions):
        lines.append(f"## {_session_label(session, i)}\n")
        for entry in session.prompts:
            prompt_num += 1
            date_str = _format_timestamp(entry.timestamp)
            lines.append(f"### Prompt {prompt_num} \u2014 {date_str}\n")
            resolved = resolve_pastes(entry, paste_cache_dir)
            lines.append(resolved)
            lines.append("")
            lines.append("---\n")

    return "\n".join(lines)


def format_json(
    project: str,
    sessions: List[Session],
    paste_cache_dir: Path,
) -> str:
    """Format sessions as structured JSON."""
    data = {
        "project": project,
        "sessions": [],
    }

    prompt_num = 0
    for session in sessions:
        session_data = {
            "session_id": session.session_id,
            "prompts": [],
        }
        for entry in session.prompts:
            prompt_num += 1
            resolved = resolve_pastes(entry, paste_cache_dir)
            session_data["prompts"].append({
                "number": prompt_num,
                "timestamp": entry.timestamp,
                "date": _format_timestamp(entry.timestamp),
                "display_raw": entry.display,
                "display_resolved": resolved,
            })
        data["sessions"].append(session_data)

    return json.dumps(data, indent=2, ensure_ascii=False)


def format_project_list(projects: List[Tuple[str, int, int]]) -> str:
    """Format project listing as a table."""
    if not projects:
        return "No projects found."

    # Calculate column widths
    header = ("Project", "Prompts", "Sessions")
    col_widths = [len(h) for h in header]
    rows = []
    for path, count, sessions in projects:
        row = (path, str(count), str(sessions))
        rows.append(row)
        for j, val in enumerate(row):
            col_widths[j] = max(col_widths[j], len(val))

    lines: List[str] = []
    fmt = "  ".join(f"{{:<{w}}}" for w in col_widths)
    lines.append(fmt.format(*header))
    lines.append(fmt.format(*("-" * w for w in col_widths)))
    for row in rows:
        lines.append(fmt.format(*row))

    return "\n".join(lines)
