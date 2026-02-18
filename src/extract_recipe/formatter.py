from __future__ import annotations

import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional, Tuple

from extract_recipe.boilerplate import audit_stopwords, is_plan
from extract_recipe.history import PromptEntry, Session
from extract_recipe.paste import resolve_pastes

# Context-break commands: /clear, /compact, /compress
_CONTEXT_BREAK_RE = re.compile(
    r"^/(clear|compact|compress)\s*(.*?)\s*$", re.DOTALL
)

# First markdown heading in a plan prompt
_PLAN_TITLE_RE = re.compile(r"^#\s+(.+)$", re.MULTILINE)


def _context_break(entry: PromptEntry) -> Optional[Tuple[str, str]]:
    """If entry is a context-break command, return (command, comment).

    Returns None for regular prompts.
    """
    m = _CONTEXT_BREAK_RE.match(entry.display)
    if m:
        return m.group(1), m.group(2)
    return None


def _plan_title(entry: PromptEntry) -> Optional[str]:
    """If entry is a plan-mode prompt, return the plan title.

    Returns None for regular prompts.
    """
    if not is_plan(entry.display):
        return None
    m = _PLAN_TITLE_RE.search(entry.display)
    if m:
        # Strip common prefixes like "Plan: " from the heading
        title = m.group(1)
        if title.lower().startswith("plan:"):
            title = title[5:].strip()
        return title
    return "untitled plan"


def _format_timestamp(ts: int, raw: bool = False) -> str:
    """Format a millisecond timestamp as a human-readable date string."""
    dt = datetime.fromtimestamp(ts / 1000, tz=timezone.utc)
    s = dt.strftime("%Y-%m-%d %H:%M:%S UTC")
    if raw:
        s += f" ({ts})"
    return s


def _session_label(session: Session, index: int) -> str:
    if session.session_id is None:
        return "Session (no ID)"
    return f"Session {session.session_id[:8]}"


def format_markdown(
    project: str,
    sessions: List[Session],
    paste_cache_dir: Path,
    raw: bool = False,
    redact: bool = False,
    title: Optional[str] = None,
) -> str:
    """Format sessions as a markdown document."""
    lines: List[str] = []
    prefix = "Recipe (redacted)" if redact else "Recipe"
    lines.append(f"# {title}\n" if title else f"# {prefix}: {project}\n")

    display_session = 0

    for si, session in enumerate(sessions):
        display_session += 1
        if redact:
            lines.append(f"## Session {display_session}\n")
        else:
            lines.append(f"## {_session_label(session, si)}\n")

        prompt_num = 0
        for entry in session.prompts:
            cb = _context_break(entry)
            if cb is not None:
                command, comment = cb
                if redact:
                    display_session += 1
                    prompt_num = 0
                    if comment:
                        lines.append(f"## Session {display_session} (context {command}ed: {comment})\n")
                    else:
                        lines.append(f"## Session {display_session} (context {command}ed)\n")
                else:
                    if comment:
                        lines.append(f"*\u2014 Context {command}ed: {comment} \u2014*\n")
                    else:
                        lines.append(f"*\u2014 Context {command}ed \u2014*\n")
                continue

            prompt_num += 1
            title = _plan_title(entry)
            if title is not None and not raw:
                if redact:
                    lines.append(f"### Prompt {display_session}.{prompt_num}\n")
                else:
                    date_str = _format_timestamp(entry.timestamp, raw=raw)
                    lines.append(f"### {date_str}\n")
                lines.append(f"*\u2014 Plan: {title} \u2014*\n")
                continue

            if redact:
                lines.append(f"### Prompt {display_session}.{prompt_num}\n")
            else:
                date_str = _format_timestamp(entry.timestamp, raw=raw)
                lines.append(f"### {date_str}\n")
            resolved = resolve_pastes(entry, paste_cache_dir)
            lines.append(resolved)
            lines.append("")

    return "\n".join(lines)


