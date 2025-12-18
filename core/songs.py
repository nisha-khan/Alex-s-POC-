from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Dict

from core.prompt_parser import parse_prompt_lines

ROOT = Path(__file__).resolve().parents[1]
PROMPTS_DIR = ROOT / "prompts"
ICONS_DIR = ROOT / "assets" / "icons"


@dataclass(frozen=True)
class SongTemplate:
    key: str
    title: str
    tokens: List[Dict[str, Optional[str]]]  # list of {big, small, icon, swatch}


def _repeat_to_length(base: List[Dict[str, Optional[str]]], target_len: int) -> List[Dict[str, Optional[str]]]:
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
    return [l.strip() for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]


def _icon_for_unit(unit: Dict[str, str]) -> Optional[str]:
    """
    Choose icon based on:
      - first character of 'big' if it's a letter (A/B/C)
      - otherwise first character of noun
    icons are stored as assets/icons/a.png etc.
    """
    big = (unit.get("big") or "").strip()
    noun = (unit.get("noun") or "").strip()

    key = ""
    if big and big[0].isalpha():
        key = big[0].lower()
    elif noun and noun[0].isalpha():
        key = noun[0].lower()
    else:
        return None

    p = ICONS_DIR / f"{key}.png"
    return str(p) if p.exists() else None


def get_templates(target_events: int = 72) -> List[SongTemplate]:
    # ---------- ABC ----------
    abc_lines = _load_prompt_lines("abc_song.txt")
    abc_units = parse_prompt_lines(abc_lines)
    abc_base = []
    for u in abc_units:
        abc_base.append(
            {
                "big": u["big"],
                "small": u["small"],
                "icon": _icon_for_unit(u),
                "swatch": None,
            }
        )
    abc_tokens = _repeat_to_length(abc_base, target_events)

    # ---------- NUMBERS ----------
    num_lines = _load_prompt_lines("numbers_song.txt")
    num_units = parse_prompt_lines(num_lines)
    num_base = []
    for u in num_units:
        num_base.append(
            {
                "big": u["big"],
                "small": u["small"],
                "icon": _icon_for_unit(u),  # optional; based on noun’s first letter
                "swatch": None,
            }
        )
    num_tokens = _repeat_to_length(num_base, target_events)

    # ---------- COLORS ----------
    color_lines = _load_prompt_lines("colors_song.txt")
    color_units = parse_prompt_lines(color_lines)

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

    color_base = []
    for u in color_units:
        big = (u["big"] or "").upper()
        sw = COLOR_HEX.get(big, "#000000")
        color_base.append(
            {
                "big": big,
                "small": "",      # keep clean for colors
                "icon": None,     # swatch is the visual
                "swatch": sw,
            }
        )
    color_tokens = _repeat_to_length(color_base, target_events)

    return [
        SongTemplate(key="abc", title="ABC Song (Prompt-Based)", tokens=abc_tokens),
        SongTemplate(key="numbers", title="Numbers Song (Prompt-Based)", tokens=num_tokens),
        SongTemplate(key="colors", title="Colors Song (Prompt-Based)", tokens=color_tokens),
    ]


def get_template_by_key(key: str, target_events: int = 72) -> SongTemplate:
    for t in get_templates(target_events):
        if t.key == key:
            return t
    return get_templates(target_events)[0]
