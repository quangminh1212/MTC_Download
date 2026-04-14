"""config.py – Constants, paths, palette, logging setup (API-only)."""
import sys, io, logging
from pathlib import Path
from logging.handlers import RotatingFileHandler

# ── Fix Windows console & Global Logging ────────────────────────────────────
LOG_FILE = Path(__file__).resolve().parent.parent / "log.txt"


class _DualLogger(io.TextIOWrapper):
    def __init__(self, buffer, encoding, errors, orig):
        super().__init__(buffer, encoding=encoding, errors=errors)
        # Reconfigure original terminal stream to UTF-8 so Vietnamese prints correctly
        try:
            orig.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
        self.terminal = orig
        self.log_file = open(LOG_FILE, "a", encoding="utf-8")

    def write(self, message):
        try:
            self.terminal.write(message)
        except UnicodeEncodeError:
            self.terminal.write(message.encode("utf-8", "replace").decode("utf-8"))
        self.log_file.write(message)
        self.log_file.flush()

    def flush(self):
        self.terminal.flush()
        self.log_file.flush()


if sys.platform == "win32":
    sys.stdout = _DualLogger(sys.stdout.buffer, "utf-8", "replace", sys.__stdout__)
    sys.stderr = _DualLogger(sys.stderr.buffer, "utf-8", "replace", sys.__stderr__)

# ── Paths ───────────────────────────────────────────────────────────────────
ROOT_DIR   = Path(__file__).resolve().parent.parent
OUTPUT_DIR = ROOT_DIR / "downloads"
DATA_DIR   = ROOT_DIR / "data"
CATALOG    = DATA_DIR / "all_books.json"
TOKEN_FILE = ROOT_DIR / "token.txt"

# ── API ─────────────────────────────────────────────────────────────────────
API_BASE   = "https://android.lonoapp.net/api"
USER_AGENT = "Dart/3.0 (dart:io)"

# ── UI Palette (for GUI) ───────────────────────────────────────────────────
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
FONT_BOLD = ("Segoe UI", 9, "bold")
FONT_HEAD = ("Segoe UI", 11, "bold")
FONT_MONO = ("Consolas", 8)

# ── Hot reload ──────────────────────────────────────────────────────────────
EXIT_RELOAD = 42

# ── Logging ─────────────────────────────────────────────────────────────────
log = logging.getLogger("mtc")
log.setLevel(logging.DEBUG)
_fh = RotatingFileHandler(
    LOG_FILE, maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8"
)
_fh.setFormatter(
    logging.Formatter(
        "%(asctime)s  %(levelname)-5s  %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )
)
log.addHandler(_fh)
_ch = logging.StreamHandler(sys.stderr)
_ch.setLevel(logging.INFO)
_ch.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
log.addHandler(_ch)
