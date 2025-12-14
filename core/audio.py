from pathlib import Path
from typing import Tuple, List

import librosa
import numpy as np


def load_audio_from_upload(uploaded_file, outputs_dir: Path) -> Tuple[np.ndarray, int, Path]:
    """
    Save the uploaded file to disk, then load it with librosa.
    Returns (waveform, sample_rate, temp_file_path).
    """
    outputs_dir.mkdir(exist_ok=True, parents=True)
    tmp_path = outputs_dir / f"tmp_{uploaded_file.name}"
    with open(tmp_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    # Load with librosa in mono
    y, sr = librosa.load(tmp_path, sr=None, mono=True)

    return y, sr, tmp_path


def get_onset_times(y: np.ndarray, sr: int, max_events: int = 3) -> List[float]:
    """
    Detect onset times (moments where sound events start).
    For this POC, we only need a few (e.g., for A, B, C).
    If detection fails or is too noisy, fall back to uniform spacing.
    """
    # Use librosa's onset detection
    onset_frames = librosa.onset.onset_detect(y=y, sr=sr, backtrack=True)
    onset_times = librosa.frames_to_time(onset_frames, sr=sr)

    # Basic sanity check
    onset_times = sorted(float(t) for t in onset_times)

    # Filter to unique and positive
    onset_times = [t for t in onset_times if t >= 0]

    # If we have more onsets than needed, take the first ones
    if len(onset_times) >= max_events:
        return onset_times[:max_events]

    # Not enough onsets? Fallback to uniform sampling across duration
    duration = len(y) / float(sr)
    if duration <= 0:
        return []

    if len(onset_times) == 0:
        # evenly spaced across the clip
        step = duration / (max_events + 1)
        fallback = [step * (i + 1) for i in range(max_events)]
        return fallback

    # If we have 1–2 onsets but need more, pad with extra times
    needed = max_events - len(onset_times)
    if needed > 0:
        last_time = onset_times[-1]
        remaining_duration = max(duration - last_time, 0.5)
        step = remaining_duration / (needed + 1)
        extra_times = [last_time + step * (i + 1) for i in range(needed)]
        onset_times.extend(extra_times)

    return onset_times[:max_events]
