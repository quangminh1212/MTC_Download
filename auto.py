#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
auto.py – MTC Novel Downloader via ADB Automation
Chạy app MTC.apk thật trên device/emulator, đọc text qua UIAutomator.
Không cần APP_KEY, không cần root.
"""
import sys, io, os, re, time, subprocess, threading, xml.etree.ElementTree as ET
from pathlib import Path
from typing import Optional, List, Dict, Callable

# ── Constants ─────────────────────────────────────────────────────────────────
APK_PATH     = Path(__file__).parent / "MTC.apk"
PACKAGE      = "com.novelfever.app.android"
PACKAGE_ALT  = "com.example.novelfeverx"           # debug/alt variant
OUTPUT_DIR   = Path(__file__).parent / "downloads"
SCROLL_STEPS = 20       # max scrolls per chapter page
SCROLL_DELAY = 0.6      # seconds between scrolls
NAV_DELAY    = 1.5      # seconds to wait after navigation

# ADB keycodes
KEY_BACK  = 4
KEY_HOME  = 3
KEY_ENTER = 66


# ── ADB Controller ────────────────────────────────────────────────────────────
class AdbController:
    """Thin wrapper around adb CLI commands."""

    def __init__(self, adb_path: str = "adb", device: Optional[str] = None):
        self.adb    = adb_path
        self.device = device  # serial number (None = first available)
        self._pkg   = None    # resolved package name

    # ── Low-level ─────────────────────────────────────────────────────────
    def _cmd(self, *args, timeout: int = 30) -> tuple[str, str]:
        cmd = [self.adb]
        if self.device:
            cmd += ["-s", self.device]
        cmd += list(str(a) for a in args)
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout,
                               encoding="utf-8", errors="replace")
            return r.stdout.strip(), r.stderr.strip()
        except subprocess.TimeoutExpired:
            return "", "timeout"
        except FileNotFoundError:
            return "", "adb not found"

    def sh(self, *args, timeout: int = 20) -> str:
        out, _ = self._cmd("shell", *args, timeout=timeout)
        return out

    # ── Device management ─────────────────────────────────────────────────
    @staticmethod
    def find_adb() -> Optional[str]:
        """Find adb binary in PATH or common Android SDK locations."""
        import shutil
        if shutil.which("adb"):
            return "adb"
        candidates = [
            Path.home() / "AppData/Local/Android/Sdk/platform-tools/adb.exe",
            Path("C:/Android/platform-tools/adb.exe"),
            Path("C:/Program Files/Android/sdk/platform-tools/adb.exe"),
        ]
        for p in candidates:
            if p.exists():
                return str(p)
        return None

    def devices(self) -> List[Dict[str, str]]:
        out, _ = self._cmd("devices", "-l")
        result = []
        for line in out.splitlines()[1:]:
            parts = line.split()
            if len(parts) >= 2 and parts[1] in ("device", "emulator"):
                info = {"serial": parts[0], "type": parts[1]}
                # Additional info
                for p in parts[2:]:
                    if ":" in p:
                        k, v = p.split(":", 1)
                        info[k] = v
                result.append(info)
        return result

    def start_server(self):
        self._cmd("start-server", timeout=10)

    # ── APK ───────────────────────────────────────────────────────────────
    def install_apk(self, apk_path: Path,
                    progress_cb: Callable[[str], None] = print) -> bool:
        progress_cb(f"Installing {apk_path.name}...")
        out, err = self._cmd("install", "-r", "-d", str(apk_path), timeout=120)
        full = out + err
        success = "Success" in full or "success" in full.lower()
        progress_cb("Install OK" if success else f"Install failed: {full[:200]}")
        return success

    def is_installed(self, package: str) -> bool:
        out = self.sh("pm", "list", "packages", package)
        return package in out

    def get_installed_package(self) -> Optional[str]:
        """Return whichever MTC variant is installed."""
        for pkg in (PACKAGE, PACKAGE_ALT):
            if self.is_installed(pkg):
                self._pkg = pkg
                return pkg
        return None

    # ── App control ───────────────────────────────────────────────────────
    def launch(self, package: str) -> None:
        """Launch app via monkey (most reliable)."""
        self.sh("monkey", "-p", package,
                "-c", "android.intent.category.LAUNCHER", "1")
        time.sleep(NAV_DELAY)

    def force_stop(self, package: str) -> None:
        self.sh("am", "force-stop", package)

    def go_back(self, times: int = 1) -> None:
        for _ in range(times):
            self.sh("input", "keyevent", str(KEY_BACK))
            time.sleep(0.4)

    def go_home(self) -> None:
        self.sh("input", "keyevent", str(KEY_HOME))

    # ── Accessibility (force Flutter semantics) ───────────────────────────
    def enable_accessibility(self) -> None:
        """
        Enable Android accessibility service to force Flutter to generate
        its semantics tree, making text readable via UIAutomator.
        TalkBack is used (available on all Android devices).
        """
        svc = "com.google.android.marvin.talkback/.TalkBackService"
        self.sh("settings", "put", "secure", "accessibility_enabled", "1")
        self.sh("settings", "put", "secure", "enabled_accessibility_services", svc)
        time.sleep(1.5)

    def disable_accessibility(self) -> None:
        self.sh("settings", "put", "secure", "accessibility_enabled", "0")
        self.sh("settings", "put", "secure", "enabled_accessibility_services", "")

    # ── Screen ────────────────────────────────────────────────────────────
    def screen_size(self) -> tuple[int, int]:
        out = self.sh("wm", "size")
        m = re.search(r"(\d+)x(\d+)", out)
        if m:
            return int(m.group(2)), int(m.group(1))  # w, h
        return 1080, 1920

    def tap(self, x: int, y: int) -> None:
        self.sh("input", "tap", str(x), str(y))
        time.sleep(0.3)

    def long_press(self, x: int, y: int) -> None:
        self.sh("input", "swipe", str(x), str(y), str(x), str(y), "800")
        time.sleep(0.5)

    def swipe_up(self, w: int, h: int) -> None:
        """Scroll content down by swiping up."""
        mx = w // 2
        self.sh("input", "swipe",
                str(mx), str(int(h * 0.75)),
                str(mx), str(int(h * 0.25)),
                "300")
        time.sleep(SCROLL_DELAY)

    def type_text(self, text: str) -> None:
        escaped = text.replace(" ", "%s").replace("'", "\\'")
        self.sh("input", "text", escaped)

    def tap_text(self, text: str) -> bool:
        """Tap on the element that contains given text (from UIAutomator dump)."""
        bounds = self._find_bounds(text)
        if bounds:
            cx, cy = bounds
            self.tap(cx, cy)
            return True
        return False

    # ── UIAutomator ───────────────────────────────────────────────────────
    def dump_ui(self, compressed: bool = True) -> str:
        """Dump current screen UI hierarchy as XML string."""
        args = ["uiautomator", "dump", "/sdcard/_ui.xml"]
        if compressed:
            args.append("--compressed")
        self.sh(*args, timeout=15)
        out, _ = self._cmd("shell", "cat", "/sdcard/_ui.xml")
        return out

    def get_all_text(self, xml_str: str) -> List[str]:
        """Extract all non-empty text values from UIAutomator XML."""
        if not xml_str:
            return []
        try:
            root = ET.fromstring(xml_str)
            texts = []
            for node in root.iter():
                t = node.get("text", "").strip()
                if t and len(t) > 1:
                    texts.append(t)
                # Also check content-desc (accessibility label)
                cd = node.get("content-desc", "").strip()
                if cd and len(cd) > 1 and cd not in texts:
                    texts.append(cd)
            return texts
        except ET.ParseError:
            # Fallback: regex
            return re.findall(r'(?:text|content-desc)="([^"]{2,})"', xml_str)

    def _find_bounds(self, text: str) -> Optional[tuple[int, int]]:
        """Find center coordinates of element with given text."""
        xml_str = self.dump_ui()
        try:
            root = ET.fromstring(xml_str)
            for node in root.iter():
                if node.get("text","") == text or node.get("content-desc","") == text:
                    b = node.get("bounds", "")
                    m = re.findall(r"\d+", b)
                    if len(m) == 4:
                        cx = (int(m[0]) + int(m[2])) // 2
                        cy = (int(m[1]) + int(m[3])) // 2
                        return cx, cy
        except Exception:
            pass
        return None

    def wait_for_text(self, text: str, timeout: float = 8.0) -> bool:
        """Wait until given text appears on screen."""
        t0 = time.time()
        while time.time() - t0 < timeout:
            xml = self.dump_ui()
            if text in xml:
                return True
            time.sleep(0.8)
        return False

    def current_activity(self) -> str:
        out = self.sh("dumpsys", "window", "windows")
        m = re.search(r"mCurrentFocus=.*?(\S+/\S+Activity)", out)
        return m.group(1) if m else ""

    # ── MTC App Navigation ────────────────────────────────────────────────
    def nav_to_book(self, book_name: str,
                    log: Callable[[str], None] = print) -> bool:
        """Navigate from home screen to a book's chapter list."""
        log("Finding search in app...")
        # Try tapping search icon (common positions)
        w, h = self.screen_size()

        # Wait for app to load
        time.sleep(2)
        dump = self.dump_ui()

        # Look for search button by content-desc
        for search_label in ["Tìm kiếm", "Search", "search", "tìm"]:
            if search_label.lower() in dump.lower():
                if self.tap_text(search_label):
                    time.sleep(1)
                    break
        else:
            # Tap top-right area where search usually is
            self.tap(w - 80, 80)
            time.sleep(1)

        # Type book name
        log(f"Searching for: {book_name}")
        self.type_text(book_name)
        self.sh("input", "keyevent", str(KEY_ENTER))
        time.sleep(2)

        # Tap first result
        dump2 = self.dump_ui()
        if book_name[:8] in dump2:
            if self.tap_text(book_name):
                time.sleep(NAV_DELAY)
                return True
        # Try partial match
        texts = self.get_all_text(dump2)
        for t in texts:
            if book_name[:6].lower() in t.lower():
                if self.tap_text(t):
                    time.sleep(NAV_DELAY)
                    return True
        return False

    def nav_to_chapter(self, chapter_index: int,
                       log: Callable[[str], None] = print) -> bool:
        """Navigate to a specific chapter number. Must be on book detail page."""
        log(f"Navigating to chapter {chapter_index}...")
        # Look for chapter list / "Danh sách chương" button
        for label in ["Danh sách chương", "Chương", f"Chương {chapter_index}", "Đọc"]:
            if self.tap_text(label):
                time.sleep(NAV_DELAY)
                break

        # Scroll to find chapter N
        w, h = self.screen_size()
        for _ in range(10):
            dump = self.dump_ui()
            target = f"Chương {chapter_index}"
            if target in dump:
                self.tap_text(target)
                time.sleep(NAV_DELAY)
                return True
            # Also try just the number
            if re.search(rf'\b{chapter_index}\b', dump):
                # Find and tap it
                pass
            self.swipe_up(w, h)
        return False

    # ── Text Extraction ───────────────────────────────────────────────────
    def read_current_chapter(self, log: Callable[[str], None] = print) -> str:
        """
        Read the full text of the currently open chapter by scrolling
        and collecting all visible text, stopping when content repeats.
        """
        w, h = self.screen_size()
        collected: List[str] = []
        seen_hashes: set     = set()
        repeats              = 0

        log("Reading chapter text...")
        for step in range(SCROLL_STEPS):
            dump  = self.dump_ui()
            texts = self.get_all_text(dump)

            # Filter out UI chrome (buttons, nav, ads)
            content = [t for t in texts if _is_story_text(t)]

            # Hash this screen's content
            h_key = "|".join(content[:6])
            if h_key in seen_hashes:
                repeats += 1
                if repeats >= 2:
                    log(f"  End of chapter detected at scroll {step}")
                    break
            else:
                seen_hashes.add(h_key)
                repeats = 0
                # Merge with deduplication
                for t in content:
                    if not collected or t != collected[-1]:
                        collected.append(t)

            log(f"  Scroll {step+1}: +{len(content)} text nodes")
            self.swipe_up(w, h)

        return "\n".join(collected)


