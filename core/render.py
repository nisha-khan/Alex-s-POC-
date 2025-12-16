from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Dict, List, Tuple


def render_video_ffmpeg(
    audio_path: str,
    storyboard: List[Dict],
    background_path: str,
    output_path: str,
    resolution: Tuple[int, int] = (1280, 720),
    fps: int = 30,
) -> str:
    """
    Render MP4 using ffmpeg only:
    - background image looped
    - overlays PNGs at specified times
    - adds audio
    """
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)

    w, h = resolution

    # Inputs: bg + audio + each overlay PNG
    cmd = ["ffmpeg", "-y"]

    # Background as a looped image
    cmd += ["-loop", "1", "-i", background_path]

    # Audio
    cmd += ["-i", audio_path]

    # Overlay images
    for e in storyboard:
        cmd += ["-i", e["asset"]]

    # Build filter graph
    # Start with background scaled
    filter_lines = [f"[0:v]scale={w}:{h},fps={fps}[base];"]
    last = "[base]"

    # Each overlay: enable between t and t+duration
    # Inputs: bg=0, audio=1, overlays start at index 2
    for idx, e in enumerate(storyboard):
        t = float(e["t"])
        d = float(e.get("duration", 1.2))
        overlay_in = f"[{idx+2}:v]"
        out_label = f"[v{idx}]"

        # Scale overlay to width ~55% of frame
        filter_lines.append(
            f"{overlay_in}scale=iw*0.55:-1[ol{idx}];"
        )
        filter_lines.append(
            f"{last}[ol{idx}]overlay=(W-w)/2:(H-h)/2:enable='between(t,{t:.3f},{(t+d):.3f})'{out_label};"
        )
        last = out_label

    filter_complex = "".join(filter_lines).rstrip(";")

    cmd += ["-filter_complex", filter_complex]

    # Map video + audio
    cmd += ["-map", last, "-map", "1:a"]

    # Output encoding
    cmd += [
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-shortest",
        str(out),
    ]

    subprocess.run(cmd, check=True)
    return str(out)
