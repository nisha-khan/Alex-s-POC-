from __future__ import annotations

import subprocess
from pathlib import Path
from typing import List, Tuple

from core.storyboard import StoryEvent

ROOT = Path(__file__).resolve().parents[1]
ICONS_DIR = ROOT / "assets" / "icons"

FONT_LINUX = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def _escape_text(s: str) -> str:
    # Safe for ffmpeg drawtext
    return (
        (s or "")
        .replace("\\", "\\\\")
        .replace(":", "\\:")
        .replace("'", "\\'")
    )


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

    # ---- pixel constants (NO expressions like w*0.12 on Streamlit Cloud) ----
    card_x = int(w * 0.12)
    card_y = int(h * 0.14)
    card_w = int(w * 0.76)
    card_h = int(h * 0.72)

    big_fs = int(h * 0.22)
    word_fs = int(h * 0.10)

    big_y = int(h * 0.22)
    word_y = int(h * 0.50)

    icon_h = int(h * 0.20)
    icon_y = int(h * 0.62)

    # Collect icons used
    icon_paths: List[Path] = []
    for e in events:
        if e.icon:
            p = (ICONS_DIR / e.icon).resolve()
            if p.exists():
                icon_paths.append(p)

    # unique preserve order
    seen = set()
    icon_paths_unique: List[Path] = []
    for p in icon_paths:
        if str(p) not in seen:
            seen.add(str(p))
            icon_paths_unique.append(p)

    # ffmpeg inputs (audio + icons as looped images)
    cmd = [
        "ffmpeg", "-y",
        "-hide_banner", "-loglevel", "error",
        "-stream_loop", "-1", "-i", audio_path,
    ]
    for p in icon_paths_unique:
        cmd += ["-loop", "1", "-i", str(p)]

    # background
    filter_parts = [f"color=c=#E6F5FF:s={w}x{h}:r={fps}:d={duration_sec}[bg];"]
    current = "[bg]"

    icon_input_idx = {str(p): i + 1 for i, p in enumerate(icon_paths_unique)}  # audio=0, icons start=1

    for i, e in enumerate(events):
        start = max(0.0, float(e.t_start))
        end = min(float(duration_sec), float(e.t_end))
        if end <= start:
            continue

        enable = f"between(t\\,{start:.3f}\\,{end:.3f})"
        next_label = f"[v{i}]"

        letter = _escape_text(e.letter)
        word = _escape_text(e.word)

        # Base card + texts
        chain = (
            f"{current}"
            f"drawbox=x={card_x}:y={card_y}:w={card_w}:h={card_h}:color=black@0.30:t=fill:enable='{enable}',"
            f"drawtext=fontfile='{FONT_LINUX}':fontsize={big_fs}:fontcolor=white:x=(w-text_w)/2:y={big_y}:text='{letter}':enable='{enable}',"
        )

        if word:
            chain += (
                f"drawtext=fontfile='{FONT_LINUX}':fontsize={word_fs}:fontcolor=white:x=(w-text_w)/2:y={word_y}:text='{word}':enable='{enable}',"
            )

        # Optional icon overlay
        if e.icon:
            p = (ICONS_DIR / e.icon).resolve()
            if p.exists():
                idx = icon_input_idx.get(str(p))
                if idx is not None:
                    ic_label = f"[ic{i}]"
                    # scale icon stream then overlay
                    chain = chain.rstrip(",")
                    chain += f"{next_label}tmp{i};"
                    # Above line makes a label we can overlay onto:
                    # But easiest is: do texts into tmp label, then overlay onto it.
                    filter_parts.append(chain)

                    filter_parts.append(
                        f"[{idx}:v]scale=-1:{icon_h}{ic_label};"
                        f"[tmp{i}]{ic_label}overlay=x=(w-overlay_w)/2:y={icon_y}:enable='{enable}'{next_label};"
                    )
                    current = next_label
                    continue

        # no icon case: just close
        chain = chain.rstrip(",") + f"{next_label};"
        filter_parts.append(chain)
        current = next_label

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
        raise RuntimeError(f"FFMPEG FAILED\n\nReturn code: {p.returncode}\n\nSTDERR:\n{p.stderr}\n")

    return str(out)
