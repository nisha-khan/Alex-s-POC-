from __future__ import annotations

import subprocess
from pathlib import Path
from typing import List, Tuple

from core.storyboard import StoryEvent


def _hex_to_ffmpeg_color(hex_color: str) -> str:
    h = (hex_color or "").strip()
    if h.startswith("#"):
        h = h[1:]
    if len(h) != 6:
        return "0x000000"
    return "0x" + h.upper()


def _escape_text(s: str) -> str:
    # Escape backslashes, colons, apostrophes (basic)
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
    duration_sec: int = 180,
    resolution: Tuple[int, int] = (1280, 720),
    fps: int = 30,
) -> str:
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)

    w, h = resolution

    # Prefer an explicit font FILE on Linux (Streamlit Cloud),
    # fallback to font name if not present.
    linux_fontfile = Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf")
    if linux_fontfile.exists():
        font_part = f"fontfile='{linux_fontfile.as_posix()}':"
    else:
        font_part = "font='DejaVuSans-Bold':"

    filter_chain = [f"color=c=#E6F5FF:s={w}x{h}:r={fps}:d={duration_sec}[bg];"]
    current = "[bg]"

    for i, e in enumerate(events):
        start = max(0.0, float(e.t_start))
        end = min(float(duration_sec), float(e.t_end))
        enable = f"between(t\\,{start:.3f}\\,{end:.3f})"

        next_label = f"[v{i}]"

        box = (
            f"{current}drawbox=x=(w*0.18):y=(h*0.28):w=(w*0.64):h=(h*0.44):"
            f"color=black@0.35:t=fill:enable='{enable}',"
        )

        if getattr(e, "swatch_hex", None):
            sw = _hex_to_ffmpeg_color(e.swatch_hex)
            box += (
                f"drawbox=x=(w*0.30):y=(h*0.70):w=(w*0.40):h=(h*0.12):"
                f"color={sw}@0.95:t=fill:enable='{enable}',"
            )

        text = (
            box
            + "drawtext="
            + font_part
            + "fontsize=h*0.20:"
            + "fontcolor=white:"
            + "x=(w-text_w)/2:"
            + "y=(h-text_h)/2:"
            + f"text='{_escape_text(e.text)}':"
            + f"enable='{enable}'"
            + next_label
            + ";"
        )

        filter_chain.append(text)
        current = next_label

    filter_complex = "".join(filter_chain).rstrip(";")

    cmd = [
        "ffmpeg", "-y",
        "-hide_banner", "-loglevel", "error",
        "-stream_loop", "-1", "-i", audio_path,
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

    print("FFMPEG FILTER (first 800 chars):", filter_complex[:800])
    print("FFMPEG CMD:", cmd[:10], "...", cmd[-6:])

    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    print("\n========== FFMPEG STDOUT ==========\n", p.stdout)
    print("\n========== FFMPEG STDERR ==========\n", p.stderr)

    if p.returncode != 0:
        raise RuntimeError(
            "FFMPEG FAILED\n\n"
            f"Return code: {p.returncode}\n\n"
            f"STDERR:\n{p.stderr}\n\n"
            f"STDOUT:\n{p.stdout}\n\n"
            f"CMD:\n{' '.join(cmd)}\n"
        )
    
    return str(out)
