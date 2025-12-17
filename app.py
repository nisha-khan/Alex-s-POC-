import sys
import uuid
import traceback
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.songs import get_templates, get_template_by_key
from core.storyboard import build_storyboard_for_template
from core.render import render_video_ffmpeg_drawtext

import core.render as cr

# Debug: verify which render file is actually loaded
st.write("RENDER FILE:", cr.__file__)
st.write("RENDER FUNC:", cr.render_video_ffmpeg_drawtext.__code__.co_filename)

BASE_DIR = ROOT
OUTPUTS_DIR = BASE_DIR / "outputs"
OUTPUTS_DIR.mkdir(exist_ok=True, parents=True)

DURATION_SEC = 180
TARGET_EVENTS = 72  # ~one screen change every 2.5 sec

st.set_page_config(page_title="Lothgha Visual-AI POC", layout="centered")


def main():
    st.title("Lothgha Visual-AI POC (3 Demo Songs)")
    st.write(
        "Upload an audio clip for your demo. The app will loop it to 3 minutes and generate "
        "a synchronized educational video using one of three built-in song templates:\n"
        "- ABCs\n- Numbers\n- Colors"
    )

    templates = get_templates(target_events=TARGET_EVENTS)
    template_labels = {t.title: t.key for t in templates}

    audio_file = st.file_uploader(
        "Upload audio (WAV/MP3/M4A). For POC you can upload a short clip; it will loop to 3 minutes.",
        type=["wav", "mp3", "m4a"],
    )

    choice_title = st.selectbox("Choose a demo song template", options=list(template_labels.keys()))
    choice_key = template_labels[choice_title]

    make_all = st.checkbox("Generate ALL 3 demo videos (ABC + Numbers + Colors)", value=False)

    if st.button("Generate video"):
        if not audio_file:
            st.error("Please upload an audio file first.")
            return

        # Save uploaded audio to outputs/
        suffix = Path(audio_file.name).suffix
        audio_path = OUTPUTS_DIR / f"audio_{uuid.uuid4().hex}{suffix}"
        audio_path.write_bytes(audio_file.getbuffer())

        st.write("Saved audio path:", str(audio_path))
        st.write("Exists:", audio_path.exists())

        if make_all:
            keys = ["abc", "numbers", "colors"]
        else:
            keys = [choice_key]

        for k in keys:
            template = get_template_by_key(k, target_events=TARGET_EVENTS)

            with st.spinner(f"Building storyboard for {template.title}..."):
                events = build_storyboard_for_template(
                    tokens=template.tokens,
                    duration_sec=DURATION_SEC,
                    token_colors=template.token_colors,
                )

            with st.spinner(f"Rendering {template.title} (3 minutes)..."):
                out_name = f"{k}_demo_{uuid.uuid4().hex[:8]}.mp4"
                out_path = OUTPUTS_DIR / out_name

                try:
                    final_path = render_video_ffmpeg_drawtext(
                        audio_path=str(audio_path),
                        events=events,
                        output_path=str(out_path),
                        duration_sec=DURATION_SEC,
                        resolution=(1280, 720),
                        fps=30,
                    )

                except Exception as e:
                    # ✅ IMPORTANT: use st.code so Streamlit DOES NOT mangle '*' into nothing
                    st.error("Render failed ❌")

                    st.write("Template:", template.title)
                    st.write("Output path:", str(out_path))

                    # raw error text
                    st.code(str(e), language="text")

                    # full traceback
                    st.code(traceback.format_exc(), language="text")

                    # stop the app run cleanly
                    st.stop()

            st.success(f"Generated: {template.title}")
            video_bytes = Path(final_path).read_bytes()
            st.video(video_bytes)
            st.download_button(
                label=f"Download {template.title}",
                data=video_bytes,
                file_name=out_name,
                mime="video/mp4",
            )

    st.caption("POC: template-driven (ABC, Numbers, Colors), 3 minutes each, ffmpeg-only rendering for reliability.")


if __name__ == "__main__":
    main()
