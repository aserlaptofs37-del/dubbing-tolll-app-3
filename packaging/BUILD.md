# Video Dubbing v3 — Windows desktop build (Setup.exe)

**Status: build package COMPLETE, Setup.exe NOT built yet.**
A Windows `.exe` cannot be built or tested on the Linux machine this
package was written on (PyInstaller does not cross-build Linux ->
Windows reliably). Nothing here claims a finished `.exe` exists. The
exact remaining step is at the bottom: one GitHub Actions run on a
Windows runner, then a manual test on a real Windows laptop.

## What the user gets after the build

Download `VideoDubbingV3-Setup.exe` -> double-click -> Next/Install
-> desktop icon "Video Dubbing v3". Double-click the icon: the app
opens in the browser. No CMD, no Python, no typing, no venv, no pip.
It works for lifetime (the app is local; only the TTS/model services
below need internet, as noted).

## Repo layout the build expects

```
repo root  (= the v3 app directory)
  app.py, dub.py, transcribe.py, translate.py, tts.py, mix.py,
  render.py, captions.py, overlay.py, verify.py, detect.py,
  timeline.py, languages.py, requirements.txt
  packaging/
    launcher.py            # PyInstaller entry point (only new code)
    VideoDubbingV3.spec    # PyInstaller build definition
    VideoDubbingV3.iss     # Inno Setup installer script
    build-windows.yml      # GitHub Actions workflow (copy of the live one)
    fonts/
      README.txt           # where to get the 3 .ttf files
      *.ttf                # maintainer adds these before building
    ffmpeg-bin/            # created by the workflow, do NOT commit
    installer-output/      # created by the build, do NOT commit
  .github/workflows/build-windows.yml   # the live workflow (identical copy)
```

## How to produce Setup.exe (maintainer steps)

1. **Put the repo on GitHub** with the layout above. Add the three
   `.ttf` files to `packaging/fonts/` per `fonts/README.txt` first --
   the workflow fails fast with a clear message if they are missing.
2. **Actions tab -> "Build Windows Setup" -> Run workflow.**
   The workflow (windows-latest runner) does, in order:
   Python 3.11 -> `pip install -r requirements.txt` + PyInstaller ->
   download Gyan ffmpeg full build, copy `ffmpeg.exe`/`ffprobe.exe`
   into `packaging/ffmpeg-bin/` -> PyInstaller (spec) -> smoke test
   (built .exe must answer on `localhost:8501/healthz`) -> Inno Setup
   (`ISCC.exe`) -> uploads the `VideoDubbingV3-Setup` artifact.
   On a version tag (`v*`) it also attaches Setup.exe to the Release.
3. **Download the artifact** (`VideoDubbingV3-Setup.exe`).
4. **Test on a real Windows laptop** with the checklist below. Do NOT
   send it to the user until the checklist passes.

## Test checklist (Windows laptop, ~30 minutes)

- [ ] Install: double-click Setup.exe, no admin prompt (per-user
      install), desktop icon appears, Start menu entry appears.
- [ ] First launch: double-click the desktop icon. A console window
      shows "Video Dubbing v3 is starting...", then the browser opens
      the app. First launch takes ~30-60 seconds -- that is normal.
- [ ] First dub WITH internet: dub a 60s clip, target Arabic. Watch
      the console: the Whisper "small" model (~470 MB) downloads once.
      The dub must finish and download as MP4.
- [ ] Second run OFFLINE: disconnect internet, dub again with the
      Piper engine and a language whose voice was already downloaded.
      It must work fully offline (cached model + cached voice).
- [ ] Offline BEFORE first download: on a fresh machine with no
      models, disconnect internet and try a dub. It must show a clear
      error in the UI, NOT crash the app. Reconnect, retry, it works.
- [ ] Captions: dub with captions ON. Arabic burn-in captions must
      render as real glyphs (not boxes) -- this proves the bundled
      fonts + libass work.
- [ ] Uninstall: Control Panel -> Uninstall. App files go away;
      `%LOCALAPPDATA%\VideoDubbingV3` (models + work files) stays, so
      reinstalling does not re-download ~470 MB.

## Expected sizes (ESTIMATES -- measure on the Windows runner)

| Piece | Estimate | Notes |
| --- | --- | --- |
| PyInstaller onedir (Python + Streamlit + faster-whisper/ctranslate2 + onnxruntime + av + deps) | ~700 MB - 1 GB | Streamlit + ctranslate2 + onnxruntime dominate |
| Bundled ffmpeg.exe + ffprobe.exe (full build, libass) | ~110 MB | Required for styled caption burn-in |
| Installer (Setup.exe, lzma2 compressed) | ~400 - 600 MB | User's one download |
| Installed size (app + ffmpeg) | ~1.0 - 1.5 GB | Before models |
| Whisper "small" model (first run, NOT in installer) | ~470 MB | Downloads once, then offline |
| Piper voice per language (first use, NOT in installer) | ~63 MB | ar/ur/hi/en have curated voices |
| edge-tts / gTTS | 0 MB local | Need internet EVERY use (voices stream) |

Keeping the ~470 MB model OUT of the installer is deliberate: it keeps
Setup.exe smaller and lets the model update without rebuilding.

## Design decisions (and why)

- **onedir, not onefile.** onefile extracts ~1 GB to temp on every
  launch (slow start) and Windows Defender flags onefile PyInstaller
  bundles far more often. onedir starts fast and is patchable. The
  user never sees the folder -- only the desktop shortcut.
