# Video Dubbing Tool v3 — FREE, no API keys

Dub any video into another language: local transcription, free
translation, free neural voices (male or female), a multi-layer
TIMELINE (voice dub + background music with ducking + captions +
text overlays), and a mobile-friendly faststart MP4 out.

**100% free with the built-in engines. No key, no account, no upload.**
Everything runs on your own computer (internet needed for the first
model/voice downloads and for the free translation + edge-tts endpoints).
ElevenLabs voices are an *optional paid extra* (see below) — the free
engines keep working with no key at all.

This replaces v2 (`../video-dubbing-app-v2/`). What is new in v3:
1. **Timeline editor** in the web UI — video, voice dub, background
   music, captions and text overlays as separate tracks. Add as many
   music tracks as you like (there is no fixed layer limit — the
   "11 layers" idea from the feature request is covered by an
   expandable track list, not a hard cap).
2. **Background music** with its own track and volume control, mixed
   under the voice with **ducking** (music drops while someone speaks,
   comes back up in gaps).
3. **106 languages** (73 edge neural + 33 gTTS coverage) — Arabic,
   Spanish, English, German and Russian included, all with male and
   female edge voices. Full table: `LANGUAGES.md` (generated from the
   same catalog the app uses).
4. **Male and female voice selection** (`--voice-gender male|female`,
   or the gender radio in the UI).
5. **Caption tools** — SRT subtitle file plus styled burned-in
   on-screen captions (professional / bold-yellow / minimal).
6. **Timeline JSON** save/load — export a timeline from the UI and
   re-run it from the CLI with `--timeline`.

## Laptop ya phone? (read this first)

**Ye tool LAPTOP / computer par chalta hai — phone par directly nahi.**
Python, ffmpeg aur Whisper phone par directly nahi chal sakte, is liye
dubbing ka kaam laptop par hota hai.

**Phone se use karna ho to:** laptop par server chalao, phir phone ke
browser se (same WiFi par) laptop ka address kholo — neeche "Run (web
UI)" me step-by-step tareeqa hai. Video file phone se upload ho sakti
hai, lekin processing laptop par hogi.

**This tool runs on a LAPTOP / computer, not directly on a phone.**
Phones cannot run Python, ffmpeg and Whisper directly, so the dubbing
work happens on the laptop. To use it from a phone, run the server on
the laptop and open it in the phone's browser on the same Wi-Fi (see
"Run (web UI)" below for steps). You can upload a video from the phone,
but the processing runs on the laptop.

## Setup

Requirements: Python 3.10+, ffmpeg + ffprobe on PATH.

```bash
# Ubuntu/Debian: sudo apt install ffmpeg fonts-noto
# macOS (brew):  brew install ffmpeg

cd video-dubbing-app-v3
python3 -m venv venv
./venv/bin/pip install -r requirements.txt
```

First run downloads (once, needs internet):
- Whisper model `small` (~470 MB) for transcription.
- Piper voice model (~63 MB) if you use `--tts-engine piper`.
- edge-tts voices stream on demand (no download).

Check ffmpeg is present: `ffmpeg -version` and `ffprobe -version`.
Ducking needs ffmpeg's `sidechaincompress` filter (present in standard
ffmpeg builds; if it is missing, music falls back to a fixed low volume
and the run prints a note).

## Run (command line — the reliable way)

