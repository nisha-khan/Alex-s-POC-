from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Dict

ROOT = Path(__file__).resolve().parents[1]
PROMPTS_DIR = ROOT / "prompts"
ICONS_DIR = ROOT / "assets" / "icons"


@dataclass(frozen=True)
class SongTemplate:
    key: str
    title: str
    tokens: List[Dict]
    token_colors: Optional[List[str]] = None


def _repeat_to_length(base: List[Dict], target_len: int) -> List[Dict]:
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


def _parse_triplet_line(line: str) -> Dict:
    """
    Expected: BIG|WORD|icon.png
    Example: A|Apple|apple.png
    """
    parts = [p.strip() for p in line.split("|")]
    if len(parts) == 3:
        big, word, icon = parts
        icon_path = str(ICONS_DIR / icon)
        return {"title": big, "subtitle": word, "icon": icon_path}

    # fallback: if old format lines exist
    return {"title": line, "subtitle": None, "icon": None}


def get_templates(target_events: int = 72) -> List[SongTemplate]:
    # ---------- ABC ----------
    abc_lines = _load_prompt_lines("abc_song.txt")
    abc_units = [_parse_triplet_line(l) for l in abc_lines]
    abc_tokens = _repeat_to_length(abc_units, target_events)

    # ---------- NUMBERS ----------
    # Keep simple for now: show just the line as title
    num_lines = _load_prompt_lines("numbers_song.txt")
    num_units = [{"title": l, "subtitle": None, "icon": None} for l in num_lines]
    num_tokens = _repeat_to_length(num_units, target_events)

    # ---------- COLORS ----------
    color_lines = _load_prompt_lines("colors_song.txt")
    color_units = [{"title": l, "subtitle": None, "icon": None} for l in color_lines]
    color_tokens = _repeat_to_length(color_units, target_events)

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

    # add swatches into the dict tokens
    for t in color_tokens:
        sw = COLOR_HEX.get(str(t["title"]).upper(), "#000000")
        t["swatch_hex"] = sw

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
