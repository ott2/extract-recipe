"""Strip system-generated boilerplate from prompt text.

AI coding tools inject lines into prompt history that aren't part of the
user's actual recipe.  This module removes them by default; pass --raw
to preserve the verbatim recorded text.

Patterns are loaded from boilerplate.conf (shipped with the package).
To add support for other tools, edit that file or send a PR.
"""

from __future__ import annotations

import importlib.resources
import re
from typing import Dict, List


def _load_conf() -> Dict[str, List[re.Pattern]]:
    """Load patterns from boilerplate.conf, keyed by section name."""
    ref = importlib.resources.files("extract_recipe").joinpath("boilerplate.conf")
    text = ref.read_text(encoding="utf-8")

    sections: Dict[str, List[re.Pattern]] = {}
    current = "strip"  # default section

    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("[") and line.endswith("]"):
            current = line[1:-1]
            continue
        sections.setdefault(current, []).append(re.compile(line))

    return sections


_SECTIONS = _load_conf()


def strip_boilerplate(text: str) -> str:
    """Remove known system-generated boilerplate from within text."""
    for pattern in _SECTIONS.get("strip", []):
        text = pattern.sub("", text)
    return text


def should_skip(display: str) -> bool:
    """Return True if a prompt should be omitted entirely from the recipe."""
    return any(p.search(display) for p in _SECTIONS.get("skip", []))


def is_plan(display: str) -> bool:
    """Return True if a prompt is a plan-mode prompt (to be collapsed)."""
    return any(p.search(display) for p in _SECTIONS.get("plan", []))
