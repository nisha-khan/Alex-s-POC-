from __future__ import annotations

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont


def ensure_assets(base_dir: Path) -> dict:
    """
    Ensures required assets exist. If missing, creates simple placeholders.
    Returns dict with resolved asset paths.
    """
    assets_dir = base_dir / "assets"
    alpha_dir = assets_dir / "alphabet"
    bg_dir = assets_dir / "backgrounds"

    alpha_dir.mkdir(parents=True, exist_ok=True)
    bg_dir.mkdir(parents=True, exist_ok=True)

    # Background
    bg_path = bg_dir / "bg_default.png"
    if not bg_path.exists():
        _make_bg(bg_path, (1280, 720))

    # Alphabet placeholders
    mapping = {
        "A": ("A", "Alligator"),
        "B": ("B", "Bear"),
        "C": ("C", "Cat"),
    }

    for k, (letter, animal) in mapping.items():
        p = alpha_dir / f"{letter}_{animal.lower()}.png"
        if not p.exists():
            _make_letter_animal_card(p, letter, animal)

    return {
        "bg_default": str(bg_path),
        "A": str(alpha_dir / "A_alligator.png"),
        "B": str(alpha_dir / "B_bear.png"),
        "C": str(alpha_dir / "C_cat.png"),
    }


def _make_bg(path: Path, size: tuple[int, int]) -> None:
    img = Image.new("RGB", size, (245, 245, 245))
    img.save(path)


def _make_letter_animal_card(path: Path, letter: str, animal: str) -> None:
    w, h = 1024, 1024
    img = Image.new("RGBA", (w, h), (255, 255, 255, 0))
    draw = ImageDraw.Draw(img)

    # Simple rounded rectangle-ish card
    draw.rectangle([80, 80, w - 80, h - 80], fill=(255, 255, 255, 235), outline=(30, 30, 30, 255), width=8)

    # Try to load a default font (works on Streamlit Cloud)
    try:
        font_big = ImageFont.truetype("DejaVuSans-Bold.ttf", 320)
        font_small = ImageFont.truetype("DejaVuSans.ttf", 72)
    except Exception:
        font_big = ImageFont.load_default()
        font_small = ImageFont.load_default()

    # Letter
    draw.text((w // 2, 340), letter, font=font_big, fill=(20, 20, 80, 255), anchor="mm")

    # Animal label
    draw.text((w // 2, 720), animal, font=font_small, fill=(10, 10, 10, 255), anchor="mm")

    img.save(path)
