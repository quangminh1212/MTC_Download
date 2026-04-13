"""Quick test: download Book 2 that previously failed."""
import sys, os, time
sys.path.insert(0, os.path.dirname(__file__))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from mtc.adb import AdbController
from mtc.pipeline import download_via_adb
from mtc.config import OUTPUT_DIR
from mtc.utils import safe_name

def log(msg):
    ts = time.strftime("%H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)

adb_path = AdbController.find_adb()
adb = AdbController(adb_path, "127.0.0.1:5555")
pkg = adb.get_installed_package()
log(f"ADB: {adb_path}, pkg: {pkg}")
adb.enable_accessibility(log)

title = "Theo Môn Phái Võ Lâm Đến Trường Sinh Tiên Môn"
max_ch = 5

log(f"Opening book: {title}")
book_info = adb.open_library_book(title, log_fn=lambda msg: log(f"  {msg}"))
if not book_info:
    log("FAIL: Book not found in library")
    sys.exit(1)

log(f"  Found: {book_info.get('title', '?')}")
time.sleep(0.5)

log(f"Downloading {max_ch} chapters via ADB (no open_current_book_reader)...")
result = download_via_adb(
    adb=adb,
    book_name=title,
    ch_start=1,
    ch_end=max_ch,
    log_fn=lambda msg: log(f"  {msg}"),
)

ok = result.get("ok", 0)
fail = result.get("fail", 0)
log(f"\nResult: ok={ok}, fail={fail}, success={result.get('success')}")
if result.get("reason"):
    log(f"Reason: {result['reason']}")

# Verify files
book_dir = OUTPUT_DIR / safe_name(title)
if book_dir.exists():
    files = sorted(book_dir.glob("*.txt"))
    log(f"\nFiles ({len(files)}):")
    for f in files[:10]:
        content = f.read_text(encoding="utf-8")
        lines = content.split("\n")
        preview = ""
        for line in lines[3:8]:
            if line.strip():
                preview = line.strip()[:80]
                break
        log(f"  {f.name} ({f.stat().st_size}b) - {preview}")

log("\nReturning to library...")
adb.return_to_library(log_fn=lambda msg: log(f"  {msg}"))
log("Done.")
