from __future__ import annotations
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class StoryEvent:
    t_start: float
    t_end: float
    letter: str
    word: str
    icon: Optional[str] = None


def build_storyboard_for_template(units: List[dict], duration_sec: int = 60) -> List[StoryEvent]:
    """
    If units have timestamps -> align events to timestamps (end = next timestamp).
    If timestamps missing -> evenly space them.
    """
    if not units:
        return []

    # If at least half units have timestamps, treat as timestamped
    ts_count = sum(1 for u in units if u.get("t") is not None)
    use_ts = ts_count >= max(1, len(units) // 2)

    events: List[StoryEvent] = []

    if use_ts:
        # filter only timestamped lines and sort
        timed = [u for u in units if u.get("t") is not None]
        timed.sort(key=lambda x: float(x["t"]))

        for i, u in enumerate(timed):
            start = float(u["t"])
            end = float(timed[i + 1]["t"]) if i + 1 < len(timed) else float(duration_sec)
            # clamp
            start = max(0.0, min(start, float(duration_sec)))
            end = max(0.0, min(end, float(duration_sec)))
            if end <= start:
                continue

            events.append(
                StoryEvent(
                    t_start=start,
                    t_end=end,
                    letter=str(u.get("letter", "")),
                    word=str(u.get("word", "")),
                    icon=(u.get("icon") or None),
                )
            )
        return events

    # fallback: evenly spaced
    n = len(units)
    step = duration_sec / float(n)
    for i, u in enumerate(units):
        start = i * step
        end = (i + 1) * step
        events.append(
            StoryEvent(
                t_start=start,
                t_end=end,
                letter=str(u.get("letter", "")),
                word=str(u.get("word", "")),
                icon=(u.get("icon") or None),
            )
        )
    return events
