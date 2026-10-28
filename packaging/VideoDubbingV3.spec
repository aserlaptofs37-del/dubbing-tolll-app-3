# PyInstaller spec for Video Dubbing v3 (Windows desktop build).
#
# Layout this spec expects (see BUILD.md):
#   repo root = the v3 app directory (app.py, dub.py, *.py, requirements.txt)
#   repo root / packaging / VideoDubbingV3.spec   <- this file
#   repo root / packaging / launcher.py           <- frozen entry point
#   repo root / packaging / ffmpeg-bin /          <- ffmpeg.exe, ffprobe.exe
#   repo root / packaging / fonts /               <- *.ttf (optional but
#                                                      recommended, see below)
#
# Build (on a Windows machine / Windows runner, from the repo root):
#   pip install -r requirements.txt
#   pip install pyinstaller
#   pyinstaller packaging/VideoDubbingV3.spec --noconfirm
# Output: dist/VideoDubbingV3/  (a folder; the Inno Setup script wraps it)
#
# ONEDIR, not onefile -- deliberate (see BUILD.md):
#   * onefile extracts ~1 GB to a temp dir on EVERY launch (slow start,
#     and Windows Defender flags onefile PyInstaller bundles far more
#     often). onedir starts fast and is patchable by replacing files.
#   * Cost: the install is a folder of many files. The user never sees
#     it -- the desktop shortcut points at VideoDubbingV3.exe.

import glob
import os

SPEC_DIR = os.path.dirname(os.path.abspath(SPEC))
SRC = os.path.dirname(SPEC_DIR)  # repo root = v3 app directory

# --- data files: the v3 .py modules must exist as REAL files at runtime,
# because Streamlit executes app.py as a script and app.py inserts its own
# directory on sys.path before importing the sibling modules. ----------
_v3_modules = [
    "app.py", "dub.py", "transcribe.py", "translate.py", "tts.py",
    "mix.py", "render.py", "captions.py", "overlay.py", "verify.py",
    "detect.py", "timeline.py", "languages.py",
]
datas = [(os.path.join(SRC, m), ".") for m in _v3_modules
         if os.path.exists(os.path.join(SRC, m))]

# Optional: bundled Noto/DejaVu fonts (see packaging/fonts/README.txt).
# They land in <install>/fonts/ and are ALSO installed into Windows
# Fonts by the Inno Setup script, so libass/fontconfig can resolve the
# "Noto Naskh Arabic" / "DejaVu Sans" caption families. If the folder
# is empty, the build still works; Arabic burn-in captions then fall
# back to a default font instead of failing (see captions.py).
for ttf in glob.glob(os.path.join(SPEC_DIR, "fonts", "*.ttf")):
    datas.append((ttf, "fonts"))

# --- bundled ffmpeg/ffprobe (full Gyan build: libass included, needed
# for styled caption burn-in). They land in <install>/ffmpeg/, which
# launcher.py puts first on PATH. If the binaries are absent, the
# build still succeeds but the app falls back to a system ffmpeg. -----
binaries = []
for exe in ("ffmpeg.exe", "ffprobe.exe"):
    p = os.path.join(SPEC_DIR, "ffmpeg-bin", exe)
    if os.path.exists(p):
        binaries.append((p, "ffmpeg"))
    else:
        print("WARNING: %s not found in packaging/ffmpeg-bin/ -- "
              "the build will rely on a system ffmpeg." % exe)

# --- hidden imports: PyInstaller's static analysis misses these because
# they are imported dynamically (Streamlit plugins, faster-whisper's
# backend, TTS engines, translation backends). --------------------------
hiddenimports = [
    "PIL", "PIL.Image", "arabic_reshaper", "bidi", "bidi.algorithm",
    "ctranslate2", "onnxruntime", "edge_tts", "gtts", "gtts.lang",
    "deep_translator", "deep_translator.google",
    "faster_whisper", "av", "av.audio", "av.container",
    "streamlit", "streamlit.web.cli",
]

# collect_all pulls each package's data files (Streamlit's static web
# assets, ctranslate2's native libs, onnxruntime DLLs, pyarrow, ...).
# These are the packages PyInstaller most often breaks without this.
# collect_all returns (datas, binaries, hiddenimports), in that order.
for pkg in ("streamlit", "altair", "pyarrow", "faster_whisper",
            "ctranslate2", "edge_tts", "gtts", "piper", "av",
            "deep_translator"):
    try:
        pkg_datas, pkg_binaries, pkg_hidden = collect_all(pkg)
        datas += pkg_datas
        binaries += pkg_binaries
        hiddenimports += pkg_hidden
    except Exception as exc:  # a missing optional package must not kill
        print("WARNING: collect_all(%s) skipped: %s" % (pkg, exc))  # the build

a = Analysis(
    [os.path.join(SPEC_DIR, "launcher.py")],
    pathex=[SRC],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Not used by this stack; excluding them saves size. Remove an
        # entry here if a future feature needs that package.
        "tkinter", "matplotlib", "PyQt5", "PySide6",
        "IPython", "notebook", "jupyter_client",
    ],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="VideoDubbingV3",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,  # UPX breaks ctranslate2/onnxruntime DLLs; keep it off.
    console=True,  # console stays: first-run downloads + errors must be
    # VISIBLE for a non-technical user, not a silent exit. Flip to
    # False in a later release once the build is proven stable.
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # icon=None  # drop an app.ico into packaging/ and set
    # icon=os.path.join(SPEC_DIR, "app.ico") to brand the .exe.
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="VideoDubbingV3",
)