```bash
# Audio-only dub (fastest: video stream is copied untouched, Full HD kept)
./venv/bin/python dub.py run --input video.mp4 --tgt ar --out dubbed.mp4

# Dub + background music (ducked under the voice) + captions
./venv/bin/python dub.py run --input video.mp4 --tgt ar \
    --music bed.mp3 --captions both --out dubbed.mp4

# Two music tracks, male voice
./venv/bin/python dub.py run --input video.mp4 --tgt ar \
    --music intro.mp3 --music bed.mp3 --voice-gender male \
    --captions both --out dubbed.mp4

# Dub + translated on-screen text (see "Labels" below)
./venv/bin/python dub.py run --input video.mp4 --tgt ar \
    --labels labels.json --out dubbed.mp4

# Drive the render from a saved timeline JSON (UI export)
./venv/bin/python dub.py run --input video.mp4 --tgt ar \
    --timeline timeline.json --out dubbed.mp4

# Use a human-checked translation instead of machine translation
./venv/bin/python dub.py run --input video.mp4 --tgt ar \
    --translation my_translation.json --out dubbed.mp4

# Fix systematic machine-translation errors with a word list
./venv/bin/python dub.py run --input video.mp4 --tgt ar \
    --glossary glossary.json --out dubbed.mp4

# Offline voices (no internet needed at run time, after model download)
./venv/bin/python dub.py run --input video.mp4 --tgt ar \
    --tts-engine piper --out dubbed.mp4

# Widest language coverage (single voice per language, no gender choice)
./venv/bin/python dub.py run --input video.mp4 --tgt sq \
    --tts-engine gtts --out dubbed.mp4

# Scan a video for banner windows (helper for writing labels.json)
./venv/bin/python dub.py detect --input video.mp4 --out windows.json

# Verify a finished file (duration, audio, faststart)
./venv/bin/python dub.py verify --input dubbed.mp4 --reference video.mp4
```

Options: `--src auto|ur|hi|en|ar|...` (default `auto`),
`--voice` (edge voice id, or full piper model key),
`--voice-gender male|female` (edge engine; ignored if `--voice` given),
`--tts-engine edge|piper|gtts|elevenlabs` (default `edge`),
`--elevenlabs-voice <voice-id>` (ElevenLabs only; blank = auto-pick),
`--elevenlabs-model eleven_multilingual_v2|eleven_v3`
(default `eleven_multilingual_v2`),
`--music FILE` (repeatable; each loops to the video length),
`--music-volume 0.0-1.0` (default `0.15`), `--no-ducking`,
`--captions none|srt|burn|both` (default `srt`),
`--caption-style professional|bold-yellow|minimal`,
`--timeline FILE` (overrides `--music/--labels/--captions`),
`--model tiny|base|small|medium` (default `small`; tiny/base are faster
but less accurate), `--workdir`, `--font`, `--clip-start/--clip-end`
(test on a slice of the video), `--no-overlay` (force audio-only even
if `--labels` is given; SRT captions are still written).

Outputs of a `--captions srt|both` run: the video, plus an SRT sidecar
next to it (`dubbed.mp4.srt`) and a copy in the workdir.

## Run (web UI — optional, phone-friendly)

The web UI is responsive: it stacks to a single column on narrow phone
screens, and all controls work by tap (no hover-only actions, no
drag-and-drop required).

```bash
./venv/bin/streamlit run app.py
```

Then open http://localhost:8501 in a browser **on the same computer**.

### Timeline editor walkthrough (UI step 3)

1. **Video track** — the video you uploaded in step 1.
2. **Voice track** — built from the step-2 voice settings (engine,
   gender, specific voice).
3. **Music tracks** — the first track is shown open; press
   **"Add another music track"** for each extra track (no limit).
   Per track: upload a music file, set volume (0–100%), keep ducking
   ON so the music dips under speech, or uncheck "Enable this track"
   to leave it out of the mix.
4. **Captions track** — mode: `both` (SRT file + burned-in styled
   captions), `srt` (file only), `burn` (video only), `off`; plus a
   style preset (professional / bold-yellow / minimal).
5. **Text overlays track** — optional labels JSON for translated
   on-screen text (same format as v2).
6. **Timeline save / load** — "Timeline JSON tayyar karo" exports the
   current timeline for download; a saved timeline can be loaded back
   and will govern the next run (or be passed to the CLI with
   `--timeline`).

### Phone se kholna (same Wi-Fi) — step by step

1. Laptop par apna local IP dekho:
   - Windows: Command Prompt me `ipconfig` (IPv4 Address, misal
     `192.168.1.5`).
   - Mac/Linux: Terminal me `ifconfig` ya `ip addr` (misal
     `192.168.1.5`).
2. Laptop par server is tarah chalao (0.0.0.0 ka matlab: phone se bhi
   reachable):
   `./venv/bin/streamlit run app.py --server.address 0.0.0.0`
