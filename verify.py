"""Verify a dubbed output: duration, audio, faststart, overlay frame."""
import json
import subprocess


def _probe(path):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries",
         "format=duration,size", "-show_entries",
         "stream=codec_type,codec_name,width,height",
         "-of", "json", path],
        check=True, capture_output=True, text=True)
    return json.loads(out.stdout)


def _faststart(path):
    with open(path, "rb") as f:
        head = f.read(64 * 1024 * 1024)
    moov, mdat = head.find(b"moov"), head.find(b"mdat")
    return moov != -1 and mdat != -1 and moov < mdat


def _audio_level(path, at, dur=10):
    out = subprocess.run(
        ["ffmpeg", "-ss", str(at), "-i", path, "-t", str(dur),
         "-af", "volumedetect", "-vn", "-sn", "-dn", "-f", "null",
         "/dev/null"],
        capture_output=True, text=True)
    mean = None
    for line in out.stderr.splitlines():
        if "mean_volume" in line:
            mean = float(line.split("mean_volume:")[1].split("dB")[0])
    return mean


def verify(output, reference=None, frame_at=None, frame_out=None):
    """Run checks; returns a dict. Raises SystemExit on hard failures."""
    info = _probe(output)
    dur = float(info["format"]["duration"])
    size = int(info["format"]["size"])
    streams = {s["codec_type"]: s for s in info["streams"]}
    video = streams.get("video", {})
    audio = streams.get("audio")
    print(f"Output: {dur:.1f}s, {size / 1e6:.1f} MB, "
          f"{video.get('width')}x{video.get('height')} "
          f"{video.get('codec_name')}, audio={audio['codec_name'] if audio else None}",
          flush=True)
    ok = True
    if reference:
        ref_dur = float(_probe(reference)["format"]["duration"])
        match = abs(dur - ref_dur) <= 1.0
        print(f"Duration vs reference ({ref_dur:.1f}s): "
              f"{'OK' if match else 'MISMATCH'}", flush=True)
        ok = ok and match
    if not audio:
        print("FAIL: no audio stream", flush=True)
        ok = False
    else:
        mid = dur / 2
        level = _audio_level(output, mid)
        audible = level is not None and level > -60
        print(f"Audio level at {mid:.0f}s: {level} dB "
              f"({'OK, audible' if audible else 'FAIL, silent/undetected'})",
              flush=True)
        ok = ok and audible
    fs = _faststart(output)
    print(f"Faststart (mobile streaming): {'OK' if fs else 'FAIL'}", flush=True)
    ok = ok and fs
    if frame_at is not None and frame_out:
        subprocess.run(
            ["ffmpeg", "-y", "-v", "error", "-ss", str(frame_at),
             "-i", output, "-frames:v", "1", "-q:v", "2", frame_out],
            check=True)
        print(f"Overlay check frame saved to {frame_out} "
              f"(open it and confirm the translated text is visible)",
              flush=True)
    print("VERIFY:", "PASS" if ok else "FAIL", flush=True)
    if not ok:
        raise SystemExit(1)
    return {"duration": dur, "size": size, "faststart": fs}
