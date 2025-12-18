from __future__ import annotations

import subprocess
from pathlib import Path
from typing import List, Tuple, Optional

from core.storyboard import StoryEvent


def _hex_to_ffmpeg_color(hex_color: str) -> str:
    h = (hex_color or "").strip()
    if h.startswith("#"):
        h = h[1:]
    if len(h) != 6:
        return "0x000000"
    return f"0x{h.upper()}"


def _escape_text(s: str) -> str:
    # Escape for ffmpeg drawtext
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
    """
    Render a simple educational video using:
      - background color
      - a soft card/box
      - big letter/number/text
      - small word below
      - optional icon (png)
      - optional color swatch
    """
    w, h = resolution
    out = str(Path(output_path))

    # Base background
    filter_parts = [f"color=c=#E6F5FF:s={w}x{h}:r={fps}:d={duration_sec}[bg]"]
    last = "[bg]"

    # layout constants (use iw/ih inside drawbox)
    box_x = "iw*0.18"
    box_y = "ih*0.22"
    box_w = "iw*0.64"
    box_h = "ih*0.56"

    for i, ev in enumerate(events):
        t0 = max(0.0, float(ev.t_start))
        t1 = max(t0, float(ev.t_end))
        enable = f"between(t\\,{t0:.3f}\\,{t1:.3f})"

        # draw card
        vtag = f"v{i}"
        part = (
            f"{last}"
            f"drawbox=x={box_x}:y={box_y}:w={box_w}:h={box_h}:color=black@0.25:t=fill:"
            f"enable='{enable}',"
        )

        # swatch (for colors)
        if ev.swatch_hex:
            sw = _hex_to_ffmpeg_color(ev.swatch_hex)
            # small square left side inside the box
            part += (
                f"drawbox=x=iw*0.22:y=ih*0.38:w=ih*0.18:h=ih*0.18:color={sw}@1.0:t=fill:"
                f"enable='{enable}',"
            )

        # icon overlay
        # We'll overlay icon near left-mid inside the box
        if ev.icon_path:
            icon_path = str(Path(ev.icon_path)).replace("\\", "/")
            # load + scale icon
            filter_parts.append(f"movie='{icon_path}',scale=ih*0.18:ih*0.18[ico{i}]")
            part += (
                f"[ico{i}]overlay=x=iw*0.22:y=ih*0.38:enable='{enable}',"
            )

        # big text
        big = _escape_text(ev.big_text)
        small = _escape_text(ev.small_text)

        part += (
            "drawtext=fontfile='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf':"
            "fontsize=ih*0.16:fontcolor=white:"
            "x=(iw-text_w)/2:y=ih*0.30:"
            f"text='{big}':enable='{enable}',"
        )

        # small text under
        if small:
            part += (
                "drawtext=fontfile='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf':"
                "fontsize=ih*0.08:fontcolor=white:"
                "x=(iw-text_w)/2:y=ih*0.52:"
                f"text='{small}':enable='{enable}'"
            )
        else:
            # remove trailing comma if no small text
            part = part.rstrip(",")

        part += f"[{vtag}]"
        filter_parts.append(part)
        last = f"[{vtag}]"

    filter_complex = ";".join(filter_parts)

    cmd = [
        "ffmpeg",
        "-y",
        "-hide_banner",
        "-loglevel", "error",
        "-stream_loop", "-1",
        "-i", str(audio_path),
        "-filter_complex", filter_complex,
        "-map", last,
        "-map", "0:a",
        "-t", str(duration_sec),
        "-r", str(fps),
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-shortest",
        out,
    ]

    p = subprocess.run(cmd, capture_output=True, text=True)
    if p.returncode != 0:
        raise RuntimeError(f"FFMPEG FAILED\n\nReturn code: {p.returncode}\n\nSTDERR:\n{p.stderr}\n")
    return out