3. Phone ko usi Wi-Fi se connect karo (laptop wali Wi-Fi).
4. Phone ke browser (Chrome) me kholo: `http://192.168.1.5:8501`
   (apna IP lagao, `:8501` mat bhoolna).
5. Agar Windows/macOS firewall poochhe to "Allow" dabao, warna phone
   connect nahi hoga.
6. Phone se video upload karo, dubbing laptop par hogi, phir result
   phone se hi download kar lo.

Note: ye sirf ghar/office Wi-Fi par kaam karta hai — laptop aur phone
ek hi network par hone chahiye. Mobile data (4G/5G) par ye tareeqa
nahi chalega, aur lambi video browser se upload karne me slow hogi;
lambi videos ke liye laptop par command line use karo (oopar dekho).

## Voices (free, no key)

### edge-tts (default) — Microsoft neural voices, needs internet
Male + female for 73 languages; the most-used defaults:
| Target | Female default | Male default |
|---|---|---|
| Arabic (`ar`) | `ar-EG-SalmaNeural` | `ar-EG-ShakirNeural` |
| Urdu (`ur`) | `ur-PK-UzmaNeural` | `ur-PK-AsadNeural` |
| Hindi (`hi`) | `hi-IN-SwaraNeural` | `hi-IN-MadhurNeural` |
| English (`en`) | `en-US-AriaNeural` | `en-US-GuyNeural` |
| Spanish (`es`) | `es-ES-ElviraNeural` | `es-ES-AlvaroNeural` |
| German (`de`) | `de-DE-KatjaNeural` | `de-DE-ConradNeural` |
| Russian (`ru`) | `ru-RU-SvetlanaNeural` | `ru-RU-DmitryNeural` |
| Persian (`fa`) | `fa-IR-DilaraNeural` | — |

Full list: `LANGUAGES.md`. List live voices on your network:
`./venv/bin/edge-tts --list-voices`. Change voice:
`--voice ar-SA-HamedNeural` (any edge-tts voice id) or
`--voice-gender male` (picks the male default for the target).

### Piper (offline fallback) — local neural voices, no internet at run time
| Target | Voice (auto-downloaded, ~63 MB) |
|---|---|
| Arabic (`ar`) | `ar_JO-kareem-medium` (male) |
| Urdu (`ur`) | `ur_PK-fasih-medium` (male) |
| Hindi (`hi`) | `hi_IN-pratham-medium` (male) |
| English (`en`) | `en_US-lessac-medium` (male) |

No verified Piper voice ships here for other languages — use edge or
gtts for those. Piper voices are good but slightly more robotic than
Microsoft neural voices. Switch with `--tts-engine piper`.

### gtts (coverage fallback) — Google Translate TTS, 100+ languages
Covers the 33 languages edge has no voice for (Albanian, Armenian,
Basque, Cebuano, ... — see `LANGUAGES.md`). **One voice per language,
no male/female choice, less natural than edge** — it exists so a dub
is possible at all for those languages, not because it sounds premium.
Switch with `--tts-engine gtts`.

### ElevenLabs (OPTIONAL, PAID) — higher-quality voices, your own key
Free engines above keep working with no key. ElevenLabs is only for
users who want its voices and already pay for an ElevenLabs account.

**Add your key (on your laptop, no CMD, no chat):** open the app →
⚙️ Settings — ElevenLabs → paste your key → Save. The key is saved
only on that machine (file `elevenlabs_settings.json` next to the
app); it is never sent anywhere except `api.elevenlabs.io` during a
dub, never logged, and never shared. CLI users can instead set the
env var `ELEVENLABS_API_KEY` — never pass a key as a CLI argument
(it would land in shell history). Pick a voice in Settings (list
from your account, or auto-pick by language + gender, or a manual
voice ID), then choose engine `elevenlabs` for the run:
`--tts-engine elevenlabs [--elevenlabs-voice <id>]`
`[--elevenlabs-model eleven_v3]`. List your voices any time:
`./venv/bin/python dub.py --list-elevenlabs-voices`.

**Cost warning: ElevenLabs is PAID — every dub spends YOUR own
ElevenLabs credits.** Check your balance/quota on your ElevenLabs
account before a long dub. A rejected key (401) or empty balance
(402) stops the run immediately with a clear message; nothing is
charged for failed requests.

