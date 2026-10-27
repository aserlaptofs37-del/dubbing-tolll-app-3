#!/usr/bin/env python3
"""video-dubbing-app-v3 — FREE, key-free video dubbing.

Pipeline: local faster-whisper transcription -> free machine translation
(or an imported human-checked translation, optionally with a --glossary
word-fix file) -> edge-tts neural voices (default, male/female choice),
offline Piper voices (--tts-engine piper), or gTTS coverage voices
(--tts-engine gtts, 100+ languages) -> ffmpeg timeline sync -> optional
background-music track with ducking -> optional SRT subtitles and/or
styled burned-in captions -> optional translated on-screen text overlays
-> 1080p high-bitrate faststart MP4.

Timeline: the render is driven by a track list (video, voice dub,
music, captions, overlays) — see timeline.py. The Streamlit UI edits it
visually; the CLI takes it with --timeline or builds it from flags.

Usage:
  # Full dub, audio only (video stream copied, fastest):
  python dub.py run --input video.mp4 --tgt ar --out dubbed.mp4

  # Dub + background music (ducked under the voice) + captions:
  python dub.py run --input video.mp4 --tgt ar --music bed.mp3 \\
      --captions both --out dubbed.mp4

  # Male voice instead of the female default:
  python dub.py run --input video.mp4 --tgt ar --voice-gender male \\
      --out dubbed.mp4

  # OPTIONAL paid ElevenLabs voices (needs your own key in Settings
  # or ELEVENLABS_API_KEY — never pass the key as a CLI argument):
  python dub.py run --input video.mp4 --tgt ar \\
      --tts-engine elevenlabs --elevenlabs-voice <voice-id> --out dubbed.mp4
  python dub.py --list-elevenlabs-voices   # needs a configured key

  # Full dub + translated on-screen text (see labels.json format in README):
  python dub.py run --input video.mp4 --tgt ar --labels labels.json --out dubbed.mp4

  # Use a human-checked translation instead of machine translation:
  python dub.py run --input video.mp4 --tgt ar --translation my_ar.json --out dubbed.mp4

  # Drive the render from a saved timeline JSON (UI export):
  python dub.py run --input video.mp4 --tgt ar --timeline tl.json --out dubbed.mp4

  # Only scan for banner windows (helper for writing labels.json):
  python dub.py detect --input video.mp4 --out windows.json

  # Verify a finished file:
  python dub.py verify --input dubbed.mp4 --reference video.mp4

Options: --src (auto|ur|hi|en|ar...), --voice (edge-tts voice id),
--voice-gender (male|female), --model (tiny|base|small|medium),
--workdir, --font, --clip-start/--clip-end
(for testing on a slice of the video), --no-overlay (force audio-only
even if --labels is given; SRT captions are still written).
"""
import argparse
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

# Default edge-tts neural voices per target language (no key, free).
# Picked for successful synthesis + Microsoft neural quality; swap with
# --voice any time (list voices: edge-tts --list-voices).
VOICES = {
    "ar": "ar-EG-SalmaNeural",   # Arabic, female (Egyptian)
    "ur": "ur-PK-UzmaNeural",   # Urdu, female (Pakistani)
    "hi": "hi-IN-SwaraNeural",  # Hindi, female (Indian)
    "en": "en-US-AriaNeural",   # English, female (US)
    "fa": "fa-IR-DilaraNeural",  # Persian, female
    "es": "es-ES-ElviraNeural",
    "fr": "fr-FR-DeniseNeural",
    "de": "de-DE-KatjaNeural",
    "tr": "tr-TR-EmelNeural",
    "bn": "bn-IN-TanishaaNeural",
}


def _clip_arg(value, name):
    if value is None:
        return None
    try:
        return float(value)
    except ValueError:
        raise SystemExit(f"--{name} must be seconds, got {value!r}")


