"""ui.py – MTC Overlay (compact, always-on-top control panel)."""
import os, re, difflib, threading, queue, time, logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta, timezone
from pathlib import Path

import tkinter as tk
from tkinter import ttk, filedialog, messagebox

try:
    import requests
    from requests.adapters import HTTPAdapter
    from urllib3.util.retry import Retry
    _HAS_REQUESTS = True
except ImportError:
    _HAS_REQUESTS = False

from .config import (
    BG, BG2, BORDER, BLUE, BLUE2, BHOV, FG, FG2, FG3,
    GREEN, YELLOW, RED, ORANGE,
    FONT, FONT_BOLD, FONT_HEAD, FONT_MONO,
    APK_PATH, OUTPUT_DIR, API_BASE, USER_AGENT, log,
)
from .adb import AdbController
from .pipeline import download_book
from .utils import safe_name


def _ef(parent, var, w=14, show=""):
    fr = tk.Frame(parent, bg=BG, highlightthickness=1,
                  highlightbackground=BORDER, highlightcolor=BLUE)
    e = tk.Entry(fr, textvariable=var, bg=BG, fg=FG,
                 font=FONT, bd=0, width=w, show=show, insertbackground=FG)
    e.pack(ipady=4, padx=5)
    e.bind("<FocusIn>",  lambda _: fr.config(highlightbackground=BLUE))
    e.bind("<FocusOut>", lambda _: fr.config(highlightbackground=BORDER))
    return fr

def _lbl(parent, text, color=FG2, font=FONT, **kw):
    kw.setdefault("bg", BG)
    return tk.Label(parent, text=text, fg=color, font=font, **kw)


