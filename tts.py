"""Voice dub — three FREE engines plus one optional PAID engine.

- edge (default): Microsoft neural voices via edge-tts. Most natural
  sounding, needs normal internet (no key). NOTE: in sandboxed/proxied
  networks the streaming endpoint can stall; if edge fails, use piper
  or gtts.
- piper (offline fallback): local Piper neural voices, fully offline
  after a one-time ~63 MB model download per language. Slightly more
  robotic than Microsoft neural, but reliable everywhere.
- gtts (coverage fallback): Google Translate TTS via the gtts package.
  Single voice per language, no gender choice, less natural than edge —
  but it covers 100+ languages, including ones edge has no voice for.
- elevenlabs (OPTIONAL, PAID): higher-quality ElevenLabs voices, only
  when the user configured their own API key (env ELEVENLABS_API_KEY
  or the UI Settings file — see elevenlabs_engine.py). Every dub
  spends the user's own ElevenLabs credits. Language support is gated
  before any synthesis: eleven_multilingual_v2 covers Arabic, English,
  German, Spanish, Russian, etc.; Urdu/Persian/Bengali need
  eleven_v3 (or a free engine). Free engines stay the default.

Each segment is saved separately; finished segments are skipped on
re-runs (resume support). Failed segments are reported, not hidden.
"""
import json
import os
import subprocess

# Piper voice models (auto-downloaded on first use into voices/).
# Paths are relative to the app dir; full URLs follow the piper-voices
# HuggingFace layout: <lang>/<lang_REGION>/<name>/<quality>/<key>.onnx
PIPER_VOICES = {
    "ar": "ar/ar_JO/kareem/medium/ar_JO-kareem-medium",
    "ur": "ur/ur_PK/fasih/medium/ur_PK-fasih-medium",
    "hi": "hi/hi_IN/pratham/medium/hi_IN-pratham-medium",
    "en": "en/en_US/lessac/medium/en_US-lessac-medium",
    # No verified Piper voice for fa/es/fr/de/tr/bn in this build;
    # use --tts-engine edge for those languages.
}
PIPER_BASE = "https://huggingface.co/rhasspy/piper-voices/resolve/main"


def _dur(path):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", path],
        check=True, capture_output=True, text=True)
    try:
        return float(out.stdout.strip())
    except ValueError:
        return 0.0


def _piper_model_path(app_dir, lang=None, voice_key=None):
    """Return local (onnx, json) paths, downloading the model if missing.

    voice_key is a full piper-voices key like
    "ar/ar_JO/kareem/medium/ar_JO-kareem-medium"; if omitted, the default
    for `lang` is used.
    """
    import urllib.request
    key = voice_key or (PIPER_VOICES.get(lang) if lang else None)
    if not key:
        raise RuntimeError(
            f"No Piper voice known for '{lang}'. "
            f"Use --tts-engine edge, or pass a full model key via --voice.")
    voices_dir = os.path.join(app_dir, "voices")
    os.makedirs(voices_dir, exist_ok=True)
    onnx = os.path.join(voices_dir, key.split("/")[-1] + ".onnx")
    cfg = onnx + ".json"
    for local, remote in ((onnx, f"{PIPER_BASE}/{key}.onnx"),
                          (cfg, f"{PIPER_BASE}/{key}.onnx.json")):
        if not (os.path.exists(local) and os.path.getsize(local) > 1000):
            print(f"  downloading Piper model {os.path.basename(local)} ...",
                  flush=True)
            urllib.request.urlretrieve(remote, local)
    return onnx, cfg


def _synth_edge(text, voice, out_path):
    import asyncio
    import edge_tts

    async def go():
        await edge_tts.Communicate(text, voice).save(out_path)
    asyncio.run(go())


def _synth_piper(text, model_path, config_path, out_wav):
    """Synthesize text to a WAV file with the piper-tts Python API.

    NOTE (piper-tts 1.8 API): PiperVoice.synthesize(text) does NOT write
    a file — it returns an iterable of AudioChunk objects that must be
    consumed. Passing a file object as the 2nd argument silently does
    nothing (it is taken as syn_config) and leaves a 0-byte file, which
    then fails downstream in ffmpeg with "Invalid data found". So we
    iterate the chunks and write a real WAV ourselves.
    """
    import wave

    from piper import PiperVoice
    voice = PiperVoice.load(model_path, config_path)
    chunks = list(voice.synthesize(text))
    if not chunks:
        raise RuntimeError("Piper produced no audio chunks")
    first = chunks[0]
    total_bytes = sum(len(c.audio_int16_bytes) for c in chunks)
    if total_bytes == 0:
        raise RuntimeError("Piper produced empty audio")
    with wave.open(out_wav, "wb") as wav:
        wav.setnchannels(first.sample_channels)
        wav.setsampwidth(first.sample_width)
        wav.setframerate(first.sample_rate)
        for c in chunks:
            wav.writeframes(c.audio_int16_bytes)


def _synth_gtts(text, lang_code, out_path):
    """Synthesize text with gTTS (free, no key). lang_code is a gtts code
    (see languages.gtts_code); output is MP3."""
    from gtts import gTTS
    gTTS(text=text, lang=lang_code, slow=False).save(out_path)


