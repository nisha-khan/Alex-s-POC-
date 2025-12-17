from __future__ import annotations

import subprocess
from pathlib import Path
from typing import List, Tuple, Optional

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

    # Create a simple background video source (solid light)
    # Then overlay text (and optional swatch box) with filter_complex
    filter_chain = [f"color=c=#E6F5FF:s={w}x{h}:r={fps}:d={duration_sec}[bg];"]

    # Base video label
    current = "[bg]"

    # Add one drawtext (and optional drawbox) per event
    # Keep it simple: center text + readable box behind it
    for i, e in enumerate(events):
        start = max(0.0, float(e.t_start))
        end = min(float(duration_sec), float(e.t_end))

        enable = f"between(t\\,{start:.3f}\\,{end:.3f})"

        # If swatch exists, draw a rounded-ish rectangle (drawbox) behind text
        # NOTE: drawbox doesn't do rounded corners; it's OK for POC.
        next_label = f"[v{i}]"

        # Draw a semi-transparent box behind text
        box = (
            f"{current}drawbox=x=(w*0.18):y=(h*0.28):w=(w*0.64):h=(h*0.44):"
            f"color=black@0.35:t=fill:enable='{enable}',"
        )

        # If it's a colors template event, add a big swatch box
        if e.swatch_hex:
            sw = _hex_to_ffmpeg_color(e.swatch_hex)
            # Swatch box at bottom
            box += (
                f"drawbox=x=(w*0.30):y=(h*0.70):w=(w*0.40):h=(h*0.12):"
                f"color={sw}@0.95:t=fill:enable='{enable}',"
            )

        # Draw the text
        # Use DejaVu Sans which we install via fonts-dejavu-core
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

    # ffmpeg command:
    # -stream_loop -1 loops audio indefinitely
    # -t duration_sec forces output duration
    cmd = [
        "ffmpeg", "-y",
        "-hide_banner", "-loglevel", "error",
        "-stream_loop", "-1", "-i", audio_path,
        "-filter_complex", filter_complex,
        "-map", current,          # video
        "-map", "0:a",            # audio
        "-t", str(duration_sec),
        "-r", str(fps),
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-shortest",
        str(out),
    ]

    print("FFMPEG FILTER:", filter_complex[:500])
    print("FFMPEG CMD:", cmd[:10], "...", cmd[-5:])


    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    print("\n========== FFMPEG STDOUT ==========\n", p.stdout)
    print("\n========== FFMPEG STDERR ==========\n", p.stderr)
    p.check_returncode()

    return str(out)


def _escape_text(s: str) -> str:
    """
    Escape text for ffmpeg drawtext.
    """
    # Escape backslashes, colons, apostrophes
    return (
        s.replace("\\", "\\\\")
         .replace(":", "\\:")
         .replace("'", "\\'")
    )
