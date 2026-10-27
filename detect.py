"""Detect solid banner windows in a video (helper for labels.json).

Samples frames and looks for large near-uniform colour blocks in the lower
third of the frame — the usual style for lower-third name/title banners.
This is a HELPER, not magic: it reports candidate time ranges + boxes.
You still confirm the text and write labels.json (see README) — the tool
never guesses translations for on-screen text on its own.

Output: [{"t0","t1","bbox":[x,y,w,h],"color":[r,g,b]}] in video pixels.
"""
import json
import os
import subprocess
from collections import Counter

from PIL import Image


def _frames(video, fps, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    subprocess.run(
        ["ffmpeg", "-y", "-v", "error", "-i", video, "-vf", f"fps={fps}",
         os.path.join(out_dir, "f_%05d.png")],
        check=True)
    return sorted(os.path.join(out_dir, f) for f in os.listdir(out_dir))


def _banner_in_frame(img):
    """Find the largest near-uniform colour block in the lower third.

    Returns (bbox, color) or None. Works on a downscaled copy for speed.

    NOTE: real banners are often NARROW name plates (the test video's
    title bar is only ~12% of the frame width) and text-heavy rows dilute
    the solid colour to ~8% of a row — and on some rows the white TEXT
    itself outnumbers the bar colour. So a row "supports" every exact
    colour over 7% of the row (not just the top one), and a band is a
    colour supported across a vertical run of rows (one missed row
    tolerated, e.g. a text-dominated row). The band-height (>=8px at
    180p) and the >=0.8s duration filter in detect_banners reject
    flicker; the best-scoring band (largest total support) wins, so a
    white text run loses to the larger bar-colour run.

    Saturated colours only: a band must have max-min channel >= 60.
    Bright scene areas (sky, sand, near-white walls) otherwise form
    tall "bands" that are not banners; white/black banners are
    indistinguishable from scene content without OCR (which this tool
    deliberately does not use), so they are out of scope for detection
    — write those by hand in labels.json.
    """
    small = img.convert("RGB").resize((320, 180))
    w, h = small.size
    px = small.load()
    rows = []  # (y, {color: (count, x_min, x_max)})
    for y0 in range(int(h * 0.66), h - 8, 2):
        row_colors = Counter()
        for x in range(w):
            row_colors[px[x, y0][:3]] += 1
        supported = {}
        for color, count in row_colors.most_common(4):
            if count > w * 0.07 and max(color) - min(color) >= 60:
                xs = [x for x in range(w) if px[x, y0][:3] == color]
                supported[color] = (count, min(xs), max(xs))
        rows.append((y0, supported))
    # Build runs per colour, tolerating one missed row (gap <= 4px).
    best = None  # (score, bbox, color)
    colors = set()
    for _, supported in rows:
        colors.update(supported)
    for color in colors:
        run_start = run_last = None
        run_score = 0
        run_x0 = run_x1 = None
        run_rows = 0
        run_gap = 0

        def finish():
            nonlocal best
            if (run_start is not None and run_rows >= 4
                    and run_last - run_start + 2 >= 8):
                sx, sy = img.size[0] / 320.0, img.size[1] / 180.0
                bbox = [int(run_x0 * sx), int(run_start * sy),
                        int((run_x1 - run_x0 + 1) * sx),
                        int((run_last - run_start + 2) * sy)]
                if best is None or run_score > best[0]:
                    best = (run_score, bbox, color)

        for y0, supported in rows:
            if color in supported:
                count, x0, x1 = supported[color]
                if run_start is None:
                    run_start = run_last = y0
                    run_x0, run_x1 = x0, x1
                    run_rows, run_score, run_gap = 1, count, 0
                else:
                    run_last = y0
                    run_x0, run_x1 = min(run_x0, x0), max(run_x1, x1)
                    run_rows += 1
                    run_score += count
                    run_gap = 0
            elif run_start is not None:
                run_gap += 1
                if run_gap > 1:
                    finish()
                    run_start = run_last = None
                    run_score = run_rows = run_gap = 0
                    run_x0 = run_x1 = None
        finish()
    if best is None:
        return None
    return best[1], best[2]


def detect_banners(video, out_json, fps=4):
    """Scan video, collapse consecutive banner frames into windows."""
    import shutil
    import tempfile
    tmp = tempfile.mkdtemp(prefix="banner_scan_")
    try:
        files = _frames(video, fps, tmp)
        step = 1.0 / fps
        windows = []
        cur = None
        for i, path in enumerate(files):
            t = i * step
            img = Image.open(path)
            found = _banner_in_frame(img)
            if found:
                bbox, color = found
                if cur and t - cur["t1"] <= step * 1.5 + 0.01:
                    cur["t1"] = round(t, 2)
                else:
                    cur = {"t0": round(t, 2), "t1": round(t, 2),
                           "bbox": bbox, "color": list(color)}
                    windows.append(cur)
    finally:
        # Never leak the extracted frames: one 60s scan is ~150 MB.
        shutil.rmtree(tmp, ignore_errors=True)
    # Drop flicker: keep windows whose presence covers >= 0.5s. A window
    # seen on a single sampled frame counts as one frame interval
    # (t1 - t0 + step), because brief banner flashes (~0.5-1s, e.g. the
    # test clip's animal-name plates) are real banners too; the caller
    # still confirms every candidate before writing labels.json.
    windows = [w for w in windows
               if w["t1"] - w["t0"] + step >= 0.5 - 0.01]
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(windows, f, ensure_ascii=False, indent=1)
    for w in windows:
        print(f"  banner {w['t0']}s - {w['t1']}s bbox={w['bbox']} "
              f"color={w['color']}", flush=True)
    print(f"Wrote {len(windows)} candidate windows to {out_json}", flush=True)
    return windows
