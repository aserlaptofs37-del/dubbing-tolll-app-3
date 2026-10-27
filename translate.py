"""FREE translation, no API key.

Primary route: the Google Translate web endpoint (translate.googleapis.com,
client=gtx) called directly — free, no key, verified working. Quality is
free machine translation: good for straightforward narration, weaker for
idioms and wordplay, and it can mistranslate ambiguous words (observed:
Urdu "شیر" (lion) -> Arabic "النمر" (tiger)). Two fixes for that:
  1. --glossary FILE.json: target-side word replacements applied after
     translation, e.g. {"النمر": "الأسد", "النمور": "الأسود"}.
  2. --translation FILE.json: import a human-checked translation instead
     (same schema: [{"start","end","text"}]) — the best-quality route.

Fallback route if the gtx endpoint fails: deep-translator's MyMemory
translator (different free service, lower daily quota).
"""
import json
import time
import urllib.parse
import urllib.request


def gtx_translate(text, src, tgt, timeout=30):
    """Translate one string via the free gtx endpoint."""
    q = urllib.parse.urlencode(
        {"client": "gtx", "sl": src, "tl": tgt, "dt": "t", "q": text})
    req = urllib.request.Request(
        "https://translate.googleapis.com/translate_a/single?" + q,
        headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        data = json.loads(r.read().decode("utf-8"))
    return "".join(s[0] for s in data[0] if s[0])


def _mymemory_translate(text, src, tgt):
    """Fallback via MyMemory (different free service). Needs locale codes."""
    from deep_translator import MyMemoryTranslator
    lang_map = {"ur": "ur-PK", "hi": "hi-IN", "en": "en-GB", "ar": "ar-SA",
                "fa": "fa-IR", "es": "es-ES", "fr": "fr-FR", "de": "de-DE",
                "tr": "tr-TR", "bn": "bn-IN"}
    if src not in lang_map or tgt not in lang_map:
        raise ValueError(f"MyMemory has no mapping for {src}->{tgt}")
    return MyMemoryTranslator(source=lang_map[src],
                              target=lang_map[tgt]).translate(text)


def apply_glossary(text, glossary):
    """Apply target-side word replacements (dict) to translated text."""
    for wrong, right in (glossary or {}).items():
        text = text.replace(wrong, right)
    return text


def load_translation_json(path, segments):
    """Load a ready translation file and validate it against segments."""
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    trans = data.get("segments", data) if isinstance(data, dict) else data
    if not isinstance(trans, list):
        raise ValueError("translation file must contain a JSON array")
    out = []
    for i, seg in enumerate(segments):
        text = seg["text"]
        if i < len(trans) and isinstance(trans[i], dict):
            text = str(trans[i].get("text", "")).strip() or text
        out.append({"start": seg["start"], "end": seg["end"], "text": text})
    if len(trans) != len(segments):
        print(f"WARNING: translation file has {len(trans)} entries for "
              f"{len(segments)} segments; missing ones kept original text.",
              flush=True)
    return out


def translate_segments(segments, src_lang, tgt_lang, out_json=None,
                       glossary=None):
    """Translate every segment (free, no key)."""
    src = "auto" if src_lang in (None, "auto") else src_lang
    out = []
    consec_429 = 0  # if Google rate-limits repeatedly, stop burning time
    for i, seg in enumerate(segments):
        text = seg["text"]
        translated = None
        if consec_429 < 2:
            for attempt in range(4):
                try:
                    translated = gtx_translate(text, src, tgt_lang)
                    consec_429 = 0
                    break
                except Exception as e:
                    print(f"  segment {i} gtx attempt {attempt + 1} failed: "
                          f"{str(e)[:120]}", flush=True)
                    if "429" in str(e):
                        consec_429 += 1
                    time.sleep([5, 15, 30, 60][attempt])
        else:
            print(f"  segment {i}: skipping gtx (rate-limited), "
                  f"using fallback directly", flush=True)
        if not translated:
            try:
                translated = _mymemory_translate(text, src, tgt_lang)
            except Exception as e:
                print(f"  segment {i} fallback failed: {str(e)[:200]}; "
                      f"keeping original", flush=True)
                translated = text
        translated = apply_glossary(translated, glossary)
        out.append({"start": seg["start"], "end": seg["end"],
                    "text": translated})
        if (i + 1) % 20 == 0:
            print(f"  translated {i + 1}/{len(segments)}", flush=True)
        time.sleep(0.5)  # be gentle with the free endpoint
    if out_json:
        with open(out_json, "w", encoding="utf-8") as f:
            json.dump(out, f, ensure_ascii=False, indent=1)
        print(f"Wrote {len(out)} translations to {out_json}", flush=True)
    return out