def _project_json(
    project: str,
    sessions: List[Session],
    paste_cache_dir: Path,
    raw: bool = False,
    redact: bool = False,
    title: Optional[str] = None,
) -> dict:
    """Build the JSON-serialisable dict for one project."""
    data = {
        "project": title or project,
        "sessions": [],
    }
    display_session = 0

    for si, session in enumerate(sessions):
        display_session += 1
        session_data: dict = {
            "session_id": display_session if redact else session.session_id,
            "prompts": [],
        }
        prompt_num = 0
        for entry in session.prompts:
            cb = _context_break(entry)
            if cb is not None:
                command, comment = cb
                if redact:
                    data["sessions"].append(session_data)
                    display_session += 1
                    prompt_num = 0
                    session_data = {
                        "session_id": display_session,
                        "context_break": command,
                        "prompts": [],
                    }
                    if comment:
                        session_data["context_break_comment"] = comment
                else:
                    item: dict = {
                        "type": "context_break",
                        "command": command,
                        "date": _format_timestamp(entry.timestamp),
                    }
                    if raw:
                        item["timestamp_ms"] = entry.timestamp
                    if comment:
                        item["comment"] = comment
                    session_data["prompts"].append(item)
                continue

            prompt_num += 1
            title = _plan_title(entry)
            if title is not None and not raw:
                item = {
                    "type": "plan",
                    "title": title,
                }
                if not redact:
                    item["date"] = _format_timestamp(entry.timestamp)
                session_data["prompts"].append(item)
                continue

            resolved = resolve_pastes(entry, paste_cache_dir)
            item = {
                "type": "prompt",
                "display_raw": entry.display,
                "display_resolved": resolved,
            }
            if not redact:
                item["date"] = _format_timestamp(entry.timestamp)
            if raw:
                item["timestamp_ms"] = entry.timestamp
            session_data["prompts"].append(item)
        data["sessions"].append(session_data)
    return data


def format_json(
    project: str,
    sessions: List[Session],
    paste_cache_dir: Path,
    raw: bool = False,
    redact: bool = False,
    title: Optional[str] = None,
) -> str:
    """Format sessions as structured JSON."""
    return json.dumps(
        _project_json(project, sessions, paste_cache_dir, raw=raw, redact=redact, title=title),
        indent=2, ensure_ascii=False,
    )


def format_all_json(
    projects: List[Tuple[str, List[Session]]],
    paste_cache_dir: Path,
    raw: bool = False,
    redact: bool = False,
) -> str:
    """Format all projects as a JSON array."""
    data = [
        _project_json(project, sessions, paste_cache_dir, raw=raw, redact=redact)
        for project, sessions in projects
    ]
    return json.dumps(data, indent=2, ensure_ascii=False)


# Capitalized word (starts uppercase, at least 3 chars, not ALL CAPS)
_CAP_WORD_RE = re.compile(r"\b([A-Z][a-z]{2,})\b")


def format_audit(entries: List["PromptEntry"], raw: bool = False) -> str:
    """Show frequently used capitalized words in prompt text.

    By default, words listed in [audit-stopwords] are filtered out.
    With raw=True, all capitalized words are shown (useful for seeing
    which common words tend to be capitalised in your prompts).
    """
    stopwords = [] if raw else audit_stopwords()
    counts: Counter = Counter()
    for entry in entries:
        for m in _CAP_WORD_RE.finditer(entry.display):
            word = m.group(1)
            if not any(p.fullmatch(word) for p in stopwords):
                counts[word] += 1

    if not counts:
        return "No frequently used capitalized words found."

    lines: List[str] = []
    if raw:
        lines.append("All frequently used capitalized words in prompts:\n")
    else:
        lines.append("Frequently used capitalized words in prompts")
        lines.append("(filtered by [audit-stopwords]; use --raw to show all):\n")
    lines.append(f"{'Count':>5}  Word")
    lines.append(f"{'-----':>5}  ----")
    for word, count in counts.most_common(50):
        if count < 2:
            break
        lines.append(f"{count:>5}  {word}")

    return "\n".join(lines)


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
