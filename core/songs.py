# core/songs.py
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
    token_icons: Optional[List[str]] = None  # icon filenames (png)
    token_words: Optional[List[str]] = None  # word under big letter

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
    return [l.strip() for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]

def get_templates(target_events: int = 24) -> List[SongTemplate]:
    """
    ABC only. 1 minute default elsewhere (app.py).
    target_events=24 => 60 sec / 24 = 2.5 sec per card (nice pacing).
    """
    abc_lines = _load_prompt_lines("abc_song.txt")
    abc_units = parse_prompt_lines(abc_lines)

    letters = _repeat_to_length([u.get("letter", "") for u in abc_units], target_events)
    words   = _repeat_to_length([u.get("word", "") for u in abc_units], target_events)
    icons   = _repeat_to_length([u.get("icon", "") for u in abc_units], target_events)

    return [
        SongTemplate(
            key="abc",
            title="ABC Song (A is for Apple)",
            tokens=letters,
            token_words=words,
            token_icons=icons,
        )
    ]

def get_template_by_key(key: str, target_events: int = 24) -> SongTemplate:
    # Only one template for POC
    return get_templates(target_events)[0]
