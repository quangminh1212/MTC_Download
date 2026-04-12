#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
auto.py – MTC Novel Downloader via ADB on BlueStacks
Chạy app MTC.apk trên BlueStacks, đọc text qua UIAutomator.
Không cần APP_KEY, không cần root.
"""
import sys, io, os, re, time, subprocess, xml.etree.ElementTree as ET
from pathlib import Path
from typing import Optional, List, Dict, Callable

# ── Constants ─────────────────────────────────────────────────────────────────
APK_PATH     = Path(__file__).parent / "MTC.apk"
PACKAGE      = "com.novelfever.app.android"
PACKAGE_ALT  = "com.example.novelfeverx"
OUTPUT_DIR   = Path(__file__).parent / "downloads"
SCROLL_STEPS = 25
SCROLL_DELAY = 0.8
NAV_DELAY    = 2.5
INSTALL_TIMEOUT = 180

KEY_BACK  = 4
KEY_HOME  = 3
KEY_ENTER = 66

# BlueStacks ADB path
_BS_ADB_PATHS = [
    Path("C:/Program Files/BlueStacks_nxt/HD-Adb.exe"),
    Path("C:/Program Files/BlueStacks/HD-Adb.exe"),
    Path("C:/Program Files (x86)/BlueStacks_nxt/HD-Adb.exe"),
]

# Fallback: standard ADB paths
_OTHER_ADB_PATHS = [
    Path.home() / "AppData/Local/Android/Sdk/platform-tools/adb.exe",
    Path("C:/LDPlayer/LDPlayer9/adb.exe"),
    Path("C:/Program Files/LDPlayer/LDPlayer9/adb.exe"),
    Path("C:/Program Files/Nox/bin/nox_adb.exe"),
]

# Accessibility services to try
_ACCESSIBILITY_SERVICES = [
    "com.google.android.marvin.talkback/com.google.android.marvin.talkback.TalkBackService",
    "com.google.android.marvin.talkback/.TalkBackService",
    "com.android.talkback/com.google.android.marvin.talkback.TalkBackService",
]


class AdbController:
    """ADB controller optimized for BlueStacks emulator."""

    def __init__(self, adb_path: str = "adb", device: Optional[str] = None):
        self.adb    = adb_path
        self.device = device
        self._pkg   = None
        self._w     = 0
        self._h     = 0

    # ── Low-level ─────────────────────────────────────────────────────────
    def _cmd(self, *args, timeout: int = 30) -> tuple:
        cmd = [self.adb]
        if self.device:
            cmd += ["-s", self.device]
        cmd += [str(a) for a in args]
        try:
            flags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout,
                               encoding="utf-8", errors="replace", creationflags=flags)
            return r.stdout.strip(), r.stderr.strip()
        except subprocess.TimeoutExpired:
            return "", "timeout"
        except FileNotFoundError:
            return "", f"adb not found: {self.adb}"
        except Exception as e:
            return "", str(e)

    def sh(self, *args, timeout: int = 20) -> str:
        out, _ = self._cmd("shell", *args, timeout=timeout)
        return out

    # ── Find ADB ──────────────────────────────────────────────────────────
    @staticmethod
    def find_adb() -> Optional[str]:
        """Find ADB binary, prioritizing BlueStacks."""
        import shutil
        # BlueStacks first
        for p in _BS_ADB_PATHS:
            if p.exists():
                return str(p)
        # System PATH
        if shutil.which("adb"):
            return "adb"
        # Other emulators
        for p in _OTHER_ADB_PATHS:
            if p.exists():
                return str(p)
        return None

    # ── Device management ─────────────────────────────────────────────────
    def devices(self) -> List[Dict[str, str]]:
        out, err = self._cmd("devices", "-l")
        if not out:
            return []
        result = []
        for line in out.splitlines()[1:]:
            parts = line.split()
            if len(parts) >= 2 and parts[1] == "device":
                info = {"serial": parts[0], "type": "emulator"}
                for p in parts[2:]:
                    if ":" in p:
                        k, v = p.split(":", 1)
                        info[k] = v
                result.append(info)
        return result

    def start_server(self):
        self._cmd("start-server", timeout=10)

    def connect(self, host_port: str) -> bool:
        out, err = self._cmd("connect", host_port, timeout=10)
        return "connected" in (out + err).lower()

    # ── APK ───────────────────────────────────────────────────────────────
    def install_apk(self, apk_path: Path,
                    log: Callable[[str], None] = print) -> bool:
        if not apk_path.exists():
            log(f"APK không tìm thấy: {apk_path}")
            return False
        log(f"Đang cài {apk_path.name}...")
        out, err = self._cmd("install", "-r", "-d", str(apk_path), timeout=INSTALL_TIMEOUT)
        full = out + err
        ok = "success" in full.lower()
        log("✔ Cài xong" if ok else f"✖ Lỗi: {full[:300]}")
        return ok

    def is_installed(self, package: str) -> bool:
        out = self.sh("pm", "list", "packages", package)
        return f"package:{package}" in out

    def get_installed_package(self) -> Optional[str]:
        for pkg in (PACKAGE, PACKAGE_ALT):
            if self.is_installed(pkg):
                self._pkg = pkg
                return pkg
        return None

    # ── App control ───────────────────────────────────────────────────────
    def launch(self, package: str) -> None:
        self.sh("monkey", "-p", package,
                "-c", "android.intent.category.LAUNCHER", "1")
        time.sleep(NAV_DELAY)

    def force_stop(self, package: str) -> None:
        self.sh("am", "force-stop", package)

    def go_back(self, times: int = 1) -> None:
        for _ in range(times):
            self.sh("input", "keyevent", str(KEY_BACK))
            time.sleep(0.5)

    # ── Accessibility ─────────────────────────────────────────────────────
    def enable_accessibility(self, log: Callable[[str], None] = print) -> bool:
        for svc in _ACCESSIBILITY_SERVICES:
            self.sh("settings", "put", "secure", "enabled_accessibility_services", svc)
            self.sh("settings", "put", "secure", "accessibility_enabled", "1")
            time.sleep(1.5)
            current = self.sh("settings", "get", "secure", "enabled_accessibility_services")
            if current and svc.split("/")[0] in current:
                log(f"Accessibility OK: {svc.split('/')[0]}")
                return True
        self.sh("settings", "put", "secure", "accessibility_enabled", "1")
        log("⚠ Không tìm thấy accessibility service chuẩn")
        return False

    def disable_accessibility(self) -> None:
        self.sh("settings", "put", "secure", "accessibility_enabled", "0")
        self.sh("settings", "put", "secure", "enabled_accessibility_services", "")

    # ── Screen ────────────────────────────────────────────────────────────
    def screen_size(self) -> tuple:
        if self._w and self._h:
            return self._w, self._h
        out = self.sh("wm", "size")
        m = re.search(r"(\d+)x(\d+)", out)
        if m:
            self._w, self._h = int(m.group(1)), int(m.group(2))
        else:
            self._w, self._h = 1080, 1920
        return self._w, self._h

    def tap(self, x: int, y: int) -> None:
        self.sh("input", "tap", str(x), str(y))
        time.sleep(0.4)

    def swipe_up(self) -> None:
        w, h = self.screen_size()
        mx = w // 2
        self.sh("input", "swipe",
                str(mx), str(int(h * 0.75)),
                str(mx), str(int(h * 0.25)), "350")
        time.sleep(SCROLL_DELAY)

    def type_text(self, text: str) -> None:
        escaped = text.replace(" ", "%s").replace("'", "\\'")
        self.sh("input", "text", escaped)

    def tap_text(self, text: str) -> bool:
        bounds = self._find_bounds(text)
        if bounds:
            self.tap(bounds[0], bounds[1])
            return True
        return False

    # ── UIAutomator ───────────────────────────────────────────────────────
    def dump_ui(self) -> str:
        self.sh("uiautomator", "dump", "--compressed", "/sdcard/_ui.xml", timeout=15)
        out, _ = self._cmd("shell", "cat", "/sdcard/_ui.xml")
        return out

    def get_all_text(self, xml_str: str) -> List[str]:
        if not xml_str:
            return []
        try:
            root = ET.fromstring(xml_str)
            texts = []
            for node in root.iter():
                t = node.get("text", "").strip()
                if t and len(t) > 1:
                    texts.append(t)
                cd = node.get("content-desc", "").strip()
                if cd and len(cd) > 1 and cd not in texts:
                    texts.append(cd)
            return texts
        except ET.ParseError:
            return re.findall(r'(?:text|content-desc)="([^"]{2,})"', xml_str)

    def _find_bounds(self, text: str) -> Optional[tuple]:
        xml_str = self.dump_ui()
        try:
            root = ET.fromstring(xml_str)
            for node in root.iter():
                if node.get("text", "") == text or node.get("content-desc", "") == text:
                    b = node.get("bounds", "")
                    m = re.findall(r"\d+", b)
                    if len(m) == 4:
                        return (int(m[0]) + int(m[2])) // 2, (int(m[1]) + int(m[3])) // 2
        except Exception:
            pass
        return None

    def _find_bounds_partial(self, text: str) -> Optional[tuple]:
        xml_str = self.dump_ui()
        tl = text.lower()
        try:
            root = ET.fromstring(xml_str)
            for node in root.iter():
                if tl in node.get("text", "").lower() or tl in node.get("content-desc", "").lower():
                    b = node.get("bounds", "")
                    m = re.findall(r"\d+", b)
                    if len(m) == 4:
                        return (int(m[0]) + int(m[2])) // 2, (int(m[1]) + int(m[3])) // 2
        except Exception:
            pass
        return None

    def wait_for_text(self, text: str, timeout: float = 10.0) -> bool:
        t0 = time.time()
        while time.time() - t0 < timeout:
            xml = self.dump_ui()
            if text in xml:
                return True
            time.sleep(1.0)
        return False

    def get_device_model(self) -> str:
        return self.sh("getprop", "ro.product.model")

    def get_android_version(self) -> str:
        return self.sh("getprop", "ro.build.version.release")

    # ── MTC Navigation ────────────────────────────────────────────────────
    def nav_to_book(self, book_name: str,
                    log: Callable[[str], None] = print) -> bool:
        log("Tìm search trong app...")
        w, h = self.screen_size()
        time.sleep(3)
        dump = self.dump_ui()

        for label in ["Tìm kiếm", "Search", "search", "tìm"]:
            if label.lower() in dump.lower():
                if self.tap_text(label):
                    time.sleep(1.5)
                    break
                b = self._find_bounds_partial(label)
                if b:
                    self.tap(b[0], b[1])
                    time.sleep(1.5)
                    break
        else:
            self.tap(w - 80, 80)
            time.sleep(1.5)

        log(f"Tìm: {book_name}")
        self.type_text(book_name)
        self.sh("input", "keyevent", str(KEY_ENTER))
        time.sleep(3)

        dump2 = self.dump_ui()
        if book_name[:8] in dump2:
            if self.tap_text(book_name):
                time.sleep(NAV_DELAY)
                return True
        texts = self.get_all_text(dump2)
        for t in texts:
            if book_name[:6].lower() in t.lower():
                if self.tap_text(t):
                    time.sleep(NAV_DELAY)
                    return True
        return False

    def nav_to_chapter(self, chapter_index: int,
                       log: Callable[[str], None] = print) -> bool:
        log(f"Đi đến chương {chapter_index}...")
        for label in ["Danh sách chương", "Chương", f"Chương {chapter_index}", "Đọc"]:
            if self.tap_text(label):
                time.sleep(NAV_DELAY)
                break

        for _ in range(15):
            dump = self.dump_ui()
            target = f"Chương {chapter_index}"
            if target in dump:
                self.tap_text(target)
                time.sleep(NAV_DELAY)
                return True
            self.swipe_up()
        return False

    # ── Text Extraction ───────────────────────────────────────────────────
    def read_current_chapter(self, log: Callable[[str], None] = print) -> str:
        collected: List[str] = []
        seen: set = set()
        repeats = 0

        log("Đọc nội dung chương...")
        for step in range(SCROLL_STEPS):
            dump  = self.dump_ui()
            texts = self.get_all_text(dump)
            content = [t for t in texts if _is_story_text(t)]

            h_key = "|".join(content[:6])
            if h_key in seen:
                repeats += 1
                if repeats >= 2:
                    log(f"  Hết chương (scroll {step})")
                    break
            else:
                seen.add(h_key)
                repeats = 0
                for t in content:
                    if not collected or t != collected[-1]:
                        collected.append(t)

            log(f"  Scroll {step+1}: +{len(content)} đoạn")
            self.swipe_up()

        return "\n".join(collected)


# ── Story text filter ─────────────────────────────────────────────────────────
_UI_NOISE = re.compile(
    r"^(Chương|Mục lục|Trang chủ|Cài đặt|Quay lại|Tiếp theo|Chương trước"
    r"|Đọc thêm|Đăng nhập|Tải|Download|Quảng cáo|Ad|Loading).*$",
    re.IGNORECASE,
)

def _is_story_text(t: str) -> bool:
    if len(t) < 10:
        return False
    if _UI_NOISE.match(t.strip()):
        return False
    if re.match(r"^\d+$", t):
        return False
    return True


# ── Main download pipeline ────────────────────────────────────────────────────
def download_via_adb(
    adb:        AdbController,
    book_name:  str,
    ch_start:   int = 1,
    ch_end:     Optional[int] = None,
    output_dir: Path = OUTPUT_DIR,
    log:        Callable[[str], None] = print,
    stop_flag:  Callable[[], bool] = lambda: False,
    progress_cb: Optional[Callable[[int, int], None]] = None,
) -> Dict:
    """
    Pipeline tải truyện qua BlueStacks:
      1. Bật accessibility → Flutter hiện semantics tree
      2. Mở app MTC
      3. Tìm truyện → mở
      4. Từng chương: điều hướng → đọc text → lưu file
    """
    from downloader import safe_name, merge_to_single_file

    pkg = adb.get_installed_package()
    if not pkg:
        log("App MTC chưa cài. Đang cài...")
        if not adb.install_apk(APK_PATH, log):
            return {"success": False, "reason": "install_failed"}
        pkg = adb.get_installed_package() or PACKAGE

    log(f"Package: {pkg}")
    model = adb.get_device_model()
    ver   = adb.get_android_version()
    if model or ver:
        log(f"Device: {model} (Android {ver})")

    log("Bật accessibility (Flutter semantics)...")
    adb.enable_accessibility(log)

    log("Mở app MTC...")
    adb.force_stop(pkg)
    time.sleep(0.5)
    adb.launch(pkg)

    if not adb.nav_to_book(book_name, log):
        log(f"⚠ Không tìm thấy «{book_name}» trong app.")
        log("  → Hãy mở truyện thủ công trên BlueStacks, tool sẽ tiếp tục...")
        time.sleep(5)
        if stop_flag():
            return {"success": False, "reason": "stopped"}

    book_dir = output_dir / safe_name(book_name)
    book_dir.mkdir(parents=True, exist_ok=True)

    if ch_end is None:
        ch_end = ch_start + 9999

    total = ch_end - ch_start + 1
    n_ok = n_fail = 0

    for ch_idx in range(ch_start, ch_end + 1):
        if stop_flag():
            log("Đã dừng.")
            break

        done_count = ch_idx - ch_start
        if progress_cb:
            progress_cb(done_count, total)

        ch_file = book_dir / f"{ch_idx:06d}_Chuong_{ch_idx}.txt"
        if ch_file.exists() and ch_file.stat().st_size > 100:
            log(f"  [ch{ch_idx}] Đã có, bỏ qua")
            n_ok += 1
            continue

        log(f"  [ch{ch_idx}] Điều hướng...")
        if not adb.nav_to_chapter(ch_idx, log):
            log(f"  [ch{ch_idx}] ⚠ Không tìm thấy chương")
            n_fail += 1
            if n_fail >= 5:
                log("Quá nhiều lỗi điều hướng. Dừng.")
                break
            continue

        text = adb.read_current_chapter(log)
        if not text or len(text) < 50:
            log(f"  [ch{ch_idx}] ⚠ Nội dung trống")
            n_fail += 1
        else:
            ch_file.write_text(
                f"{'='*60}\nChương {ch_idx}\n{'='*60}\n\n{text}\n",
                encoding="utf-8",
            )
            log(f"  [ch{ch_idx}] ✔ ({len(text)} ký tự)")
            n_ok += 1

        adb.go_back(2)
        time.sleep(1.0)

    merge_to_single_file(book_dir, book_name)
    log(f"\nXong! ✔{n_ok}  ✖{n_fail}  →  {book_dir}")

    adb.disable_accessibility()
    return {"success": True, "ok": n_ok, "fail": n_fail, "output": str(book_dir)}