def synthesize_segment(text, engine, voice, out_path, app_dir,
                       piper_model=None, retries=3, elevenlabs_key=None,
                       elevenlabs_model=None):
    """Synthesize one segment; returns duration or raises RuntimeError.

    For engine 'gtts', `voice` carries the target language code.
    For engine 'elevenlabs', `voice` is the ElevenLabs voice id
    (already resolved by synthesize_all) and elevenlabs_key must be set.
    """
    if engine == "elevenlabs":
        # Dedicated path: 401/402 (dead key / empty balance) must fail
        # immediately instead of burning retries; 429 sleeps and retries.
        import time

        from elevenlabs_engine import (ElevenLabsError, synthesize as
                                       el_synthesize)
        if not elevenlabs_key:
            raise RuntimeError(
                "ElevenLabs engine needs an API key. Add it in the app's "
                "Settings (or set ELEVENLABS_API_KEY) — free engines keep "
                "working without one.")
        last_err = None
        for attempt in range(retries):
            try:
                el_synthesize(text, voice, out_path, elevenlabs_key,
                              elevenlabs_model or "eleven_multilingual_v2")
                if (os.path.exists(out_path)
                        and os.path.getsize(out_path) > 1000):
                    return _dur(out_path)
                raise ElevenLabsError("ElevenLabs returned no usable audio")
            except ElevenLabsError as e:
                last_err = e
                if e.status in (401, 402):
                    raise RuntimeError(str(e))
                if e.status == 429 and attempt < retries - 1:
                    time.sleep(5)
                    continue
                print(f"    attempt {attempt + 1} failed: {e}", flush=True)
        raise RuntimeError(f"ElevenLabs TTS failed after {retries} "
                           f"attempts: {last_err}")
    for attempt in range(retries):
        try:
            if engine == "edge":
                _synth_edge(text, voice, out_path)
            elif engine == "gtts":
                from languages import gtts_code
                _synth_gtts(text, gtts_code(voice), out_path)
            elif engine == "piper":
                # `voice` here is a full piper-voices model key.
                onnx, cfg = piper_model or _piper_model_path(
                    app_dir, voice_key=voice)
                wav_tmp = out_path + ".tmp.wav"
                _synth_piper(text, onnx, cfg, wav_tmp)
                # Fail loudly here (not inside ffmpeg) if synthesis
                # produced nothing usable.
                if not (os.path.exists(wav_tmp)
                        and os.path.getsize(wav_tmp) > 1000):
                    raise RuntimeError(
                        "Piper synthesis produced no usable WAV")
                subprocess.run(
                    ["ffmpeg", "-y", "-v", "error", "-i", wav_tmp,
                     "-codec:a", "libmp3lame", "-q:a", "2", out_path],
                    check=True)
                os.remove(wav_tmp)
            else:
                raise ValueError(f"unknown engine {engine!r}")
            if os.path.exists(out_path) and os.path.getsize(out_path) > 1000:
                return _dur(out_path)
        except Exception as e:
            print(f"    attempt {attempt + 1} failed: {e}", flush=True)
    raise RuntimeError(f"TTS failed after {retries} attempts: {text[:60]}")


def synthesize_all(translated, engine, voice, seg_dir, log_path, app_dir,
                   piper_model=None, tgt=None, voice_gender=None,
                   elevenlabs_model=None):
    """Synthesize every segment. Returns the duration log dict.

    For engine 'elevenlabs', the API key is resolved once (env, else
    local settings file), the target language is gated against the
    chosen model BEFORE any synthesis (fail fast, no credits spent on
    an unsupported language), and the voice id is auto-picked once
    from (language, gender) when --elevenlabs-voice was not given.
    """
    os.makedirs(seg_dir, exist_ok=True)
    if engine == "elevenlabs":
        from elevenlabs_engine import (DEFAULT_MODEL, check_language,
                                       get_api_key, pick_voice)
        model = elevenlabs_model or DEFAULT_MODEL
        key = get_api_key(app_dir)
        if not key:
            raise RuntimeError(
                "ElevenLabs engine needs an API key. Add it in the app's "
                "Settings (or set ELEVENLABS_API_KEY) — free engines keep "
                "working without one.")
        check_language(tgt, model)
        if not voice:
            voice = pick_voice(key, tgt, voice_gender)
            print(f"  ElevenLabs voice auto-picked: {voice} "
                  f"(lang {tgt}, gender {voice_gender or 'any'}, "
                  f"model {model})", flush=True)
        else:
            print(f"  ElevenLabs voice: {voice} (model {model})", flush=True)
    else:
        key, model = None, None
    done = {}
    if os.path.exists(log_path):
        done = json.load(open(log_path, encoding="utf-8"))
    failed = []
    for i, seg in enumerate(translated):
        out = os.path.join(seg_dir, f"seg_{i:03d}.mp3")
        if str(i) in done and os.path.exists(out) and os.path.getsize(out) > 1000:
            continue
        try:
            d = synthesize_segment(seg["text"], engine, voice, out, app_dir,
                                   piper_model,
                                   elevenlabs_key=key,
                                   elevenlabs_model=model)
            done[str(i)] = {"dur": d,
                            "target": round(seg["end"] - seg["start"], 2)}
            json.dump(done, open(log_path, "w", encoding="utf-8"),
                      ensure_ascii=False, indent=1)
            print(f"  [{i + 1}/{len(translated)}] {d:.1f}s "
                  f"(target {seg['end'] - seg['start']:.1f}s)", flush=True)
        except RuntimeError as e:
            print(f"  SEGMENT {i} FAILED: {e}", flush=True)
            failed.append(i)
    print(f"DONE: {len(done)}/{len(translated)} segments synthesized; "
          f"failed: {failed}", flush=True)
    if failed and len(failed) > max(1, len(translated) // 10):
        raise RuntimeError(f"Too many TTS failures ({len(failed)}); aborting.")
    return done
