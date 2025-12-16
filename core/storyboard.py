from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class StoryEvent:
    t_start: float
    t_end: float
    text: str
    # Optional swatch (for Colors)
    swatch_hex: Optional[str] = None


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

        events.append(
            StoryEvent(
                t_start=start,
                t_end=end,
                text=str(tok),
                swatch_hex=swatch,
            )
        )
    return events
