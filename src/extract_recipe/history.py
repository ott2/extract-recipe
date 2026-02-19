from __future__ import annotations

import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple


@dataclass
class PasteRef:
    id: Optional[int]
    type: Optional[str]
    content_hash: Optional[str]


@dataclass
class PromptEntry:
    display: str
    pasted_contents: Dict[str, PasteRef]
    timestamp: int
    project: str
    session_id: Optional[str]


@dataclass
class Session:
    session_id: Optional[str]
    prompts: List[PromptEntry] = field(default_factory=list)


def load_history(claude_dir: Path) -> List[PromptEntry]:
    """Parse history.jsonl and return entries sorted by timestamp."""
    history_file = claude_dir / "history.jsonl"
    entries: List[PromptEntry] = []
    with open(history_file, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                pasted = {}
                for key, val in (obj.get("pastedContents") or {}).items():
                    pasted[key] = PasteRef(
                        id=val.get("id"),
                        type=val.get("type"),
                        content_hash=val.get("contentHash"),
                    )
                entries.append(PromptEntry(
                    display=obj["display"],
                    pasted_contents=pasted,
                    timestamp=obj["timestamp"],
                    project=obj["project"],
                    session_id=obj.get("sessionId"),
                ))
            except (json.JSONDecodeError, KeyError, AttributeError, TypeError) as e:
                print(f"Warning: skipping malformed history line: {e}", file=sys.stderr)
    entries.sort(key=lambda e: e.timestamp)
    return entries


def filter_by_project(entries: List[PromptEntry], project: str) -> List[PromptEntry]:
    """Filter entries by exact project path match."""
    return [e for e in entries if e.project == project]


def group_by_session(entries: List[PromptEntry]) -> List[Session]:
    """Group entries into sessions, sorted by start time.

    Entries without a sessionId are collected into a single Session with
    session_id=None, placed first.
    """
    sessions: Dict[Optional[str], Session] = {}
    for entry in entries:
        sid = entry.session_id
        if sid not in sessions:
            sessions[sid] = Session(session_id=sid)
        sessions[sid].prompts.append(entry)

    result: List[Session] = []
    if None in sessions:
        result.append(sessions.pop(None))
    remaining = sorted(sessions.values(), key=lambda s: s.prompts[0].timestamp)
    result.extend(remaining)
    return result


def list_projects(entries: List[PromptEntry]) -> List[Tuple[str, int, int]]:
    """Return (path, prompt_count, session_count) tuples sorted by path."""
    projects: Dict[str, Dict[str, object]] = {}
    for entry in entries:
        p = entry.project
        if p not in projects:
            projects[p] = {"count": 0, "sessions": set()}
        projects[p]["count"] += 1
        if entry.session_id is not None:
            projects[p]["sessions"].add(entry.session_id)

    result = []
    for path in sorted(projects):
        info = projects[path]
        session_count = len(info["sessions"])
        # Count None-session group as 1 session if there are entries without sessionId
        has_none = any(
            e.session_id is None and e.project == path for e in entries
        )
        if has_none:
            session_count += 1
        result.append((path, info["count"], session_count))
    return result