def resolve_voice(tgt, engine, voice, gender):
    """Pick the TTS voice for a run.

    Explicit --voice always wins. Otherwise: edge -> catalog default for
    (language, gender) with the old female defaults as fallback; piper ->
    the known Piper model key (or fail with a clear message); gtts ->
    the target language code itself (gtts has one voice per language).
    """
    if voice:
        return voice
    if engine == "elevenlabs":
        # Voice id may stay None: synthesize_all auto-picks from
        # (language, gender) via the ElevenLabs catalog. Language
        # support is gated there too, before any synthesis.
        return None
    if engine == "edge":
        from languages import default_voice, edge_voices
        v = default_voice(tgt, gender)
        if v:
            return v
        v = VOICES.get(tgt)
        if v:
            return v
        known = edge_voices(tgt)
        raise SystemExit(
            f"No default edge voice for '{tgt}'"
            + (f" (known voices: {', '.join(known)})" if known else "")
            + "; pass --voice (list: edge-tts --list-voices)")
    if engine == "gtts":
        from languages import engine_for
        if engine_for(tgt) is None:
            raise SystemExit(f"Language '{tgt}' is not in the v3 catalog; "
                             f"see LANGUAGES.md")
        return tgt
    from tts import PIPER_VOICES
    v = PIPER_VOICES.get(tgt)
    if not v:
        raise SystemExit(
            f"No Piper voice for '{tgt}'; use --tts-engine edge or gtts, "
            f"or pass a full model key via --voice.")
    return v


