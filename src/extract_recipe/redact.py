"""Redact sensitive content from recipe output."""

from __future__ import annotations

import re


# Token patterns: (regex, replacement)
_TOKEN_PATTERNS = [
    (re.compile(r"AKIA[0-9A-Z]{16}"), "[REDACTED]"),           # AWS access key
    (re.compile(r"ghp_[A-Za-z0-9]{36,}"), "[REDACTED]"),       # GitHub PAT
    (re.compile(r"ghs_[A-Za-z0-9]{36,}"), "[REDACTED]"),       # GitHub app token
    (re.compile(r"gho_[A-Za-z0-9]{36,}"), "[REDACTED]"),       # GitHub OAuth token
    (re.compile(r"github_pat_[A-Za-z0-9_]{59,}"), "[REDACTED]"),  # GitHub fine-grained PAT
    (re.compile(r"sk-proj-[A-Za-z0-9_-]{20,}"), "[REDACTED]"), # OpenAI project key
    (re.compile(r"sk-[A-Za-z0-9]{20,}"), "[REDACTED]"),        # OpenAI key
]

# Matches /Users/<name>/ or /home/<name>/ paths
_HOME_DIR_RE = re.compile(r"/(Users|home)/\w+")

# Session IDs in their known output contexts (headings / JSON keys)
_MD_SESSION_RE = re.compile(r"(## Session )([0-9a-f]{8})")
_JSON_SESSION_RE = re.compile(r'("session_id": ")([0-9a-f]{8}(?:-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})?)"')

# Bare UUIDs anywhere in text (e.g. transcript paths inside prompts)
_UUID_RE = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}")


def _redact_session_ids(text: str) -> str:
    """Replace session IDs with sequential numbers (Session 1, Session 2, ...).

    Also replaces bare UUIDs in prompt text with [SESSION].
    """
    id_map: dict[str, int] = {}

    def _next_id(hex8: str) -> str:
        if hex8 not in id_map:
            id_map[hex8] = len(id_map) + 1
        return str(id_map[hex8])

    def _replace_md(m: re.Match) -> str:
        return m.group(1) + _next_id(m.group(2))

    def _replace_json(m: re.Match) -> str:
        key = m.group(2)[:8]
        return m.group(1) + _next_id(key) + '"'

    # First pass: replace session IDs in structured positions (headings/JSON keys)
    text = _MD_SESSION_RE.sub(_replace_md, text)
    text = _JSON_SESSION_RE.sub(_replace_json, text)

    # Second pass: replace remaining bare UUIDs in prompt text
    text = _UUID_RE.sub("[SESSION]", text)
    return text


def redact(text: str) -> str:
    """Redact sensitive content from text.

    - Replaces home directory paths (/Users/name/..., /home/name/...) with ~
    - Replaces session IDs with sequential numbers
    - Replaces known secret/token patterns with [REDACTED]
    """
    # Find all unique home-dir prefixes in the text, replace longest first
    home_prefixes = sorted(
        {m.group(0) for m in _HOME_DIR_RE.finditer(text)},
        key=len,
        reverse=True,
    )
    for prefix in home_prefixes:
        text = text.replace(prefix, "~")

    text = _redact_session_ids(text)

    for pattern, replacement in _TOKEN_PATTERNS:
        text = pattern.sub(replacement, text)

    return text
