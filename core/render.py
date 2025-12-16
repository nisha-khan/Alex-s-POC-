from __future__ import annotations

from typing import List, Dict, Tuple
from pathlib import Path

# MoviePy 1.0.3 style imports
from moviepy.editor import (
    ImageClip,
    AudioFileClip,
    CompositeVideoClip,
    ColorClip,
)


def render_video(
    audio_path: str,
    storyboard: List[Dict],
    background_path: str | None,
    output_path: str,
    resolution: Tuple[int, int] = (1280, 720),
    fps: int = 30,
) -> str:
    """
    Given an audio file + storyboard, render an MP4 video.
    """
    output_path = str(output_path)
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    audio_clip = AudioFileClip(audio_path)
    audio_duration = float(audio_clip.duration or 0)

    if storyboard:
        last_event_time = max(float(e["t"]) + float(e.get("duration", 1.0)) for e in storyboard)
        total_duration = max(audio_duration, last_event_time + 0.5)
    else:
        total_duration = max(audio_duration, 1.0)

    w, h = resolution

    # Background: if missing, use a solid color
    bg_clip = _make_background_clip(background_path, total_duration, resolution)

    clips = [bg_clip]

    for event in storyboard:
        asset_path = event["asset"]
        start_t = float(event["t"])
        duration = float(event.get("duration", 1.0))

        if not Path(asset_path).exists():
            raise FileNotFoundError(f"Asset missing: {asset_path}")

        img_clip = (
            ImageClip(asset_path)
            .set_start(start_t)
            .set_duration(duration)
            .resize(width=int(w * 0.55))
            .set_position("center")
            .fadein(0.12)
        )

        clips.append(img_clip)

    video = CompositeVideoClip(clips, size=resolution).set_duration(total_duration).set_audio(audio_clip)

    video.write_videofile(
        output_path,
        fps=fps,
        codec="libx264",
        audio_codec="aac",
        threads=2,
        verbose=False,
        logger=None,
    )

    audio_clip.close()
    video.close()

    return output_path


def _make_background_clip(background_path: str | None, duration: float, resolution: Tuple[int, int]):
    w, h = resolution

    if background_path:
        p = Path(background_path)
        if p.exists():
            try:
                return ImageClip(str(p)).set_duration(duration).resize(newsize=resolution)
            except Exception:
                pass

    # fallback
    return ColorClip(size=(w, h), color=(20, 20, 80)).set_duration(duration)