def cmd_run(args):
    from transcribe import extract_audio, has_audio, probe, transcribe
    from translate import load_translation_json, translate_segments
    from tts import synthesize_all
    from mix import build_dubbed_track
    from overlay import merge_audio_only, merge_with_overlays
    from verify import verify as verify_out

    inp = args.input
    if not os.path.exists(inp):
        raise SystemExit(f"Input not found: {inp}")
    workdir = args.workdir or os.path.join(
        os.getcwd(), os.path.splitext(os.path.basename(inp))[0] + "_dub_work")
    os.makedirs(workdir, exist_ok=True)
    seg_dir = os.path.join(workdir, "segments")
    texts_dir = os.path.join(workdir, "texts")

    # --- Timeline first (fail fast on bad music files/volumes). ---
    from timeline import (captions_track, from_options, music_tracks,
                          overlays_track, validate)
    if args.timeline:
        timeline = json.load(open(args.timeline, encoding="utf-8"))
        errs = validate(timeline)
        if errs:
            raise SystemExit("Timeline invalid:\n- " + "\n- ".join(errs))
        print(f"Timeline loaded from {args.timeline}", flush=True)
        if args.music or args.labels or args.captions != "srt":
            print("NOTE: --timeline overrides --music/--labels/--captions "
                  "flags.", flush=True)
    else:
        music_files = [(m, args.music_volume, not args.no_ducking)
                       for m in (args.music or [])]
        labels_flag = None
        if args.labels and not args.no_overlay:
            labels_flag = json.load(open(args.labels, encoding="utf-8"))
        timeline = from_options(music_files, args.captions,
                                args.caption_style, labels_flag)
        errs = validate(timeline)
        if errs:
            raise SystemExit("Timeline invalid:\n- " + "\n- ".join(errs))
    music_list = music_tracks(timeline)
    cap = captions_track(timeline)
    cap_mode = cap["mode"] if cap else "off"
    cap_style = cap["style"] if cap else "professional"
    ov = overlays_track(timeline)
    labels = ov["labels"] if (ov and not args.no_overlay) else None
    if labels:
        print(f"Overlay: {len(labels)} label(s)", flush=True)

    clip_start = _clip_arg(args.clip_start, "clip-start")
    clip_end = _clip_arg(args.clip_end, "clip-end")
    src_video = inp
    if clip_start is not None or clip_end is not None:
        cs = clip_start or 0.0
        dur = (clip_end - cs) if clip_end is not None else None
        clipped = os.path.join(workdir, "clip.mp4")
        use_labels = bool(args.labels and not args.no_overlay)
        if use_labels:
            # Accurate cut (re-encode) so label times line up exactly.
            dur_arg = f"-t {dur}" if dur else ""
            print(f"Cutting test clip (accurate, for labels) -> {clipped} ...",
                  flush=True)
            subprocess.run(
                ["ffmpeg", "-y", "-v", "error", "-i", inp,
                 "-ss", str(cs)] + (["-t", str(dur)] if dur else []) +
                ["-c:v", "libx264", "-crf", "18", "-preset", "fast",
                 "-c:a", "aac", clipped],
                check=True)
        else:
            # Fast keyframe cut; everything stays clip-relative internally,
            # so transcription/translation/dub all still line up.
            print(f"Cutting test clip (fast) -> {clipped} ...", flush=True)
            cmd = ["ffmpeg", "-y", "-v", "error", "-ss", str(cs), "-i", inp]
            if dur:
                cmd += ["-t", str(dur)]
            cmd += ["-c", "copy", clipped]
            subprocess.run(cmd, check=True)
        src_video = clipped
        print(f"NOTE: with --clip-start, times in --labels (if any) must be "
              f"clip-relative, i.e. original time minus {cs}.", flush=True)

    total_dur, w, h = probe(src_video)
    print(f"Source: {total_dur:.1f}s, {w}x{h}", flush=True)
    if not has_audio(src_video):
        raise SystemExit(
            "Input video has NO audio stream, so there is nothing to dub.\n"
            "If you downloaded it with yt-dlp, get a format with audio, e.g.:\n"
            "  yt-dlp -f 'bestvideo+bestaudio/best' <url>")

    wav = os.path.join(workdir, "original.wav")
    print("Extracting audio ...", flush=True)
    extract_audio(src_video, wav)

    seg_json = os.path.join(workdir, "segments.json")
    print("Transcribing (local faster-whisper, CPU) ...", flush=True)
    segments, detected = transcribe(wav, seg_json, model=args.model,
                                    lang=args.src)
    src_lang = args.src if args.src not in (None, "auto") else detected

    trans_json = os.path.join(workdir, "translated.json")
    glossary = None
    if args.glossary:
        glossary = json.load(open(args.glossary, encoding="utf-8"))
        print(f"Glossary: {len(glossary)} replacement(s)", flush=True)
    if args.translation:
        print(f"Loading human translation {args.translation} ...", flush=True)
        translated = load_translation_json(args.translation, segments)
        json.dump(translated, open(trans_json, "w", encoding="utf-8"),
                  ensure_ascii=False, indent=1)
    else:
        print(f"Translating {src_lang} -> {args.tgt} "
              f"(free machine translation) ...", flush=True)
        translated = translate_segments(segments, src_lang, args.tgt,
                                        trans_json, glossary)

    # UI/CLI may carry the ElevenLabs voice id in its own field.
    if (args.tts_engine == "elevenlabs"
            and getattr(args, "elevenlabs_voice", None)
            and not args.voice):
        args.voice = args.elevenlabs_voice
    voice = resolve_voice(args.tgt, args.tts_engine, args.voice,
                          args.voice_gender)
    print(f"TTS engine: {args.tts_engine}, voice: {voice}", flush=True)
    log_path = os.path.join(workdir, "tts_log.json")
    tts_log = synthesize_all(
        translated, args.tts_engine, voice, seg_dir, log_path, HERE,
        tgt=args.tgt, voice_gender=args.voice_gender,
        elevenlabs_model=getattr(args, "elevenlabs_model", None))

    dubbed_wav = os.path.join(workdir, "dubbed.wav")
    build_dubbed_track(translated, tts_log, seg_dir, total_dur, dubbed_wav)

    # --- Final mix: voice dub + background-music bus (ducked). ---
    from mix import mix_final_track
    final_wav = os.path.join(workdir, "final_mix.wav")
    if music_list:
        mix_final_track(dubbed_wav, music_list, total_dur, final_wav,
                        workdir)
    else:
        final_wav = dubbed_wav

    # --- Captions: SRT file and/or burned-in styled captions. ---
    srt_path = None
    ass_path = None
    if cap_mode in ("srt", "both"):
        from captions import write_srt
        srt_path = os.path.join(workdir, "captions.srt")
        n = write_srt(translated, srt_path)
        print(f"Captions SRT: {n} cue(s) -> {srt_path}", flush=True)
    if cap_mode in ("burn", "both"):
        if args.no_overlay:
            print("NOTE: --no-overlay disables burned-in captions; "
                  "SRT still written.", flush=True)
        else:
            from captions import write_ass
            ass_path = os.path.join(workdir, "captions.ass")
            n = write_ass(translated, ass_path, args.tgt, cap_style)
            print(f"Captions burned in ({cap_style} style): {n} cue(s)",
                  flush=True)

    from overlay import merge_final
    out = merge_final(src_video, final_wav, args.out, labels, args.tgt,
                      texts_dir, ass_path, args.font)

    print(f"\nDone: {out}", flush=True)
    if srt_path:
        import shutil
        sidecar = args.out + ".srt"
        shutil.copyfile(srt_path, sidecar)
        print(f"SRT sidecar: {sidecar}", flush=True)
    frame_at = None
    if labels:
        frame_at = labels[0]["t0"] + 0.3
    verify_out(out, reference=src_video, frame_at=frame_at,
               frame_out=(os.path.join(workdir, "overlay_check.jpg")
                          if frame_at else None))
    return out


