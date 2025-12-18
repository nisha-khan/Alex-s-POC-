from __future__ import annotations

import subprocess
from pathlib import Path
from typing import List, Tuple

from core.storyboard import StoryEvent


def _hex_to_ffmpeg_color(hex_color: str) -> str:
    h = hex_color.strip()
    if h.startswith("#"):
        h = h[1:]
    if len(h) != 6:
        return "0x000000"
    return "0x" + h.upper()


def _escape_text(s: str) -> str:
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
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)

    w, h = resolution

    # IMPORTANT: ffmpeg drawbox doesn't like (w*0.18) on some builds, use explicit pixel math:
    box_x = int(w * 0.18)
    box_y = int(h * 0.28)
    box_w = int(w * 0.64)
    box_h = int(h * 0.44)

    icon_size = int(h * 0.18)  # icon height
    icon_y = int(h * 0.62)

    filter_chain = [f"color=c=#E6F5FF:s={w}x{h}:r={fps}:d={duration_sec}[bg];"]
    current = "[bg]"

    for i, e in enumerate(events):
        start = max(0.0, float(e.t_start))
        end = min(float(duration_sec), float(e.t_end))
        enable = f"between(t\\,{start:.3f}\\,{end:.3f})"
        next_label = f"[v{i}]"

        chain = f"{current}"

        # background box
        chain += (
            f"drawbox=x={box_x}:y={box_y}:w={box_w}:h={box_h}:"
            f"color=black@0.35:t=fill:enable='{enable}',"
        )

        # swatch for colors template
        if e.swatch_hex:
            sw = _hex_to_ffmpeg_color(e.swatch_hex)
            sw_x = int(w * 0.30)
            sw_y = int(h * 0.70)
            sw_w = int(w * 0.40)
            sw_h = int(h * 0.12)
            chain += (
                f"drawbox=x={sw_x}:y={sw_y}:w={sw_w}:h={sw_h}:"
                f"color={sw}@0.95:t=fill:enable='{enable}',"
            )

        # ICON overlay (PNG)
        # We do it via movie=... then overlay
        # (Only if file exists at runtime)
        if e.icon_path:
            icon_path = Path(e.icon_path)
            if icon_path.exists():
                # Load icon as a stream and overlay
                # scale it to icon_size, keep aspect
                chain += (
                    f"movie='{str(icon_path)}':loop=0,scale=-1:{icon_size}[ic{i}];"
                    f"{current}overlay=x=(W-w)/2:y={icon_y}:enable='{enable}'"
                )
                # But overlay needs two inputs -> easiest is do it in a separate mini graph
                # so we skip chaining this way and do a clean branch below.
                pass

        # We'll handle icon with a separate branch safely:
        # if icon exists: [current][icon]overlay -> [tmp] then drawtext on [tmp]
        if e.icon_path and Path(e.icon_path).exists():
            filter_chain.append(
                f"movie='{str(Path(e.icon_path))}':loop=0,scale=-1:{icon_size}[ic{i}];"
                f"{current}[ic{i}]overlay=x=(W-w)/2:y={icon_y}:enable='{enable}'[tmp{i}];"
            )
            base_for_text = f"[tmp{i}]"
        else:
            base_for_text = current

        # Big title
        title = _escape_text(e.title or "")
        filter_chain.append(
            f"{base_for_text}drawtext="
            f"fontfile='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf':"
            f"fontsize={int(h*0.20)}:"
            f"fontcolor=white:"
            f"x=(w-text_w)/2:"
            f"y={int(h*0.40)}:"
            f"text='{title}':"
            f"enable='{enable}'"
            f"{next_label};"
        )

        # Subtitle (word under title)
        if e.subtitle:
            sub = _escape_text(e.subtitle)
            filter_chain.append(
                f"{next_label}drawtext="
                f"fontfile='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf':"
                f"fontsize={int(h*0.08)}:"
                f"fontcolor=white:"
                f"x=(w-text_w)/2:"
                f"y={int(h*0.55)}:"
                f"text='{sub}':"
                f"enable='{enable}'"
                f"{next_label};"
            )

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
        "-preset", "veryfast",
        "-crf", "28",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-shortest",
        str(out),
    ]

    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if p.returncode != 0:
        raise RuntimeError(f"FFMPEG FAILED\n\nSTDERR:\n{p.stderr}\n\nCMD:\n{cmd}")

    return str(out)
