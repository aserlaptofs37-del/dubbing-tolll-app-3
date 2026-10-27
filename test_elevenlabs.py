#!/usr/bin/env python3
"""Tests for the optional ElevenLabs engine (mocked, no real key).

Run:  python3 test_elevenlabs.py
Uses ONLY dummy values (DUMMY_KEY_FOR_TESTS_ONLY). No network call
leaves this file: every HTTP call is mocked. A real voice generation
still needs the user's own key on their own machine.
"""
import io
import json
import os
import subprocess
import sys
import tempfile
import urllib.error

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from unittest import mock

import elevenlabs_engine as el
import tts

DUMMY = "DUMMY_KEY_FOR_TESTS_ONLY"
FAKE_VOICES = {
    "voices": [
        {"voice_id": "voice-ar-f", "name": "Layla",
         "category": "premade",
         "labels": {"gender": "feminine", "language": "ar"}},
        {"voice_id": "voice-ar-m", "name": "Omar",
         "category": "premade",
         "labels": {"gender": "masculine", "language": "ar"}},
        {"voice_id": "voice-nolabel", "name": "Mystery",
         "category": "generated", "labels": {}},
    ]
}


class FakeResp:
    def __init__(self, body, status=200):
        self._body = body
        self.status = status

    def read(self):
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def check(name, cond, extra=""):
    print(f"  [{'PASS' if cond else 'FAIL'}] {name} {extra}")
    if not cond:
        raise SystemExit(f"FAILED: {name}")