def cmd_detect(args):
    from detect import detect_banners
    detect_banners(args.input, args.out, fps=args.fps)


def cmd_verify(args):
    from verify import verify as verify_out
    verify_out(args.input, reference=args.reference,
               frame_at=args.frame_at, frame_out=args.frame_out)


def cmd_list_elevenlabs_voices():
    """Print the account's ElevenLabs voice catalog (needs a key).

    Key resolution: env ELEVENLABS_API_KEY, else the local settings
    file. The key itself is never printed.
    """
    from elevenlabs_engine import (ElevenLabsError, get_api_key,
                                   list_voices, mask_key)
    key = get_api_key(HERE)
    if not key:
        raise SystemExit(
            "No ElevenLabs key configured. Add it in the app's Settings "
            "(or set ELEVENLABS_API_KEY) — free engines keep working "
            "without one.")
    try:
        voices = list_voices(key)
    except ElevenLabsError as e:
        raise SystemExit(f"ElevenLabs: {e}")
    print(f"ElevenLabs voices (key {mask_key(key)}): {len(voices)}",
          flush=True)
    print(f"{'voice_id':<24} {'name':<28} {'gender':<10} "
          f"{'lang':<6} category", flush=True)
    for v in voices:
        print(f"{v['voice_id']:<24} {v['name']:<28} "
              f"{v['gender']:<10} {v['language']:<6} {v['category']}",
              flush=True)


