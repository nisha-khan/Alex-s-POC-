# core/storyboard.py
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Dict


@dataclass
class StoryEvent:
    t_start: float
    t_end: float
    letter: str
    word: str
    icon: Optional[str] = None


def build_storyboard_from_units(
    units: List[Dict[str, object]],
    duration_sec: int = 60,
) -> List[StoryEvent]:
    """
    units: list of {"t": float, "letter": str, "word": str, "icon": str}

    We convert:
      start = units[i]["t"]
      end   = units[i+1]["t"] OR duration_sec for the last one
    """
    if not units:
        return []

    # sort by time
    units = sorted(units, key=lambda u: float(u.get("t", 0.0)))

    events: List[StoryEvent] = []
    for i, u in enumerate(units):
        start = float(u.get("t", 0.0))
        end = float(units[i + 1].get("t", duration_sec)) if i + 1 < len(units) else float(duration_sec)

        # clamp
        start = max(0.0, min(start, float(duration_sec)))
        end = max(0.0, min(end, float(duration_sec)))
        if end <= start:
            # skip broken/duplicate timestamps
            continue

        events.append(
            StoryEvent(
                t_start=start,
                t_end=end,
                letter=str(u.get("letter", "")),
                word=str(u.get("word", "")),
                icon=(str(u.get("icon", "")).strip() or None),
            )
        )

    return events
