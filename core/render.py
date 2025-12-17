from __future__ import annotations

import subprocess
from pathlib import Path
from typing import List, Tuple

from core.storyboard import StoryEvent


def _hex_to_ffmpeg_color(hex_color: str) -> str:
    """
    Convert '#RRGGBB' into '0xRRGGBB' for ffmpeg.
    """
    h = hex_color.strip()
    if h.startswith("#"):
        h = h[1:]
    if len(h) != 6:
        return "0x000000"
    return "0x" + h.upper()


def _escape_text(s: str) -> str:
    """
    Escape text for ffmpeg drawtext.
    """
    return (
        s.replace("\\", "\\\\")
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
    """
    Renders a 3-minute video by:
    - looping the audio to duration_sec
    - drawing text overlays per event
    - optional color swatch box for Colors template
    """
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)

    w, h = resolution

    # Background
    filter_chain = [f"color=c=#E6F5FF:s={w}x{h}:r={fps}:d={duration_sec}[bg];"]
    current = "[bg]"

    # NOTE:
    # In drawbox, use iw/ih for input width/height (NOT w/h).
    # w/h in drawbox can refer to the box itself and breaks evaluation.
    for i, e in enumerate(events):
        start = max(0.0, float(e.t_start))
        end = min(float(duration_sec), float(e.t_end))
        enable = f"between(t\\,{start:.3f}\\,{end:.3f})"

        next_label = f"[v{i}]"

        box = (
            f"{current}"
            f"drawbox=x=(iw*0.18):y=(ih*0.28):w=(iw*0.64):h=(ih*0.44):"
            f"color=black@0.35:t=fill:enable='{enable}',"
        )

        # Optional swatch box (Colors template)
        if getattr(e, "swatch_hex", None):
            sw = _hex_to_ffmpeg_color(e.swatch_hex)
            box += (
                f"drawbox=x=(iw*0.30):y=(ih*0.70):w=(iw*0.40):h=(ih*0.12):"
                f"color={sw}@0.95:t=fill:enable='{enable}',"
            )

        # Text overlay
        text = (
            box
            + "drawtext="
            + "fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:"
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

    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    if p.returncode != 0:
        raise RuntimeError(
            "FFMPEG FAILED\n\n"
            f"Return code: {p.returncode}\n\n"
            f"STDERR:\n{p.stderr}\n\n"
            f"STDOUT:\n{p.stdout}\n"
        )

    return str(out)
