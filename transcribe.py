"""Transcription with local faster-whisper (CPU, no API key)."""
import json
import os
import subprocess


def has_audio(video_path):
    """True when the input contains at least one audio stream."""
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "stream=codec_type",
         "-of", "csv=p=0", video_path],
        check=True, capture_output=True, text=True)
    return "audio" in out.stdout.split()


def extract_audio(video_path, wav_path):
    """Extract 16 kHz mono WAV — the ideal input for Whisper."""
    r = subprocess.run(
        ["ffmpeg", "-y", "-i", video_path, "-vn",
         "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1", wav_path],
        capture_output=True, text=True)
    if r.returncode != 0:
        print("ffmpeg audio extraction failed:", flush=True)
        print(r.stderr[-2000:], flush=True)
        raise SystemExit(1)


def probe(path):
    """Return (duration_seconds, width, height) via ffprobe."""
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries",
         "format=duration", "-show_entries", "stream=width,height,codec_type",
         "-of", "json", path],
        check=True, capture_output=True, text=True)
    data = json.loads(out.stdout)
    dur = float(data["format"]["duration"])
    w = h = None
    for s in data.get("streams", []):
        if s.get("codec_type") == "video":
            w, h = s.get("width"), s.get("height")
            break
    return dur, w, h


def transcribe(wav_path, out_json, model="small", lang="auto"):
    """Transcribe with faster-whisper. Returns (segments, detected_lang).

    Each segment: {"start": float, "end": float, "text": str}
    First run downloads the model (~470 MB for "small") — needs internet once.
    """
    from faster_whisper import WhisperModel

    language = None if lang in (None, "auto") else lang
    m = WhisperModel(model, device="cpu", compute_type="int8")
    segments, info = m.transcribe(
        wav_path, language=language, beam_size=5,
        vad_filter=True, vad_parameters={"min_silence_duration_ms": 500})
    print(f"Detected language: {info.language} "
          f"(prob {info.language_probability:.2f})", flush=True)
    segs = []
    for s in segments:
        text = s.text.strip()
        if text:
            segs.append({"start": round(s.start, 2),
                         "end": round(s.end, 2), "text": text})
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(segs, f, ensure_ascii=False, indent=1)
    print(f"Wrote {len(segs)} segments to {out_json}", flush=True)
    return segs, info.language
