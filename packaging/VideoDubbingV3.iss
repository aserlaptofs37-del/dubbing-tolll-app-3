; Inno Setup script for Video Dubbing v3 -- produces Setup.exe.
;
; Build (on Windows, after the PyInstaller step, from the repo root):
;   "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" packaging\VideoDubbingV3.iss
; Output: packaging\installer-output\VideoDubbingV3-Setup.exe
;
; Paths below use {#SourcePath} (= this script's folder, packaging/), so
; the build works no matter which directory ISCC is launched from.
;
; INSTALL MODEL -- no admin-only assumptions:
;   PrivilegesRequired=lowest + {autopf} means:
;     * Normal double-click (not "Run as administrator") installs
;       per-user to %LOCALAPPDATA%\Programs\VideoDubbingV3 -- NO admin
;       prompt, and the folder is user-writable. That matters: Piper
;       voice models download into <install>\voices (see launcher.py),
;       which only works if the install folder is writable.
;     * If the user DOES run Setup as administrator, {autopf} becomes
;       real Program Files instead. That install works, but Piper
;       downloads then fail with a permission error -- edge/gTTS
;       engines still work, or reinstall per-user. See BUILD.md.
;   Uninstall removes the app files. It deliberately does NOT delete
;   %LOCALAPPDATA%\VideoDubbingV3 (Whisper models + work files), so an
;   uninstall/reinstall does not force a ~470 MB re-download.

#define AppName "Video Dubbing v3"
#define AppVersion "3.0.0"
#define AppPublisher "Funny"
#define AppExe "VideoDubbingV3.exe"

[Setup]
AppId={{7A3B1C9D-4E2F-4A8B-9C1D-5E6F7A8B9C0D}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
DefaultDirName={autopf}\VideoDubbingV3
DefaultGroupName={#AppName}
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
OutputDir={#SourcePath}\installer-output
OutputBaseFilename=VideoDubbingV3-Setup
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
DisableProgramGroupPage=yes
UninstallDisplayIcon={app}\{#AppExe}
; Uncomment after dropping an icon file into packaging/:
; SetupIconFile={#SourcePath}\app.ico

[Tasks]
Name: "desktopicon"; Description: "Desktop icon"; GroupDescription: "Additional icons:"; Flags: checkedonce

[Files]
; The PyInstaller onedir output. Built by the workflow / BUILD.md step
; before this script runs; the build fails loudly if it is missing.
Source: "{#SourcePath}\..\dist\VideoDubbingV3\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Fonts]
; Install the bundled Noto/DejaVu fonts into Windows Fonts so
; libass/fontconfig can resolve the "Noto Naskh Arabic" / "DejaVu Sans"
; caption families (see captions.py). If a TTF is missing from
; packaging\fonts\, DELETE its line here or the build fails.
; uninsneveruninstall: uninstall must not yank shared system fonts.
Source: "{#SourcePath}\fonts\NotoNaskhArabic-Bold.ttf"; DestDir: "{fonts}"; FontInstall: "Noto Naskh Arabic"; Flags: onlybelowversion 0 0 uninsneveruninstall
Source: "{#SourcePath}\fonts\NotoNastaliqUrdu-Bold.ttf"; DestDir: "{fonts}"; FontInstall: "Noto Nastaliq Urdu"; Flags: onlybelowversion 0 0 uninsneveruninstall
Source: "{#SourcePath}\fonts\DejaVuSans.ttf"; DestDir: "{fonts}"; FontInstall: "DejaVu Sans"; Flags: onlybelowversion 0 0 uninsneveruninstall

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\{#AppExe}"
Name: "{group}\Uninstall {#AppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExe}"; Tasks: desktopicon

[Run]
; Offer to launch right after install (unchecked box = skip). The app
; opens in the default browser; first launch takes ~30-60 seconds
; (Streamlit + model checks) -- the console window shows progress.
Filename: "{app}\{#AppExe}"; Description: "Launch {#AppName}"; Flags: nowait postinstall skipifsilent
