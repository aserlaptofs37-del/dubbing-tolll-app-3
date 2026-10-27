"""Optional PAID ElevenLabs TTS engine for video-dubbing-app-v3.

Free engines (edge / piper / gtts) stay the default and keep working
with no key at all. ElevenLabs activates ONLY when an API key is
configured, and every dub then spends the user's own ElevenLabs
credits — this tool never pays for it and never sees the key.

How the key is provided (never in chat, never in code, never as a CLI
argument — a CLI flag would land in shell history):
  1. Env var ELEVENLABS_API_KEY (CLI users), or
  2. The app's Settings section in the Streamlit UI, which writes it to
     elevenlabs_settings.json next to this file (local machine only).
The packaged Windows launcher may redirect the settings file to a
per-user folder via ELEVENLABS_SETTINGS_FILE (see packaging/BUILD.md).

API: direct HTTPS calls to https://api.elevenlabs.io/v1 with the
xi-api-key header. No new pip dependency (stdlib urllib only).
  - GET  /v1/voices                       -> voice catalog
  - POST /v1/text-to-speech/{voice_id}    -> MP3 audio bytes

Language support (verified against ElevenLabs model docs, Oct 2026):
  - eleven_multilingual_v2 (~29-31 langs): Arabic, English, German,
    Spanish, Russian, French, Hindi, Italian, Portuguese, Polish,
    Turkish, Dutch, and others listed in V2_LANGS below.
  - eleven_v3 (70+ langs): everything in v2 PLUS Urdu, Persian,
    Bengali, Punjabi, Pashto, and others listed in V3_EXTRA below.
  - NOT in either documented set (e.g. some gTTS-only languages):
    the engine FAILS with a clear message telling the user to pick a
    free engine for that language. It never silently dubs in the
    wrong language or accent.
The API itself does not reliably reject an unsupported language, so
this module gates on the documented sets BEFORE any characters (and
credits) are spent.
"""
import json
import os
import urllib.error
import urllib.request

API_BASE = "https://api.elevenlabs.io/v1"
DEFAULT_MODEL = "eleven_multilingual_v2"
SETTINGS_FILENAME = "elevenlabs_settings.json"

# Language codes as used by this app's catalog (ISO-ish: ar, ur, ...).
# eleven_multilingual_v2 documented set (29-31 languages).
V2_LANGS = {
    "ar", "bg", "ceb", "hr", "cs", "da", "nl", "en", "fil", "fi", "fr",
    "de", "el", "hi", "id", "it", "ja", "ko", "ms", "ps", "pl", "pa",
    "pt", "ro", "ru", "sk", "sv", "ta", "tr", "uk", "es",
}
# Languages documented as eleven_v3-only (v3 covers 70+ languages;
# this is the subset confirmed from the published v3 column, plus the
# app's core languages). v3 includes everything in V2_LANGS as well.
V3_EXTRA = {
    "ur", "fa", "bn", "af", "hy", "as", "az", "be", "bs", "ca", "ny",
    "et", "gl", "ka", "gu", "ha", "he", "hu", "is", "ga", "jv", "kn",
    "kk", "ky", "lv", "ln", "lt", "lb", "mk", "ml", "zh", "mr", "ne",
    "no",
}

KNOWN_MODELS = {"eleven_multilingual_v2", "eleven_v3"}


class ElevenLabsError(RuntimeError):
    """API or configuration error. `status` is the HTTP status or None.

    The message never contains the API key.
    """

    def __init__(self, message, status=None):
        super().__init__(message)
        self.status = status


# ---------------------------------------------------------------- settings
def settings_path(app_dir):
    """Where the local settings file lives.

    ELEVENLABS_SETTINGS_FILE (used by the packaged launcher) wins, so
    the key can live in a per-user folder instead of the install dir.
    """
    override = os.environ.get("ELEVENLABS_SETTINGS_FILE")
    if override:
        return override
    return os.path.join(app_dir, SETTINGS_FILENAME)


def load_settings(app_dir):
    """Return the settings dict, or {} if missing/unreadable."""
    try:
        with open(settings_path(app_dir), encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def save_settings(app_dir, api_key=None, voice_id=None, model_id=None):
    """Merge new values into the local settings file.

    Pass api_key="" to CLEAR a stored key. The file is written with
    owner-only permissions where the OS supports it. The key is never
    printed or logged by this function.
    """
    path = settings_path(app_dir)
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    data = load_settings(app_dir)
    if api_key is not None:
        if api_key == "":
            data.pop("api_key", None)
        else:
            data["api_key"] = api_key
    if voice_id is not None:
        if voice_id == "":
            data.pop("voice_id", None)
        else:
            data["voice_id"] = voice_id
    if model_id is not None:
        data["model_id"] = model_id
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=1)
    try:
        os.chmod(tmp, 0o600)
    except OSError:
        pass  # Windows has no POSIX perms; file is local-only anyway.
    os.replace(tmp, path)
    return path


def get_api_key(app_dir):
    """Resolve the key: env var wins, else the local settings file."""
    env = os.environ.get("ELEVENLABS_API_KEY")
    if env:
        return env
    return load_settings(app_dir).get("api_key") or None


def mask_key(key):
    """Safe display form: never show more than the last 4 characters."""
    if not key:
        return "(no key)"
    return "…" + key[-4:] if len(key) > 4 else "…"


# ---------------------------------------------------------------- API calls
def _headers(api_key):
    return {
        "xi-api-key": api_key,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }


def _read_error_body(err):
    try:
        raw = err.read().decode("utf-8", "replace")
        data = json.loads(raw)
        detail = data.get("detail", {})
        if isinstance(detail, dict):
            return detail.get("message") or raw[:300]
        return str(detail)[:300] or raw[:300]
    except Exception:
        return ""


