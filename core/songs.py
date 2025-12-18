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
    units: List[dict]


def _load_prompt_lines(filename: str) -> List[str]:
    path = PROMPTS_DIR / filename
    if not path.exists():
        raise FileNotFoundError(f"Missing prompt file: {path}")
    return [l.strip() for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]


def get_template_by_key(key: str) -> SongTemplate:
    if key != "abc":
        key = "abc"

    abc_lines = _load_prompt_lines("abc_song.txt")
    abc_units = parse_prompt_lines(abc_lines)

    return SongTemplate(
        key="abc",
        title="ABC Song (Timestamped)",
        units=abc_units,
    )
