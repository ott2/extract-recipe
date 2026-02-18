"""Redact sensitive content from recipe output.

Simple pattern→replacement pairs are loaded from boilerplate.conf [redact].
UUIDs embedded in prompt text are replaced with [UUID].
Session IDs and timestamps are handled at format time (formatter.py).
"""

from __future__ import annotations

import re

from extract_recipe.boilerplate import redact_patterns

# Bare UUIDs anywhere in text (e.g. transcript paths inside prompts)
_UUID_RE = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}")


def redact(text: str) -> str:
    """Redact sensitive content from text.

    - Applies pattern→replacement pairs from [redact] config section
    - Replaces bare UUIDs with [UUID]
    """
    for pattern, replacement in redact_patterns():
        text = pattern.sub(replacement, text)

    text = _UUID_RE.sub("[UUID]", text)

    return text
