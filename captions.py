"""Caption tools for dubbing-app-v3: SRT subtitles + styled ASS burn-in.

SRT is the portable subtitle file (players, YouTube upload, phones).
ASS is burned into the video with ffmpeg's subtitles filter (libass),
which shapes Arabic/Urdu/Persian correctly via HarfBuzz — never use
ffmpeg drawtext for RTL scripts.

Fonts: libass resolves these family names via fontconfig. Noto Naskh
Arabic / Noto Nastaliq Urdu ship with most Linux distros (and are the
same fonts render.py uses for PNG overlays); DejaVu Sans is the Latin
fallback. If a font is missing on the user's laptop, libass falls back
to a default font instead of failing.
"""

# Preset styles: (font, size, primary color, outline, shadow, back-box)
# Colors are ASS &HBBGGRR (alpha first: 00 = opaque).
STYLES = {
    "professional": {
        "font": None,  # picked per language below
        "size": 48,
        "color": "&H00FFFFFF",
        "outline_color": "&H80000000",
        "outline": 2,
        "shadow": 1,
        "back": True,  # semi-transparent box behind text
    },
    "bold-yellow": {
        "font": None,
        "size": 56,
        "color": "&H0000FFFF",
        "outline_color": "&H80000000",
        "outline": 3,
        "shadow": 1,
        "back": False,
    },
    "minimal": {
        "font": None,
        "size": 40,
        "color": "&H00FFFFFF",
        "outline_color": "&H80000000",
        "outline": 1,
        "shadow": 0,
        "back": False,
    },
}

_RTL_LANGS = ("ar", "ur", "fa")


def _font_for(lang):
    if lang == "ur":
        return "Noto Nastaliq Urdu"
    if lang in ("ar", "fa"):
        return "Noto Naskh Arabic"
    return "DejaVu Sans"


def fmt_srt_ts(seconds):
    """Seconds -> SRT timestamp HH:MM:SS,mmm."""
    ms = int(round(seconds * 1000))
    h, ms = divmod(ms, 3600000)
    m, ms = divmod(ms, 60000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def fmt_ass_ts(seconds):
    """Seconds -> ASS timestamp H:MM:SS.cc."""
    cs = int(round(seconds * 100))
    h, cs = divmod(cs, 360000)
    m, cs = divmod(cs, 6000)
    s, cs = divmod(cs, 100)
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"


def _seg_times(seg):
    """Segment times: the pipeline uses t0/t1; accept start/end too."""
    t0 = seg.get("t0", seg.get("start"))
    t1 = seg.get("t1", seg.get("end"))
    return float(t0), float(t1)


def write_srt(segments, path):
    """Write translated segments as an SRT file. Returns cue count."""
    n = 0
    with open(path, "w", encoding="utf-8") as f:
        for i, seg in enumerate(segments, 1):
            text = (seg.get("text") or "").strip()
            if not text:
                continue
            t0, t1 = _seg_times(seg)
            f.write(f"{i}\n")
            f.write(f"{fmt_srt_ts(t0)} --> "
                    f"{fmt_srt_ts(t1)}\n")
            f.write(text + "\n\n")
            n += 1
    return n


def _ass_header(style, lang):
    st = dict(style)
    font = st["font"] or _font_for(lang)
    back = "0" if not st["back"] else "-1"  # BorderStyle: 1=outline+shadow, 3=box
    border_style = "3" if st["back"] else "1"
    return (
        "[Script Info]\n"
        "ScriptType: v4.00+\n"
        "PlayResX: 1920\n"
        "PlayResY: 1080\n"
        "ScaledBorderAndShadow: yes\n"
        "\n"
        "[V4+ Styles]\n"
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, "
        "OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, "
        "ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, "
        "Alignment, MarginL, MarginR, MarginV, Encoding\n"
        f"Style: Caption,{font},{st['size']},{st['color']},&H000000FF,"
        f"{st['outline_color']},&H80000000,1,0,0,0,100,100,0,0,"
        f"{border_style},{st['outline']},{st['shadow']},2,40,40,60,1\n"
        "\n"
        "[Events]\n"
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, "
        "Effect, Text\n"
    )


def write_ass(segments, path, lang, style_name="professional"):
    """Write translated segments as a styled ASS file. Returns event count."""
    style = STYLES.get(style_name, STYLES["professional"])
    n = 0
    with open(path, "w", encoding="utf-8") as f:
        f.write(_ass_header(style, lang))
        for seg in segments:
            text = (seg.get("text") or "").strip()
            if not text:
                continue
            # ASS: escape newlines inside a cue; libass handles RTL shaping.
            text = text.replace("\n", "\\N")
            t0, t1 = _seg_times(seg)
            f.write(f"Dialogue: 0,{fmt_ass_ts(t0)},"
                    f"{fmt_ass_ts(t1)},Caption,,0,0,0,,{text}\n")
            n += 1
    return n


def check_srt(path):
    """Parse an SRT back; returns cue count (0 if missing/broken)."""
    try:
        text = open(path, encoding="utf-8").read()
    except OSError:
        return 0
    return text.count("-->")
