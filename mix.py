"""Mix dubbed segments into one track aligned to the original timeline.

Each segment is time-stretched with atempo (clamped 0.5-2.0) so it fits its
original slot, delayed to its start time, then everything is mixed and
padded to the full video length. Same approach as the proven v1 pipeline.
"""
import json
import os
import subprocess


def _run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print(r.stderr[-3000:])
        raise SystemExit(1)


def _has_filter(name):
    out = subprocess.run(["ffmpeg", "-hide_banner", "-filters"],
                         capture_output=True, text=True)
    return f" {name} " in out.stdout


def _loop_music(music_file, total_dur, out_wav):
    """Loop (or trim) a music file to exactly total_dur seconds as WAV."""
    if not os.path.exists(music_file):
        raise SystemExit(f"Music file not found: {music_file}")
    _run(["ffmpeg", "-y", "-stream_loop", "-1", "-i", music_file,
          "-t", f"{total_dur:.2f}",
          "-acodec", "pcm_s16le", "-ar", "44100", "-ac", "2", out_wav])
    return out_wav


def mix_final_track(voice_wav, music_tracks, total_dur, out_wav, workdir):
    """Mix the voice dub with one or more background-music tracks.

    music_tracks: list of (file, volume 0.0-1.0, ducking bool).
    Each music file is looped to the video length, volume-adjusted, and
    summed into a music bus. When ducking is on, the bus is
    sidechain-compressed by the voice track so speech stays clear; if
    this ffmpeg lacks sidechaincompress, music falls back to its fixed
    volume (a printed note says so). All intermediates live in workdir —
    nothing is written to /tmp. Returns out_wav.
    """
    if not music_tracks:
        _run(["ffmpeg", "-y", "-i", voice_wav,
              "-af", f"apad=whole_dur={total_dur:.2f}",
              "-acodec", "pcm_s16le", "-ar", "44100", "-ac", "2", out_wav])
        return out_wav
    inputs = ["-i", voice_wav]
    filters = []
    looped = []
    for j, (mfile, vol, _duck) in enumerate(music_tracks):
        loop = os.path.join(workdir, f"music_loop_{j}.wav")
        _loop_music(mfile, total_dur, loop)
        looped.append(loop)
        inputs += ["-i", loop]
        filters.append(f"[{j + 1}:a]volume={vol:.3f}[m{j}]")
    duck_idx = [j for j, (_f, _v, d) in enumerate(music_tracks) if d]
    plain_idx = [j for j, (_f, _v, d) in enumerate(music_tracks) if not d]
    can_duck = bool(duck_idx) and _has_filter("sidechaincompress")
    if duck_idx and not can_duck:
        print("NOTE: ffmpeg lacks sidechaincompress; music ducking "
              "disabled, using fixed volumes.", flush=True)
    buses = []
    if duck_idx:
        if can_duck:
            ins = "".join(f"[m{j}]" for j in duck_idx)
            k = len(duck_idx)
            filters.append(f"{ins}amix=inputs={k}:normalize=0[mduck]")
            filters.append("[mduck][0:a]sidechaincompress=threshold=0.03"
                           ":ratio=6:attack=200:release=500[mducked]")
            buses.append("[mducked]")
        else:
            plain_idx = plain_idx + duck_idx
    if plain_idx:
        ins = "".join(f"[m{j}]" for j in plain_idx)
        k = len(plain_idx)
        filters.append(f"{ins}amix=inputs={k}:normalize=0[mplain]")
        buses.append("[mplain]")
    mix_ins = "[0:a]" + "".join(buses)
    n = 1 + len(buses)
    filters.append(f"{mix_ins}amix=inputs={n}:normalize=0,"
                   f"apad=whole_dur={total_dur:.2f}[mix]")
    print(f"Mixing voice + {len(music_tracks)} music track(s) "
          f"(ducking={'on' if can_duck else 'off'}) ...", flush=True)
    _run(["ffmpeg", "-y"] + inputs +
         ["-filter_complex", ";".join(filters),
          "-map", "[mix]", "-acodec", "pcm_s16le", "-ar", "44100", "-ac", "2",
          out_wav])
    return out_wav


def build_dubbed_track(translated, tts_log, seg_dir, total_dur, out_wav):
    """Mix per-segment MP3s into one WAV. Returns out_wav."""
    inputs, filters, labels = [], [], []
    used = []
    for i, seg in enumerate(translated):
        seg_mp3 = os.path.join(seg_dir, f"seg_{i:03d}.mp3")
        if str(i) not in tts_log or not os.path.exists(seg_mp3):
            continue  # failed segment stays silent
        used.append(i)
        actual = tts_log[str(i)]["dur"]
        target = seg["end"] - seg["start"]
        rate = max(0.5, min(2.0, actual / target)) if target > 0 else 1.0
        delay_ms = int(seg["start"] * 1000)
        idx = len(used) - 1
        filters.append(
            f"[{idx}:a]atempo={rate:.3f},adelay={delay_ms}|{delay_ms}[a{idx}]")
        labels.append(f"[a{idx}]")
        inputs += ["-i", seg_mp3]
    if not used:
        raise SystemExit("No TTS segments available to mix.")
    n = len(used)
    filters.append(
        f"{''.join(labels)}amix=inputs={n}:duration=longest:normalize=0,"
        f"apad=whole_dur={total_dur:.2f}[mix]")
    print(f"Mixing {n} segments into {out_wav} ...", flush=True)
    _run(["ffmpeg", "-y"] + inputs +
         ["-filter_complex", ";".join(filters),
          "-map", "[mix]", "-acodec", "pcm_s16le", "-ar", "44100", "-ac", "2",
          out_wav])
    return out_wav
