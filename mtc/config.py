"""config.py – Constants, paths, palette, logging setup."""
import sys, io, logging
from pathlib import Path
from logging.handlers import RotatingFileHandler

# ── Fix Windows console ───────────────────────────────────────────────────────
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# ── Paths ─────────────────────────────────────────────────────────────────────
ROOT_DIR   = Path(__file__).resolve().parent.parent
APK_PATH   = ROOT_DIR / "MTC.apk"
OUTPUT_DIR = ROOT_DIR / "downloads"
LOG_FILE   = ROOT_DIR / "mtc.log"

# ── MTC App ───────────────────────────────────────────────────────────────────
PACKAGE     = "com.novelfever.app.android"
PACKAGE_ALT = "com.example.novelfeverx"

# ── ADB / Automation ─────────────────────────────────────────────────────────
SCROLL_STEPS    = 20
SCROLL_DELAY    = 0.25
NAV_DELAY       = 0.8
TAP_DELAY       = 0.15
BACK_DELAY      = 0.15
INSTALL_TIMEOUT = 180
KEY_BACK  = 4
KEY_HOME  = 3
KEY_ENTER = 66

# BlueStacks ADB paths (priority)
BS_ADB_PATHS = [
    Path("C:/Program Files/BlueStacks_nxt/HD-Adb.exe"),
    Path("C:/Program Files/BlueStacks/HD-Adb.exe"),
    Path("C:/Program Files (x86)/BlueStacks_nxt/HD-Adb.exe"),
]
# Fallback ADB paths
OTHER_ADB_PATHS = [
    Path.home() / "AppData/Local/Android/Sdk/platform-tools/adb.exe",
    Path("C:/LDPlayer/LDPlayer9/adb.exe"),
    Path("C:/Program Files/LDPlayer/LDPlayer9/adb.exe"),
    Path("C:/Program Files/Nox/bin/nox_adb.exe"),
]
# Accessibility services
ACCESSIBILITY_SERVICES = [
    "com.google.android.marvin.talkback/com.google.android.marvin.talkback.TalkBackService",
    "com.google.android.marvin.talkback/.TalkBackService",
    "com.android.talkback/com.google.android.marvin.talkback.TalkBackService",
]

# ── API ───────────────────────────────────────────────────────────────────────
API_BASE    = "https://android.lonoapp.net/api"
USER_AGENT  = "Dart/3.0 (dart:io)"
API_TIMEOUT = 30
API_RETRY   = 3

# ── UI Palette ────────────────────────────────────────────────────────────────
BG     = "#ffffff"
BG2    = "#f8f9fa"
BORDER = "#dadce0"
BLUE   = "#1a73e8"
BLUE2  = "#1557b0"
BHOV   = "#e8f0fe"
FG     = "#202124"
FG2    = "#5f6368"
FG3    = "#80868b"
GREEN  = "#137333"
YELLOW = "#f29900"
RED    = "#c5221f"
ORANGE = "#fa7b17"

FONT      = ("Segoe UI", 9)
FONT_BOLD = ("Segoe UI", 9,  "bold")
FONT_HEAD = ("Segoe UI", 11, "bold")
FONT_MONO = ("Consolas", 8)

# ── Hot reload ────────────────────────────────────────────────────────────────
EXIT_RELOAD = 42

# ── Logging ───────────────────────────────────────────────────────────────────
log = logging.getLogger("mtc")
log.setLevel(logging.DEBUG)
_fh = RotatingFileHandler(LOG_FILE, maxBytes=5*1024*1024, backupCount=3,
                           encoding="utf-8")
_fh.setFormatter(logging.Formatter(
    "%(asctime)s  %(levelname)-5s  %(message)s", datefmt="%Y-%m-%d %H:%M:%S"))
log.addHandler(_fh)
_ch = logging.StreamHandler(sys.stderr)
_ch.setLevel(logging.INFO)
_ch.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
log.addHandler(_ch)
