"""Render translated overlay text as transparent PNGs.

CRITICAL: never use ffmpeg drawtext for Arabic/Urdu/Persian — it does not
shape connected letters. This module renders with Pillow:
- If Pillow has libraqm (normal on Linux), pass the LOGICAL string with
  direction="rtl" and let raqm shape + order it. Do NOT pre-shape with
  arabic_reshaper/bidi in that case (double-processing misplaces digits).
- If raqm is missing, fall back to arabic_reshaper + python-bidi shaping.
Fonts: NotoNaskhArabic for Arabic, NotoNastaliqUrdu for Urdu, NotoSansArabic
as a generic fallback. All ship with most Linux distros; override with
--font if yours live elsewhere.
"""
import json
import os

from PIL import Image, ImageDraw, ImageFont, features

ARABIC_FONTS = [
    "/usr/share/fonts/truetype/noto/NotoNaskhArabic-Bold.ttf",
    "/usr/share/fonts/truetype/noto/NotoSansArabic-Bold.ttf",
    # Windows: installer puts these TTFs into Windows Fonts.
    r"C:\Windows\Fonts\NotoNaskhArabic-Bold.ttf",
]
URDU_FONTS = [
    "/usr/share/fonts/truetype/noto/NotoNastaliqUrdu-Bold.ttf",
    "/usr/share/fonts/truetype/noto/NotoNaskhArabic-Bold.ttf",
    # Windows: installer puts these TTFs into Windows Fonts.
    r"C:\Windows\Fonts\NotoNastaliqUrdu-Bold.ttf",
    r"C:\Windows\Fonts\NotoNaskhArabic-Bold.ttf",
]
DEFAULT_FONTS = ARABIC_FONTS + URDU_FONTS


def pick_font(lang, size, font_path=None):
    """Return a truetype font for lang/size, or raise a clear error."""
    candidates = [font_path] if font_path else []
    if lang in ("ur",):
        candidates += URDU_FONTS
    elif lang in ("ar", "fa"):
        candidates += ARABIC_FONTS
    candidates += DEFAULT_FONTS
    for path in candidates:
        if path and os.path.exists(path):
            return ImageFont.truetype(path, size)
    raise FileNotFoundError(
        "No Arabic/Urdu font found. Install fonts-noto (Linux) or pass --font.")


def _draw_text(img, text, font, color, rtl):
    d = ImageDraw.Draw(img)
    if rtl:
        if features.check("raqm"):
            d.text((0, 0), text, font=font, fill=color,
                   direction="rtl", language="ar")
        else:
            import arabic_reshaper
            from bidi.algorithm import get_display
            shaped = get_display(arabic_reshaper.reshape(text))
            d.text((0, 0), shaped, font=font, fill=color)
    else:
        d.text((0, 0), text, font=font, fill=color)


def render_text_png(text, lang, size, color, out_path, font_path=None):
    """Render one text string to a transparent PNG. Returns (w, h)."""
    rtl = lang in ("ar", "ur", "fa")
    font = pick_font(lang, size, font_path)
    tmp = Image.new("RGBA", (10, 10))
    d = ImageDraw.Draw(tmp)
    if rtl and features.check("raqm"):
        bbox = d.textbbox((0, 0), text, font=font,
                          direction="rtl", language="ar")
    elif rtl:
        import arabic_reshaper
        from bidi.algorithm import get_display
        shaped = get_display(arabic_reshaper.reshape(text))
        bbox = d.textbbox((0, 0), shaped, font=font)
    else:
        bbox = d.textbbox((0, 0), text, font=font)
    w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
    img = Image.new("RGBA", (w + 20, h + 20), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    if rtl and features.check("raqm"):
        d.text((10 - bbox[0], 10 - bbox[1]), text, font=font, fill=color,
               direction="rtl", language="ar")
    elif rtl:
        import arabic_reshaper
        from bidi.algorithm import get_display
        shaped = get_display(arabic_reshaper.reshape(text))
        d.text((10 - bbox[0], 10 - bbox[1]), shaped, font=font, fill=color)
    else:
        d.text((10 - bbox[0], 10 - bbox[1]), text, font=font, fill=color)
    img.save(out_path)
    return img.size


def render_labels(labels, lang, texts_dir, font_path=None):
    """Render every label's text PNG. Returns manifest {name: {w, h}}.

    labels: list of dicts with keys name, text, font_size (default 88),
    text_color [r,g,b,a] (default white).
    """
    os.makedirs(texts_dir, exist_ok=True)
    manifest = {}
    for lab in labels:
        size = int(lab.get("font_size", 88))
        color = tuple(lab.get("text_color", [255, 255, 255, 255]))
        out = os.path.join(texts_dir, lab["name"] + ".png")
        w, h = render_text_png(lab["text"], lang, size, color, out, font_path)
        manifest[lab["name"]] = {"w": w, "h": h}
        print(f"  rendered {lab['name']}: {w}x{h} -> {lab['text']}",
              flush=True)
    return manifest
