"""Video Dubbing v3 -- Windows desktop launcher (PyInstaller entry point).

This is the ONLY new code for the desktop build. It does not change any
v3 app source file: it just starts the existing Streamlit UI (app.py)
from inside the frozen bundle, with the environment a desktop app needs:

  * Bundled ffmpeg/ffprobe come FIRST on PATH. The v3 code calls
    "ffmpeg"/"ffprobe" by bare name, so without this the packaged app
    would depend on a system ffmpeg install.
  * Whisper models download into a per-user cache
    (%LOCALAPPDATA%\\VideoDubbingV3\\models\\huggingface) instead of the
    default HF cache, so the cache survives and is easy to find/clear.
  * The working directory is a per-user work folder
    (%LOCALAPPDATA%\\VideoDubbingV3\\work). app.py builds its workdir
    from os.getcwd(), and Program Files is not writable for a normal
    user, so launching from the install dir would break uploads/output.
  * Piper voice models still download into <install-dir>\\voices
    (tts.py resolves app_dir from dub.py's location, which in an
    onedir bundle is the install dir). That works for the default
    per-user install (Inno Setup {autopf} -> %LOCALAPPDATA%\\Programs,
    user-writable). If the app was installed as admin into real
    Program Files, Piper downloads fail with a permission error --
    in that case use the edge or gTTS engines, or reinstall per-user.
    See BUILD.md.

First-run behaviour (no crash, clear message):
  * If the Whisper "small" model is not in the cache yet, the launcher
    prints a plain notice and still starts the UI. The model (~470 MB)
    downloads once, automatically, on the FIRST dub -- internet is
    needed that once. If the machine is offline before that download,
    the first dub's transcription step fails with an error shown in
    the UI (the app itself stays open); connect once and retry.
  * Piper voices (~63 MB per language) download on first use per
    language, same rule: offline before first download -> that dub
    fails with a clear error, app stays open.

Run: this file is the PyInstaller entry point (see VideoDubbingV3.spec).
It is never run with a system Python on the user's machine.
"""

import os
import shutil
import socket
import sys
import threading
import urllib.request
import webbrowser

APP_NAME = "VideoDubbingV3"
PORT = 8501
HOST = "127.0.0.1"  # laptop-local only; see BUILD.md for the LAN option
STARTUP_TIMEOUT_SECS = 180


def bundle_dir():
    """Directory holding the frozen app (onedir: beside the .exe)."""
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def bundle_file(bdir, name):
    """Resolve a bundled file/dir: PyInstaller 6 onedir puts data files
    under _internal\\, while older layouts put them beside the exe.
    Falls back to the beside-exe path so existing checks still fail
    cleanly when the file is missing from both places."""
    p = os.path.join(bdir, name)
    if os.path.exists(p):
        return p
    p2 = os.path.join(bdir, "_internal", name)
    if os.path.exists(p2):
        return p2
    return p


def user_data_dir():
    base = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
    path = os.path.join(base, APP_NAME)
    os.makedirs(path, exist_ok=True)
    return path


def port_busy():
    try:
        with socket.create_connection((HOST, PORT), timeout=1):
            return True
    except OSError:
        return False


def wait_for_server():
    """Poll Streamlit's /healthz until it answers, or time out."""
    deadline = __import__("time").time() + STARTUP_TIMEOUT_SECS
    while __import__("time").time() < deadline:
        try:
            with urllib.request.urlopen(
                    "http://%s:%d/healthz" % (HOST, PORT), timeout=2) as r:
                if r.status == 200:
                    return True
        except Exception:
            pass
        __import__("time").sleep(2)
    return False


def whisper_model_cached(hf_home):
    """Heuristic: faster-whisper 'small' cache present?"""
    hub = os.path.join(hf_home, "hub", "models--Systran--faster-whisper-small")
    if not os.path.isdir(hub):
        return False
    snap = os.path.join(hub, "snapshots")
    if not os.path.isdir(snap):
        return False
    return any(os.listdir(snap))