**Language support (gated before any synthesis, so no credits are
spent on an unsupported language):** default model
`eleven_multilingual_v2` covers Arabic, English, German, Spanish,
Russian, French, Hindi, Italian, Portuguese, Polish, Turkish, Dutch,
and ~20 more. **Urdu, Persian and Bengali are NOT in multilingual
v2** — for those, either use a free engine or re-run with
`--elevenlabs-model eleven_v3` (70+ languages incl. Urdu; credit
cost may be higher). A language outside the chosen model's
documented set fails with a clear message instead of dubbing in
the wrong language.

**Honest note on voice testing:** edge-tts voices could not be
verified inside the sandboxed build environment (its proxy stalls the
Microsoft streaming endpoint), so the edge voice IDs in `LANGUAGES.md`
are the standard recommended Microsoft neural picks, not voices
auditioned here — verify with `edge-tts --list-voices` on your own
network. Piper and gTTS paths WERE verified end-to-end in this
environment (Piper in the v3 build test below; gTTS imports and
resolves in the test venv). If edge fails on your network, rerun with
`--tts-engine piper` (or `gtts` for coverage languages).

## Test evidence (60s clip, 2026-10-26 build test)

Input: a synthetic 60.0s 1920x1080 clip with Urdu narration (Piper
`ur_PK-fasih-medium`), dubbed Urdu → Arabic with
`--tts-engine piper --music music_bed.mp3 --captions both`.
- Transcription: local faster-whisper `small`, CPU — 23 segments.
- Translation: free gtx endpoint — 23/23 segments.
- TTS: Piper `ar_JO-kareem-medium` — 23/23 segments, 0 failed.
- Mix: voice + 1 music track (volume 0.15, ducking ON via ffmpeg
  sidechaincompress). Unit check on synthetic tracks: speech-region
  level −29.7 dB with ducking vs −29.1 dB without (music compressed
  under voice), gap-region level equal (−36.4 vs −36.1 dB, music at
  full volume where no voice is present). E2E gap check: final mix
  −50.0 dB in the trailing 5s (music bed audible) vs −91.0 dB for the
  voice-only track (silence). Two-track mix unit check also passes.
- Captions: SRT 23 cues + sidecar; ASS burn-in carries the
  professional style + Arabic text (unit round-trip check), and a
  burned caption is visible on an extracted frame (bottom-band pixel
  stdev 14.74 vs 0.0 for the uncaptioned source frame).
- Output: `dub.py verify` **PASS** — 60.0s exact, 1.5 MB, 1920x1080
  h264 + AAC, audio −19.1 dB at 30s (audible), faststart OK.
  All intermediates live in `--workdir`; nothing is written to `/tmp`.
- Streamlit UI serves HTTP 200 (phone-friendly single-column layout;
  see "Laptop ya phone?" above).

## Translation quality (read this)

Free machine translation is good for straightforward narration and
weaker for idioms, wordplay and ambiguous words. Observed example:
Urdu "شیر" (lion) was machine-translated to Arabic "النمر" (tiger).
Two fixes, in order of quality:
1. **Best:** `--translation your_file.json` — a human-checked
   translation in segments format `[{"start","end","text"}]`. The tool
   keeps your text exactly and only does voice + sync + merge.
2. **Quick fix:** `--glossary glossary.json` — target-side word
   replacements applied after machine translation, e.g.
   `{"النمر": "الأسد", "النمور": "الأسود"}`.

Two more observed behaviours:
- If Whisper auto-detects the language but writes the transcript in
  Latin (romanized) script, free translation quality drops sharply —
  the fallback service may return near-untranslated text. For Urdu /
  Hindi sources, force `--src ur` or `--src hi` (native script output
  translates far better) or supply `--translation`.
- The free translation endpoint rate-limits shared IPs (HTTP 429). The
  tool retries, then automatically falls back to a second free
  service; if both are throttled, re-run later or supply
  `--translation` — the run resumes from already-finished TTS segments.

