"""adb.py – ADB controller for BlueStacks emulator (speed-optimized)."""
import sys, re, time, difflib, subprocess, shutil, xml.etree.ElementTree as ET
from pathlib import Path
from typing import Optional, List, Dict, Callable

from .config import (
    PACKAGE, PACKAGE_ALT, APK_PATH,
    SCROLL_STEPS, SCROLL_DELAY, NAV_DELAY, TAP_DELAY, BACK_DELAY,
    INSTALL_TIMEOUT, KEY_BACK, KEY_ENTER, KEY_DEL,
    BS_ADB_PATHS, OTHER_ADB_PATHS, ACCESSIBILITY_SERVICES,
    log,
)
from .utils import repair_adb_text

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


def _clean_ui_text(value: str) -> str:
    value = repair_adb_text((value or "").replace("\xa0", " "))
    return value.strip()


def _parse_bounds_rect(bounds: str) -> Optional[tuple]:
    numbers = re.findall(r"\d+", bounds or "")
    if len(numbers) != 4:
        return None
    return tuple(int(n) for n in numbers)


def _normalize_xml_dump(raw: str) -> str:
    if not raw:
        return ""
    start = raw.find("<?xml")
    if start < 0:
        start = raw.find("<hierarchy")
    if start < 0:
        return raw.strip()

    end_tag = "</hierarchy>"
    end = raw.rfind(end_tag)
    if end < 0:
        return raw[start:].strip()
    end += len(end_tag)
    return raw[start:end].strip()


