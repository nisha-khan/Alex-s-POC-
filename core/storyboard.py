from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class StoryEvent:
    t_start: float
    t_end: float

    # What we show on screen
    big_text: str
    small_text: str = ""

    # Optional icon (PNG path)
    icon_path: Optional[str] = None

    # Optional swatch (for Colors)
    swatch_hex: Optional[str] = None


def build_storyboard_for_template(
    tokens: List[dict],
    duration_sec: int = 180,
) -> List[StoryEvent]:
    """
    Builds evenly spaced events across duration_sec.
    tokens is a list of dicts like:
      { "big": "A", "small": "Apple", "icon": "assets/icons/a.png", "swatch": None }
    """
    if not tokens:
        return []

    n = len(tokens)
    step = duration_sec / float(n)

    events: List[StoryEvent] = []
    for i, tok in enumerate(tokens):
        start = i * step
        end = (i + 1) * step

        events.append(
            StoryEvent(
                t_start=start,
                t_end=end,
                big_text=str(tok.get("big", "")),
                small_text=str(tok.get("small", "")),
                icon_path=tok.get("icon"),
                swatch_hex=tok.get("swatch"),
            )
        )
    return events
