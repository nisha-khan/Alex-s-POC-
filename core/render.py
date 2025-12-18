# core/render.py
from __future__ import annotations

import subprocess
from pathlib import Path
from typing import List, Tuple

from core.storyboard import StoryEvent

ROOT = Path(__file__).resolve().parents[1]
ICONS_DIR = ROOT / "assets" / "icons"

FONT_LINUX = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_WIN_FALLBACK = "C:/Windows/Fonts/arialbd.ttf"


def _escape_text(s: str) -> str:
    return (
        (s or "")
        .replace("\\", "\\\\")
        .replace(":", "\\:")
        .replace("'", "\\'")
    )


def _font_arg() -> str:
    # Prefer fontfile (more reliable on Streamlit Cloud)
    if Path(FONT_LINUX).exists():
        return f"fontfile='{FONT_LINUX}'"
    # Windows fallback (note: ffmpeg drawtext is picky on Windows paths)
    return f"fontfile='{FONT_WIN_FALLBACK}'"


def render_video_ffmpeg_drawtext(
    audio_path: str,
    events: List[StoryEvent],
    output_path: str,
    duration_sec: int = 60,
    resolution: Tuple[int, int] = (854, 480),
    fps: int = 24,
) -> str:
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)

    w, h = resolution
    icon_h = max(32, int(h * 0.20))  # icon height in pixels

    # Collect unique icon files that actually exist
    icon_files_unique: List[Path] = []
    seen = set()
    for e in events:
        if not getattr(e, "icon", None):
            continue
        p = (ICONS_DIR / e.icon).resolve()
        if p.exists() and str(p) not in seen:
            seen.add(str(p))
            icon_files_unique.append(p)

    # ffmpeg inputs: audio (0), then each icon image (1..n)
    cmd = [
        "ffmpeg", "-y",
        "-hide_banner", "-loglevel", "error",
        "-stream_loop", "-1", "-i", audio_path,
    ]

    for p in icon_files_unique:
        cmd += ["-loop", "1", "-i", str(p)]

    # map icon path -> input index
    icon_input_map = {str(p): idx + 1 for idx, p in enumerate(icon_files_unique)}

    filter_parts: List[str] = []
    filter_parts.append(f"color=c=#E6F5FF:s={w}x{h}:r={fps}:d={duration_sec}[bg];")

    current = "[bg]"

    for i, e in enumerate(events):
        start = max(0.0, float(e.t_start))
        end = min(float(duration_sec), float(e.t_end))
        enable = f"between(t\\,{start:.3f}\\,{end:.3f})"

        letter = _escape_text(getattr(e, "letter", ""))
        word = _escape_text(getattr(e, "word", ""))

        text_label = f"[t{i}]"
        out_label = f"[v{i}]"

        # 1) draw card + text onto current -> [t{i}]
        chain = (
            f"{current}"
            f"drawbox=x=w*0.12:y=h*0.14:w=w*0.76:h=h*0.72:"
            f"color=black@0.30:t=fill:enable='{enable}',"
            f"drawtext={_font_arg()}:fontsize=h*0.22:fontcolor=white:"
            f"x=(w-text_w)/2:y=h*0.22:text='{letter}':enable='{enable}'"
        )

        if word:
            chain += (
                f",drawtext={_font_arg()}:fontsize=h*0.10:fontcolor=white:"
                f"x=(w-text_w)/2:y=h*0.50:text='{word}':enable='{enable}'"
            )

        chain += f"{text_label};"
        filter_parts.append(chain)

        # 2) if icon exists -> scale icon -> overlay on [t{i}] -> [v{i}]
        icon_name = getattr(e, "icon", None)
        if icon_name:
            icon_path = (ICONS_DIR / icon_name).resolve()
            idx = icon_input_map.get(str(icon_path))

            if idx is not None:
                icon_scaled = f"[ic{i}]"
                # scale icon to fixed pixel height (safe)
                filter_parts.append(f"[{idx}:v]scale=-1:{icon_h}{icon_scaled};")

                # overlay onto text_label -> out_label
                filter_parts.append(
                    f"{text_label}{icon_scaled}"
                    f"overlay=x=(main_w-overlay_w)/2:y=main_h*0.62:"
                    f"enable='{enable}'"
                    f"{out_label};"
                )
                current = out_label
                continue

        # 3) no icon -> just pass text_label forward as out_label
        filter_parts.append(f"{text_label}copy{out_label};")
        current = out_label

    filter_complex = "".join(filter_parts).rstrip(";")

    cmd += [
        "-filter_complex", filter_complex,
        "-map", current,
        "-map", "0:a",
        "-t", str(duration_sec),
        "-r", str(fps),
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-shortest",
        str(out),
    ]

    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if p.returncode != 0:
        raise RuntimeError(
            "FFMPEG FAILED\n\n"
            f"Return code: {p.returncode}\n\n"
            f"STDERR:\n{p.stderr}\n"
        )

    return str(out)
