from __future__ import annotations

import re
from pathlib import Path
from typing import Optional

from extract_recipe.history import PromptEntry

PASTE_PATTERN = re.compile(r'\[Pasted text #(\d+) \+(\d+) lines?\]')


def resolve_pastes(entry: PromptEntry, paste_cache_dir: Path) -> str:
    """Return display text with paste markers replaced by actual content.

    Paste markers like [Pasted text #2 +26 lines] are replaced with the
    file content fenced by delimiter lines. If the cache file is missing,
    a note is inserted instead.
    """
    def replace_match(m: re.Match) -> str:
        paste_id = m.group(1)
        ref = entry.pasted_contents.get(paste_id)
        if ref is None or ref.content_hash is None:
            return m.group(0)  # no ref info or no hash, leave as-is

        cache_file = paste_cache_dir / f"{ref.content_hash}.txt"
        if cache_file.exists():
            content = cache_file.read_text(encoding="utf-8")
            return (
                f"\n--- Pasted text #{paste_id} ---\n"
                f"{content}\n"
                f"--- End pasted text #{paste_id} ---\n"
            )
        else:
            return f"[Pasted text #{paste_id}: cache file missing ({ref.content_hash}.txt)]"

    return PASTE_PATTERN.sub(replace_match, entry.display)
