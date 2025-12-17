from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class StoryEvent:
    t_start: float
    t_end: float

    # What to show
    title: str                  # Big text (e.g., "A" or "3" or "RED")
    subtitle: Optional[str] = None  # Smaller text (e.g., "Apple" or "apples")

    # Visuals
    icon_path: Optional[str] = None   # local png path (assets/icons/xxx.png)
    swatch_hex: Optional[str] = None  # for Colors blocks


def build_storyboard_for_template(
    tokens: List[dict],
    duration_sec: int = 180,
) -> List[StoryEvent]:
    """
    tokens: list of dicts like:
      { "title": "A", "subtitle": "Apple", "icon": "assets/icons/apple.png" }
    """
    if not tokens:
        return []

    n = len(tokens)
    step = duration_sec / float(n)

    events: List[StoryEvent] = []
    for i, t in enumerate(tokens):
        start = i * step
        end = (i + 1) * step

        events.append(
            StoryEvent(
                t_start=start,
                t_end=end,
                title=str(t.get("title", "")),
                subtitle=t.get("subtitle"),
                icon_path=t.get("icon"),
                swatch_hex=t.get("swatch_hex"),
            )
        )
    return events