Translated lines are time-stretched (max 2x, min 0.5x) to fit their
original slots, so a much longer/shorter translation still stays in
sync — at the cost of slightly faster/slower speech on those lines.

## Labels (on-screen text translation)

`labels.json` is a JSON array; coordinates are in INPUT video pixels:

```json
[{"name": "buffaloes", "text": "الجواميس البرية",
  "t0": 78.1, "t1": 80.2,
  "bar": {"x": 0, "y": 880, "w": 1150, "h": 190, "color": "0xCD0000"},
  "font_size": 88}]
```

- `t0`/`t1`: seconds the banner is visible. `bar`: the solid box
  drawn over the original text (colour as `0xRRGGBB`). `text`: the
  translated text, drawn centred in the box.
- Only the listed bars are covered, only for the listed times.
  **Channel logos, watermarks and branding are never touched.**
- With labels or burned-in captions, the video is re-encoded (CRF 18,
  same resolution, faststart) because overlays cannot be added to a
  copied stream. Without labels/captions, the video stream is copied
  untouched (faster, and the original quality is bit-identical).
- Text is rendered with Pillow + libraqm (correct connected Arabic /
  Urdu letters). ffmpeg drawtext is never used for Arabic/Urdu — it
  cannot shape connected letters. Burned-in captions use libass
  (HarfBuzz shaping) for the same reason.
- `detect` finds candidate banner windows (saturated solid-colour
  blocks in the lower third — red, blue, etc.), but it cannot read or
  translate the text — you confirm the text and write `labels.json`
  yourself. Times are approximate (frame sampling), and white/black
  banners are out of scope (they look like ordinary bright/dark scene
  areas without OCR); write those by hand.

## Timeline JSON format

A timeline is a JSON object with a `version` (3) and a `tracks` list.
Track types: `video`, `voice`, `music`, `captions`, `overlays`.
Example (what the UI exports):

```json
{"version": 3, "tracks": [
  {"type": "video", "enabled": true},
  {"type": "voice", "enabled": true},
  {"type": "music", "enabled": true, "file": "bed.mp3",
   "volume": 0.15, "ducking": true},
  {"type": "captions", "enabled": true, "mode": "both",
   "style": "professional"},
  {"type": "overlays", "enabled": true, "labels": []}
]}
```

`timeline.py` validates a timeline before any slow work starts:
missing music file, volume outside 0.0–1.0, or a bad captions mode
fails fast with a clear error instead of after transcription.

## Output

- MP4, same resolution as the input (1080p kept), high bitrate,
  `faststart` set (plays while downloading, mobile-friendly).
- Audio: the dubbed voice + background music mix (original audio is
  replaced, not mixed under it — same as a real dub, with music as
  the bed).
- SRT sidecar next to the output when captions are `srt`/`both`.
- Intermediates (transcript, translation, per-segment audio, dub
  track, final mix, captions) stay in `--workdir` (default
  `<input>_dub_work/`) so a failed run can resume TTS segments
  instead of starting over. Nothing is written to `/tmp`.

## Limitations (honest)

- Free machine translation can mistranslate words and idioms; use
  `--translation` for publish-grade accuracy.
- edge-tts needs a normal (non-proxied) network; behind an
  SSL-intercepting proxy its endpoint fails — use piper/gtts there.
  Edge voice IDs are standard picks, not auditioned here (see
  "Honest note on voice testing" above).
- gTTS voices are single-voice and less natural than edge neural
  voices; they exist for coverage, not quality.
- Piper voices sound more robotic than Microsoft neural voices.
- Very long videos take a while: transcription is CPU-bound
  (~real-time or slower on weak machines) and TTS runs per segment.
- Banner detection only finds saturated solid-colour lower-third
  bars; fancy animated/gradient titles and white/black banners need
  manual label coordinates.
- Caption ASS fonts fall back via fontconfig if Noto Naskh/Nastaliq
  is missing on the user's laptop (install `fonts-noto`).
- Ducking needs ffmpeg's sidechaincompress; without it, music uses
  its fixed volume (a note is printed).
- This tool dubs a video you own or have the right to adapt. Dubbing
  someone else's video and re-uploading it as your own can violate
  copyright and YouTube's reused-content rules.
