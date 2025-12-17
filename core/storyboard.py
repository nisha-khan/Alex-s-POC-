from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Tuple


@dataclass
class StoryEvent:
    t_start: float
    t_end: float

    # Backwards-compatible "combined" text (we can still use this in render)
    text: str

    # New structured fields (for "A is for Apple" vibe)
    letter: str = ""
    word: str = ""
    icon: str = ""  # emoji or placeholder string

    # Optional swatch (for Colors)
    swatch_hex: Optional[str] = None


def _parse_token(tok: str) -> Tuple[str, str, str, str]:
    """
    Token formats supported:

    1) Old:
       "A" -> letter="A", word="", icon="", text="A"

    2) New (recommended):
       "A|Apple|🍎" -> letter="A", word="Apple", icon="🍎", text="A\nApple"

       If icon missing:
       "A|Apple" -> icon=""

    We return: (letter, word, icon, combined_text)
    """
    s = str(tok).strip()

    if "|" not in s:
        # Old behavior: token is the whole text
        return s, "", "", s

    parts = [p.strip() for p in s.split("|")]

    letter = parts[0] if len(parts) > 0 else ""
    word = parts[1] if len(parts) > 1 else ""
    icon = parts[2] if len(parts) > 2 else ""

    # Combined text used by renderer if needed
    if letter and word:
        combined = f"{letter}\n{word}"
    else:
        combined = letter or word or s

    return letter, word, icon, combined


def build_storyboard_for_template(
    tokens: List[str],
    duration_sec: int = 180,
    token_colors: Optional[List[str]] = None,
) -> List[StoryEvent]:
    """
    Builds evenly spaced events across duration_sec.
    tokens length determines how many events occur.
    """
    if not tokens:
        return []

    n = len(tokens)
    step = duration_sec / float(n)

    events: List[StoryEvent] = []
    for i, tok in enumerate(tokens):
        start = i * step
        end = (i + 1) * step

        swatch = None
        if token_colors and i < len(token_colors):
            swatch = token_colors[i]

        letter, word, icon, combined_text = _parse_token(tok)

        events.append(
            StoryEvent(
                t_start=start,
                t_end=end,
                text=combined_text,  # still works with your current renderer
                letter=letter,
                word=word,
                icon=icon,
                swatch_hex=swatch,
            )
        )

    return events