class App(tk.Tk):
    """Compact overlay panel for MTC novel downloading via ADB."""

    def __init__(self):
        super().__init__()
        self.title("MTC Overlay")
        self.geometry("420x580")
        self.minsize(380, 480)
        self.configure(bg=BG)
        self.attributes("-topmost", True)  # Always on top

        # State
        self._q      = queue.Queue()
        self._thread = None
        self._stop   = False
        self._catalog_books_cache = []
        self._catalog_total_cache = 0
        self._catalog_detail_cache = {}

        # ADB
        self._adb_path = AdbController.find_adb()
        self._adb      = None
        self._selected_book_id = None
        self._selected_book_title = ""

        self._style()
        self._ui()
        self._poll()
        self.after(300, self._auto_connect)

    # ── Style ─────────────────────────────────────────────────────────────
    def _style(self):
        s = ttk.Style(self)
        s.theme_use("clam")
        s.configure(".", background=BG, foreground=FG, font=FONT, borderwidth=0)
        s.configure("TButton", background=ORANGE, foreground="#fff",
                    font=FONT_BOLD, padding=(12,6), relief="flat")
        s.map("TButton",
              background=[("active","#e8630a"),("pressed","#e8630a")])
        s.configure("G.TButton", background=BG2, foreground=FG,
                    font=FONT, padding=(8,4), relief="flat")
        s.map("G.TButton", background=[("active",BORDER)])
        s.configure("Horizontal.TProgressbar",
                    troughcolor=BORDER, background=ORANGE,
                    borderwidth=0, thickness=4)

    # ── UI ────────────────────────────────────────────────────────────────
    def _ui(self):
        # Header
        hdr = tk.Frame(self, bg=ORANGE, height=36)
        hdr.pack(fill="x"); hdr.pack_propagate(False)
        tk.Label(hdr, text="📖 MTC Overlay", bg=ORANGE, fg="#fff",
                 font=FONT_BOLD).pack(side="left", padx=10)
        self._chip = tk.Label(hdr, text="⏳", bg="#e8630a", fg="#fff",
                              font=("Segoe UI",8), padx=8, pady=1)
        self._chip.pack(side="right", padx=8, pady=4)

        body = tk.Frame(self, bg=BG)
        body.pack(fill="both", expand=True, padx=12, pady=8)

        # ── ADB status row ────────────────────────────────────────────────
        af = tk.Frame(body, bg=BG)
        af.pack(fill="x", pady=(0,6))
        _lbl(af, "BlueStacks:", FG2, FONT_BOLD).pack(side="left")
        self._adb_lbl = _lbl(af, "tuỳ chọn fallback, đang dò...", FG3)
        self._adb_lbl.pack(side="left", padx=4)
        ttk.Button(af, text="Dò", style="G.TButton",
                   command=self._scan_devices).pack(side="right")
        self._btn_apk = ttk.Button(af, text="Cài APK", style="G.TButton",
                                    command=self._install_apk)
        self._btn_apk.pack(side="right", padx=(0,4))

        tk.Frame(body, bg=BORDER, height=1).pack(fill="x", pady=4)

        # ── Book name + list button ──────────────────────────────────────
        bf2 = tk.Frame(body, bg=BG)
        bf2.pack(fill="x", pady=(0,2))
        _lbl(bf2, "Tên truyện:", FG2).pack(side="left")
        ttk.Button(bf2, text="📋 Danh sách", style="G.TButton",
                   command=self._show_scanned_books).pack(side="right")
        ttk.Button(bf2, text="📚 Quét hết", style="G.TButton",
                   command=self._show_scanned_books).pack(side="right", padx=(0,4))
        ttk.Button(bf2, text="Khám phá", style="G.TButton",
                   command=self._goto_explore).pack(side="right", padx=(0,4))
        self._book_var = tk.StringVar()
        self._book_var.trace_add("write", self._on_book_var_changed)
        _ef(body, self._book_var, 36).pack(fill="x", pady=(2,6))

        # ── Chapter range ─────────────────────────────────────────────────
        cr = tk.Frame(body, bg=BG)
        cr.pack(fill="x", pady=(0,6))
        _lbl(cr, "Từ chương:").pack(side="left")
        self._ch_from = tk.StringVar(value="1")
        _ef(cr, self._ch_from, 5).pack(side="left", padx=(4,12))
        _lbl(cr, "Đến:").pack(side="left")
        self._ch_to = tk.StringVar()
        _ef(cr, self._ch_to, 5).pack(side="left", padx=(4,0))

        # ── Output dir ────────────────────────────────────────────────────
        of = tk.Frame(body, bg=BG)
        of.pack(fill="x", pady=(0,6))
        _lbl(of, "Lưu vào:").pack(side="left")
        self._out_dir = tk.StringVar(value=str(OUTPUT_DIR))
        _ef(of, self._out_dir, 22).pack(side="left", padx=(4,4))
        ttk.Button(of, text="...", style="G.TButton",
                   command=self._browse).pack(side="left")

        # ── Info ──────────────────────────────────────────────────────────
        info = tk.Frame(body, bg="#fff8e1", highlightthickness=1,
                        highlightbackground="#fdd835")
        info.pack(fill="x", pady=(0,6))
        tk.Label(info, text="ℹ️  Ưu tiên tải trực tiếp qua API.\n"
             "     BlueStacks chỉ cần cho quét / khám phá / fallback khi API lỗi.",
                 bg="#fff8e1", fg="#5d4037", font=("Segoe UI",8),
                 justify="left", anchor="w").pack(padx=8, pady=6)

        # ── Progress ──────────────────────────────────────────────────────
        self._bar = ttk.Progressbar(body, mode="determinate",
                                     style="Horizontal.TProgressbar")
        self._bar.pack(fill="x", pady=(0,2))
        self._bar_lbl = tk.StringVar()
        tk.Label(body, textvariable=self._bar_lbl, bg=BG, fg=FG2,
                 font=FONT).pack(anchor="w", pady=(0,4))

        # ── Buttons ───────────────────────────────────────────────────────
        bf = tk.Frame(body, bg=BG)
        bf.pack(fill="x", pady=(0,6))
        self._btn_start = ttk.Button(bf, text="▶  Bắt đầu tải",
                                      command=self._start)
        self._btn_start.pack(side="left")
        self._btn_stop = ttk.Button(bf, text="Dừng", style="G.TButton",
                                     command=self._stop_dl, state="disabled")
        self._btn_stop.pack(side="left", padx=(6,0))
        ttk.Button(bf, text="📂", style="G.TButton",
                   command=self._open_folder).pack(side="right")

        tk.Frame(body, bg=BORDER, height=1).pack(fill="x")

        # ── Log ───────────────────────────────────────────────────────────
        lh = tk.Frame(body, bg=BG)
        lh.pack(fill="x", pady=(4,2))
        _lbl(lh, "Log", FG3, ("Segoe UI",8,"bold")).pack(side="left")
        ttk.Button(lh, text="Xoá", style="G.TButton",
                   command=self._clear_log).pack(side="right")

        self._log = tk.Text(body, bg=BG2, fg=FG2, font=FONT_MONO, bd=0,
                             wrap="word", state="disabled", height=8,
                             highlightthickness=1, highlightbackground=BORDER,
                             selectbackground=BHOV)
        vsb = ttk.Scrollbar(body, orient="vertical", command=self._log.yview)
        self._log.configure(yscrollcommand=vsb.set)
        lf = tk.Frame(body, bg=BG)
        lf.pack(fill="both", expand=True)
        vsb2 = ttk.Scrollbar(lf, orient="vertical", command=self._log.yview)
        self._log.configure(yscrollcommand=vsb2.set)
        vsb2.pack(side="right", fill="y")
        self._log.pack(in_=lf, side="left", fill="both", expand=True)

        for tag, color in [("ok",GREEN),("w",YELLOW),("err",RED),
                           ("acc",BLUE),("dim",FG3),("ora",ORANGE)]:
            self._log.tag_configure(tag, foreground=color)

    # ── Logging ───────────────────────────────────────────────────────────
    def _lg(self, msg, tag=""):
        self._q.put((msg, tag))
        lvl = {"err": logging.ERROR, "w": logging.WARNING,
               "ok": logging.INFO, "acc": logging.INFO,
               "ora": logging.INFO}.get(tag, logging.DEBUG)
        log.log(lvl, msg)

    def _poll(self):
        try:
            while True:
                msg, tag = self._q.get_nowait()
                self._log.config(state="normal")
                self._log.insert("end", f"{time.strftime('%H:%M:%S')}  ", "dim")
                self._log.insert("end", msg + "\n", tag or None)
                self._log.see("end")
                self._log.config(state="disabled")
        except queue.Empty:
            pass
        self.after(80, self._poll)

    def _clear_log(self):
        self._log.config(state="normal")
        self._log.delete("1.0", "end")
        self._log.config(state="disabled")

    # ── ADB ───────────────────────────────────────────────────────────────
    def _auto_connect(self):
        if not self._adb_path:
            self._chip.config(text="API")
            self._adb_lbl.config(text="không có fallback ADB", fg=YELLOW)
            self._lg("Không tìm thấy ADB. Vẫn tải trực tiếp qua API; BlueStacks chỉ là fallback.", "w")
            return
        self._lg(f"ADB: {self._adb_path}", "acc")
        threading.Thread(target=self._do_connect, daemon=True).start()

    def _do_connect(self):
        self._adb = AdbController(self._adb_path)
        self._adb.start_server()
        devs = self._adb.devices()
        if not devs:
            self._adb.connect("127.0.0.1:5555")
            time.sleep(1)
            devs = self._adb.devices()
        if devs:
            self._adb.device = devs[0]["serial"]
            serial = devs[0]["serial"]
            self.after(0, lambda: self._on_ok(serial))
        else:
            self.after(0, self._on_fail)

    def _on_ok(self, serial):
        self._chip.config(text="API + ADB")
        self._adb_lbl.config(text=f"fallback sẵn sàng: {serial}", fg=GREEN)
        self._lg(f"BlueStacks fallback OK: {serial}", "ok")
        pkg = self._adb.get_installed_package()
        if pkg:
            self._btn_apk.config(text="✔ APK")
            self._lg(f"APK: {pkg}", "ok")
        else:
            self._btn_apk.config(text="Cài APK")
            self._lg("MTC chưa cài. Bấm 'Cài APK'.", "w")

    def _on_fail(self):
        self._chip.config(text="API")
        self._adb_lbl.config(text="không thấy BlueStacks, API vẫn dùng được", fg=YELLOW)
        self._lg("Không tìm thấy BlueStacks. Vẫn tiếp tục ở chế độ API trực tiếp.", "w")

    def _scan_devices(self):
        self._lg("Dò BlueStacks fallback...", "acc")
        threading.Thread(target=self._do_connect, daemon=True).start()

    def _install_apk(self):
        if not self._adb or not self._adb.device:
            messagebox.showwarning("", "Tính năng này cần BlueStacks đã kết nối"); return
        if not APK_PATH.exists():
            messagebox.showerror("", f"Không tìm thấy\n{APK_PATH}"); return
        self._lg("Cài APK...", "ora")
        def _w():
            ok = self._adb.install_apk(APK_PATH, self._lg)
            if ok:
                self.after(0, lambda: self._btn_apk.config(text="✔ APK"))
                self._lg("✔ Đã cài", "ok")
            else:
                self._lg("✖ Lỗi cài APK", "err")
        threading.Thread(target=_w, daemon=True).start()

    # ── Download ──────────────────────────────────────────────────────────
    def _start(self):
        book = self._book_var.get().strip()
        if not book:
            messagebox.showwarning("", "Nhập tên truyện"); return
        if self._thread and self._thread.is_alive():
            return
        try:
            start = int(self._ch_from.get() or 1)
            end   = int(self._ch_to.get()) if self._ch_to.get().strip() else None
        except ValueError:
            messagebox.showerror("", "Số chương không hợp lệ"); return

        book_id = None
        if self._selected_book_id and \
           self._book_lookup_key(self._selected_book_title) == self._book_lookup_key(book):
            book_id = self._selected_book_id

        if self._adb and self._adb.device:
            self._lg("Ưu tiên tải qua API; BlueStacks chỉ dùng nếu cần fallback.", "dim")
        else:
            self._lg("Chưa có BlueStacks fallback. Sẽ tải trực tiếp qua API.", "dim")

        self._btn_start.config(state="disabled")
        self._btn_stop.config(state="normal")
        self._stop = False
        self._bar["value"] = 0
        self._bar_lbl.set("")

        self._thread = threading.Thread(
            target=self._worker,
            args=(book, Path(self._out_dir.get()), start, end, book_id),
            daemon=True,
        )
        self._thread.start()

    def _stop_dl(self):
        self._stop = True
        self._lg("Đang dừng...", "w")

    def _worker(self, book_name, out_dir, start, end, book_id=None):
        self._lg(f"Bắt đầu: «{book_name}»", "ora")
        try:
            def _progress(done, total):
                if total > 0:
                    pct = min(int(done / total * 100), 100)
                    self.after(0, lambda p=pct, m=f"{done}/{total}":
                               (self._bar.config(value=p),
                                self._bar_lbl.set(m)))
            result = download_book(
                adb=self._adb, book_name=book_name,
                ch_start=start, ch_end=end, output_dir=out_dir,
                log_fn=self._lg, stop_flag=lambda: self._stop,
                progress_cb=_progress, book_id=book_id,
            )
            if result.get("success"):
                self._lg(f"Xong! ✔{result['ok']}  ✖{result['fail']}", "ok")
                self._log_verify_result(result)
            else:
                self._lg(f"Lỗi: {result.get('reason','')}", "err")
                self._log_verify_result(result)
        except Exception as e:
            self._lg(f"Lỗi: {e}", "err")
        finally:
            self.after(0, lambda: (
                self._btn_start.config(state="normal"),
                self._btn_stop.config(state="disabled"),
                self._bar.config(value=100)))

    @staticmethod
    def _book_lookup_key(text: str) -> str:
        return "".join(ch for ch in (text or "").casefold() if ch.isalnum())

    def _on_book_var_changed(self, *_):
        current = (self._book_var.get() or "").strip()
        if self._book_lookup_key(current) != self._book_lookup_key(self._selected_book_title):
            self._selected_book_id = None
            self._selected_book_title = ""

    def _format_chapter_ranges(self, items, limit=12):
        nums = sorted({int(item) for item in (items or []) if isinstance(item, int) or str(item).isdigit()})
        if not nums:
            return ""
        ranges = []
        start = prev = nums[0]
        for num in nums[1:]:
            if num == prev + 1:
                prev = num
                continue
            ranges.append(f"{start}-{prev}" if start != prev else str(start))
            start = prev = num
        ranges.append(f"{start}-{prev}" if start != prev else str(start))
        if len(ranges) > limit:
            return ", ".join(ranges[:limit]) + ", ..."
        return ", ".join(ranges)

    def _log_verify_result(self, result):
        verified = result.get("verified")
        total = result.get("verify_total") or result.get("total")
        if verified is not None and total:
            tag = "ok" if result.get("success") else "w"
            self._lg(f"Verify: đủ {verified}/{total} chương", tag)

        sections = [
            ("Chương khóa thiếu file", result.get("locked_missing"), "w"),
            ("Chương khóa còn file cụt", result.get("locked_short"), "w"),
            ("Chương thiếu file", result.get("missing_files"), "err"),
            ("Chương ngắn bất thường", result.get("short_files"), "err"),
            ("Chương lệch word_count", result.get("word_count_mismatch"), "err"),
            ("Chương API báo khóa", result.get("locked_chapters"), "w"),
            ("Chương API còn lỗi", result.get("failed_chapter_indices"), "err"),
        ]
        for label, values, tag in sections:
            text = self._format_chapter_ranges(values)
            if text:
                self._lg(f"{label}: {text}", tag)

    def _http_session(self):
        sess = requests.Session()
        retry = Retry(total=2, backoff_factor=1,
                      status_forcelist=[429,500,502,503,504])
        sess.mount("https://", HTTPAdapter(max_retries=retry))
        sess.headers.update({"User-Agent": USER_AGENT, "Accept": "application/json"})
        return sess

    def _get_author_name(self, sess, cache, user_id: int) -> str:
        if not user_id:
            return ""
        if user_id in cache:
            return cache[user_id]
        try:
            resp = sess.get(f"{API_BASE}/users/{user_id}", timeout=10)
            data = (resp.json() or {}).get("data") or {}
            cache[user_id] = (data.get("name") or "").strip()
        except Exception:
            cache[user_id] = ""
        return cache[user_id]

    def _fetch_catalog_books(self, status=0, search="", log_fn=None):
        if not status and not search and self._catalog_books_cache:
            return [dict(book) for book in self._catalog_books_cache], self._catalog_total_cache or len(self._catalog_books_cache)

        sess = self._http_session()
        page = 1
        last = 1
        total = 0
        books = []
        seen_ids = set()

        while page <= last:
            params = {"limit": 100, "page": page}
            if status:
                params["filter[status]"] = status
            if search:
                params["search"] = search

            resp = sess.get(f"{API_BASE}/books", params=params, timeout=20)
            resp.raise_for_status()
            payload = resp.json() or {}
            chunk = payload.get("data") or []
            pagination = payload.get("pagination") or {}
            last = max(int(pagination.get("last") or page), 1)
            total = int(pagination.get("total") or total or len(chunk))

            for book in chunk:
                book_id = book.get("id")
                if not book_id or book_id in seen_ids:
                    continue
                seen_ids.add(book_id)
                books.append(book)

            if log_fn:
                log_fn(f"Quét catalog API: trang {page}/{last} (+{len(chunk)} truyện)", "dim")
            page += 1

        books.sort(key=lambda item: self._book_lookup_key(item.get("name") or ""))
        if not status and not search:
            self._catalog_books_cache = [dict(book) for book in books]
            self._catalog_total_cache = total or len(books)
        return books, total or len(books)

    @staticmethod
    def _format_score_text(raw_score):
        if raw_score in (None, ""):
            return ""
        try:
            return f"{float(raw_score):.1f}"
        except (TypeError, ValueError):
            return str(raw_score)

    @staticmethod
    def _parse_api_datetime(value):
        if not value:
            return None
        try:
            return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        except ValueError:
            return None

    @staticmethod
    def _coerce_text(value):
        if value is None:
            return ""
        if isinstance(value, str):
            return value.strip()
        if isinstance(value, dict):
            for key in ("name", "title", "label", "value"):
                text = value.get(key)
                if isinstance(text, str) and text.strip():
                    return text.strip()
            return ""
        if isinstance(value, (list, tuple, set)):
            parts = [App._coerce_text(part) for part in value]
            return ", ".join(part for part in parts if part)
        return str(value).strip()

    @staticmethod
    def _kind_label(kind):
        mapping = {
            1: "Chuyển ngữ",
            2: "Sáng tác",
        }
        return mapping.get(kind, "")

    def _catalog_item_from_api(self, book):
        chapter_count = book.get("latest_index") or book.get("chapter_count") or 0
        return {
            "id": book.get("id"),
            "api_id": book.get("id"),
            "name": book.get("name") or "",
            "title": book.get("name") or "",
            "chapter_count": chapter_count,
            "status_name": book.get("status_name") or book.get("state") or "",
            "bookmark_count": book.get("bookmark_count") or 0,
            "rating_text": self._format_score_text(book.get("review_score")),
            "synopsis": (book.get("synopsis") or "").strip(),
            "note": (book.get("note") or "").strip(),
            "link": book.get("link") or "",
            "kind": book.get("kind"),
            "kind_label": self._kind_label(book.get("kind")),
            "sex": book.get("sex"),
            "status": book.get("status"),
            "manager_pick": bool(book.get("manager_pick")),
            "high_quality": bool(book.get("high_quality")),
            "ready_for_sale": bool(book.get("ready_for_sale")),
            "published_at": book.get("published_at") or "",
            "published_dt": self._parse_api_datetime(book.get("published_at")),
            "new_chap_at": book.get("new_chap_at") or "",
            "new_chap_dt": self._parse_api_datetime(book.get("new_chap_at")),
            "view_count": book.get("view_count") or 0,
            "vote_count": book.get("vote_count") or 0,
            "comment_count": book.get("comment_count") or 0,
            "review_count": book.get("review_count") or 0,
            "review_score": book.get("review_score") or 0,
            "word_count": book.get("word_count") or 0,
            "genres": [],
            "personality_tags": [],
            "world_tags": [],
            "flow_tags": [],
            "perspective_tags": [],
            "source": "api_catalog",
        }

    def _fetch_book_detail(self, book_id: int):
        if book_id in self._catalog_detail_cache:
            return self._catalog_detail_cache[book_id]

        sess = self._http_session()
        resp = sess.get(f"{API_BASE}/books/{book_id}", timeout=20)
        resp.raise_for_status()
        detail = (resp.json() or {}).get("data") or {}
        if not isinstance(detail, dict):
            detail = {}
        self._catalog_detail_cache[book_id] = detail
        return detail

    def _merge_catalog_detail(self, item, detail):
        merged = dict(item)
        if not isinstance(detail, dict):
            detail = {}
        creator = detail.get("creator") or {}
        tag_groups = {}
        for tag in detail.get("tags") or []:
            name = (tag.get("name") or "").strip()
            type_id = str(tag.get("type_id") or "")
            if name and type_id:
                tag_groups.setdefault(type_id, []).append(name)

        genres = [
            (genre.get("name") or "").strip()
            for genre in (detail.get("genres") or [])
            if (genre.get("name") or "").strip()
        ]

        merged.update({
            "author": self._coerce_text(detail.get("author") or creator.get("name") or merged.get("author")),
            "chapter_count": detail.get("latest_index") or detail.get("chapter_count") or merged.get("chapter_count") or 0,
            "status_name": detail.get("status_name") or merged.get("status_name") or "",
            "status": detail.get("status") if detail.get("status") is not None else merged.get("status"),
            "bookmark_count": detail.get("bookmark_count") or merged.get("bookmark_count") or 0,
            "rating_text": self._format_score_text(detail.get("review_score") if detail.get("review_score") is not None else merged.get("review_score")),
            "review_score": detail.get("review_score") if detail.get("review_score") is not None else merged.get("review_score") or 0,
            "review_count": detail.get("review_count") or merged.get("review_count") or 0,
            "view_count": detail.get("view_count") or merged.get("view_count") or 0,
            "vote_count": detail.get("vote_count") or merged.get("vote_count") or 0,
            "comment_count": detail.get("comment_count") or merged.get("comment_count") or 0,
            "word_count": detail.get("word_count") or merged.get("word_count") or 0,
            "synopsis": self._coerce_text(detail.get("synopsis") or merged.get("synopsis")),
            "note": self._coerce_text(detail.get("note") or merged.get("note")),
            "link": detail.get("link") or merged.get("link") or "",
            "kind": detail.get("kind") if detail.get("kind") is not None else merged.get("kind"),
            "kind_label": self._kind_label(detail.get("kind") if detail.get("kind") is not None else merged.get("kind")),
            "sex": detail.get("sex") if detail.get("sex") is not None else merged.get("sex"),
            "manager_pick": bool(detail.get("manager_pick")) or merged.get("manager_pick", False),
            "high_quality": bool(detail.get("high_quality")) or merged.get("high_quality", False),
            "ready_for_sale": bool(detail.get("ready_for_sale")) if detail.get("ready_for_sale") is not None else merged.get("ready_for_sale", False),
            "published_at": detail.get("published_at") or merged.get("published_at") or "",
            "published_dt": self._parse_api_datetime(detail.get("published_at") or merged.get("published_at")),
            "new_chap_at": detail.get("new_chap_at") or merged.get("new_chap_at") or "",
            "new_chap_dt": self._parse_api_datetime(detail.get("new_chap_at") or merged.get("new_chap_at")),
            "genres": genres,
            "personality_tags": tag_groups.get("1", []),
            "world_tags": tag_groups.get("2", []),
            "flow_tags": tag_groups.get("3", []),
            "perspective_tags": tag_groups.get("4", []),
            "source": merged.get("source") or "api_catalog",
        })
        return merged

    def _hydrate_catalog_metadata(self, items, progress_cb=None):
        if not items:
            return []

        item_ids = [item.get("api_id") or item.get("id") for item in items]
        unique_ids = sorted({book_id for book_id in item_ids if book_id})
        missing_ids = [book_id for book_id in unique_ids if book_id not in self._catalog_detail_cache]

        done = 0
        total = len(items)
        if progress_cb:
            progress_cb(done, total)

        if missing_ids:
            max_workers = min(8, max(1, len(missing_ids)))
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                future_map = {executor.submit(self._fetch_book_detail, book_id): book_id for book_id in missing_ids}
                for future in as_completed(future_map):
                    book_id = future_map[future]
                    try:
                        self._catalog_detail_cache[book_id] = future.result()
                    except Exception:
                        self._catalog_detail_cache[book_id] = {}
                    if progress_cb:
                        progress_cb(min(done + 1, total), total)
                    done += 1

        enriched = []
        for item in items:
            book_id = item.get("api_id") or item.get("id")
            merged = self._merge_catalog_detail(item, self._catalog_detail_cache.get(book_id, {}))
            enriched.append(merged)

        if progress_cb:
            progress_cb(total, total)
        return enriched

    def _enrich_scanned_book(self, sess, book, user_cache):
        title = (book.get("title") or "").strip()
        if not title:
            return book

        try:
            resp = sess.get(
                f"{API_BASE}/books",
                params={"per_page": 10, "page": 1, "search": title},
                timeout=15,
            )
            candidates = (resp.json() or {}).get("data") or []
        except Exception:
            return book

        lookup_key = self._book_lookup_key(title)
        best = None
        best_score = 0.0
        for candidate in candidates:
            candidate_key = self._book_lookup_key(candidate.get("name", ""))
            score = difflib.SequenceMatcher(None, lookup_key, candidate_key).ratio()
            if lookup_key and lookup_key == candidate_key:
                score += 0.25
            if score > best_score:
                best = candidate
                best_score = score

        if not best or best_score < 0.65:
            return book

        enriched = dict(book)
        poster = best.get("poster") or {}
        enriched.update({
            "api_id": best.get("id"),
            "chapter_count": best.get("latest_index") or best.get("chapter_count") or 0,
            "status_name": best.get("status_name") or best.get("state") or "",
            "bookmark_count": best.get("bookmark_count") or 0,
            "synopsis": (best.get("synopsis") or "").strip(),
            "note": (best.get("note") or "").strip(),
            "poster_url": poster.get("150") or poster.get("300") or poster.get("default") or "",
            "link": best.get("link") or "",
        })

        api_author = self._get_author_name(sess, user_cache, best.get("user_id"))
        if api_author:
            enriched["api_author"] = api_author
            if not enriched.get("author"):
                enriched["author"] = api_author

        return enriched

    def _select_book_from_item(self, book):
        title = (book.get("title") or book.get("name") or "").strip()
        if not title:
            return
        self._book_var.set(title)
        self._selected_book_id = book.get("api_id") or book.get("id")
        self._selected_book_title = title
        chapter_count = book.get("chapter_count")
        if chapter_count:
            self._ch_to.set(str(chapter_count))
        self._lg(
            f"Chọn truyện: {title}"
            f"{' (' + str(chapter_count) + ' chương)' if chapter_count else ''}",
            "acc",
        )

    def _show_scanned_books(self):
        if not _HAS_REQUESTS and (not self._adb or not self._adb.device):
            messagebox.showwarning("", "Cần API hoặc BlueStacks để quét danh sách truyện")
            return

        win = tk.Toplevel(self)
        win.title("Quét toàn bộ danh sách truyện – MTC")
        win.geometry("1040x620")
        win.configure(bg=BG)
        win.attributes("-topmost", True)

        top = tk.Frame(win, bg=BG)
        top.pack(fill="x", padx=8, pady=6)
        _lbl(top, "Quét toàn bộ catalog truyện qua API; ADB chỉ fallback khi API lỗi", FG2,
             FONT_BOLD, bg=BG).pack(side="left")
        count_lbl = _lbl(top, "", FG3, ("Segoe UI", 8), bg=BG)
        count_lbl.pack(side="right")

        filters = tk.Frame(win, bg=BG)
        filters.pack(fill="x", padx=8, pady=(0, 6))
        _lbl(filters, "Lọc:", bg=BG).pack(side="left")
        filter_var = tk.StringVar(value="Tất cả")
        cb = ttk.Combobox(filters, textvariable=filter_var, state="readonly",
                          values=["Tất cả", "Hoàn thành", "Còn tiếp", "Tạm dừng"],
                          width=12, font=FONT)
        cb.pack(side="left", padx=(4, 8))
        _lbl(filters, "🔍", bg=BG).pack(side="left")
        search_var = tk.StringVar()
        se = tk.Entry(filters, textvariable=search_var, bg=BG, fg=FG, font=FONT,
                      bd=1, relief="solid", width=22, insertbackground=FG)
        se.pack(side="left", padx=4)

        tree_wrap = tk.Frame(win, bg=BG)
        tree_wrap.pack(fill="both", expand=True, padx=8, pady=(0, 6))
        cols = ("name", "status", "ch", "follow", "score")
        tree = ttk.Treeview(tree_wrap, columns=cols, show="headings", selectmode="browse")
        tree.heading("name", text="Tên truyện")
        tree.heading("status", text="Trạng thái")
        tree.heading("ch", text="Chương")
        tree.heading("follow", text="Theo dõi")
        tree.heading("score", text="Điểm")
        tree.column("name", width=530, anchor="w")
        tree.column("status", width=120, anchor="center", stretch=False)
        tree.column("ch", width=70, anchor="center", stretch=False)
        tree.column("follow", width=90, anchor="center", stretch=False)
        tree.column("score", width=70, anchor="center", stretch=False)
        vsb = ttk.Scrollbar(tree_wrap, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        tree.pack(side="left", fill="both", expand=True)

        info = tk.Frame(win, bg=BG2, highlightthickness=1, highlightbackground=BORDER)
        info.pack(fill="x", padx=8, pady=(0, 6))
        detail_var = tk.StringVar(value="Đang quét danh sách truyện...")
        tk.Label(info, textvariable=detail_var, bg=BG2, fg=FG, justify="left",
                 anchor="nw", font=FONT, wraplength=980).pack(fill="x", padx=10, pady=10)

        actions = tk.Frame(win, bg=BG)
        actions.pack(fill="x", padx=8, pady=(0, 8))

        items = []
        full_items = []

        def _selected_book():
            sel = tree.selection()
            if not sel:
                return None
            try:
                idx = int(sel[0].split(":", 1)[1])
            except (IndexError, ValueError):
                return None
            if 0 <= idx < len(items):
                return items[idx]
            return None

        def _format_detail(book):
            rating = book.get("rating_text") or "—"
            chapter_count = book.get("chapter_count") or "—"
            lines = [
                book.get("title") or "—",
                f"Trạng thái: {book.get('status_name') or '—'}   Chương: {chapter_count}",
                f"Theo dõi: {book.get('bookmark_count') or 0}   Điểm: {rating}",
            ]
            if book.get("author"):
                lines.append(f"Tác giả: {book['author']}")
            meta_bits = []
            if book.get("genres"):
                meta_bits.append("Thể loại: " + ", ".join(book.get("genres")[:6]))
            if book.get("flow_tags"):
                meta_bits.append("Lưu phái: " + ", ".join(book.get("flow_tags")[:6]))
            if book.get("world_tags"):
                meta_bits.append("Bối cảnh: " + ", ".join(book.get("world_tags")[:6]))
            if book.get("personality_tags"):
                meta_bits.append("Tính cách: " + ", ".join(book.get("personality_tags")[:6]))
            lines.extend(meta_bits[:3])
            if book.get("link"):
                lines.append(book["link"])
            synopsis = book.get("synopsis") or book.get("note") or ""
            synopsis = re.sub(r"\s+", " ", synopsis).strip()
            if synopsis:
                if len(synopsis) > 420:
                    synopsis = synopsis[:420].rsplit(" ", 1)[0] + "..."
                lines.append("")
                lines.append(synopsis)
            return "\n".join(lines)

        def _on_select(_=None):
            book = _selected_book()
            if book:
                detail_var.set(_format_detail(book))

        def _choose_selected():
            book = _selected_book()
            if not book:
                return
            self._select_book_from_item(book)
            win.destroy()

        filter_summary_var = tk.StringVar(value="Lọc nâng cao: chưa bật")
        tk.Label(win, textvariable=filter_summary_var, bg=BG, fg=FG3,
                 font=("Segoe UI", 8), anchor="w", justify="left").pack(fill="x", padx=8, pady=(0, 6))

        ttk.Button(actions, text="Quét lại", style="G.TButton",
                   command=lambda: _load_scan()).pack(side="left")
        filter_btn = ttk.Button(actions, text="Bộ lọc nâng cao", style="G.TButton",
                                state="disabled")
        filter_btn.pack(side="left", padx=(6, 0))
        ttk.Button(actions, text="Dùng truyện đã chọn", style="TButton",
                   command=_choose_selected).pack(side="left", padx=(6, 0))
        metadata_var = tk.StringVar(value="Metadata lọc: đang nạp...")
        tk.Label(actions, textvariable=metadata_var, bg=BG, fg=FG3,
                 font=("Segoe UI", 8)).pack(side="right")

        source_label = [""]
        metadata_ready = [False]
        filter_options = {
            "genres": [],
            "personality": [],
            "world": [],
            "flow": [],
        }
        filter_state = {
            "sort": "Mới lên chương",
            "kind": None,
            "sex": None,
            "status": None,
            "chapter_range": None,
            "publish_range": None,
            "attributes": set(),
            "genres": set(),
            "personality": set(),
            "world": set(),
            "flow": set(),
        }

        sort_options = [
            "Mới lên chương", "Mới đăng", "Lượt đọc", "Lượt đọc tuần", "Lượt đề cử",
            "Lượt đề cử tuần", "Lượt bình luận", "Lượt bình luận tuần", "Lượt đánh dấu",
            "Lượt đánh giá", "Điểm đánh giá", "Số chương", "Lượt mở khóa", "Tên truyện",
        ]
        kind_options = ["Chuyển ngữ", "Sáng tác"]
        sex_options = ["Truyện nam", "Truyện nữ"]
        status_options = ["Còn tiếp", "Hoàn thành", "Tạm dừng"]
        attribute_options = ["Chọn lọc", "Chất lượng cao", "Miễn phí", "Thu phí"]
        chapter_options = ["< 300", "300-600", "600-1000", "> 1000"]
        publish_options = ["Trong 1 tuần", "Trong 1 tháng", "Trong 3 tháng", "Trong 1 năm"]

        def _book_sex_label(book):
            return {1: "Truyện nam", 2: "Truyện nữ"}.get(book.get("sex"), "")

        def _build_dynamic_options(books):
            groups = {
                "genres": set(),
                "personality": set(),
                "world": set(),
                "flow": set(),
            }
            for book in books:
                groups["genres"].update(book.get("genres") or [])
                groups["personality"].update(book.get("personality_tags") or [])
                groups["world"].update(book.get("world_tags") or [])
                groups["flow"].update(book.get("flow_tags") or [])
            return {key: sorted(value) for key, value in groups.items()}

        def _filter_summary():
            parts = []
            if filter_state["sort"] and filter_state["sort"] != "Mới lên chương":
                parts.append(f"Sắp xếp: {filter_state['sort']}")
            for key, label in [
                ("kind", "Loại"),
                ("sex", "Giới tính"),
                ("status", "Tình trạng"),
                ("chapter_range", "Số chương"),
                ("publish_range", "Ngày xuất bản"),
            ]:
                if filter_state[key]:
                    parts.append(f"{label}: {filter_state[key]}")
            for key, label in [
                ("attributes", "Thuộc tính"),
                ("genres", "Thể loại"),
                ("personality", "Tính cách"),
                ("world", "Bối cảnh"),
                ("flow", "Lưu phái"),
            ]:
                values = sorted(filter_state[key])
                if values:
                    preview = ", ".join(values[:3])
                    suffix = "..." if len(values) > 3 else ""
                    parts.append(f"{label}: {preview}{suffix}")
            return "Lọc nâng cao: chưa bật" if not parts else " • ".join(parts)

        def _match_chapter_bucket(book):
            bucket = filter_state["chapter_range"]
            if not bucket:
                return True
            count = int(book.get("chapter_count") or 0)
            if bucket == "< 300":
                return count < 300
            if bucket == "300-600":
                return 300 <= count <= 600
            if bucket == "600-1000":
                return 600 < count <= 1000
            if bucket == "> 1000":
                return count > 1000
            return True

        def _match_publish_bucket(book):
            bucket = filter_state["publish_range"]
            if not bucket:
                return True
            published_dt = book.get("published_dt")
            if not published_dt:
                return False
            now = datetime.now(timezone.utc)
            day_ranges = {
                "Trong 1 tuần": 7,
                "Trong 1 tháng": 31,
                "Trong 3 tháng": 93,
                "Trong 1 năm": 366,
            }
            days = day_ranges.get(bucket)
            return bool(days) and published_dt >= now - timedelta(days=days)

        def _match_advanced(book):
            if filter_state["kind"] and (book.get("kind_label") or "") != filter_state["kind"]:
                return False
            if filter_state["sex"] and _book_sex_label(book) != filter_state["sex"]:
                return False
            if filter_state["status"] and (book.get("status_name") or "") != filter_state["status"]:
                return False
            attrs = filter_state["attributes"]
            if "Chọn lọc" in attrs and not book.get("manager_pick"):
                return False
            if "Chất lượng cao" in attrs and not book.get("high_quality"):
                return False
            if "Miễn phí" in attrs and book.get("ready_for_sale"):
                return False
            if "Thu phí" in attrs and not book.get("ready_for_sale"):
                return False
            if not _match_chapter_bucket(book):
                return False
            if not _match_publish_bucket(book):
                return False
            for selected, values in [
                (filter_state["genres"], set(book.get("genres") or [])),
                (filter_state["personality"], set(book.get("personality_tags") or [])),
                (filter_state["world"], set(book.get("world_tags") or [])),
                (filter_state["flow"], set(book.get("flow_tags") or [])),
            ]:
                if selected and not (selected & values):
                    return False
            return True

        def _sort_books(books):
            default_dt = datetime.min.replace(tzinfo=timezone.utc)
            mapping = {
                "Mới lên chương": (lambda book: book.get("new_chap_dt") or book.get("published_dt") or default_dt, True),
                "Mới đăng": (lambda book: book.get("published_dt") or default_dt, True),
                "Lượt đọc": (lambda book: int(book.get("view_count") or 0), True),
                "Lượt đọc tuần": (lambda book: int(book.get("view_count") or 0), True),
                "Lượt đề cử": (lambda book: int(book.get("vote_count") or 0), True),
                "Lượt đề cử tuần": (lambda book: int(book.get("vote_count") or 0), True),
                "Lượt bình luận": (lambda book: int(book.get("comment_count") or 0), True),
                "Lượt bình luận tuần": (lambda book: int(book.get("comment_count") or 0), True),
                "Lượt đánh dấu": (lambda book: int(book.get("bookmark_count") or 0), True),
                "Lượt đánh giá": (lambda book: int(book.get("review_count") or 0), True),
                "Điểm đánh giá": (lambda book: float(book.get("review_score") or 0), True),
                "Số chương": (lambda book: int(book.get("chapter_count") or 0), True),
                "Lượt mở khóa": (lambda book: int(book.get("unlock_count") or 0), True),
                "Tên truyện": (lambda book: self._book_lookup_key(book.get("title") or ""), False),
            }
            key_fn, reverse = mapping.get(filter_state["sort"], mapping["Mới lên chương"])
            return sorted(books, key=key_fn, reverse=reverse)

        def _passes_filter(book):
            selected_status = filter_var.get()
            if selected_status != "Tất cả" and (book.get("status_name") or "") != selected_status:
                return False
            if not _match_advanced(book):
                return False

            query = (search_var.get() or "").strip()
            if not query:
                return True

            query_key = self._book_lookup_key(query)
            haystacks = [
                book.get("title") or "",
                book.get("synopsis") or "",
                book.get("note") or "",
                book.get("link") or "",
                book.get("author") or "",
            ]
            return any(query_key in self._book_lookup_key(value) for value in haystacks if value)

        def _fill(books, source_label=""):
            nonlocal items
            items = _sort_books(list(books))
            for row in tree.get_children():
                tree.delete(row)
            if not items:
                count_lbl.config(text="0 truyện")
                detail_var.set("Không có truyện nào khớp bộ lọc hiện tại.")
                return

            for idx, book in enumerate(items):
                tree.insert(
                    "", "end", iid=f"scan:{idx}",
                    values=(
                        book.get("title") or "",
                        book.get("status_name") or "",
                        book.get("chapter_count") or "",
                        book.get("bookmark_count") or 0,
                        book.get("rating_text") or "",
                    ),
                    tags=(("odd" if idx % 2 else "even"),),
                )
            tree.tag_configure("odd", background=BG2)
            tree.tag_configure("even", background=BG)
            extra = f" ({source_label})" if source_label else ""
            count_lbl.config(text=f"{len(items)} truyện{extra}")
            first = tree.get_children()
            if first:
                tree.selection_set(first[0])
                _on_select()

        def _safe_ui(callback):
            def _run():
                try:
                    if not win.winfo_exists():
                        return
                    callback()
                except tk.TclError:
                    pass

            try:
                if not win.winfo_exists():
                    return
                win.after(0, _run)
            except tk.TclError:
                pass

        def _open_filter_sheet():
            if not metadata_ready[0]:
                messagebox.showinfo("", "Đang nạp metadata cho bộ lọc nâng cao, thử lại sau vài giây.")
                return

            popup = tk.Toplevel(win)
            popup.title("Bảng lọc truyện")
            popup.geometry("900x760")
            popup.configure(bg=BG)
            popup.attributes("-topmost", True)

            temp_state = {
                key: (set(value) if isinstance(value, set) else value)
                for key, value in filter_state.items()
            }
            chip_buttons = {}

            header = tk.Frame(popup, bg=BG)
            header.pack(fill="x", padx=10, pady=(10, 6))
            _lbl(header, "Bộ lọc truyện", FG, FONT_HEAD, bg=BG).pack(side="left")
            _lbl(header, "Chọn chip để lọc như trên app", FG3, ("Segoe UI", 8), bg=BG).pack(side="right")

            canvas_wrap = tk.Frame(popup, bg=BG)
            canvas_wrap.pack(fill="both", expand=True, padx=10, pady=(0, 8))
            canvas = tk.Canvas(canvas_wrap, bg=BG, highlightthickness=0)
            vsb = ttk.Scrollbar(canvas_wrap, orient="vertical", command=canvas.yview)
            content = tk.Frame(canvas, bg=BG)
            content.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
            canvas.create_window((0, 0), window=content, anchor="nw", width=850)
            canvas.configure(yscrollcommand=vsb.set)
            canvas.pack(side="left", fill="both", expand=True)
            vsb.pack(side="right", fill="y")

            def _selected(key, option):
                value = temp_state[key]
                return option in value if isinstance(value, set) else value == option

            def _paint_button(key, option):
                btn = chip_buttons[(key, option)]
                active = _selected(key, option)
                btn.config(
                    bg=BLUE if active else BG2,
                    fg="#ffffff" if active else FG,
                    activebackground=BLUE2 if active else BHOV,
                    activeforeground="#ffffff" if active else FG,
                    highlightbackground=BLUE if active else BORDER,
                )

            def _refresh_buttons():
                for key, option in chip_buttons:
                    _paint_button(key, option)

            def _toggle_chip(key, option, multi=False):
                if multi:
                    values = temp_state[key]
                    if option in values:
                        values.remove(option)
                    else:
                        values.add(option)
                else:
                    temp_state[key] = None if temp_state[key] == option else option
                _refresh_buttons()

            def _render_section(parent, title, options, key, multi=False, columns=4):
                if not options:
                    return
                section = tk.Frame(parent, bg=BG)
                section.pack(fill="x", pady=(0, 12))
                _lbl(section, title, FG, FONT_BOLD, bg=BG).pack(anchor="w", pady=(0, 6))
                grid = tk.Frame(section, bg=BG)
                grid.pack(fill="x")
                for idx, option in enumerate(options):
                    btn = tk.Button(
                        grid,
                        text=option,
                        font=FONT,
                        bd=0,
                        relief="flat",
                        padx=10,
                        pady=6,
                        cursor="hand2",
                        command=lambda opt=option: _toggle_chip(key, opt, multi),
                    )
                    btn.grid(row=idx // columns, column=idx % columns, padx=4, pady=4, sticky="w")
                    chip_buttons[(key, option)] = btn
                _refresh_buttons()

            _render_section(content, "Sắp xếp", sort_options, "sort", multi=False, columns=4)
            _render_section(content, "Loại", kind_options, "kind", multi=False, columns=4)
            _render_section(content, "Giới tính", sex_options, "sex", multi=False, columns=4)
            _render_section(content, "Tình trạng", status_options, "status", multi=False, columns=4)
            _render_section(content, "Thuộc tính", attribute_options, "attributes", multi=True, columns=4)
            _render_section(content, "Số chương", chapter_options, "chapter_range", multi=False, columns=4)
            _render_section(content, "Ngày xuất bản", publish_options, "publish_range", multi=False, columns=4)
            _render_section(content, "Thể loại", filter_options["genres"], "genres", multi=True, columns=5)
            _render_section(content, "Tính cách nhân vật chính", filter_options["personality"], "personality", multi=True, columns=5)
            _render_section(content, "Bối cảnh thế giới", filter_options["world"], "world", multi=True, columns=4)
            _render_section(content, "Lưu phái", filter_options["flow"], "flow", multi=True, columns=4)

            footer = tk.Frame(popup, bg=BG)
            footer.pack(fill="x", padx=10, pady=(0, 10))

            def _clear_filters():
                temp_state.update({
                    "sort": "Mới lên chương",
                    "kind": None,
                    "sex": None,
                    "status": None,
                    "chapter_range": None,
                    "publish_range": None,
                    "attributes": set(),
                    "genres": set(),
                    "personality": set(),
                    "world": set(),
                    "flow": set(),
                })
                _refresh_buttons()

            def _apply_advanced():
                for key, value in temp_state.items():
                    filter_state[key] = set(value) if isinstance(value, set) else value
                filter_var.set(filter_state["status"] or "Tất cả")
                filter_summary_var.set(_filter_summary())
                popup.destroy()
                _apply_filter()

            ttk.Button(footer, text="Xóa hết", style="G.TButton", command=_clear_filters).pack(side="left")
            ttk.Button(footer, text="Đóng", style="G.TButton", command=popup.destroy).pack(side="right")
            ttk.Button(footer, text="Áp dụng", style="TButton", command=_apply_advanced).pack(side="right", padx=(0, 6))

        filter_btn.config(command=_open_filter_sheet)

        def _metadata_worker(base_books):
            try:
                def _progress(done, total):
                    _safe_ui(lambda d=done, t=total: metadata_var.set(f"Metadata lọc: {d}/{t}" if t else "Metadata lọc: 0/0"))

                enriched = self._hydrate_catalog_metadata(base_books, progress_cb=_progress)
                dynamic_options = _build_dynamic_options(enriched)

                def _commit():
                    nonlocal full_items
                    full_items = enriched
                    filter_options.update(dynamic_options)
                    metadata_ready[0] = True
                    metadata_var.set("Metadata lọc: sẵn sàng")
                    filter_btn.config(state="normal")
                    filter_summary_var.set(_filter_summary())
                    _apply_filter()

                _safe_ui(_commit)
            except Exception as exc:
                _safe_ui(lambda e=exc: metadata_var.set(f"Metadata lọc lỗi: {e}"))

        def _scan_worker():
            self._lg("Quét toàn bộ danh sách truyện...", "acc")
            try:
                current_source = "API"
                if _HAS_REQUESTS:
                    api_books, total = self._fetch_catalog_books(log_fn=self._lg)
                    books = [self._catalog_item_from_api(book) for book in api_books]
                    self._lg(f"Quét catalog xong: {len(books)}/{total} truyện", "ok")
                elif self._adb and self._adb.device:
                    current_source = "ADB fallback"
                    books = self._adb.scan_book_list(max_items=300, max_scrolls=40, log_fn=self._lg)
                else:
                    raise RuntimeError("Không có API hoặc BlueStacks để quét danh sách")

                def _update_full():
                    nonlocal full_items
                    full_items = books
                    source_label[0] = current_source
                    metadata_ready[0] = False
                    metadata_var.set("Metadata lọc: đang nạp...")
                    filter_btn.config(state="disabled")
                    filter_summary_var.set(_filter_summary())
                    _fill([book for book in full_items if _passes_filter(book)], current_source)

                _safe_ui(_update_full)
                if _HAS_REQUESTS and books:
                    threading.Thread(target=lambda: _metadata_worker(books), daemon=True).start()
            except Exception as e:
                self._lg(f"API catalog lỗi: {e}", "w")
                if self._adb and self._adb.device:
                    try:
                        current_source = "ADB fallback"
                        books = self._adb.scan_book_list(max_items=300, max_scrolls=40, log_fn=self._lg)
                        if _HAS_REQUESTS and books:
                            sess = self._http_session()
                            user_cache = {}
                            books = [self._enrich_scanned_book(sess, book, user_cache) for book in books]

                        def _update_full_fallback():
                            nonlocal full_items
                            full_items = books
                            source_label[0] = current_source
                            metadata_ready[0] = False
                            metadata_var.set("Metadata lọc: đang nạp...")
                            filter_btn.config(state="disabled")
                            filter_summary_var.set(_filter_summary())
                            _fill([book for book in full_items if _passes_filter(book)], current_source)

                        _safe_ui(_update_full_fallback)
                        if _HAS_REQUESTS and books:
                            threading.Thread(target=lambda: _metadata_worker(books), daemon=True).start()
                        return
                    except Exception as fallback_error:
                        e = f"{e}\n\nADB fallback: {fallback_error}"

                _safe_ui(lambda: (
                    count_lbl.config(text="Lỗi quét"),
                    detail_var.set(f"Không quét được danh sách truyện.\n\n{e}"),
                ))

        def _apply_filter(*_):
            _fill([book for book in full_items if _passes_filter(book)], source_label[0])

        def _load_scan():
            count_lbl.config(text="Đang quét...")
            detail_var.set("Đang quét toàn bộ catalog truyện và nạp vào danh sách...")
            metadata_var.set("Metadata lọc: đang nạp...")
            filter_btn.config(state="disabled")
            for row in tree.get_children():
                tree.delete(row)
            threading.Thread(target=_scan_worker, daemon=True).start()

        tree.bind("<<TreeviewSelect>>", _on_select)
        tree.bind("<Double-1>", lambda _: _choose_selected())
        cb.bind("<<ComboboxSelected>>", _apply_filter)
        search_var.trace_add("write", _apply_filter)

        _load_scan()

    # ── Misc ──────────────────────────────────────────────────────────────
    def _browse(self):
        d = filedialog.askdirectory()
        if d:
            self._out_dir.set(d)

    def _open_folder(self):
        out = Path(self._out_dir.get())
        book = self._book_var.get().strip()
        if book:
            sub = out / safe_name(book)
            if sub.exists():
                out = sub
        out.mkdir(parents=True, exist_ok=True)
        os.startfile(str(out))

    # ── Khám phá (ADB) ───────────────────────────────────────────────────
    def _goto_explore(self):
        if not self._adb or not self._adb.device:
            messagebox.showwarning("", "Khám phá bằng tap ADB cần BlueStacks đã kết nối"); return
        self._lg("Mở tab Khám Phá...", "acc")
        def _w():
            if self._adb.open_explore_tab(self._lg):
                self._lg("Đã mở tab Khám Phá", "ok")
            else:
                self._lg("⚠ Không mở được tab Khám Phá", "err")
        threading.Thread(target=_w, daemon=True).start()

    # ── Danh sách truyện (API metadata popup) ────────────────────────────
    def _show_book_list(self):
        if not _HAS_REQUESTS:
            messagebox.showerror("", "Cần cài requests:\npip install requests")
            return
        win = tk.Toplevel(self)
        win.title("Danh sách truyện – MTC")
        win.geometry("520x500")
        win.configure(bg=BG)
        win.attributes("-topmost", True)

        # Filter row
        top = tk.Frame(win, bg=BG)
        top.pack(fill="x", padx=8, pady=6)
        _lbl(top, "Lọc:", bg=BG).pack(side="left")
        filter_var = tk.StringVar(value="Hoàn thành")
        cb = ttk.Combobox(top, textvariable=filter_var, state="readonly",
                          values=["Hoàn thành","Còn tiếp","Tạm dừng","Tất cả"],
                          width=12, font=FONT)
        cb.pack(side="left", padx=(4,8))
        # Search
        _lbl(top, "🔍", bg=BG).pack(side="left")
        search_var = tk.StringVar()
        se = tk.Entry(top, textvariable=search_var, bg=BG, fg=FG, font=FONT,
                      bd=1, relief="solid", width=18, insertbackground=FG)
        se.pack(side="left", padx=4)
        count_lbl = _lbl(top, "", FG3, ("Segoe UI",8), bg=BG)
        count_lbl.pack(side="right")

        # Treeview
        tf = tk.Frame(win, bg=BG)
        tf.pack(fill="both", expand=True, padx=8, pady=(0,4))
        cols = ("name","ch")
        tree = ttk.Treeview(tf, columns=cols, show="headings", selectmode="browse")
        tree.heading("name", text="Tên truyện")
        tree.heading("ch",   text="Chương", anchor="center")
        tree.column("name", width=380, anchor="w")
        tree.column("ch",   width=60,  anchor="center", stretch=False)
        vsb = ttk.Scrollbar(tf, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        tree.pack(side="left", fill="both", expand=True)

        # Page nav
        pg = tk.Frame(win, bg=BG)
        pg.pack(fill="x", padx=8, pady=(0,6))
        page_var = [1, 1]  # [current, last]
        pg_lbl = _lbl(pg, "—", FG2, bg=BG)
        pg_lbl.pack(side="left", padx=8)
        ttk.Button(pg, text="‹ Trước", style="G.TButton",
                   command=lambda: _load(page_var[0]-1)).pack(side="left")
        ttk.Button(pg, text="Sau ›", style="G.TButton",
                   command=lambda: _load(page_var[0]+1)).pack(side="left", padx=4)

        _STATUS = {"Hoàn thành":2, "Còn tiếp":1, "Tạm dừng":3, "Tất cả":0}
        all_books = []

        def _load(page=1):
            if page < 1 or (page_var[1] and page > page_var[1]):
                return
            page_var[0] = page
            count_lbl.config(text="Đang tải...")
            threading.Thread(target=lambda: _fetch(page), daemon=True).start()

        def _fetch(page):
            try:
                sess = requests.Session()
                retry = Retry(total=2, backoff_factor=1,
                              status_forcelist=[429,500,502,503,504])
                sess.mount("https://", HTTPAdapter(max_retries=retry))
                sess.headers.update({"User-Agent": USER_AGENT,
                                     "Accept": "application/json"})
                params = {"per_page": 50, "page": page}
                st = _STATUS.get(filter_var.get(), 0)
                if st:
                    params["filter[status]"] = st
                q = search_var.get().strip()
                if q:
                    params["search"] = q
                r = sess.get(f"{API_BASE}/books", params=params, timeout=15)
                d = r.json()
                books = d.get("data", [])
                pagi = d.get("pagination", {}) or {}
                page_var[1] = pagi.get("last", 1)
                total = pagi.get("total", len(books))
                nonlocal all_books
                all_books = books
                win.after(0, lambda: _fill(books, total, page))
            except Exception as e:
                win.after(0, lambda: count_lbl.config(text=f"Lỗi: {e}"))

        def _fill(books, total, page):
            for r in tree.get_children():
                tree.delete(r)
            for i, b in enumerate(books):
                ch = b.get("latest_index", b.get("chapter_count", 0))
                tree.insert("", "end", iid=str(b["id"]),
                            values=(b.get("name",""), ch),
                            tags=("o" if i%2 else "e",))
            tree.tag_configure("o", background=BG2)
            tree.tag_configure("e", background=BG)
            count_lbl.config(text=f"{total} truyện")
            pg_lbl.config(text=f"Trang {page}/{page_var[1]}")

        def _on_select(_=None):
            sel = tree.selection()
            if not sel:
                return
            bid = int(sel[0])
            book = next((b for b in all_books if b["id"]==bid), None)
            if book:
                self._select_book_from_item({
                    "id": book.get("id"),
                    "name": book.get("name", ""),
                    "chapter_count": book.get("latest_index", book.get("chapter_count", 0)),
                })
                win.destroy()

        tree.bind("<Double-1>", _on_select)

        cb.bind("<<ComboboxSelected>>", lambda _: _load(1))
        se.bind("<Return>", lambda _: _load(1))

        _load(1)
