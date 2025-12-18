# app.py
import sys
import uuid
from pathlib import Path
import streamlit as st

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.prompt_parser import parse_prompt_lines
from core.storyboard import build_storyboard_from_units
from core.render import render_video_ffmpeg

OUTPUTS_DIR = ROOT / "outputs"
OUTPUTS_DIR.mkdir(exist_ok=True, parents=True)

PROMPTS_DIR = ROOT / "prompts"
ABC_PROMPT_FILE = PROMPTS_DIR / "abc_song.txt"

DURATION_SEC = 60

st.set_page_config(page_title="ABC Visual POC", layout="centered")


def load_lines(p: Path) -> list[str]:
    if not p.exists():
        raise FileNotFoundError(f"Missing prompt file: {p}")
    return [l.strip() for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]


def main():
    st.title("ABC Visual POC (Timestamp Aligned)")
    st.write("Uses **prompts/abc_song.txt timestamps** to align visuals to the song (1 minute).")

    audio_file = st.file_uploader("Upload audio (WAV/MP3/M4A).", type=["wav", "mp3", "m4a"])

    if st.button("Generate ABC video"):
        if not audio_file:
            st.error("Please upload an audio file first.")
            return

        suffix = Path(audio_file.name).suffix
        audio_path = OUTPUTS_DIR / f"audio_{uuid.uuid4().hex}{suffix}"
        audio_path.write_bytes(audio_file.getbuffer())

        try:
            lines = load_lines(ABC_PROMPT_FILE)
            units = parse_prompt_lines(lines)  # expects timestamped lines
            events = build_storyboard_from_units(units, duration_sec=DURATION_SEC)
        except Exception as e:
            st.error(f"Prompt/storyboard error: {e}")
            return

        out_name = f"abc_demo_{uuid.uuid4().hex[:8]}.mp4"
        out_path = OUTPUTS_DIR / out_name

        try:
            final_path = render_video_ffmpeg(
                audio_path=str(audio_path),
                events=events,
                output_path=str(out_path),
                duration_sec=DURATION_SEC,
                resolution=(854, 480),
                fps=15,
            )
        except Exception as e:
            st.error(str(e))
            return

        st.success("Generated ABC video")
        video_bytes = Path(final_path).read_bytes()
        st.video(video_bytes)
        st.download_button("Download ABC video", data=video_bytes, file_name=out_name, mime="video/mp4")

    st.caption("Format for prompts/abc_song.txt: MM:SS.xx|A|Apple|a.png  (icon must exist in assets/icons/)")

if __name__ == "__main__":
    main()
