from __future__ import annotations

import subprocess
from pathlib import Path
from typing import List, Tuple

from core.storyboard import StoryEvent


def _hex_to_ffmpeg_color(hex_color: str) -> str:
    """
    Convert '#RRGGBB' into '0xRRGGBB' for ffmpeg.
    """
    h = (hex_color or "").strip()
    if h.startswith("#"):
        h = h[1:]
    if len(h) != 6:
        return "0x000000"
    return "0x" + h.upper()


def render_video_ffmpeg_drawtext(
    audio_path: str,
    events: List[StoryEvent],
    output_path: str,
    duration_sec: int = 180,
    resolution: Tuple[int, int] = (1280, 720),
    fps: int = 30,
) -> str:
    """
    Renders a video by:
    - looping the audio to duration_sec
    - drawing text overlays per event
    - optional color swatch box for Colors template
    """
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)

    w, h = resolution

    # Create a simple background video source (solid light)
    filter_chain = [f"color=c=#E6F5FF:s={w}x{h}:r={fps}:d={duration_sec}[bg];"]

    # Base video label
    current = "[bg]"

    for i, e in enumerate(events):
        start = max(0.0, float(e.t_start))
        end = min(float(duration_sec), float(e.t_end))

        enable = f"between(t\\,{start:.3f}\\,{end:.3f})"
        next_label = f"[v{i}]"

        # Semi-transparent box behind text
        box = (
            f"{current}drawbox=x=(w*0.18):y=(h*0.28):w=(w*0.64):h=(h*0.44):"
            f"color=black@0.35:t=fill:enable='{enable}',"
        )

        # Optional swatch box
        if getattr(e, "swatch_hex", None):
            sw = _hex_to_ffmpeg_color(e.swatch_hex)
            box += (
                f"drawbox=x=(w*0.30):y=(h*0.70):w=(w*0.40):h=(h*0.12):"
                f"color={sw}@0.95:t=fill:enable='{enable}',"
            )

        # Draw text
        text = (
            box
            + "drawtext="
            + "font='DejaVuSans-Bold':"
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
        "ffmpeg",
        "-y",
        "-hide_banner",
        "-loglevel",
        "warning",  # <-- changed from "error" so you see real messages
        "-stream_loop",
        "-1",
        "-i",
        audio_path,
        "-filter_complex",
        filter_complex,
        "-map",
        current,  # video
        "-map",
        "0:a",  # audio
        "-t",
        str(duration_sec),
        "-r",
        str(fps),
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        "-c:a",
        "aac",
        "-shortest",
        str(out),
    ]

    # Keep logs short-ish in console
    print("FFMPEG FILTER (first 800 chars):", filter_complex[:800])
    print("FFMPEG CMD (head/tail):", cmd[:12], "...", cmd[-8:])

    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    # Always print for local debugging
    print("\n========== FFMPEG STDOUT ==========\n", p.stdout)
    print("\n========== FFMPEG STDERR ==========\n", p.stderr)

    # IMPORTANT: raise with stderr so Streamlit shows the real reason
    if p.returncode != 0:
        raise RuntimeError(
            "FFmpeg failed.\n\n"
            "STDERR:\n" + (p.stderr or "") + "\n\n"
            "STDOUT:\n" + (p.stdout or "")
        )

    return str(out)


def _escape_text(s: str) -> str:
    """
    Escape text for ffmpeg drawtext.
    """
    s = s or ""
    return (
        s.replace("\\", "\\\\")
        .replace(":", "\\:")
        .replace("'", "\\'")
    )
