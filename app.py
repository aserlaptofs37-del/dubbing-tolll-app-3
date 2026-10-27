"""Streamlit UI for video-dubbing-app-v3 (optional; CLI is primary).

Run:  streamlit run app.py
Then open http://localhost:8501 in a browser on the SAME computer.
From a phone on the same Wi-Fi: run
  streamlit run app.py --server.address 0.0.0.0
and open http://<computer-IP>:8501 on the phone.
Uploading a long video through the browser is slow; for videos over a few
minutes prefer the CLI (see README).

v3 additions over v2: a multi-layer TIMELINE editor (video, voice dub,
background music with ducking, captions, text overlays — add as many
music tracks as you like), 100+ target languages, male/female voice
choice, and SRT + styled burned-in captions.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import streamlit as st

import languages
import timeline as timeline_mod
from dub import VOICES

st.set_page_config(page_title="Video Dubbing v3 — Timeline Editor",
                   page_icon="🎙️", layout="wide",
                   initial_sidebar_state="collapsed")
st.title("🎙️ Video Dubbing v3 — Free, no API keys")
st.caption("Local Whisper transcription → free translation → "
           "edge-tts / Piper / gTTS voices → timeline mix (voice + music "
           "with ducking + captions) → ffmpeg render.")
st.info("Laptop par chalta hai — phone se use karna ho to laptop par "
        "server chalao aur same Wi-Fi par phone ke browser me laptop ka "
        "IP kholo (misal http://192.168.1.5:8501). Tareeqa README me hai.")

WORKDIR = os.path.join(os.getcwd(), "dub_work_ui")
os.makedirs(WORKDIR, exist_ok=True)

LANG_OPTIONS = [c for c, _n, _e in languages.all_languages()]
LANG_LABELS = {c: f"{languages.language_name(c)} ({c}) "
                  f"[{languages.engine_for(c)}]"
               for c in LANG_OPTIONS}


def _save_upload(uploaded, name):
    path = os.path.join(WORKDIR, name)
    with open(path, "wb") as f:
        f.write(uploaded.getbuffer())
    return path


# ---------------------------------------------------------------- step 1
st.header("1️⃣ Video aur languages")
uploaded = st.file_uploader("Video file (MP4)", type=["mp4"])
col1, col2 = st.columns(2)
with col1:
    src = st.selectbox("Source language", ["auto"] + LANG_OPTIONS,
                       index=0, format_func=lambda c: (
                           "auto (pehchano)" if c == "auto"
                           else LANG_LABELS[c]))
with col2:
    tgt = st.selectbox("Target language", LANG_OPTIONS,
                       index=LANG_OPTIONS.index("ar"),
                       format_func=lambda c: LANG_LABELS[c])

# ---------------------------------------------------------------- step 2
st.header("2️⃣ Voice")
tgt_engine = languages.engine_for(tgt)
engine = st.selectbox(
    "TTS engine", ["edge", "piper", "gtts", "elevenlabs"], index=0,
    help="edge = Microsoft neural (natural, needs internet, male/female); "
         "piper = offline local voices; gtts = 100+ languages, one voice; "
         "elevenlabs = PAID ElevenLabs voices (needs your own key — "
         "see Settings below).")
if tgt_engine == "gtts" and engine == "edge":
    st.warning(f"{tgt} ke liye edge ki voice nahi hai — gtts engine chuno.")
if engine == "edge" and tgt_engine == "gtts":
    st.warning(f"{tgt} ke liye edge ki voice nahi hai — gtts engine chuno.")
gender = st.radio("Voice gender (edge engine / ElevenLabs auto-pick)",
                  ["female", "male"],
                  index=0, horizontal=True,
                  help="gtts me gender ka choice nahi hota (ek hi voice). "
                       "ElevenLabs me gender sirf auto-pick ke liye hai; "
                       "koi voice khud chuno to gender ignore hoga.")
voice = ""
if engine == "edge":
    opts = ["(default)"] + languages.edge_voices(tgt, gender)
    pick = st.selectbox(f"Voice ({gender})", opts)
    voice = "" if pick == "(default)" else pick
elif engine == "piper":
    voice = st.text_input("Piper model key (blank = default)",
                          value="", help="Misal: ar/ar_JO/kareem/medium/"
                          "ar_JO-kareem-medium. Blank ho to target language "
                          "ka default model use hoga (agar maujood ho).")
elif engine == "elevenlabs":
    st.caption("ElevenLabs voice neeche ⚙️ Settings section me chuno "
               "(key + voice list wahi hai).")
else:
    st.caption("gtts: is language ki ek hi voice hoti hai, koi choice nahi.")

# ------------------------------------------------- settings: ElevenLabs
import elevenlabs_engine as el

el_settings = el.load_settings(HERE)
el_key = el.get_api_key(HERE)
el_model = el_settings.get("model_id", el.DEFAULT_MODEL)
with st.expander("⚙️ Settings — ElevenLabs (optional, PAID)", expanded=False):
    st.markdown(
        "**ElevenLabs PAID service hai** — har dub aapke apne ElevenLabs "
        "credits kharch karta hai. Free engines (edge / piper / gtts) "
        "bina key ke chalte rahenge, un par koi farq nahi parega.")
    st.markdown(
        "Key sirf **is machine par** save hoti hai (is folder ki "
        "`elevenlabs_settings.json` file me). Ye key chat me, code me ya "
        "kisi aur ko nahi bheji jati — sirf dubbing ke waqt "
        "`api.elevenlabs.io` ko jati hai.")
    if el_key:
        st.success(f"ElevenLabs key saved hai ({el.mask_key(el_key)}).")
    else:
        st.info("Koi ElevenLabs key save nahi hai — free engines use ho "
                "rahe hain.")
    key_in = st.text_input("ElevenLabs API key", type="password",
                           key="el_key_in",
                           help="ElevenLabs account → Profile → API Keys "
                                "se banti hai. Paste karke Save dabao.")
    col_save, col_clear = st.columns(2)
    with col_save:
        if st.button("💾 Save key"):
            if key_in.strip():
                el.save_settings(HERE, api_key=key_in.strip())
                st.session_state.pop("el_voices", None)
                st.success("Key save ho gayi (is machine par hi).")
                st.rerun()
            else:
                st.warning("Pehle key paste karo.")
    with col_clear:
        if st.button("🗑️ Clear saved key"):
            el.save_settings(HERE, api_key="")
            st.session_state.pop("el_voices", None)
            st.success("Saved key clear ho gayi.")
            st.rerun()
    el_model = st.selectbox(
        "ElevenLabs model", ["eleven_multilingual_v2", "eleven_v3"],
        index=0 if el_model == "eleven_multilingual_v2" else 1,
        help="multilingual_v2: Arabic, English, German, Spanish, Russian, "
             "... (default, behtar quality/price). v3: 70+ languages, "
             "Urdu/Persian/Bengali bhi — credit cost zyada ho sakti hai.")
    if st.button("🔑 Test key (voice list dikhao)"):
        try:
            st.session_state["el_voices"] = el.list_voices(el.get_api_key(HERE))
            st.success(f"{len(st.session_state['el_voices'])} voices mili.")
        except Exception as e:
            st.error(f"Key test fail: {e}")
    el_voice = ""
    if el_key:
        voices = st.session_state.get("el_voices")
        if voices is None:
            try:
                voices = el.list_voices(el_key)
                st.session_state["el_voices"] = voices
            except Exception as e:
                st.warning(f"Voice list nahi mili ({e}) — voice ID "
                           f"manual daal sakte ho.")
                voices = []
        if voices:
            opts = ["(auto-pick by gender)"] + [
                f"{v['name']} ({v['gender'] or 'any'}, "
                f"{v['language'] or 'multi'}) — {v['voice_id']}"
                for v in voices]
            pick = st.selectbox("ElevenLabs voice", opts, key="el_voice_pick")
            if pick != "(auto-pick by gender)":
                el_voice = pick.rsplit("—", 1)[-1].strip()
        manual = st.text_input("...ya voice ID manual likho (is ka "
                               "priority sab se zyada hai)", key="el_voice_id")
        if manual.strip():
            el_voice = manual.strip()
    else:
        st.caption("Voice list dekhne ke liye pehle key save karo.")
    # Remember the Settings choices for the Run step.
    st.session_state["el_model"] = el_model
    st.session_state["el_voice"] = el_voice if el_key else ""
if engine == "elevenlabs":
    voice = st.session_state.get("el_voice", "") or ""
    el_model = st.session_state.get("el_model", el.DEFAULT_MODEL)

# ------------------------------------------------------- step 3: timeline
st.header("3️⃣ 🎬 Timeline editor")
st.caption("Har track ko on/off karo. Music tracks jitne chaho add karo — "
           "koi fixed limit nahi (user ne 11 layers ka zikr kiya tha; "
           "timeline utni hi lambi ho sakti hai jitni zaroorat ho).")
st.markdown("**Track 1 — Video:** source video (upar upload ki hui).")
st.markdown("**Track 2 — Voice dub:** upar wali voice settings se banegi.")

if "music_slots" not in st.session_state:
    st.session_state.music_slots = [0]
if st.button("➕ Add another music track"):
    st.session_state.music_slots.append(max(st.session_state.music_slots) + 1)

music_entries = []
for slot in st.session_state.music_slots:
    with st.expander(f"🎵 Music track {slot + 1}", expanded=(slot == 0)):
        mfile = st.file_uploader(f"Music file (MP3/WAV)", type=["mp3", "wav"],
                                 key=f"music_{slot}")
        mvol = st.slider("Volume", 0, 100, 15, key=f"mvol_{slot}",
                         help="Voice ke muqable me music kitna loud ho.")
        mduck = st.checkbox("Ducking (voice aate hi music halka ho)",
                            value=True, key=f"mduck_{slot}")
        menabled = st.checkbox("Enable this track", value=(slot == 0),
                               key=f"men_{slot}")
        if mfile and menabled:
            mpath = _save_upload(mfile, f"music_{slot}_{mfile.name}")
            music_entries.append((mpath, mvol / 100.0, mduck))
        elif mfile and not menabled:
            st.caption("Track disabled — mix me nahi aayega.")

with st.expander("💬 Captions track", expanded=True):
    cap_mode = st.selectbox("Captions", ["both", "srt", "burn", "off"],
                            index=0, help="both = SRT file + video me "
                            "styled captions; srt = sirf SRT file; burn = "
                            "sirf video me captions; off = band.")
    cap_style = st.selectbox("Caption style",
                             ["professional", "bold-yellow", "minimal"],
                             index=0)

with st.expander("🖼️ Text overlays track (optional)"):
    labels_file = st.file_uploader("Labels JSON for on-screen text",
                                   type=["json"])
    labels = None
    if labels_file:
        try:
            labels = json.loads(labels_file.getvalue().decode("utf-8"))
            st.caption(f"{len(labels)} label(s) loaded.")
        except Exception as e:
            st.error(f"Labels JSON samajh nahi aaya: {e}")

with st.expander("💾 Timeline save / load"):
    if st.button("Timeline JSON tayyar karo"):
        tl = timeline_mod.from_options(
            music_entries,
            cap_mode if cap_mode != "off" else "off", cap_style, labels)
        st.session_state["timeline_json"] = json.dumps(tl, indent=1)
    if st.session_state.get("timeline_json"):
        st.download_button("⬇️ Download timeline JSON",
                           data=st.session_state["timeline_json"],
                           file_name="timeline.json",
                           mime="application/json")
    tl_file = st.file_uploader("Timeline JSON load karo (optional)",
                               type=["json"], key="tl_load")
    if tl_file:
        try:
            loaded = json.loads(tl_file.getvalue().decode("utf-8"))
            errs = timeline_mod.validate(loaded)
            if errs:
                st.error("Timeline invalid:\n- " + "\n- ".join(errs))
            else:
                st.success("Timeline load ho gaya — Run dabate hi yehi "
                           "timeline use hogi.")
                st.session_state["timeline_loaded"] = loaded
        except Exception as e:
            st.error(f"Timeline load nahi hua: {e}")

# ---------------------------------------------------------------- step 4
st.header("4️⃣ Advanced (optional)")
model = st.selectbox("Whisper model", ["tiny", "base", "small"], index=2)
trans_file = st.file_uploader("Human translation JSON (optional)",
                              type=["json"])
glossary_file = st.file_uploader("Glossary JSON (optional)", type=["json"])

# ---------------------------------------------------------------- run
st.header("▶️ Run")
if uploaded and st.button("🚀 Start dubbing", type="primary"):
    errors = []
    if tgt_engine == "edge" and engine != "edge":
        pass  # edge langs work with any engine only if a voice exists
    if engine == "edge" and tgt_engine == "gtts":
        errors.append(f"{tgt} ke liye edge voice nahi hai — engine gtts chuno.")
    if engine == "piper" and not voice:
        from tts import PIPER_VOICES
        if tgt not in PIPER_VOICES:
            errors.append(f"{tgt} ke liye Piper voice nahi hai — engine "
                          f"edge ya gtts chuno, ya model key do.")
    if engine == "elevenlabs":
        if not el.get_api_key(HERE):
            errors.append("ElevenLabs ke liye key chahiye — ⚙️ Settings me "
                          "key save karo, ya free engine (edge/piper/gtts) "
                          "chuno.")
        else:
            try:
                el.check_language(
                    tgt, st.session_state.get("el_model", el.DEFAULT_MODEL))
            except Exception as e:
                errors.append(str(e))
    if errors:
        for e in errors:
            st.error(e)
        st.stop()
    src_path = _save_upload(uploaded, "input.mp4")
    trans_path = gloss_path = None
    if trans_file:
        trans_path = _save_upload(trans_file, "translation.json")
    if glossary_file:
        gloss_path = _save_upload(glossary_file, "glossary.json")
    if st.session_state.get("timeline_loaded"):
        tl = st.session_state["timeline_loaded"]
    else:
        tl = timeline_mod.from_options(
            music_entries,
            cap_mode if cap_mode != "off" else "off", cap_style, labels)
    errs = timeline_mod.validate(tl)
    if errs:
        for e in errs:
            st.error(e)
        st.stop()
    tl_path = os.path.join(WORKDIR, "timeline.json")
    with open(tl_path, "w", encoding="utf-8") as f:
        json.dump(tl, f, indent=1, ensure_ascii=False)
    out_path = os.path.join(WORKDIR, "dubbed_output.mp4")
    status = st.status("Dubbing in progress… (this takes a while)",
                       expanded=True)
    try:
        import dub as dub_cli

        class Args:
            pass
        a = Args()
        a.input = src_path
        a.tgt = tgt
        a.src = src
        a.voice = voice or None
        a.voice_gender = gender
        a.tts_engine = engine
        a.elevenlabs_voice = (
            st.session_state.get("el_voice") or None
            if engine == "elevenlabs" else None)
        a.elevenlabs_model = st.session_state.get(
            "el_model", el.DEFAULT_MODEL)
        a.glossary = gloss_path
        a.model = model
        a.workdir = WORKDIR
        a.out = out_path
        a.translation = trans_path
        a.labels = None
        a.no_overlay = False
        a.font = None
        a.clip_start = None
        a.clip_end = None
        a.music = []
        a.music_volume = 0.15
        a.no_ducking = False
        a.captions = "srt"
        a.caption_style = cap_style
        a.timeline = tl_path
        dub_cli.cmd_run(a)
        status.update(label="✅ Dubbing complete!", state="complete")
        st.success("Your dubbed video is ready.")
        st.video(out_path)
        with open(out_path, "rb") as f:
            st.download_button("⬇️ Download dubbed video (MP4)", data=f,
                               file_name="dubbed_video.mp4",
                               mime="video/mp4")
        srt_sidecar = out_path + ".srt"
        if os.path.exists(srt_sidecar):
            with open(srt_sidecar, "rb") as f:
                st.download_button("⬇️ Download subtitles (SRT)", data=f,
                                   file_name="subtitles.srt",
                                   mime="text/plain")
    except SystemExit as e:
        status.update(label="❌ Dubbing failed", state="error")
        st.error(f"Dubbing failed: {e}")
    except Exception as e:
        status.update(label="❌ Dubbing failed", state="error")
        st.error(f"Dubbing failed: {e}")
