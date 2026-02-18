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
from typing import List


def _load_conf() -> tuple[List[re.Pattern], List[re.Pattern]]:
    """Load patterns from boilerplate.conf.

    Returns (strip_patterns, skip_patterns).
    """
    ref = importlib.resources.files("extract_recipe").joinpath("boilerplate.conf")
    text = ref.read_text(encoding="utf-8")

    strip_patterns: List[re.Pattern] = []
    skip_patterns: List[re.Pattern] = []
    target = strip_patterns  # default section

    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if line == "[strip]":
            target = strip_patterns
            continue
        if line == "[skip]":
            target = skip_patterns
            continue
        target.append(re.compile(line))

    return strip_patterns, skip_patterns


_STRIP_PATTERNS, _SKIP_PATTERNS = _load_conf()


def strip_boilerplate(text: str) -> str:
    """Remove known system-generated boilerplate from within text."""
    for pattern in _STRIP_PATTERNS:
        text = pattern.sub("", text)
    return text


def should_skip(display: str) -> bool:
    """Return True if a prompt should be omitted entirely from the recipe."""
    return any(p.search(display) for p in _SKIP_PATTERNS)
