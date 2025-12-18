import sys
import uuid
from pathlib import Path
import streamlit as st

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.songs import get_template_by_key
from core.storyboard import build_storyboard_for_template
from core.render import render_video_ffmpeg_drawtext

OUTPUTS_DIR = ROOT / "outputs"
OUTPUTS_DIR.mkdir(exist_ok=True, parents=True)

DURATION_SEC = 60  # client wants 1 minute

st.set_page_config(page_title="ABC Visual POC", layout="centered")

def main():
    st.title("ABC Visual POC (Timestamp-aligned)")
    st.write("Upload the ABC song audio. We render visuals aligned to your `prompts/abc_song.txt` timestamps.")

    audio_file = st.file_uploader("Upload audio (WAV/MP3/M4A).", type=["wav", "mp3", "m4a"])

    if st.button("Generate ABC video"):
        if not audio_file:
            st.error("Please upload an audio file first.")
            return

        suffix = Path(audio_file.name).suffix
        audio_path = OUTPUTS_DIR / f"audio_{uuid.uuid4().hex}{suffix}"
        audio_path.write_bytes(audio_file.getbuffer())

        template = get_template_by_key("abc")

        with st.spinner("Building storyboard from timestamps..."):
            events = build_storyboard_for_template(template.units, duration_sec=DURATION_SEC)

        with st.spinner("Rendering (ffmpeg)..."):
            out_name = f"abc_demo_{uuid.uuid4().hex[:8]}.mp4"
            out_path = OUTPUTS_DIR / out_name

            try:
                final_path = render_video_ffmpeg_drawtext(
                    audio_path=str(audio_path),
                    events=events,
                    output_path=str(out_path),
                    duration_sec=DURATION_SEC,
                    resolution=(854, 480),
                    fps=24,
                )
            except Exception as e:
                st.error(str(e))
                return

        st.success("Generated ABC video ✅")
        video_bytes = Path(final_path).read_bytes()
        st.video(video_bytes)
        st.download_button("Download ABC video", data=video_bytes, file_name=out_name, mime="video/mp4")

    st.caption("abc_song.txt format: 00:00.01|A|Apple|a.png (icons in assets/icons/)")

if __name__ == "__main__":
    main()
