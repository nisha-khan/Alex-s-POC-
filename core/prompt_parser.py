from __future__ import annotations
from typing import List, Dict, Optional
import re


def ts_to_seconds(ts: str) -> float:
    """
    Accepts:
      - "MM:SS"
      - "MM:SS.xx"
      - "HH:MM:SS"
      - "HH:MM:SS.xx"
      - also your format "00:00.01" (MM:SS.xx)
    """
    ts = ts.strip()
    if not ts:
        return 0.0

    parts = ts.split(":")
    if len(parts) == 1:
        # "SS" or "SS.xx"
        return float(parts[0])

    if len(parts) == 2:
        m = int(parts[0])
        s = float(parts[1])
        return m * 60 + s

    # len == 3
    h = int(parts[0])
    m = int(parts[1])
    s = float(parts[2])
    return h * 3600 + m * 60 + s


_TS_PREFIX = re.compile(r"^\s*(\d{1,2}:\d{2}(?::\d{2})?(?:\.\d+)?)\s*\|\s*(.*)$")


def parse_prompt_lines(lines: List[str]) -> List[Dict]:
    """
    Supported line formats:

    A) Timestamped (recommended):
       00:00.01|A|Apple|a.png
       00:02.50|B|Ball|b.png

    B) Non-timestamped:
       A|Apple|a.png

    Returns list of units:
      {"t": float_seconds_or_None, "letter": str, "word": str, "icon": str}
    """
    out: List[Dict] = []

    for raw in lines:
        line = (raw or "").strip()
        if not line:
            continue

        t: Optional[float] = None

        m = _TS_PREFIX.match(line)
        if m:
            ts = m.group(1)
            rest = m.group(2)
            t = ts_to_seconds(ts)
            parts = [p.strip() for p in rest.split("|")]
        else:
            parts = [p.strip() for p in line.split("|")]

        letter = parts[0] if len(parts) > 0 else ""
        word = parts[1] if len(parts) > 1 else ""
        icon = parts[2] if len(parts) > 2 else ""

        out.append({"t": t, "letter": letter, "word": word, "icon": icon})

    return out
