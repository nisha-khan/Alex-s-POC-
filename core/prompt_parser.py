# core/prompt_parser.py
from __future__ import annotations
from typing import List, Dict


def _ts_to_seconds(ts: str) -> float:
    """
    Accepts:
      - "MM:SS"
      - "MM:SS.xx"
      - "HH:MM:SS"
      - "HH:MM:SS.xx"
    """
    ts = ts.strip()
    parts = ts.split(":")
    if len(parts) == 2:
        m = int(parts[0])
        s = float(parts[1])
        return m * 60 + s
    if len(parts) == 3:
        h = int(parts[0])
        m = int(parts[1])
        s = float(parts[2])
        return h * 3600 + m * 60 + s
    # fallback
    return float(ts)


def parse_prompt_lines(lines: List[str]) -> List[Dict[str, object]]:
    """
    Preferred (timestamped):
      "00:00.01|A|Apple|a.png"

    Also supports (no timestamp):
      "A|Apple|a.png"
      "A is for Apple|a.png" (fallback)
      "A" (fallback)

    Returns list of dicts:
      { "t": float, "letter": str, "word": str, "icon": str }
    """
    out: List[Dict[str, object]] = []

    for raw in lines:
        line = raw.strip()
        if not line:
            continue

        if "|" in line:
            parts = [p.strip() for p in line.split("|")]

            # Timestamped format: t|letter|word|icon
            if len(parts) >= 4 and (":" in parts[0] or parts[0].replace(".", "", 1).isdigit()):
                t = _ts_to_seconds(parts[0])
                letter = parts[1]
                word = parts[2]
                icon = parts[3]
                out.append({"t": t, "letter": letter, "word": word, "icon": icon})
                continue

            # Non-timestamp: letter|word|icon
            letter = parts[0] if len(parts) > 0 else ""
            word = parts[1] if len(parts) > 1 else ""
            icon = parts[2] if len(parts) > 2 else ""
            out.append({"t": 0.0, "letter": letter, "word": word, "icon": icon})
            continue

        # Minimal fallback: "A"
        letter = line[:1].strip()
        out.append({"t": 0.0, "letter": letter, "word": "", "icon": ""})

    return out