def main():
    print("== imports ==")
    check("elevenlabs_engine imports", el is not None)
    check("tts imports", tts is not None)

    print("== language gating ==")
    for lang in ("ar", "en", "de", "es", "ru", "fr", "hi"):
        el.check_language(lang, "eleven_multilingual_v2")
    check("v2 allows ar/en/de/es/ru/fr/hi", True)
    for lang in ("ur", "fa", "bn"):
        try:
            el.check_language(lang, "eleven_multilingual_v2")
            check(f"v2 rejects {lang}", False)
        except el.ElevenLabsError as e:
            check(f"v2 rejects {lang} with clear message",
                  "free engine" in str(e), f"({str(e)[:60]}...)")
    try:
        el.check_language("ur", "eleven_multilingual_v2")
    except el.ElevenLabsError as e:
        check("ur v2 error mentions eleven_v3", "eleven_v3" in str(e))
    for lang in ("ur", "fa", "bn", "ar"):
        el.check_language(lang, "eleven_v3")
    check("v3 allows ur/fa/bn/ar", True)
    el.check_language("ar", "some_future_model")  # warns, does not raise
    check("unknown model warns instead of raising", True)

    print("== settings round-trip (dummy key only) ==")
    with tempfile.TemporaryDirectory() as d:
        check("no key before save", el.get_api_key(d) is None)
        el.save_settings(d, api_key=DUMMY, voice_id="voice-ar-f",
                         model_id="eleven_multilingual_v2")
        loaded = el.load_settings(d)
        check("key round-trips", loaded.get("api_key") == DUMMY)
        check("voice round-trips", loaded.get("voice_id") == "voice-ar-f")
        check("model round-trips",
              loaded.get("model_id") == "eleven_multilingual_v2")
        check("mask hides key", el.mask_key(DUMMY) == "…ONLY"
              and DUMMY not in el.mask_key(DUMMY))
        with mock.patch.dict(os.environ, {"ELEVENLABS_API_KEY": "DUMMY_ENV"}):
            check("env key wins over file",
                  el.get_api_key(d) == "DUMMY_ENV")
        el.save_settings(d, api_key="")
        check("clear removes key", el.get_api_key(d) is None)

    print("== list_voices parsing (mocked HTTP) ==")
    body = json.dumps(FAKE_VOICES).encode()
    with mock.patch("urllib.request.urlopen",
                    return_value=FakeResp(body)):
        voices = el.list_voices(DUMMY)
    check("3 voices parsed", len(voices) == 3)
    check("labels parsed",
          voices[0]["gender"] == "feminine" and voices[0]["language"] == "ar")

    print("== pick_voice gender filter (mocked HTTP) ==")
    with mock.patch("urllib.request.urlopen",
                    return_value=FakeResp(body)):
        check("female pick", el.pick_voice(DUMMY, "ar", "female")
              == "voice-ar-f")
    with mock.patch("urllib.request.urlopen",
                    return_value=FakeResp(body)):
        check("male pick", el.pick_voice(DUMMY, "ar", "male")
              == "voice-ar-m")
    with mock.patch("urllib.request.urlopen",
                    return_value=FakeResp(body)):
        check("no-gender pick is first",
              el.pick_voice(DUMMY, "ar") == "voice-ar-f")

    print("== error mapping (mocked HTTP errors) ==")
    def _http_err(code):
        err = urllib.error.HTTPError("url", code, "x", {}, None)
        err.read = lambda: b'{"detail": {"message": "boom"}}'
        return err
    for code, needle in ((401, "rejected"), (402, "credits"),
                         (429, "rate limit")):
        with mock.patch("urllib.request.urlopen",
                        side_effect=_http_err(code)):
            try:
                el.list_voices(DUMMY)
                check(f"HTTP {code} raises", False)
            except el.ElevenLabsError as e:
                check(f"HTTP {code} -> clear message + status",
                      needle in str(e) and e.status == code)

    print("== synthesize_segment (mocked TTS, real ffprobe) ==")
    mp3 = os.path.join(tempfile.gettempdir(), "el_test_tone.mp3")
    r = subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi",
                        "-i", "sine=frequency=440:duration=0.5",
                        "-codec:a", "libmp3lame", mp3],
                       capture_output=True)
    if r.returncode == 0 and os.path.getsize(mp3) > 1000:
        tone = open(mp3, "rb").read()
        out = os.path.join(tempfile.gettempdir(), "el_test_seg.mp3")
        with mock.patch("urllib.request.urlopen",
                        return_value=FakeResp(tone)):
            dur = tts.synthesize_segment("hello", "elevenlabs",
                                         "voice-ar-f", out, HERE,
                                         elevenlabs_key=DUMMY,
                                         elevenlabs_model=
                                         "eleven_multilingual_v2")
        check("segment written + duration>0",
              os.path.getsize(out) > 1000 and dur > 0, f"(dur={dur:.2f})")
    else:
        print("  [SKIP] ffmpeg tone generation unavailable in sandbox")

    print("== synthesize_all fails fast on unsupported language ==")
    def _boom(*a, **k):
        raise AssertionError("network must not be touched before gating")
    with tempfile.TemporaryDirectory() as d:
        with mock.patch.dict(os.environ, {"ELEVENLABS_API_KEY": DUMMY}), \
                mock.patch("urllib.request.urlopen", side_effect=_boom):
            try:
                tts.synthesize_all([{"text": "x", "start": 0, "end": 1}],
                                   "elevenlabs", None, d,
                                   os.path.join(d, "log.json"), d,
                                   tgt="ur",
                                   elevenlabs_model="eleven_multilingual_v2")
                check("ur+v2 gated before synthesis", False)
            except RuntimeError as e:
                check("ur+v2 gated before synthesis",
                      "eleven_v3" in str(e))

    print("== synthesize_all no-key error ==")
    with tempfile.TemporaryDirectory() as d:
        env = {k: v for k, v in os.environ.items()
               if k != "ELEVENLABS_API_KEY"}
        with mock.patch.dict(os.environ, env, clear=True):
            # clear=True wipes PATH etc. for the child code only in this
            # block; restore by re-adding essentials for subprocess-free
            # code below (no subprocess runs inside this block).
            try:
                tts.synthesize_all([{"text": "x", "start": 0, "end": 1}],
                                   "elevenlabs", None, d,
                                   os.path.join(d, "log.json"), d,
                                   tgt="ar")
                check("no-key raises", False)
            except RuntimeError as e:
                check("no-key raises clear message", "API key" in str(e))

    print("== CLI help shows new flags ==")
    env = {k: v for k, v in os.environ.items()
           if k != "ELEVENLABS_API_KEY"}
    top = subprocess.run([sys.executable, "dub.py", "--help"],
                         capture_output=True, text=True, cwd=HERE, env=env)
    check("top --help lists --list-elevenlabs-voices",
          "--list-elevenlabs-voices" in top.stdout)
    run = subprocess.run([sys.executable, "dub.py", "run", "--help"],
                         capture_output=True, text=True, cwd=HERE, env=env)
    check("run --help lists elevenlabs engine",
          "elevenlabs" in run.stdout)
    check("run --help lists --elevenlabs-voice",
          "--elevenlabs-voice" in run.stdout)
    check("run --help lists --elevenlabs-model",
          "--elevenlabs-model" in run.stdout)
    no_key = subprocess.run(
        [sys.executable, "dub.py", "--list-elevenlabs-voices"],
        capture_output=True, text=True, cwd=HERE, env=env)
    check("list-voices without key exits with Settings hint",
          no_key.returncode != 0 and "Settings" in (no_key.stdout
                                                    + no_key.stderr))

    print("== compile checks ==")
    for f in ("elevenlabs_engine.py", "tts.py", "dub.py", "app.py"):
        r = subprocess.run([sys.executable, "-m", "py_compile",
                            os.path.join(HERE, f)],
                           capture_output=True, text=True)
        check(f"py_compile {f}", r.returncode == 0, r.stderr.strip()[:100])

    print("\nALL ELEVENLABS TESTS PASSED (mocked; no real key used).")


if __name__ == "__main__":
    main()