- **ffmpeg BUNDLED, not system-only.** The v3 code calls bare
  `ffmpeg`/`ffprobe`. The user's laptop already has winget ffmpeg,
  but a "real software" must work on ANY machine. The ~110 MB is
  worth it. If bundled binaries are ever missing, the launcher falls
  back to a system ffmpeg on PATH.
- **Per-user install (PrivilegesRequired=lowest + {autopf}).**
  No admin prompt for a normal double-click, and the install folder
  is user-writable -- which Piper voice downloads REQUIRE (they land
  in `<install>\voices`). An admin install into real Program Files
  breaks Piper downloads (edge/gTTS still work).
- **Whisper cache redirected** to `%LOCALAPPDATA%\VideoDubbingV3\
  models\huggingface` (launcher sets `HF_HOME`). Predictable,
  survives reinstalls, easy to clear.
- **Work folder redirected** to `%LOCALAPPDATA%\VideoDubbingV3\work`
  (launcher sets cwd). app.py builds its workdir from `os.getcwd()`,
  and Program Files is not writable for normal users.
- **Console window KEPT (console=True).** For a non-technical user,
  a silent failure from a desktop icon is the worst outcome. The
  console shows first-run downloads and real errors. Flip to
  `console=False` in the spec only after the build is proven stable.
- **No v3 source modified.** The only new code is `packaging/
  launcher.py`. v2 was not touched at all.
- **ElevenLabs (optional, paid engine, added after packaging).**
  `elevenlabs_engine.py` needs no new pip package (stdlib urllib) and
  no spec change. ONE packaging follow-up: the launcher should set
  `ELEVENLABS_SETTINGS_FILE=%LOCALAPPDATA%\VideoDubbingV3\
  elevenlabs_settings.json` so the user's API key is stored in the
  per-user folder, not next to the app in the install dir. The key
  is entered in the app's Settings on the user's own machine; it is
  never baked into the installer.

## Known risks (read before shipping)

1. **Windows Defender / SmartScreen false positives.** PyInstaller
   bundles are routinely flagged by heuristic AV on first release.
   Mitigations, in order: (a) ship the onedir build (fewer flags
   than onefile); (b) if flagged, submit the file to Microsoft
   Defender analysis for clearance; (c) code-signing removes most
   warnings but needs a paid certificate -- not in this package.
   Tell the user: if SmartScreen appears, "More info -> Run anyway".
2. **Streamlit startup time.** First launch ~30-60s (Python +
   Streamlit + native libs). The console explains the wait; later
   launches are faster. If it ever exceeds ~3 minutes, something is
   wrong -- check the console, not the browser.
3. **libass fonts on Windows.** Gyan ffmpeg bundles fontconfig,
   which reads Windows Fonts. The installer installs the 3 bundled
   fonts, so "Noto Naskh Arabic" resolves. If Arabic captions still
   show boxes, the fonts did not install -- check Windows Fonts.
4. **Labels/overlay feature on Windows (NOT fixed here).**
   `render.py` looks for Linux font paths only and raises a clear
   error when none exist. The core dub (transcription, TTS, burn-in
   captions) does not use it. Fix (needs approval, 3 lines):
   add Windows paths (`C:\Windows\Fonts\NotoNaskhArabic-Bold.ttf`,
   `C:\Windows\Fonts\NotoNastaliqUrdu-Bold.ttf`) to the font lists
   in `render.py`. Deliberately NOT applied here: the packaging
   task forbids modifying v3 source beyond the launcher.
5. **Admin install breaks Piper.** See "Design decisions". If the
   user installed as admin and Piper fails, reinstall per-user.
6. **edge-tts and gTTS need internet every use.** Only Piper +
   cached Whisper are truly offline. The UI already offers the
   engine choice; the user must pick Piper for offline dubs.
7. **Streamlit/PyInstaller version drift.** `requirements.txt`
   leaves `streamlit` unpinned. If a future Streamlit breaks the
   frozen build, pin the last known-good version in the workflow
   and rebuild. Record the working versions after the first green
   build.
8. **Sizes are estimates.** Measure `dist/`, the installer, and the
   first-run downloads on the Windows runner and update the table
   above with real numbers before promising the user a size.

## Remaining step to a downloadable Setup.exe (exact)

1. Repo on GitHub (layout above) + 3 fonts in `packaging/fonts/`.
2. Actions -> "Build Windows Setup" -> Run workflow -> wait for green.
3. Download the `VideoDubbingV3-Setup` artifact.
4. Pass the Windows test checklist above.
5. Only then send Setup.exe to the user with: double-click to
   install, desktop icon to launch, first dub needs internet once
   (~470 MB model download, a few minutes), after that Piper dubs
   work offline.

## What was verified on Linux (and what was not)

- Verified: `launcher.py` + `VideoDubbingV3.spec` compile
  (`py_compile`); the workflow YAML parses; the two workflow copies
  are identical; no v3 source file was modified (all mtimes still
  2026-10-26); v2 untouched.
- NOT verified (impossible on Linux): the PyInstaller build itself,
  the Inno Setup compile, launching the .exe, any dub, font
  rendering, Defender behaviour. All of that is the Windows runner +
  manual checklist above. Do not describe this package as a tested
  Windows app until those pass.
