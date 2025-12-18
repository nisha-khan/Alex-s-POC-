# core/prompt_parser.py
from __future__ import annotations
from typing import List, Dict

def parse_prompt_lines(lines: List[str]) -> List[Dict[str, str]]:
    """
    Accepts:
      - "A|Apple|a.png"
      - "A is for Apple|a.png" (fallback)
      - "A" (fallback)

    Returns list of dicts:
      { "letter": "A", "word": "Apple", "icon": "a.png", "text": "A is for Apple" }
    """
    out: List[Dict[str, str]] = []

    for raw in lines:
        line = raw.strip()
        if not line:
            continue

        # Preferred: A|Apple|a.png
        if "|" in line:
            parts = [p.strip() for p in line.split("|")]
            letter = parts[0] if len(parts) > 0 else ""
            word = parts[1] if len(parts) > 1 else ""
            icon = parts[2] if len(parts) > 2 else ""
            text = f"{letter} is for {word}".strip()
            out.append({"letter": letter, "word": word, "icon": icon, "text": text})
            continue

        # Fallback: "A is for Apple|a.png"
        if "|" in line:
            left, right = line.split("|", 1)
            text = left.strip()
            icon = right.strip()
            # try to extract letter/word naïvely
            # e.g. "A is for Apple"
            letter = text[:1].strip()
            word = text.split()[-1].strip() if text.split() else ""
            out.append({"letter": letter, "word": word, "icon": icon, "text": text})
            continue

        # Minimal fallback: "A"
        letter = line[:1].strip()
        out.append({"letter": letter, "word": "", "icon": "", "text": letter})

    return out
