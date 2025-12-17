from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from core.prompt_parser import parse_prompt_lines

ROOT = Path(__file__).resolve().parents[1]
PROMPTS_DIR = ROOT / "prompts"


@dataclass(frozen=True)
class SongTemplate:
    key: str
    title: str
    tokens: List[str]
    token_colors: Optional[List[str]] = None


def _repeat_to_length(base: List[str], target_len: int) -> List[str]:
    if not base or target_len <= 0:
        return []
    out = []
    i = 0
    while len(out) < target_len:
        out.append(base[i % len(base)])
        i += 1
    return out[:target_len]


def _load_prompt_lines(filename: str) -> List[str]:
    path = PROMPTS_DIR / filename
    if not path.exists():
        raise FileNotFoundError(f"Missing prompt file: {path}")
    return [l.strip() for l in path.read_text().splitlines() if l.strip()]


# --- NEW: basic icon map (POC) ---
ICON_MAP = {
    "APPLE": "🍎",
    "AIRPLANE": "✈️",
    "BALL": "⚽",
    "CAT": "🐱",
    "DOG": "🐶",
    "EGG": "🥚",
    "FISH": "🐟",
    "GOAT": "🐐",
    "HAT": "🎩",
    "ICE": "🧊",
    "JAR": "🫙",
    "KITE": "🪁",
    "LION": "🦁",
    "MOON": "🌙",
    "NOSE": "👃",
    "ORANGE": "🍊",
    "PIG": "🐷",
    "QUEEN": "👑",
    "RABBIT": "🐰",
    "SUN": "☀️",
    "TREE": "🌳",
    "UMBRELLA": "☂️",
    "VIOLIN": "🎻",
    "WHALE": "🐋",
    "XYLOPHONE": "🎶",
    "YACHT": "⛵",
    "ZEBRA": "🦓",
}


def _abc_line_to_token(text: str) -> str:
    """
    Convert a prompt line like:
      "A is for Apple"
      "A for Apple"
      "A - Apple"
    into:
      "A|Apple|🍎"

    If parsing fails, fallback to original text.
    """
    s = text.strip()

    # normalize common patterns
    # We’ll try to split on "is for" first, then "for", then "-"
    upper = s.upper()

    if " IS FOR " in upper:
        parts = s.split(" is for ")
        if len(parts) == 1:
            parts = s.split(" IS FOR ")
        if len(parts) >= 2:
            left = parts[0].strip()
            right = " is for ".join(parts[1:]).strip()
            letter = left[:1].upper()
            word = right.strip()
            icon = ICON_MAP.get(word.upper(), "")
            return f"{letter}|{word}|{icon}".rstrip("|")

    if " FOR " in upper:
        parts = s.split(" for ")
        if len(parts) == 1:
            parts = s.split(" FOR ")
        if len(parts) >= 2:
            left = parts[0].strip()
            right = " for ".join(parts[1:]).strip()
            letter = left[:1].upper()
            word = right.strip()
            icon = ICON_MAP.get(word.upper(), "")
            return f"{letter}|{word}|{icon}".rstrip("|")

    if "-" in s:
        parts = [p.strip() for p in s.split("-", 1)]
        if len(parts) == 2 and parts[0] and parts[1]:
            letter = parts[0][:1].upper()
            word = parts[1]
            icon = ICON_MAP.get(word.upper(), "")
            return f"{letter}|{word}|{icon}".rstrip("|")

    # fallback: if it’s just "A" return "A"
    if len(s) == 1 and s.isalpha():
        return s.upper()

    return s


def get_templates(target_events: int = 72) -> List[SongTemplate]:
    # ---------- ABC ----------
    abc_lines = _load_prompt_lines("abc_song.txt")
    abc_units = parse_prompt_lines(abc_lines)

    # Convert prompt text into structured tokens for storyboard
    abc_tokens_raw = [u["text"] for u in abc_units]
    abc_tokens_structured = [_abc_line_to_token(t) for t in abc_tokens_raw]
    abc_tokens = _repeat_to_length(abc_tokens_structured, target_events)

    # ---------- NUMBERS ----------
    num_lines = _load_prompt_lines("numbers_song.txt")
    num_units = parse_prompt_lines(num_lines)
    num_tokens = _repeat_to_length([u["text"] for u in num_units], target_events)

    # ---------- COLORS ----------
    color_lines = _load_prompt_lines("colors_song.txt")
    color_units = parse_prompt_lines(color_lines)
    color_tokens = _repeat_to_length([u["text"] for u in color_units], target_events)

    COLOR_HEX = {
        "RED": "#FF3B30",
        "BLUE": "#007AFF",
        "GREEN": "#34C759",
        "YELLOW": "#FFCC00",
        "ORANGE": "#FF9500",
        "PURPLE": "#AF52DE",
        "PINK": "#FF2D55",
        "BLACK": "#111111",
        "WHITE": "#FFFFFF",
    }

    color_swatches = _repeat_to_length(
        [COLOR_HEX.get(u["text"], "#000000") for u in color_units],
        target_events,
    )

    return [
        SongTemplate(
            key="abc",
            title="ABC Song (Prompt-Based)",
            tokens=abc_tokens,
        ),
        SongTemplate(
            key="numbers",
            title="Numbers Song (Prompt-Based)",
            tokens=num_tokens,
        ),
        SongTemplate(
            key="colors",
            title="Colors Song (Prompt-Based)",
            tokens=color_tokens,
            token_colors=color_swatches,
        ),
    ]


def get_template_by_key(key: str, target_events: int = 72) -> SongTemplate:
    for t in get_templates(target_events):
        if t.key == key:
            return t
    return get_templates(target_events)[0]