def main():
    bdir = bundle_dir()
    data = user_data_dir()
    work = os.path.join(data, "work")
    os.makedirs(work, exist_ok=True)

    # 1. Bundled ffmpeg/ffprobe first on PATH (fallback: system ffmpeg).
    ffmpeg_bin = bundle_file(bdir, "ffmpeg")
    if os.path.isdir(ffmpeg_bin):
        os.environ["PATH"] = ffmpeg_bin + os.pathsep + os.environ["PATH"]

    # 2. Per-user Whisper model cache (only if the user did not set one).
    hf_home = os.environ.setdefault(
        "HF_HOME", os.path.join(data, "models", "huggingface"))

    # 2b. Per-user ElevenLabs settings file, so an API key entered in
    # the app's Settings lands in %LOCALAPPDATA%\VideoDubbingV3 (not
    # next to the app in the install dir). See BUILD.md follow-up.
    os.environ.setdefault(
        "ELEVENLABS_SETTINGS_FILE",
        os.path.join(data, "elevenlabs_settings.json"))

    # 3. Writable working directory (app.py builds WORKDIR from cwd).
    os.chdir(work)

    # 4. Preflight, with plain messages instead of tracebacks.
    ffmpeg = shutil.which("ffmpeg")
    ffprobe = shutil.which("ffprobe")
    if not ffmpeg or not ffprobe:
        print("ERROR: ffmpeg/ffprobe not found (not bundled, not on PATH).")
        print("Reinstall Video Dubbing v3, or install ffmpeg and add it")
        print("to PATH, then start the app again.")
        return 2
    print("Video Dubbing v3 is starting...")
    print("Work folder (your videos and outputs): %s" % work)
    if not whisper_model_cached(hf_home):
        print("FIRST RUN NOTE: the transcription model (~470 MB) is not")
        print("downloaded yet. It downloads automatically, once, on your")
        print("first dub -- internet is needed that once. If you are")
        print("offline now, the first dub will show an error instead of")
        print("transcribing; connect once and retry. The app stays open.")

    # 5. Already running? Just open the browser on the existing server.
    if port_busy():
        print("The app is already running -- opening it in your browser.")
        webbrowser.open("http://%s:%d" % (HOST, PORT))
        return 0

    # 6. Start Streamlit in a thread, open the browser once it answers.
    app_py = bundle_file(bdir, "app.py")
    if not os.path.exists(app_py):
        print("ERROR: app.py is missing from the install folder: %s" % bdir)
        print("Reinstall Video Dubbing v3.")
        return 2

    def run_server():
        from streamlit.web import cli as stcli
        sys.argv = ["streamlit", "run", app_py,
                    "--server.port", str(PORT),
                    "--server.address", HOST,
                    "--server.headless", "true",
                    "--browser.gatherUsageStats", "false",
                    # Frozen (PyInstaller) builds resolve
                    # global.developmentMode as true, which Streamlit
                    # refuses to combine with an explicit server.port
                    # (the run #8 smoke-test crash). Force it off.
                    "--global.developmentMode", "false"]
        stcli.main()

    thread = threading.Thread(target=run_server, daemon=True)
    thread.start()
    if wait_for_server():
        print("App is ready -- opening it in your browser.")
    else:
        print("The app is taking longer than usual to start; opening")
        print("the browser anyway -- if the page is empty, wait a")
        print("minute and refresh.")
    webbrowser.open("http://%s:%d" % (HOST, PORT))
    thread.join()
    return 0


if __name__ == "__main__":
    try:
        code = main()
    except KeyboardInterrupt:
        code = 0
    except Exception as exc:  # never die silently from a desktop icon
        print("Video Dubbing v3 failed to start: %s: %s"
              % (type(exc).__name__, exc))
        try:
            input("Press Enter to close this window...")
        except (EOFError, KeyboardInterrupt):
            pass
        code = 1
    sys.exit(code)