def _request(method, url, api_key, payload=None):
    """One HTTPS call. Returns (status, bytes). Raises ElevenLabsError
    with a readable message (never the key) on HTTP/network failure."""
    body = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = urllib.request.Request(url, data=body, method=method,
                                 headers=_headers(api_key))
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            return resp.status, resp.read()
    except urllib.error.HTTPError as e:
        msg = _read_error_body(e)
        if e.code == 401:
            raise ElevenLabsError(
                "ElevenLabs key rejected (401). Check the key in Settings "
                "— it may be wrong, revoked, or pasted with a space.",
                status=401)
        if e.code == 402:
            raise ElevenLabsError(
                "ElevenLabs credits exhausted (402). Top up credits on "
                "your ElevenLabs account, or use a free engine "
                "(--tts-engine edge/piper/gtts) for this dub.",
                status=402)
        if e.code == 429:
            raise ElevenLabsError(
                "ElevenLabs rate limit hit (429). Wait a minute and retry, "
                "or use a free engine for this dub.", status=429)
        raise ElevenLabsError(
            f"ElevenLabs request failed (HTTP {e.code})"
            + (f": {msg}" if msg else "."), status=e.code)
    except urllib.error.URLError as e:
        raise ElevenLabsError(
            f"Could not reach api.elevenlabs.io: {e.reason}. Check your "
            f"internet connection, or use a free engine for this dub.")


def list_voices(api_key):
    """Return the account's voice catalog as a list of dicts.

    Each entry: voice_id, name, category, labels (gender, age, accent,
    language, ...). Labels may be missing for some voices.
    """
    _status, raw = _request("GET", f"{API_BASE}/voices", api_key)
    try:
        data = json.loads(raw.decode("utf-8"))
    except ValueError:
        raise ElevenLabsError("ElevenLabs returned an unreadable "
                              "voice list.")
    voices = data.get("voices", [])
    out = []
    for v in voices:
        labels = v.get("labels") or {}
        out.append({
            "voice_id": v.get("voice_id", ""),
            "name": v.get("name", ""),
            "category": v.get("category", ""),
            "gender": labels.get("gender", ""),
            "language": labels.get("language", ""),
            "accent": labels.get("accent", ""),
        })
    return out


def pick_voice(api_key, tgt, gender=None):
    """Auto-pick a voice for (language, gender) from the catalog.

    Prefers voices whose language label matches the target, then the
    requested gender (male -> masculine, female -> feminine). Voices
    without a language label are still candidates (many premade voices
    work multilingually) but rank below labeled matches. Raises a clear
    error if the catalog is empty or nothing matches the gender.
    """
    voices = list_voices(api_key)
    if not voices:
        raise ElevenLabsError(
            "ElevenLabs returned no voices for this account. Check the "
            "account, or pick a voice ID manually "
            "(--elevenlabs-voice <id>).")
    want_gender = {"male": "masculine", "female": "feminine"}.get(gender)
    labeled = [v for v in voices if v["language"] == tgt]
    pool = labeled or voices
    if want_gender:
        gendered = [v for v in pool
                    if v["gender"].lower() == want_gender]
        if gendered:
            return gendered[0]["voice_id"]
        if labeled:
            raise ElevenLabsError(
                f"No {gender} ElevenLabs voice labeled for '{tgt}'. "
                f"Pick a voice ID manually (--elevenlabs-voice <id>) or "
                f"use a free engine.")
    return pool[0]["voice_id"]


# ---------------------------------------------------------------- language
def check_language(tgt, model_id):
    """Fail fast on languages the chosen model does not support.

    Raises ElevenLabsError with the user's options. Unknown model ids
    are allowed with a printed warning (the user chose them explicitly);
    the API will reject them if they are invalid.
    """
    if model_id == "eleven_multilingual_v2":
        allowed = V2_LANGS
    elif model_id == "eleven_v3":
        allowed = V2_LANGS | V3_EXTRA
    else:
        print(f"  WARNING: language support for model {model_id!r} is "
              f"unverified — proceeding at your own credit risk.",
              flush=True)
        return
    if tgt in allowed:
        return
    if model_id == "eleven_multilingual_v2" and tgt in V3_EXTRA:
        raise ElevenLabsError(
            f"ElevenLabs model 'eleven_multilingual_v2' does not support "
            f"'{tgt}'. Options: use a free engine for this language "
            f"(--tts-engine edge/piper/gtts), or re-run with "
            f"--elevenlabs-model eleven_v3 (supports 70+ languages "
            f"including {tgt}; higher credit cost).")
    raise ElevenLabsError(
        f"ElevenLabs model '{model_id}' does not support '{tgt}' in its "
        f"documented language set. Use a free engine for this language "
        f"(--tts-engine edge/piper/gtts).")


def synthesize(text, voice_id, out_path, api_key,
               model_id=DEFAULT_MODEL):
    """Synthesize one text to MP3 at out_path. Returns nothing.

    Raises ElevenLabsError (401/402/429 carry .status so callers can
    fail fast instead of retrying a dead key or an empty balance).
    """
    payload = {
        "text": text,
        "model_id": model_id,
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.75,
            "style": 0.0,
            "use_speaker_boost": True,
        },
    }
    url = (f"{API_BASE}/text-to-speech/{voice_id}"
           f"?output_format=mp3_44100_128")
    _status, audio = _request("POST", url, api_key, payload)
    if len(audio) < 1000:
        raise ElevenLabsError(
            "ElevenLabs returned suspiciously little audio "
            f"({len(audio)} bytes) — the request probably failed "
            f"upstream. No retry will fix a bad voice id; check it.")
    with open(out_path, "wb") as f:
        f.write(audio)
