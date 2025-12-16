import sys
import uuid
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.audio import load_audio_from_upload, get_onset_times
from core.storyboard import build_storyboard, DEFAULT_LABELS
from core.visuals import ensure_background
from core.render import render_video_ffmpeg

BASE_DIR = ROOT
OUTPUTS_DIR = BASE_DIR / "outputs"
OUTPUTS_DIR.mkdir(exist_ok=True, parents=True)

ASSETS_DIR = OUTPUTS_DIR / "generated_assets" / "alphabet"
BG_PATH = OUTPUTS_DIR / "generated_assets" / "backgrounds" / "bg_default.png"

st.set_page_config(page_title="Lothgha Visual-AI POC", layout="centered")


def main():
    st.title("Lothgha Visual-AI POC")
    st.write("Upload a short ABC / nursery rhyme clip. This will generate a simple video synced to audio.")

    audio_file = st.file_uploader("Upload audio (WAV/MP3/M4A, < 60s recommended)", type=["wav", "mp3", "m4a"])
    st.selectbox("Visual theme", options=["Alphabet Animals (A, B, C)"], index=0)

    if st.button("Generate video"):
        if not audio_file:
            st.error("Upload an audio file first.")
            return

        bg = ensure_background(BG_PATH)

        with st.spinner("Loading audio..."):
            y, sr, tmp_audio_path = load_audio_from_upload(audio_file, OUTPUTS_DIR)

        with st.spinner("Detecting timing points..."):
            onset_times = get_onset_times(y, sr, max_events=len(DEFAULT_LABELS), min_gap=0.55)

        st.success(f"Detected {len(onset_times)} key timing points.")
        storyboard = build_storyboard(onset_times, DEFAULT_LABELS, ASSETS_DIR)

        st.subheader("Storyboard preview")
        st.json(storyboard)

        with st.spinner("Rendering with ffmpeg..."):
            output_filename = f"lothgha_demo_{uuid.uuid4().hex[:8]}.mp4"
            out_path = OUTPUTS_DIR / output_filename
            try:
                final_path = render_video_ffmpeg(
                    audio_path=str(tmp_audio_path),
                    storyboard=storyboard,
                    background_path=bg,
                    output_path=str(out_path),
                )
            except Exception as e:
                st.error(f"Render failed: {e}")
                return

        st.success("Video generated!")
        video_bytes = Path(final_path).read_bytes()
        st.video(video_bytes)
        st.download_button("Download video", data=video_bytes, file_name=output_filename, mime="video/mp4")


if __name__ == "__main__":
    main()

