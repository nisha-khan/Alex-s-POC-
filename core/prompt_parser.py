from __future__ import annotations

import re
from typing import List, Dict


_IS_FOR_RE = re.compile(r"^\s*(.+?)\s+is\s+for\s+(.+?)\s*$", re.IGNORECASE)


def parse_prompt_lines(lines: List[str]) -> List[Dict[str, str]]:
    """
    Turn lines into units.
    Supports:
      - "A is for Apple"
      - "3 apples"
      - "RED"
      - fallback: any text line

    Returns list of dicts:
      { "big": "...", "small": "...", "noun": "..." }
    """
    out: List[Dict[str, str]] = []

    for raw in lines:
        s = (raw or "").strip()
        if not s:
            continue

        m = _IS_FOR_RE.match(s)
        if m:
            big = m.group(1).strip()
            small = m.group(2).strip()
            # noun is usually the small word’s first token
            noun = small.split()[0] if small else ""
            out.append({"big": big, "small": small, "noun": noun})
            continue

        # "3 apples" style
        parts = s.split()
        if len(parts) >= 2 and parts[0].isdigit():
            big = parts[0]
            small = " ".join(parts[1:])
            noun = parts[1]
            out.append({"big": big, "small": small, "noun": noun})
            continue

        # "RED" style (color)
        out.append({"big": s, "small": "", "noun": s})

    return out
