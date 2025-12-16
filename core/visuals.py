from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Dict


ANIMALS = {"A": "Alligator", "B": "Bear", "C": "Cat"}


def ensure_visual_assets(out_dir: Path) -> Dict[str, str]:
    """
    Creates simple kid-safe PNGs using ImageMagick if missing.
    Returns label -> absolute filepath.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    mapping: Dict[str, str] = {}

    for letter, animal in ANIMALS.items():
        p = out_dir / f"{letter}_{animal.lower()}.png"
        if not p.exists():
            _make_card_png(p, letter, animal)
        mapping[letter] = str(p.resolve())

    return mapping


def _make_card_png(path: Path, letter: str, animal: str) -> None:
    # 1024x1024, light background, border, big letter, animal label
    cmd = [
        "convert",
        "-size", "1024x1024",
        "xc:#F5F5F5",
        "-fill", "#141414",
        "-stroke", "#141414",
        "-strokewidth", "8",
        "-draw", "roundrectangle 60,60 964,964 60,60",
        "-font", "DejaVu-Sans-Bold",
        "-pointsize", "520",
        "-fill", "#0F3CAA",
        "-gravity", "north",
        "-annotate", "+0+120", letter,
        "-font", "DejaVu-Sans-Bold",
        "-pointsize", "96",
        "-fill", "#141414",
        "-gravity", "south",
        "-annotate", "+0+120", animal,
        str(path),
    ]
    subprocess.run(cmd, check=True)


def ensure_background(bg_path: Path) -> str:
    bg_path.parent.mkdir(parents=True, exist_ok=True)
    if not bg_path.exists():
        cmd = [
            "convert",
            "-size", "1280x720",
            "xc:#E6F5FF",
            "-fill", "#D7EEFF",
            "-draw", "rectangle 0,0 640,720",
            str(bg_path),
        ]
        subprocess.run(cmd, check=True)
    return str(bg_path.resolve())
