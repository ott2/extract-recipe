"""Load pattern configuration for extract-recipe.

Lookup order:
  1. User config at ~/.config/extract-recipe/patterns.conf (if it exists)
  2. --config flag overrides the user config path
  3. Package default (boilerplate.conf shipped with the package) as fallback

If a user config exists it replaces the package defaults entirely.
Use --init-config to copy the package defaults to the user config location.
"""

from __future__ import annotations

import importlib.resources
import re
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Sections where each line is a plain regex
_PLAIN_SECTIONS = {"strip", "skip", "plan"}

# Sections where each line is "pattern = replacement"
_PAIR_SECTIONS = {"redact"}

_DEFAULT_USER_CONFIG = Path.home() / ".config" / "extract-recipe" / "patterns.conf"


def _parse_conf(text: str, sections: Dict, pairs: Dict) -> None:
    """Parse a conf file, appending to sections and pairs dicts."""
    current = "strip"  # default section

    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("[") and line.endswith("]"):
            current = line[1:-1]
            continue

        if current in _PAIR_SECTIONS:
            # Split on last " = " to allow = in patterns
            if " = " in line:
                pattern_str, replacement = line.rsplit(" = ", 1)
                pairs.setdefault(current, []).append(
                    (re.compile(pattern_str), replacement)
                )
            continue

        sections.setdefault(current, []).append(re.compile(line))


def _default_conf() -> importlib.resources.abc.Traversable:
    """Return a reference to the package-shipped boilerplate.conf."""
    return importlib.resources.files("extract_recipe").joinpath("boilerplate.conf")


def load_config(
    user_config: Optional[Path] = None,
) -> Tuple[Dict[str, List[re.Pattern]], Dict[str, List[Tuple[re.Pattern, str]]]]:
    """Load patterns from user config (if it exists) or package defaults.

    Returns (sections, pairs) where:
      sections: {name: [compiled regex, ...]} for plain pattern sections
      pairs:    {name: [(compiled regex, replacement), ...]} for pair sections
    """
    sections: Dict[str, List[re.Pattern]] = {}
    pairs: Dict[str, List[Tuple[re.Pattern, str]]] = {}

    config_path = user_config or _DEFAULT_USER_CONFIG
    if config_path.exists():
        _parse_conf(config_path.read_text(encoding="utf-8"), sections, pairs)
    else:
        _parse_conf(_default_conf().read_text(encoding="utf-8"), sections, pairs)

    return sections, pairs


def init_user_config(target: Optional[Path] = None) -> Path:
    """Copy the package default config to the user config location.

    Returns the path written to. Raises FileExistsError if already present.
    """
    dest = target or _DEFAULT_USER_CONFIG
    if dest.exists():
        raise FileExistsError(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(str(_default_conf()), str(dest))
    return dest


# Module-level defaults (loaded without user config override;
# cli.py calls init() with the resolved config path)
_sections: Dict[str, List[re.Pattern]] = {}
_pairs: Dict[str, List[Tuple[re.Pattern, str]]] = {}


def init(user_config: Optional[Path] = None) -> None:
    """Initialise patterns from package defaults + user config."""
    global _sections, _pairs
    _sections, _pairs = load_config(user_config)


# Load package defaults immediately so imports work without init()
init()


def strip_boilerplate(text: str) -> str:
    """Remove known system-generated boilerplate from within text."""
    for pattern in _sections.get("strip", []):
        text = pattern.sub("", text)
    return text


def should_skip(display: str) -> bool:
    """Return True if a prompt should be omitted entirely from the recipe."""
    return any(p.search(display) for p in _sections.get("skip", []))


def is_plan(display: str) -> bool:
    """Return True if a prompt is a plan-mode prompt (to be collapsed)."""
    return any(p.search(display) for p in _sections.get("plan", []))


def redact_patterns() -> List[Tuple[re.Pattern, str]]:
    """Return the list of (pattern, replacement) pairs for redaction."""
    return _pairs.get("redact", [])
