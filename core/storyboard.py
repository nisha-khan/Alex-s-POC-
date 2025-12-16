from __future__ import annotations

from typing import List, Dict

DEFAULT_LABELS = ["A", "B", "C"]

ASSET_MAP = {
    "A": "assets/alphabet/A_alligator.png",
    "B": "assets/alphabet/B_bear.png",
    "C": "assets/alphabet/C_cat.png",
}


def build_storyboard(onset_times: List[float], labels: List[str]) -> List[Dict]:
    """
    Map each onset time to a letter/asset event.
    """
    events = []
    n = min(len(onset_times), len(labels))

    for i in range(n):
        label = labels[i]
        asset_path = ASSET_MAP.get(label)
        if not asset_path:
            continue

        events.append(
            {
                "t": float(onset_times[i]),
                "label": label,
                "asset": asset_path,
                "duration": 1.2,
                "effect": "bounce",
            }
        )

    return events