def main():
    p = argparse.ArgumentParser(description="FREE key-free video dubbing "
                                "(ElevenLabs voices optional, paid)")
    p.add_argument("--list-elevenlabs-voices", action="store_true",
                   help="list your ElevenLabs voices (needs a configured "
                        "key) and exit; no subcommand needed")
    sub = p.add_subparsers(dest="cmd", required=False)

    r = sub.add_parser("run", help="run the full dubbing pipeline")
    r.add_argument("--input", required=True)
    r.add_argument("--tgt", required=True,
                   help="target language code: ar, ur, hi, en, fa, ...")
    r.add_argument("--src", default="auto",
                   help="source language code or auto (default)")
    r.add_argument("--voice", default=None,
                   help="edge voice id, or full piper model key for piper")
    r.add_argument("--voice-gender", default=None,
                   choices=["male", "female"],
                   help="pick a male/female voice for the target language "
                        "(edge engine; ignored if --voice is given)")
    r.add_argument("--tts-engine", default="edge",
                   choices=["edge", "piper", "gtts", "elevenlabs"],
                   help="edge = Microsoft neural (natural, needs internet); "
                        "piper = offline local voices; "
                        "gtts = Google TTS, 100+ languages, single voice; "
                        "elevenlabs = paid ElevenLabs voices (needs your "
                        "own key in Settings or ELEVENLABS_API_KEY)")
    r.add_argument("--elevenlabs-voice", default=None,
                   help="ElevenLabs voice id (list: dub.py "
                        "--list-elevenlabs-voices). Blank = auto-pick from "
                        "language + --voice-gender.")
    r.add_argument("--elevenlabs-model", default="eleven_multilingual_v2",
                   help="ElevenLabs model: eleven_multilingual_v2 (default; "
                        "Arabic, English, German, Spanish, Russian, ...) or "
                        "eleven_v3 (70+ languages incl. Urdu/Persian/"
                        "Bengali; higher credit cost)")
    r.add_argument("--music", action="append", default=[],
                   help="background music file (repeatable; each loops to "
                        "the video length and is ducked under the voice)")
    r.add_argument("--music-volume", type=float, default=0.15,
                   help="music volume 0.0-1.0 (default 0.15)")
    r.add_argument("--no-ducking", action="store_true",
                   help="disable voice ducking for music tracks")
    r.add_argument("--captions", default="srt",
                   choices=["none", "srt", "burn", "both"],
                   help="subtitle mode: srt file, burned-in styled "
                        "captions, both, or none (default srt)")
    r.add_argument("--caption-style", default="professional",
                   choices=["professional", "bold-yellow", "minimal"],
                   help="style for burned-in captions")
    r.add_argument("--timeline", default=None,
                   help="timeline JSON file (overrides --music/--labels/"
                        "--captions; see timeline.py)")
    r.add_argument("--glossary", default=None,
                   help="JSON word replacements applied after translation")
    r.add_argument("--model", default="small",
                   help="whisper model: tiny|base|small|medium (default small)")
    r.add_argument("--workdir", default=None)
    r.add_argument("--out", required=True, help="output MP4 path")
    r.add_argument("--translation", default=None,
                   help="import a human-checked translation JSON")
    r.add_argument("--labels", default=None,
                   help="labels JSON for on-screen text translation")
    r.add_argument("--no-overlay", action="store_true")
    r.add_argument("--font", default=None)
    r.add_argument("--clip-start", default=None)
    r.add_argument("--clip-end", default=None)
    r.set_defaults(fn=cmd_run)

    d = sub.add_parser("detect", help="scan for banner windows")
    d.add_argument("--input", required=True)
    d.add_argument("--out", required=True)
    d.add_argument("--fps", type=int, default=4)
    d.set_defaults(fn=cmd_detect)

    v = sub.add_parser("verify", help="verify a finished dub")
    v.add_argument("--input", required=True)
    v.add_argument("--reference", default=None)
    v.add_argument("--frame-at", type=float, default=None)
    v.add_argument("--frame-out", default=None)
    v.set_defaults(fn=cmd_verify)

    args = p.parse_args()
    if args.list_elevenlabs_voices:
        cmd_list_elevenlabs_voices()
        return
    if not args.cmd:
        p.error("a subcommand (run, detect, verify) is required, or use "
                "--list-elevenlabs-voices")
    # CLI --elevenlabs-voice feeds the generic --voice slot for the
    # elevenlabs engine (keeps tts.py's interface unchanged).
    if args.cmd == "run" and args.tts_engine == "elevenlabs":
        if args.elevenlabs_voice and not args.voice:
            args.voice = args.elevenlabs_voice
    args.fn(args)


if __name__ == "__main__":
    main()
