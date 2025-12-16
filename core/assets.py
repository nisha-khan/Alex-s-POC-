from __future__ import annotations

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont


def ensure_assets(base_dir: Path) -> dict:
    """
    Ensures required assets exist. If missing, creates simple kid-safe placeholders.
    Returns paths used by the app.
    """
    assets_dir = base_dir / "assets"
    alphabet_dir = assets_dir / "alphabet"
    backgrounds_dir = assets_dir / "backgrounds"

    alphabet_dir.mkdir(parents=True, exist_ok=True)
    backgrounds_dir.mkdir(parents=True, exist_ok=True)

    bg_path = backgrounds_dir / "bg_default.png"
    if not bg_path.exists():
        _make_bg(bg_path, size=(1280, 720))

    # Create alphabet placeholders if missing
    for letter, animal in [("A", "Alligator"), ("B", "Bear"), ("C", "Cat")]:
        p = alphabet_dir / f"{letter}_{animal.lower()}.png"
        if not p.exists():
            _make_letter_card(p, letter=letter, label=animal)

    return {
        "bg_default": str(bg_path),
        "A": str(alphabet_dir / "A_alligator.png"),
        "B": str(alphabet_dir / "B_bear.png"),
        "C": str(alphabet_dir / "C_cat.png"),
    }


def _make_bg(path: Path, size: tuple[int, int]) -> None:
    img = Image.new("RGB", size, (245, 245, 245))
    draw = ImageDraw.Draw(img)
    draw.rectangle([0, 0, size[0], size[1]], outline=(220, 220, 220), width=10)
    img.save(path)


def _make_letter_card(path: Path, letter: str, label: str) -> None:
    w, h = 1024, 1024
    img = Image.new("RGBA", (w, h), (255, 255, 255, 0))
    draw = ImageDraw.Draw(img)

    # Card
    draw.rectangle([80, 80, w - 80, h - 80], fill=(255, 255, 255, 235), outline=(30, 30, 30, 255), width=8)

    # Fonts (DejaVu is usually available on Linux)
    try:
        font_big = ImageFont.truetype("DejaVuSans-Bold.ttf", 320)
        font_small = ImageFont.truetype("DejaVuSans.ttf", 72)
    except Exception:
        font_big = ImageFont.load_default()
        font_small = ImageFont.load_default()

    draw.text((w // 2, 360), letter, font=font_big, fill=(20, 20, 80, 255), anchor="mm")
    draw.text((w // 2, 720), label, font=font_small, fill=(10, 10, 10, 255), anchor="mm")

    img.save(path)