class AdbController:
    """ADB controller optimized for BlueStacks (speed-tuned)."""

    def __init__(self, adb_path: str = "adb", device: Optional[str] = None):
        self.adb    = adb_path
        self.device = device
        self._pkg   = None
        self._w     = 0
        self._h     = 0

    @staticmethod
    def _extract_ui_size(xml_str: str) -> Optional[tuple]:
        if not xml_str:
            return None
        try:
            root = ET.fromstring(xml_str)
        except ET.ParseError:
            return None

        max_x = 0
        max_y = 0
        for node in root.iter():
            rect = _parse_bounds_rect(node.get("bounds", ""))
            if not rect:
                continue
            max_x = max(max_x, rect[2])
            max_y = max(max_y, rect[3])

        if max_x > 0 and max_y > 0:
            return max_x, max_y
        return None

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

    def ensure_device(self) -> bool:
        if not self.device:
            return True
        serials = {item["serial"] for item in self.devices()}
        if self.device in serials:
            return True
        if re.match(r"^\d+\.\d+\.\d+\.\d+:\d+$", self.device):
            self.start_server()
            self.connect(self.device)
            time.sleep(0.2)
            serials = {item["serial"] for item in self.devices()}
            return self.device in serials
        return False

    def sh(self, *args, timeout: int = 15) -> str:
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
            time.sleep(BACK_DELAY)

    # ── Accessibility ─────────────────────────────────────────────────────
    def enable_accessibility(self, log_fn: Callable[[str], None] = print) -> bool:
        for svc in ACCESSIBILITY_SERVICES:
            self.sh("settings", "put", "secure",
                    "enabled_accessibility_services", svc)
            self.sh("settings", "put", "secure", "accessibility_enabled", "1")
            time.sleep(0.5)
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

        ui_size = self._extract_ui_size(self.dump_ui())
        if ui_size:
            self._w, self._h = ui_size
            return self._w, self._h

        m = re.search(r"(\d+)x(\d+)", self.sh("wm", "size"))
        if m:
            self._w, self._h = int(m.group(1)), int(m.group(2))
        else:
            self._w, self._h = 1080, 1920
        return self._w, self._h

    def _main_tabs_visible(self, xml_str: str = "") -> bool:
        texts = "\n".join(self.get_all_text(xml_str or self.dump_ui()))
        return all(label in texts for label in ("Tủ Truyện", "Khám Phá", "Xếp Hạng", "Tài Khoản"))

    def _find_bottom_tab_center(self, tab_index: int, xml_str: str = "") -> Optional[tuple]:
        xml = xml_str or self.dump_ui()
        try:
            root = ET.fromstring(xml)
        except ET.ParseError:
            return None

        marker = f"Tab {tab_index} trong tổng số 4"
        for node in root.iter():
            if node.get("clickable") != "true":
                continue
            desc = _clean_ui_text(node.get("content-desc", ""))
            if marker not in desc:
                continue
            rect = _parse_bounds_rect(node.get("bounds", ""))
            if rect:
                return (rect[0] + rect[2]) // 2, (rect[1] + rect[3]) // 2
        return None

    def ensure_main_tabs(self, log_fn: Callable[[str], None] = print) -> bool:
        if self._main_tabs_visible():
            return True

        pkg = self._pkg or self.get_installed_package()
        if not pkg:
            log_fn("⚠ Không tìm thấy package MTC để mở app")
            return False

        for attempt in range(2):
            self.force_stop(pkg)
            time.sleep(0.5)
            self.launch(pkg)
            time.sleep(1.6)
            if self._main_tabs_visible():
                return True
            log_fn(f"⚠ Chưa về được màn hình chính (lượt {attempt + 1})")
        return False

    def open_explore_tab(self, log_fn: Callable[[str], None] = print) -> bool:
        if not self.ensure_main_tabs(log_fn):
            return False

        center = self._find_bottom_tab_center(2)
        if not center:
            log_fn("⚠ Không tìm thấy tab Khám Phá")
            return False

        self.tap(*center)
        time.sleep(0.8)
        return True

    def _find_clickable_text_center(
        self,
        text: str,
        *,
        exact: bool = False,
        xml_str: str = "",
    ) -> Optional[tuple]:
        xml = xml_str or self.dump_ui()
        try:
            root = ET.fromstring(xml)
        except ET.ParseError:
            return None

        query = _clean_ui_text(text)
        query_key = query.casefold()
        query_norm = self._book_key(query)
        for node in root.iter():
            if node.get("clickable") != "true":
                continue

            values = (
                _clean_ui_text(node.get("text", "")),
                _clean_ui_text(node.get("content-desc", "")),
            )
            if exact:
                match = any(
                    value == query or (query_norm and self._book_key(value) == query_norm)
                    for value in values if value
                )
            else:
                match = any(
                    query_key in value.casefold() or (query_norm and query_norm in self._book_key(value))
                    for value in values if value
                )
            if not match:
                continue

            rect = _parse_bounds_rect(node.get("bounds", ""))
            if rect:
                return (rect[0] + rect[2]) // 2, (rect[1] + rect[3]) // 2
        return None

    def open_library_tab(self, log_fn: Callable[[str], None] = print) -> bool:
        if not self.ensure_main_tabs(log_fn):
            return False

        center = self._find_bottom_tab_center(1)
        if not center:
            log_fn("⚠ Không tìm thấy tab Tủ Truyện")
            return False

        self.tap(*center)
        time.sleep(0.8)

        xml = self.dump_ui()
        history_center = self._find_clickable_text_center("Lịch sử", xml_str=xml)
        if history_center:
            self.tap(*history_center)
            time.sleep(0.35)

        xml = self.dump_ui()
        if self.scan_visible_library_books(xml_str=xml):
            return True

        texts = self.get_all_text(xml)
        return any(text == "Tủ Truyện" for text in texts)

    def _find_header_buttons(self, xml_str: str = "") -> List[tuple]:
        xml = xml_str or self.dump_ui()
        try:
            root = ET.fromstring(xml)
        except ET.ParseError:
            return []

        buttons: List[tuple] = []
        for node in root.iter():
            if node.get("class") != "android.widget.Button":
                continue
            if node.get("clickable") != "true":
                continue
            rect = _parse_bounds_rect(node.get("bounds", ""))
            if not rect or rect[1] > 140:
                continue
            desc = _clean_ui_text(node.get("content-desc", ""))
            text = _clean_ui_text(node.get("text", ""))
            buttons.append((rect, desc, text))
        buttons.sort(key=lambda item: item[0][0])
        return buttons

    def open_search_screen(self, log_fn: Callable[[str], None] = print) -> bool:
        if not self.open_explore_tab(log_fn):
            return False

        buttons = self._find_header_buttons()
        blank_buttons = [item for item in buttons if not item[1] and not item[2]]
        if len(blank_buttons) < 1:
            log_fn("⚠ Không tìm thấy nút mở màn hình tìm kiếm")
            return False

        rect = blank_buttons[0][0]
        self.tap((rect[0] + rect[2]) // 2, (rect[1] + rect[3]) // 2)
        time.sleep(0.8)
        return bool(self._parse_bounds(self.dump_ui(), "Tìm", exact=False))

    def tap(self, x: int, y: int) -> None:
        self.sh("input", "tap", str(x), str(y))
        time.sleep(TAP_DELAY)

    def swipe_up(self) -> None:
        w, h = self.screen_size()
        mx = w // 2
        # Fast swipe: 150ms duration
        self.sh("input", "swipe",
                str(mx), str(int(h * 0.75)), str(mx), str(int(h * 0.25)), "150")
        time.sleep(SCROLL_DELAY)

    def swipe_down(self) -> None:
        """Scroll content DOWN (reveal items above current view)."""
        w, h = self.screen_size()
        mx = w // 2
        self.sh("input", "swipe",
                str(mx), str(int(h * 0.25)), str(mx), str(int(h * 0.75)), "150")
        time.sleep(SCROLL_DELAY)

    def scroll_to_top(self, max_swipes: int = 15) -> None:
        """Scroll to the top of the current scrollable view."""
        prev_xml = ""
        for _ in range(max_swipes):
            self.swipe_down()
            xml = self.dump_ui()
            if xml == prev_xml:
                break
            prev_xml = xml

    def type_text(self, text: str) -> None:
        self.sh("input", "text", text.replace(" ", "%s").replace("'", "\\'"))

    # ── UIAutomator (speed-optimized) ─────────────────────────────────────
    def dump_ui(self) -> str:
        """Dump UI XML using the fastest working transport and retry on transient failures."""
        self.ensure_device()

        for attempt in range(2):
            out, err = self._cmd(
                "exec-out", "uiautomator", "dump", "--compressed", "/dev/tty",
                timeout=8,
            )
            merged = (out or "") + (err or "")
            if "<hierarchy" in merged:
                return _normalize_xml_dump(merged)

            self._cmd("shell", "uiautomator", "dump", "--compressed", "/sdcard/_ui.xml", timeout=8)
            file_out, file_err = self._cmd("shell", "cat", "/sdcard/_ui.xml", timeout=8)
            merged = (file_out or "") + (file_err or "")
            if "<hierarchy" in merged:
                return _normalize_xml_dump(merged)

            if attempt == 0:
                self.ensure_device()
                time.sleep(0.15)

        return ""

    @staticmethod
    def _extract_reader_payload(xml_str: str) -> Optional[Dict]:
        if not xml_str:
            return None
        try:
            root = ET.fromstring(xml_str)
        except ET.ParseError:
            return None

        candidates = []
        for node in root.iter():
            payload = _clean_ui_text(node.get("content-desc", "") or node.get("text", ""))
            if payload.count("\n") < 5:
                continue
            rect = _parse_bounds_rect(node.get("bounds", ""))
            if rect:
                width = max(0, rect[2] - rect[0])
                height = max(0, rect[3] - rect[1])
                if width < 100 or height < 100:
                    continue
                area = width * height
            else:
                area = 0
            candidates.append((area, payload))

        if not candidates:
            return None

        _, best_text = max(candidates, key=lambda item: (item[0], len(item[1])))

        lines = [line.strip() for line in best_text.splitlines()]
        lines = [line for line in lines if line]
        if not lines:
            return None

        title = lines[0]
        match = re.search(r"Chương\s+(\d+)", title, re.IGNORECASE)
        body_lines = lines[1:]
        if body_lines and body_lines[0] == title:
            body_lines = body_lines[1:]
        body = "\n\n".join(body_lines).strip()
        if len(body) < 50:
            return None

        return {
            "title": title,
            "chapter_index": int(match.group(1)) if match else None,
            "text": body,
        }

    def _reader_menu_visible(self, xml_str: str) -> bool:
        texts = self.get_all_text(xml_str)
        lookup = {item.lower() for item in texts}
        return "d.s chương" in lookup and "tải lại nội dung" in lookup

    def _reader_nav_point(self, direction: str) -> tuple:
        w, h = self.screen_size()
        if direction == "next":
            return int(w * 0.70), int(h * 0.392)
        return int(w * 0.293), int(h * 0.392)

    def reader_open_menu(self) -> None:
        w, h = self.screen_size()
        self.tap(w // 2, int(h * 0.75))
        time.sleep(0.05)

    def reader_toggle_menu(self) -> None:
        w, h = self.screen_size()
        self.tap(w // 2, h // 2)

    def reader_close_menu(self) -> None:
        w, h = self.screen_size()
        self.tap(int(w * 0.933), int(h * 0.305))
        time.sleep(0.05)

    def reader_next_chapter(self, log_fn: Callable[[str], None] = print) -> bool:
        before = self._extract_reader_payload(self.dump_ui())

        self.reader_open_menu()
        time.sleep(0.35)
        overlay_xml = self.dump_ui()
        if not self._reader_menu_visible(overlay_xml):
            log_fn("  Fast next bỏ qua: không bật được menu reader")
            return False

        self.tap(*self._reader_nav_point("next"))
        time.sleep(0.4)
        self.reader_close_menu()
        time.sleep(0.25)

        after = self._extract_reader_payload(self.dump_ui())
        before_idx = before.get("chapter_index") if before else None
        after_idx = after.get("chapter_index") if after else None
        if before_idx is not None and after_idx == before_idx + 1:
            log_fn("  Sang chương tiếp theo (fast)")
            return True
        if before and after and before.get("title") != after.get("title"):
            log_fn("  Sang chương tiếp theo (fast)")
            return True

        log_fn("  Fast next thất bại, sẽ fallback sang mở danh sách chương")
        return False

    @staticmethod
    def _chapter_list_visible(texts: List[str]) -> bool:
        if any(text.startswith("Số chương") for text in texts):
            return True
        return any(text[:1].isdigit() and "\nChương " in text for text in texts)

    def _find_visible_chapter_item_center(self, xml_str: str = "") -> Optional[tuple]:
        xml = xml_str or self.dump_ui()
        try:
            root = ET.fromstring(xml)
        except ET.ParseError:
            return None

        candidates = []
        for node in root.iter():
            if node.get("clickable") != "true":
                continue
            value = _clean_ui_text(node.get("text", "") or node.get("content-desc", ""))
            if not value or "Chương " not in value:
                continue
            if not (value.startswith("Chương ") or value[:1].isdigit()):
                continue

            rect = _parse_bounds_rect(node.get("bounds", ""))
            if not rect:
                continue
            candidates.append((rect[1], ((rect[0] + rect[2]) // 2, (rect[1] + rect[3]) // 2)))

        if not candidates:
            return None

        candidates.sort(key=lambda item: item[0])
        return candidates[-1][1]

    def open_chapter_list(self, log_fn: Callable[[str], None] = print) -> bool:
        xml = self.dump_ui()
        texts = self.get_all_text(xml)
        if self._chapter_list_visible(texts):
            return True

        center = self._parse_bounds(xml, "D.S Chương", exact=False)
        if center:
            self.tap(*center)
            time.sleep(0.25)
            xml = self.dump_ui()
            texts = self.get_all_text(xml)
            if self._chapter_list_visible(texts):
                return True

        payload = self._extract_reader_payload(xml)
        if payload:
            self.reader_open_menu()
            time.sleep(0.4)
            overlay_xml = self.dump_ui()
            center = self._parse_bounds(overlay_xml, "D.S Chương", exact=False)
            if center:
                self.tap(*center)
                time.sleep(0.35)
            xml = self.dump_ui()
            texts = self.get_all_text(xml)
            if self._chapter_list_visible(texts):
                return True

        log_fn("⚠ Không mở được danh sách chương")
        return False

    def _find_chapter_center(self, xml_str: str, chapter_index: int) -> Optional[tuple]:
        try:
            root = ET.fromstring(xml_str)
        except ET.ParseError:
            return None

        target = f"Chương {chapter_index}"
        for node in root.iter():
            if node.get("clickable") != "true":
                continue
            text = _clean_ui_text(node.get("text", ""))
            desc = _clean_ui_text(node.get("content-desc", ""))
            haystack = text or desc
            if target not in haystack:
                continue
            rect = _parse_bounds_rect(node.get("bounds", ""))
            if rect:
                return (rect[0] + rect[2]) // 2, (rect[1] + rect[3]) // 2
        return None

    def get_all_text(self, xml_str: str) -> List[str]:
        if not xml_str:
            return []
        try:
            root = ET.fromstring(xml_str)
            texts = []
            for node in root.iter():
                t = _clean_ui_text(node.get("text", ""))
                if t and len(t) > 1:
                    texts.append(t)
                cd = _clean_ui_text(node.get("content-desc", ""))
                if cd and len(cd) > 1 and cd not in texts:
                    texts.append(cd)
            return texts
        except ET.ParseError:
            return [_clean_ui_text(t) for t in re.findall(r'(?:text|content-desc)="([^"]{2,})"', xml_str)]

    def tap_text(self, text: str, xml_cache: str = "") -> bool:
        """Tap on text element. Pass xml_cache to avoid redundant dump."""
        xml = xml_cache or self.dump_ui()
        bounds = self._parse_bounds(xml, text, exact=True)
        if bounds:
            self.tap(bounds[0], bounds[1])
            return True
        return False

    def tap_text_partial(self, text: str, xml_cache: str = "") -> bool:
        """Tap on partial text match."""
        xml = xml_cache or self.dump_ui()
        bounds = self._parse_bounds(xml, text, exact=False)
        if bounds:
            self.tap(bounds[0], bounds[1])
            return True
        return False

    @staticmethod
    def _parse_bounds(xml_str: str, text: str, exact: bool) -> Optional[tuple]:
        try:
            root = ET.fromstring(xml_str)
            tl = text.lower()
            for node in root.iter():
                nt = _clean_ui_text(repair_adb_text(node.get("text", "")))
                nc = _clean_ui_text(repair_adb_text(node.get("content-desc", "")))
                match = (nt == text or nc == text) if exact \
                        else (tl in nt.lower() or tl in nc.lower())
                if match:
                    rect = _parse_bounds_rect(node.get("bounds", ""))
                    if rect:
                        return (rect[0] + rect[2]) // 2, (rect[1] + rect[3]) // 2
        except Exception:
            pass
        return None

    def wait_for_text(self, text: str, timeout: float = 5.0) -> bool:
        t0 = time.time()
        while time.time() - t0 < timeout:
            dump = self.dump_ui()
            if any(text.lower() in item.lower() for item in self.get_all_text(dump)):
                return True
            time.sleep(0.3)
        return False

    def get_device_model(self) -> str:
        return self.sh("getprop", "ro.product.model")

    def get_android_version(self) -> str:
        return self.sh("getprop", "ro.build.version.release")

    # ── MTC Navigation (speed-optimized) ──────────────────────────────────
    def nav_to_book(self, book_name: str,
                    log_fn: Callable[[str], None] = print) -> bool:
        log_fn("Mở màn hình tìm truyện...")
        if not self.open_search_screen(log_fn):
            return False

        dump = self.dump_ui()
        center = self._parse_bounds(dump, "Tìm", exact=False)
        if not center:
            log_fn("⚠ Không tìm thấy ô tìm kiếm trong app")
            return False

        self.tap(*center)
        time.sleep(0.2)
        log_fn(f"Tìm: {book_name}")
        self.type_text(book_name)
        time.sleep(1.2)

        dump2 = self.dump_ui()
        return self._tap_book_result(book_name, dump2)

    def nav_to_chapter(self, chapter_index: int,
                       log_fn: Callable[[str], None] = print) -> bool:
        log_fn(f"Đi đến chương {chapter_index}...")
        if not self.open_chapter_list(log_fn):
            return False

        for _ in range(10):
            dump = self.dump_ui()
            center = self._find_chapter_center(dump, chapter_index)
            if center:
                self.tap(*center)
                time.sleep(0.18)
                return True
            self.swipe_up()
        return False

    @staticmethod
    def _book_key(title: str) -> str:
        return "".join(ch for ch in title.casefold() if ch.isalnum())

    def _parse_book_card(self, raw_text: str, bounds: str) -> Optional[Dict]:
        lines = [re.sub(r"\s+", " ", _clean_ui_text(line)) for line in raw_text.splitlines()]
        lines = [line for line in lines if line]
        if len(lines) < 4:
            return None

        tags = []
        while lines and lines[0].startswith("#"):
            tags.append(lines.pop(0))

        if len(lines) < 3:
            return None

        detail_lines = lines[:-2]
        if not detail_lines:
            return None

        title = detail_lines[0]
        author = detail_lines[1] if len(detail_lines) > 1 else ""
        extra = detail_lines[2:] if len(detail_lines) > 2 else []

        rating_text = lines[-2]
        chapter_line = lines[-1]
        chapter_digits = re.sub(r"\D", "", chapter_line)
        rect = _parse_bounds_rect(bounds)
        if not rect:
            return None

        rating = None
        try:
            rating = float(rating_text.replace(",", "."))
        except ValueError:
            pass

        return {
            "title": title,
            "author": author,
            "tags": tags,
            "extra_lines": extra,
            "rating": rating,
            "rating_text": rating_text,
            "chapter_count": int(chapter_digits) if chapter_digits else None,
            "chapter_text": chapter_digits or chapter_line,
            "raw_text": "\n".join(tags + detail_lines + [rating_text, chapter_line]),
            "bounds": rect,
            "center": ((rect[0] + rect[2]) // 2, (rect[1] + rect[3]) // 2),
        }

    def _tap_book_result(self, book_name: str, xml_str: str = "") -> bool:
        query_key = self._book_key(book_name)
        best = None
        best_score = 0.0

        for book in self.scan_visible_books(log_fn=lambda *_: None, xml_str=xml_str):
            title_key = self._book_key(book["title"])
            score = difflib.SequenceMatcher(None, query_key, title_key).ratio()
            if query_key and (query_key in title_key or title_key in query_key):
                score += 0.2
            if score > best_score:
                best = book
                best_score = score

        if not best or best_score < 0.65:
            return False

        self.tap(*best["center"])
        time.sleep(NAV_DELAY)
        return True

    @staticmethod
    def _parse_library_book_item(raw_desc: str, bounds: str) -> Optional[Dict]:
        lines = [re.sub(r"\s+", " ", _clean_ui_text(line)) for line in raw_desc.splitlines()]
        lines = [line for line in lines if line]
        if len(lines) < 2:
            return None

        progress_line = next((line for line in lines[1:] if "Đã đọc" in line), "")
        match = re.search(r"Đã đọc\s*(\d+)\s*/\s*(\d+)", progress_line, re.IGNORECASE)
        if not match:
            return None

        rect = _parse_bounds_rect(bounds)
        if not rect:
            return None

        read_current = int(match.group(1))
        read_total = int(match.group(2))
        title = lines[0]
        return {
            "title": title,
            "progress_text": progress_line,
            "read_current": read_current,
            "read_total": read_total,
            "fully_read": read_total > 0 and read_current >= read_total,
            "bounds": rect,
            "center": ((rect[0] + rect[2]) // 2, (rect[1] + rect[3]) // 2),
            "key": AdbController._book_key(title),
        }

    def scan_visible_library_books(
        self,
        log_fn: Callable[[str], None] = print,
        xml_str: str = "",
    ) -> List[Dict]:
        xml = xml_str or self.dump_ui()
        if not xml:
            return []

        try:
            root = ET.fromstring(xml)
        except ET.ParseError:
            log_fn("⚠ Không đọc được UI dump ở Tủ Truyện")
            return []

        books: List[Dict] = []
        seen = set()
        for node in root.iter():
            if node.get("clickable") != "true":
                continue
            raw_desc = _clean_ui_text(node.get("content-desc", ""))
            if "Đã đọc" not in raw_desc:
                continue

            rect = _parse_bounds_rect(node.get("bounds", ""))
            if not rect:
                continue
            if rect[1] < 200 or (rect[3] - rect[1]) < 40:
                continue

            book = self._parse_library_book_item(raw_desc, node.get("bounds", ""))
            if not book:
                continue
            if book["key"] in seen:
                continue

            seen.add(book["key"])
            books.append(book)

        books.sort(key=lambda item: (item["bounds"][1], item["bounds"][0]))
        return books

    def scan_library_books(
        self,
        max_items: int = 200,
        max_scrolls: int = 40,
        log_fn: Callable[[str], None] = print,
    ) -> List[Dict]:
        if not self.open_library_tab(log_fn):
            return []

        # Scroll to top first to ensure we start from the beginning
        self.scroll_to_top(max_swipes=10)

        all_books: List[Dict] = []
        seen = set()
        stagnant_rounds = 0

        for round_idx in range(max_scrolls):
            current = self.scan_visible_library_books(log_fn=lambda *_: None)
            new_count = 0
            for book in current:
                if book["key"] in seen:
                    continue
                seen.add(book["key"])
                all_books.append(book)
                new_count += 1

            log_fn(f"Quét Tủ Truyện lượt {round_idx + 1}: +{new_count} truyện")
            if len(all_books) >= max_items:
                break

            if new_count == 0:
                stagnant_rounds += 1
                if stagnant_rounds >= 2:
                    break
            else:
                stagnant_rounds = 0

            self.swipe_up()

        return all_books[:max_items]

    def open_library_book(
        self,
        book_name: str,
        max_scrolls: int = 40,
        log_fn: Callable[[str], None] = print,
    ) -> Optional[Dict]:
        if not self.open_library_tab(log_fn):
            return None

        # Scroll to top first to ensure we search from the beginning
        self.scroll_to_top(max_swipes=10)

        query_key = self._book_key(book_name)
        seen_pages = set()
        stagnant_rounds = 0

        for round_idx in range(max_scrolls):
            xml = self.dump_ui()
            visible_books = self.scan_visible_library_books(log_fn=lambda *_: None, xml_str=xml)
            best = None
            best_score = 0.0

            for book in visible_books:
                title_key = book.get("key") or self._book_key(book.get("title", ""))
                score = difflib.SequenceMatcher(None, query_key, title_key).ratio()
                if query_key and (query_key in title_key or title_key in query_key):
                    score += 0.2
                if score > best_score:
                    best = book
                    best_score = score

            if best and best_score >= 0.70:
                log_fn(f"Mở từ Tủ Truyện: {best['title']}")
                self.tap(*best["center"])
                time.sleep(1.1)
                return best

            page_signature = tuple(book["key"] for book in visible_books)
            if page_signature in seen_pages:
                stagnant_rounds += 1
                if stagnant_rounds >= 2:
                    break
            else:
                seen_pages.add(page_signature)
                stagnant_rounds = 0

            log_fn(f"Quét Tủ Truyện để mở truyện: lượt {round_idx + 1}")
            self.swipe_up()

        log_fn(f"⚠ Không tìm thấy truyện trong Tủ Truyện: {book_name}")
        return None

    def get_book_detail_meta(self, xml_str: str = "") -> Dict:
        xml = xml_str or self.dump_ui()
        texts = self.get_all_text(xml)
        status_text = next((text for text in texts if text.startswith("Chương - ")), "")
        read_center = self._find_clickable_text_center("Đọc truyện", exact=True, xml_str=xml)
        if not read_center:
            read_center = self._find_clickable_text_center("Đọc", exact=True, xml_str=xml)
        return {
            "status_text": status_text,
            "can_read": bool(read_center),
            "read_center": read_center,
        }

    @staticmethod
    def detail_status_is_completed(status_text: str) -> bool:
        lowered = _clean_ui_text(status_text).casefold()
        if not lowered:
            return False
        if "còn tiếp" in lowered:
            return False
        return "hoàn thành" in lowered

    def open_current_book_reader(self, log_fn: Callable[[str], None] = print) -> bool:
        detail = self.get_book_detail_meta()
        center = detail.get("read_center")
        if not center:
            log_fn("  ⚠ Không tìm thấy nút Đọc truyện")
            return False

        self.tap(*center)
        time.sleep(1.2)
        xml = self.dump_ui()
        if self._extract_reader_payload(xml):
            return True

        texts = self.get_all_text(xml)
        if self._chapter_list_visible(texts):
            chapter_center = self._find_visible_chapter_item_center(xml)
            if not chapter_center:
                log_fn("  ⚠ Đang ở D.S Chương nhưng không tìm thấy item để mở reader")
                return False
            self.tap(*chapter_center)
            time.sleep(1.0)
            xml = self.dump_ui()
            if self._extract_reader_payload(xml):
                return True
            texts = self.get_all_text(xml)
        if any(text.startswith("Chương ") for text in texts):
            return True

        log_fn("  ⚠ Không vào được reader")
        return False

    def _parse_reader_download_dialog(self, xml_str: str = "") -> Optional[Dict[str, tuple]]:
        xml = xml_str or self.dump_ui()
        try:
            root = ET.fromstring(xml)
        except ET.ParseError:
            return None

        fields = []
        confirm = None
        cancel = None
        for node in root.iter():
            cls = node.get("class", "")
            rect = _parse_bounds_rect(node.get("bounds", ""))
            if not rect:
                continue

            center = ((rect[0] + rect[2]) // 2, (rect[1] + rect[3]) // 2)
            if cls == "android.widget.EditText":
                fields.append((rect[1], center))
                continue

            desc = _clean_ui_text(node.get("content-desc", ""))
            if desc == "Đồng ý":
                confirm = center
            elif desc == "Hủy":
                cancel = center

        fields.sort(key=lambda item: item[0])
        if len(fields) < 2 or not confirm:
            return None

        return {
            "start": fields[0][1],
            "end": fields[1][1],
            "confirm": confirm,
            "cancel": cancel,
        }

    def open_reader_download_dialog(self, log_fn: Callable[[str], None] = print) -> bool:
        overlay_xml = ""
        center = None
        for attempt in range(2):
            if attempt == 0:
                self.reader_open_menu()
            else:
                self.reader_toggle_menu()
            time.sleep(0.55)
            overlay_xml = self.dump_ui()
            if not self._reader_menu_visible(overlay_xml):
                continue
            center = self._find_clickable_text_center("Tải truyện", exact=True, xml_str=overlay_xml)
            if center:
                break

        if not center:
            log_fn("  ⚠ Không tìm thấy mục Tải truyện trong reader")
            return False

        self.tap(*center)
        time.sleep(0.6)
        dialog = self._parse_reader_download_dialog(self.dump_ui())
        if dialog:
            return True

        log_fn("  ⚠ Không mở được popup tải truyện")
        return False

    def _clear_focused_text(self, max_chars: int = 8) -> None:
        for _ in range(max_chars):
            self.sh("input", "keyevent", str(KEY_DEL))
            time.sleep(0.03)

    def submit_reader_download_range(
        self,
        ch_start: int,
        ch_end: int,
        log_fn: Callable[[str], None] = print,
    ) -> bool:
        dialog = self._parse_reader_download_dialog(self.dump_ui())
        if not dialog:
            log_fn("  ⚠ Popup tải truyện chưa sẵn sàng")
            return False

        for key, value in (("start", ch_start), ("end", ch_end)):
            self.tap(*dialog[key])
            time.sleep(0.15)
            self._clear_focused_text()
            time.sleep(0.05)
            self.type_text(str(value))
            time.sleep(0.15)

        self.tap(*dialog["confirm"])
        time.sleep(0.8)

        texts = self.get_all_text(self.dump_ui())
        if any("Bạn đã tải tất cả các chương rồi." in text for text in texts):
            log_fn(f"  App báo đã tải đủ ch{ch_start}-{ch_end}")
            return True
        if any("Bạn muốn tải" in text for text in texts):
            log_fn("  ⚠ Popup tải truyện vẫn còn mở sau khi bấm Đồng ý")
            return False

        log_fn(f"  Đã gửi lệnh tải trong app: ch{ch_start}-{ch_end}")
        return True

    def queue_current_book_full_download(
        self,
        ch_end: int,
        ch_start: int = 1,
        log_fn: Callable[[str], None] = print,
    ) -> bool:
        if ch_end < ch_start:
            log_fn("  ⚠ Khoảng chương không hợp lệ")
            return False
        if not self.open_reader_download_dialog(log_fn):
            return False
        return self.submit_reader_download_range(ch_start, ch_end, log_fn)

    def return_to_library(self, log_fn: Callable[[str], None] = print, max_steps: int = 6) -> bool:
        for _ in range(max_steps):
            xml = self.dump_ui()
            if self.scan_visible_library_books(xml_str=xml):
                return True
            if self._main_tabs_visible(xml):
                return self.open_library_tab(log_fn)
            self.go_back()
            time.sleep(0.8)

        xml = self.dump_ui()
        if self.scan_visible_library_books(xml_str=xml):
            return True

        log_fn("⚠ Không quay lại được Tủ Truyện")
        return False

    def scan_visible_books(self, log_fn: Callable[[str], None] = print, xml_str: str = "") -> List[Dict]:
        xml = xml_str or self.dump_ui()
        if not xml:
            return []

        try:
            root = ET.fromstring(xml)
        except ET.ParseError:
            log_fn("⚠ Không đọc được UI dump")
            return []

        books = []
        seen = set()

        for node in root.iter():
            if node.get("class") != "android.view.View":
                continue
            if node.get("clickable") != "true":
                continue

            raw_text = _clean_ui_text(node.get("content-desc", ""))
            if raw_text.count("\n") < 3:
                continue

            rect = _parse_bounds_rect(node.get("bounds", ""))
            if not rect:
                continue
            if rect[1] < 120 or (rect[3] - rect[1]) < 100:
                continue

            book = self._parse_book_card(raw_text, node.get("bounds", ""))
            if not book or len(book["title"]) < 4:
                continue

            key = self._book_key(book["title"])
            if key in seen:
                continue

            seen.add(key)
            books.append(book)

        books.sort(key=lambda item: (item["bounds"][1], item["bounds"][0]))
        if books:
            log_fn(f"Quét thấy {len(books)} truyện trên màn hình")
        return books

    def scan_book_list(self, max_items: int = 40, max_scrolls: int = 6,
                       log_fn: Callable[[str], None] = print) -> List[Dict]:
        all_books: List[Dict] = []
        seen = set()
        stagnant_rounds = 0

        for round_idx in range(max_scrolls):
            current = self.scan_visible_books(log_fn=lambda *_: None)
            new_count = 0
            for book in current:
                key = self._book_key(book["title"])
                if key in seen:
                    continue
                seen.add(key)
                all_books.append(book)
                new_count += 1

            log_fn(f"Quét lượt {round_idx + 1}: +{new_count} truyện")
            if len(all_books) >= max_items:
                break

            if new_count == 0:
                stagnant_rounds += 1
                if stagnant_rounds >= 2:
                    break
            else:
                stagnant_rounds = 0

            self.swipe_up()

        return all_books[:max_items]

    # ── Text Extraction (speed-optimized) ─────────────────────────────────
    def read_current_chapter_payload(self,
                                     log_fn: Callable[[str], None] = print) -> Dict:
        xml = self.dump_ui()
        if self._reader_menu_visible(xml):
            self.reader_close_menu()
            time.sleep(0.08)
            xml = self.dump_ui()

        payload = self._extract_reader_payload(xml)
        if payload:
            log_fn(f"Đọc nhanh {payload['title']}...")
            return payload

        collected, seen, repeats = [], set(), 0
        title = ""
        chapter_index = None
        log_fn("Đọc nội dung chương...")

        for step in range(SCROLL_STEPS):
            dump = self.dump_ui()
            texts = self.get_all_text(dump)
            if not title:
                title = next((item for item in texts if item.startswith("Chương ")), "")
                if title:
                    match = re.search(r"Chương\s+(\d+)", title, re.IGNORECASE)
                    if match:
                        chapter_index = int(match.group(1))

            content = [t for t in texts if _is_story_text(t)]
            h_key = "|".join(content[:5])

            if h_key in seen:
                repeats += 1
                if repeats >= 1:
                    log_fn(f"  Hết chương (scroll {step})")
                    break
            else:
                seen.add(h_key)
                repeats = 0
                for t in content:
                    if not collected or t != collected[-1]:
                        collected.append(t)

            log_fn(f"  Scroll {step+1}: +{len(content)} đoạn")
            self.swipe_up()

        return {
            "title": title,
            "chapter_index": chapter_index,
            "text": "\n".join(collected),
        }

    def read_current_chapter(self,
                             log_fn: Callable[[str], None] = print) -> str:
        return self.read_current_chapter_payload(log_fn).get("text", "")
