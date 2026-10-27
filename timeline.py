"""Multi-layer TIMELINE model for dubbing-app-v3.

A timeline is a plain JSON dict so the Streamlit UI can save/load it and
the CLI can accept it with --timeline. Track types:

- video:    the source video (trim start/end optional).
- voice:    the generated dub track (from transcription/TTS).
- music:    background music/sound bed. Fields: file, volume (0.0-1.0),
            ducking (bool). Any number of music tracks may be enabled;
            they are looped to the video length, volume-adjusted, summed,
            then ducked as one bus under the voice track.
- captions: subtitle track. Fields: mode (srt|burn|both|off),
            style (professional|bold-yellow|minimal).
- overlays: translated on-screen text labels (v2 labels.json schema).

The timeline does NOT render by itself: dub.py reads it and calls
mix/overlay/captions helpers. validate() catches bad input with clear
messages before any slow work starts (professional UX: fail fast).
"""

TRACK_TYPES = ("video", "voice", "music", "captions", "overlays")


def default_timeline():
    """A timeline with the standard tracks; music/captions off by default
    in the CLI path (the UI turns captions on by default)."""
    return {
        "version": 3,
        "tracks": [
            {"type": "video", "enabled": True, "name": "Video"},
            {"type": "voice", "enabled": True, "name": "Voice dub"},
            {"type": "music", "enabled": False, "name": "Music 1",
             "file": "", "volume": 0.15, "ducking": True},
            {"type": "captions", "enabled": True, "name": "Captions",
             "mode": "srt", "style": "professional"},
            {"type": "overlays", "enabled": False, "name": "Text overlays",
             "labels": []},
        ],
    }


def add_music_track(timeline, name=None):
    """Append an extra music track (expandable track count — the UI's
    'Add another music track' button uses this; there is no hard cap)."""
    n = 1 + sum(1 for t in timeline["tracks"] if t["type"] == "music")
    timeline["tracks"].append(
        {"type": "music", "enabled": True,
         "name": name or f"Music {n}", "file": "", "volume": 0.15,
         "ducking": True})
    return timeline


def music_tracks(timeline):
    """Enabled music tracks as [(file, volume, ducking)]."""
    import os
    out = []
    for t in timeline.get("tracks", []):
        if t.get("type") == "music" and t.get("enabled") and t.get("file"):
            out.append((t["file"], float(t.get("volume", 0.15)),
                        bool(t.get("ducking", True))))
    return out


def captions_track(timeline):
    """The captions track dict, or None."""
    for t in timeline.get("tracks", []):
        if t.get("type") == "captions" and t.get("enabled"):
            return t
    return None


def overlays_track(timeline):
    """The overlays track dict, or None."""
    for t in timeline.get("tracks", []):
        if t.get("type") == "overlays" and t.get("enabled"):
            return t
    return None


def validate(timeline):
    """Return a list of error strings (empty = valid)."""
    import os
    errors = []
    if not isinstance(timeline, dict) or "tracks" not in timeline:
        return ["Timeline JSON must be an object with a 'tracks' list."]
    seen_types = set()
    for i, t in enumerate(timeline["tracks"]):
        if not isinstance(t, dict):
            errors.append(f"Track {i} is not an object.")
            continue
        ttype = t.get("type")
        if ttype not in TRACK_TYPES:
            errors.append(f"Track {i}: unknown type {ttype!r}.")
            continue
        seen_types.add(ttype)
        if ttype == "music" and t.get("enabled"):
            if not t.get("file"):
                errors.append(f"Music track '{t.get('name', i)}' is enabled "
                              f"but has no file.")
            elif not os.path.exists(t["file"]):
                errors.append(f"Music file not found: {t['file']}")
            v = t.get("volume", 0.15)
            if not isinstance(v, (int, float)) or not (0.0 <= v <= 1.0):
                errors.append(f"Music track '{t.get('name', i)}': volume "
                              f"must be 0.0-1.0, got {v!r}.")
        if ttype == "captions" and t.get("enabled"):
            if t.get("mode") not in ("srt", "burn", "both", "off"):
                errors.append(f"Captions mode must be srt|burn|both|off, "
                              f"got {t.get('mode')!r}.")
    if "video" not in seen_types:
        errors.append("Timeline has no video track.")
    if "voice" not in seen_types:
        errors.append("Timeline has no voice track.")
    return errors


def from_options(music_files, captions_mode, captions_style, labels):
    """Build a timeline from CLI/UI options.

    music_files: list of (file, volume, ducking). labels: list or None.
    """
    tl = default_timeline()
    for t in tl["tracks"]:
        if t["type"] == "music":
            t["enabled"] = False
        if t["type"] == "captions":
            t["mode"] = captions_mode
            t["enabled"] = captions_mode != "off"
        if t["type"] == "overlays":
            t["enabled"] = bool(labels)
            t["labels"] = labels or []
    # Replace the placeholder music track with the real ones.
    tl["tracks"] = [t for t in tl["tracks"] if t["type"] != "music"]
    for j, (f, v, d) in enumerate(music_files, 1):
        tl["tracks"].append({"type": "music", "enabled": True,
                             "name": f"Music {j}", "file": f, "volume": v,
                             "ducking": d})
    return tl
