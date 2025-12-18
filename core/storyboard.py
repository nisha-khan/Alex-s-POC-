# core/storyboard.py
from __future__ import annotations
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class StoryEvent:
    t_start: float
    t_end: float
    letter: str
    word: str
    icon: Optional[str] = None  # filename like "a.png"

def build_storyboard_for_template(
    tokens: List[str],
    duration_sec: int = 60,
    token_words: Optional[List[str]] = None,
    token_icons: Optional[List[str]] = None,
) -> List[StoryEvent]:
    if not tokens:
        return []

    n = len(tokens)
    step = duration_sec / float(n)

    events: List[StoryEvent] = []
    for i, letter in enumerate(tokens):
        start = i * step
        end = (i + 1) * step

        word = ""
        if token_words and i < len(token_words):
            word = token_words[i] or ""

        icon = None
        if token_icons and i < len(token_icons):
            icon = token_icons[i] or None

        events.append(
            StoryEvent(
                t_start=start,
                t_end=end,
                letter=str(letter),
                word=str(word),
                icon=icon,
            )
        )

    return events
