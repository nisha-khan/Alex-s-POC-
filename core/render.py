from typing import List, Dict
from pathlib import Path

from moviepy.video.VideoClip import ImageClip
from moviepy.audio.io.AudioFileClip import AudioFileClip
from moviepy.video.compositing.CompositeVideoClip import CompositeVideoClip

from PIL import Image


def render_video(
    audio_path: str,
    storyboard: List[Dict],
    background_path: str,
    output_path: str,
    resolution=(1280, 720),
    fps: int = 30,
) -> str:
    """
    Given an audio file, storyboard, and background, render an MP4 video.
    Returns the path to the rendered video.
    """
    output_path = str(output_path)

    # Determine total duration: audio duration or last event + padding
    audio_clip = AudioFileClip(audio_path)
    audio_duration = audio_clip.duration

    if storyboard:
        last_event_time = max(event["t"] + event.get("duration", 1.0) for event in storyboard)
        total_duration = max(audio_duration, last_event_time + 0.5)
    else:
        total_duration = audio_duration

    # Background
    bg_w, bg_h = resolution
    bg_clip = _make_background_clip(background_path, total_duration, resolution)

    # Foreground image clips
    clips = [bg_clip]

    for event in storyboard:
        asset_path = event["asset"]
        start_t = float(event["t"])
        duration = float(event.get("duration", 1.0))

        img_clip = (
            ImageClip(asset_path)
            .set_start(start_t)
            .set_duration(duration)
            .resize(width=int(bg_w * 0.5))  # make it reasonably large
            .set_position("center")
        )

        clips.append(img_clip)

    video = CompositeVideoClip(clips, size=resolution).set_duration(total_duration)
    video = video.set_audio(audio_clip)

    # Ensure parent folder exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    # Write final video
    video.write_videofile(
        output_path,
        fps=fps,
        codec="libx264",
        audio_codec="aac",
        threads=4,
        verbose=False,
        logger=None,
    )

    audio_clip.close()
    video.close()

    return output_path


def _make_background_clip(background_path: str, duration: float, resolution):
    """
    Create a background clip from an image. If it fails, fall back to a solid color.
    """
    from moviepy.editor import ColorClip

    w, h = resolution

    try:
        img = Image.open(background_path)
        img_w, img_h = img.size
        # we won't use `img` directly, but ensure file exists and is valid
        bg_clip = (
            ImageClip(background_path)
            .set_duration(duration)
            .resize(newsize=resolution)
        )
        return bg_clip
    except Exception:
        # fallback to plain color
        return ColorClip(size=resolution, color=(20, 20, 80)).set_duration(duration)