# ── Story text heuristic ──────────────────────────────────────────────────────
_UI_NOISE = re.compile(
    r"^(Chương|Mục lục|Trang chủ|Cài đặt|Quay lại|Tiếp theo|Chương trước"
    r"|Đọc thêm|Đăng nhập|Tải|Download|Quảng cáo|Ad|Loading).*$",
    re.IGNORECASE,
)

def _is_story_text(t: str) -> bool:
    """Heuristic: is this text body text, not UI chrome?"""
    if len(t) < 10:
        return False
    if _UI_NOISE.match(t.strip()):
        return False
    if re.match(r"^\d+$", t):
        return False
    return True


# ── High-level downloader ─────────────────────────────────────────────────────
def download_via_adb(
    adb:        AdbController,
    book_name:  str,
    ch_start:   int = 1,
    ch_end:     Optional[int] = None,
    output_dir: Path = OUTPUT_DIR,
    log:        Callable[[str], None] = print,
    stop_flag:  Callable[[], bool] = lambda: False,
) -> Dict:
    """
    Full pipeline:
      1. Enable accessibility (force Flutter semantics)
      2. Launch MTC app
      3. Search + open book
      4. For each chapter: navigate → read → save
    """
    from downloader import safe_name, merge_to_single_file

    # Resolve package
    pkg = adb.get_installed_package()
    if not pkg:
        log("MTC app not installed. Installing...")
        if not adb.install_apk(APK_PATH, log):
            log("ERROR: Install failed.")
            return {"success": False, "reason": "install_failed"}
        pkg = adb.get_installed_package() or PACKAGE

    log(f"Package: {pkg}")

    # Enable accessibility for Flutter semantics
    log("Enabling accessibility (Flutter semantics)...")
    adb.enable_accessibility()

    # Launch app
    log("Launching MTC app...")
    adb.launch(pkg)

    # Navigate to book
    if not adb.nav_to_book(book_name, log):
        log(f"WARNING: Could not auto-navigate to '{book_name}'. "
            f"Please open the book manually and press Ctrl+C when ready.")
        try:
            input("Press ENTER when chapter list is visible → ")
        except EOFError:
            pass

    # Prepare output directory
    book_dir = output_dir / safe_name(book_name)
    book_dir.mkdir(parents=True, exist_ok=True)

    if ch_end is None:
        ch_end = ch_start + 9999  # effectively unlimited

    n_ok = n_fail = 0
    for ch_idx in range(ch_start, ch_end + 1):
        if stop_flag():
            log("Stopped by user.")
            break

        ch_file = book_dir / f"{ch_idx:06d}_Chuong_{ch_idx}.txt"
        if ch_file.exists() and ch_file.stat().st_size > 100:
            log(f"  [ch{ch_idx}] Already done, skip")
            n_ok += 1
            continue

        log(f"  [ch{ch_idx}] Navigating...")
        if not adb.nav_to_chapter(ch_idx, log):
            log(f"  [ch{ch_idx}] WARN: Could not navigate to chapter")
            n_fail += 1
            if n_fail >= 5:
                log("Too many navigation failures. Stopping.")
                break
            continue

        # Read text
        text = adb.read_current_chapter(log)
        if not text or len(text) < 50:
            log(f"  [ch{ch_idx}] WARN: Empty content")
            n_fail += 1
        else:
            ch_file.write_text(
                f"{'='*60}\nChương {ch_idx}\n{'='*60}\n\n{text}\n",
                encoding="utf-8",
            )
            log(f"  [ch{ch_idx}] OK  ({len(text)} chars)")
            n_ok += 1

        # Go back to chapter list
        adb.go_back(2)
        time.sleep(0.8)

    # Merge
    merge_to_single_file(book_dir, book_name)
    log(f"\nDone! ✔{n_ok}  ✖{n_fail}  →  {book_dir}")

    # Cleanup
    adb.disable_accessibility()
    return {"success": True, "ok": n_ok, "fail": n_fail, "output": str(book_dir)}


# ── CLI entrypoint ────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(description="MTC ADB Automator")
    p.add_argument("book",  help="Book name to search")
    p.add_argument("--from", dest="start", type=int, default=1)
    p.add_argument("--to",   dest="end",   type=int, default=None)
    p.add_argument("--device",             default=None)
    p.add_argument("--output",             default=str(OUTPUT_DIR))
    args = p.parse_args()

    adb_path = AdbController.find_adb()
    if not adb_path:
        print("ERROR: adb not found. Install Android SDK platform-tools.")
        sys.exit(1)

    adb = AdbController(adb_path, args.device)
    adb.start_server()
    devs = adb.devices()
    if not devs:
        print("ERROR: No device connected. Connect a device or start an emulator.")
        sys.exit(1)
    print(f"Using device: {devs[0]['serial']}")
    if not args.device:
        adb.device = devs[0]["serial"]

    download_via_adb(
        adb, args.book,
        ch_start=args.start, ch_end=args.end,
        output_dir=Path(args.output),
    )
