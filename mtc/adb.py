"""adb.py – ADB controller for BlueStacks emulator."""
import sys, re, time, subprocess, shutil, xml.etree.ElementTree as ET
from pathlib import Path
from typing import Optional, List, Dict, Callable

from .config import (
    PACKAGE, PACKAGE_ALT, APK_PATH,
    SCROLL_STEPS, SCROLL_DELAY, NAV_DELAY, INSTALL_TIMEOUT,
    KEY_BACK, KEY_ENTER,
    BS_ADB_PATHS, OTHER_ADB_PATHS, ACCESSIBILITY_SERVICES,
    log,
)

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


class AdbController:
    """ADB controller optimized for BlueStacks."""

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
        for p in BS_ADB_PATHS:
            if p.exists():
                return str(p)
        if shutil.which("adb"):
            return "adb"
        for p in OTHER_ADB_PATHS:
            if p.exists():
                return str(p)
        return None

    # ── Device management ─────────────────────────────────────────────────
    def devices(self) -> List[Dict[str, str]]:
        out, _ = self._cmd("devices", "-l")
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
    def install_apk(self, apk_path: Path = APK_PATH,
                    log_fn: Callable[[str], None] = print) -> bool:
        if not apk_path.exists():
            log_fn(f"APK không tìm thấy: {apk_path}")
            return False
        log_fn(f"Đang cài {apk_path.name}...")
        out, err = self._cmd("install", "-r", "-d", str(apk_path),
                             timeout=INSTALL_TIMEOUT)
        ok = "success" in (out + err).lower()
        log_fn("✔ Cài xong" if ok else f"✖ Lỗi: {(out+err)[:300]}")
        return ok

    def is_installed(self, package: str) -> bool:
        return f"package:{package}" in self.sh("pm", "list", "packages", package)

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
    def enable_accessibility(self, log_fn: Callable[[str], None] = print) -> bool:
        for svc in ACCESSIBILITY_SERVICES:
            self.sh("settings", "put", "secure",
                    "enabled_accessibility_services", svc)
            self.sh("settings", "put", "secure", "accessibility_enabled", "1")
            time.sleep(1.5)
            current = self.sh("settings", "get", "secure",
                              "enabled_accessibility_services")
            if current and svc.split("/")[0] in current:
                log_fn(f"Accessibility OK: {svc.split('/')[0]}")
                return True
        self.sh("settings", "put", "secure", "accessibility_enabled", "1")
        log_fn("⚠ Không tìm thấy accessibility service chuẩn")
        return False

    def disable_accessibility(self) -> None:
        self.sh("settings", "put", "secure", "accessibility_enabled", "0")
        self.sh("settings", "put", "secure", "enabled_accessibility_services", "")

    # ── Screen ────────────────────────────────────────────────────────────
    def screen_size(self) -> tuple:
        if self._w and self._h:
            return self._w, self._h
        m = re.search(r"(\d+)x(\d+)", self.sh("wm", "size"))
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
                str(mx), str(int(h * 0.75)), str(mx), str(int(h * 0.25)), "350")
        time.sleep(SCROLL_DELAY)

    def type_text(self, text: str) -> None:
        self.sh("input", "text", text.replace(" ", "%s").replace("'", "\\'"))

    def tap_text(self, text: str) -> bool:
        bounds = self._find_bounds(text)
        if bounds:
            self.tap(bounds[0], bounds[1])
            return True
        return False

    # ── UIAutomator ───────────────────────────────────────────────────────
    def dump_ui(self) -> str:
        self.sh("uiautomator", "dump", "--compressed", "/sdcard/_ui.xml",
                timeout=15)
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
        return self._parse_bounds(self.dump_ui(), text, exact=True)

    def _find_bounds_partial(self, text: str) -> Optional[tuple]:
        return self._parse_bounds(self.dump_ui(), text, exact=False)

    @staticmethod
    def _parse_bounds(xml_str: str, text: str, exact: bool) -> Optional[tuple]:
        try:
            root = ET.fromstring(xml_str)
            tl = text.lower()
            for node in root.iter():
                nt = node.get("text", "")
                nc = node.get("content-desc", "")
                match = (nt == text or nc == text) if exact \
                        else (tl in nt.lower() or tl in nc.lower())
                if match:
                    m = re.findall(r"\d+", node.get("bounds", ""))
                    if len(m) == 4:
                        return (int(m[0])+int(m[2]))//2, (int(m[1])+int(m[3]))//2
        except Exception:
            pass
        return None

    def wait_for_text(self, text: str, timeout: float = 10.0) -> bool:
        t0 = time.time()
        while time.time() - t0 < timeout:
            if text in self.dump_ui():
                return True
            time.sleep(1.0)
        return False

    def get_device_model(self) -> str:
        return self.sh("getprop", "ro.product.model")

    def get_android_version(self) -> str:
        return self.sh("getprop", "ro.build.version.release")

    # ── MTC Navigation ────────────────────────────────────────────────────
    def nav_to_book(self, book_name: str,
                    log_fn: Callable[[str], None] = print) -> bool:
        log_fn("Tìm search trong app...")
        w, h = self.screen_size()
        time.sleep(3)
        dump = self.dump_ui()

        for label in ["Tìm kiếm", "Search", "search", "tìm"]:
            if label.lower() in dump.lower():
                if self.tap_text(label):
                    time.sleep(1.5); break
                b = self._find_bounds_partial(label)
                if b:
                    self.tap(b[0], b[1]); time.sleep(1.5); break
        else:
            self.tap(w - 80, 80); time.sleep(1.5)

        log_fn(f"Tìm: {book_name}")
        self.type_text(book_name)
        self.sh("input", "keyevent", str(KEY_ENTER))
        time.sleep(3)

        dump2 = self.dump_ui()
        if book_name[:8] in dump2 and self.tap_text(book_name):
            time.sleep(NAV_DELAY); return True
        for t in self.get_all_text(dump2):
            if book_name[:6].lower() in t.lower() and self.tap_text(t):
                time.sleep(NAV_DELAY); return True
        return False

    def nav_to_chapter(self, chapter_index: int,
                       log_fn: Callable[[str], None] = print) -> bool:
        log_fn(f"Đi đến chương {chapter_index}...")
        for label in ["Danh sách chương", "Chương",
                       f"Chương {chapter_index}", "Đọc"]:
            if self.tap_text(label):
                time.sleep(NAV_DELAY); break

        target = f"Chương {chapter_index}"
        for _ in range(15):
            if target in self.dump_ui():
                self.tap_text(target); time.sleep(NAV_DELAY); return True
            self.swipe_up()
        return False

    # ── Text Extraction ───────────────────────────────────────────────────
    def read_current_chapter(self,
                             log_fn: Callable[[str], None] = print) -> str:
        collected, seen, repeats = [], set(), 0
        log_fn("Đọc nội dung chương...")

        for step in range(SCROLL_STEPS):
            texts   = self.get_all_text(self.dump_ui())
            content = [t for t in texts if _is_story_text(t)]
            h_key   = "|".join(content[:6])

            if h_key in seen:
                repeats += 1
                if repeats >= 2:
                    log_fn(f"  Hết chương (scroll {step})"); break
            else:
                seen.add(h_key); repeats = 0
                for t in content:
                    if not collected or t != collected[-1]:
                        collected.append(t)

            log_fn(f"  Scroll {step+1}: +{len(content)} đoạn")
            self.swipe_up()

        return "\n".join(collected)
