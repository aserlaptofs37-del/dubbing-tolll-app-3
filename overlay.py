"""Merge dubbed audio into video, with optional translated-text overlays.

- Without labels: video stream is COPIED untouched (fast, Full HD preserved).
- With labels: the original banner is covered with a solid box and the
  translated text PNG is overlaid, so the video must be re-encoded
  (1080p kept, CRF 18, faststart MP4 for mobile download).

Labels file schema (JSON array, coordinates in INPUT video pixels):
  [{"name": "buffaloes", "text": "الجواميس البرية",
    "t0": 78.1, "t1": 80.2,
    "bar": {"x": 0, "y": 880, "w": 1150, "h": 190, "color": "0xCD0000"},
    "font_size": 88}]
Channel logos/branding are never touched: only the bars listed here are
covered, and only for the listed time ranges.
"""
import json
import os
import subprocess

from render import render_labels


def _run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print(r.stderr[-3000:])
        raise SystemExit(1)


def merge_audio_only(video, dubbed_wav, out_mp4):
    """Copy video stream, replace audio with the dub. Faststart MP4."""
    print("Merging (video stream copied, no re-encode) ...", flush=True)
    _run(["ffmpeg", "-y", "-i", video, "-i", dubbed_wav,
          "-c:v", "copy", "-map", "0:v:0", "-map", "1:a:0",
          "-shortest", "-movflags", "+faststart", out_mp4])
    return out_mp4


def merge_with_overlays(video, dubbed_wav, out_mp4, labels, lang,
                        texts_dir, font_path=None):
    """Cover listed bars + overlay translated text, re-encode, faststart.

    Kept for backward compatibility; delegates to merge_final.
    """
    return merge_final(video, dubbed_wav, out_mp4, labels, lang,
                       texts_dir, None, font_path)


def merge_final(video, audio_wav, out_mp4, labels=None, lang=None,
                texts_dir=None, ass_path=None, font_path=None):
    """Final render: optional label overlays + optional burned captions.

    With neither labels nor captions this is merge_audio_only (stream
    copy, fast). Otherwise the video is re-encoded (1080p kept, CRF 18,
    faststart MP4). Caption ASS is applied after labels so captions sit
    on top. Returns out_mp4.
    """
    if not labels and not ass_path:
        return merge_audio_only(video, audio_wav, out_mp4)
    inputs = ["-i", video, "-i", audio_wav]
    filters = []
    last = "0:v"
    if labels:
        manifest = render_labels(labels, lang, texts_dir, font_path)
        for i, lab in enumerate(labels):
            bar = lab["bar"]
            bx, by, bw, bh = bar["x"], bar["y"], bar["w"], bar["h"]
            color = bar.get("color", "0xCD0000")
            t0, t1 = lab["t0"], lab["t1"]
            filters.append(
                f"[{last}]drawbox=x={bx}:y={by}:w={bw}:h={bh}:color={color}"
                f":t=fill:enable='between(t,{t0},{t1})'[v{i}]")
            tw, th = manifest[lab["name"]]["w"], manifest[lab["name"]]["h"]
            tx = bx + (bw - tw) // 2
            ty = by + (bh - th) // 2
            png = os.path.join(texts_dir, lab["name"] + ".png")
            inputs += ["-i", png]
            vidx = 2 + i
            filters.append(
                f"[v{i}][{vidx}:v]overlay=x={tx}:y={ty}"
                f":enable='between(t,{t0},{t1})'[v{i}o]")
            last = f"v{i}o"
    if ass_path:
        esc = (ass_path.replace("\\", "\\\\").replace("'", "\\'")
               .replace(":", "\\:"))
        filters.append(f"[{last}]subtitles='{esc}'[vsub]")
        last = "vsub"
    print(f"Re-encoding (labels={len(labels or [])}, "
          f"captions={'yes' if ass_path else 'no'}) ...", flush=True)
    _run(["ffmpeg", "-y"] + inputs +
         ["-filter_complex", ";".join(filters),
          "-map", f"[{last}]", "-map", "1:a:0",
          "-c:v", "libx264", "-crf", "18", "-preset", "medium",
          "-pix_fmt", "yuv420p",
          "-c:a", "aac", "-b:a", "160k",
          "-shortest", "-movflags", "+faststart", out_mp4])
    return out_mp4
