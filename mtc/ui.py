"""ui.py – MTC Overlay (compact, always-on-top control panel)."""
import os, re, difflib, threading, queue, time, logging
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
from .pipeline import download_via_adb
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

        # ADB
        self._adb_path = AdbController.find_adb()
        self._adb      = None

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
        _lbl(af, "ADB:", FG2, FONT_BOLD).pack(side="left")
        self._adb_lbl = _lbl(af, "đang quét...", FG3)
        self._adb_lbl.pack(side="left", padx=4)
        ttk.Button(af, text="Quét", style="G.TButton",
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
                   command=self._show_book_list).pack(side="right")
        ttk.Button(bf2, text="📱 Quét", style="G.TButton",
               command=self._show_scanned_books).pack(side="right", padx=(0,4))
        ttk.Button(bf2, text="Khám phá", style="G.TButton",
                   command=self._goto_explore).pack(side="right", padx=(0,4))
        self._book_var = tk.StringVar()
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
        tk.Label(info, text="ℹ️  Mở MTC trên BlueStacks → vào truyện cần tải\n"
                 "     → nhập tên + chương → bấm Bắt đầu",
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
            self._chip.config(text="✖ No ADB")
            self._adb_lbl.config(text="không tìm thấy", fg=RED)
            self._lg("ADB không tìm thấy. Cài BlueStacks.", "err")
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
        self._chip.config(text=f"✔ {serial}")
        self._adb_lbl.config(text=f"✔ {serial}", fg=GREEN)
        self._lg(f"Kết nối OK: {serial}", "ok")
        pkg = self._adb.get_installed_package()
        if pkg:
            self._btn_apk.config(text="✔ APK")
            self._lg(f"APK: {pkg}", "ok")
        else:
            self._btn_apk.config(text="Cài APK")
            self._lg("MTC chưa cài. Bấm 'Cài APK'.", "w")

    def _on_fail(self):
        self._chip.config(text="✖ Offline")
        self._adb_lbl.config(text="không tìm thấy", fg=RED)
        self._lg("Không tìm thấy BlueStacks.", "err")

    def _scan_devices(self):
        self._lg("Quét thiết bị...", "acc")
        threading.Thread(target=self._do_connect, daemon=True).start()

    def _install_apk(self):
        if not self._adb or not self._adb.device:
            messagebox.showwarning("", "Kết nối BlueStacks trước"); return
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
        if not self._adb or not self._adb.device:
            messagebox.showwarning("", "Kết nối BlueStacks trước"); return
        if self._thread and self._thread.is_alive():
            return
        try:
            start = int(self._ch_from.get() or 1)
            end   = int(self._ch_to.get()) if self._ch_to.get().strip() else None
        except ValueError:
            messagebox.showerror("", "Số chương không hợp lệ"); return

        self._btn_start.config(state="disabled")
        self._btn_stop.config(state="normal")
        self._stop = False
        self._bar["value"] = 0
        self._bar_lbl.set("")

        self._thread = threading.Thread(
            target=self._worker,
            args=(book, Path(self._out_dir.get()), start, end),
            daemon=True,
        )
        self._thread.start()

    def _stop_dl(self):
        self._stop = True
        self._lg("Đang dừng...", "w")

    def _worker(self, book_name, out_dir, start, end):
        self._lg(f"Bắt đầu: «{book_name}»", "ora")
        try:
            def _progress(done, total):
                if total > 0:
                    pct = min(int(done / total * 100), 100)
                    self.after(0, lambda p=pct, m=f"{done}/{total}":
                               (self._bar.config(value=p),
                                self._bar_lbl.set(m)))
            result = download_via_adb(
                adb=self._adb, book_name=book_name,
                ch_start=start, ch_end=end, output_dir=out_dir,
                log_fn=self._lg, stop_flag=lambda: self._stop,
                progress_cb=_progress,
            )
            if result.get("success"):
                self._lg(f"Xong! ✔{result['ok']}  ✖{result['fail']}", "ok")
            else:
                self._lg(f"Lỗi: {result.get('reason','')}", "err")
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
        title = (book.get("title") or "").strip()
        if not title:
            return
        self._book_var.set(title)
        chapter_count = book.get("chapter_count")
        if chapter_count:
            self._ch_to.set(str(chapter_count))
        self._lg(
            f"Chọn truyện: {title}"
            f"{' (' + str(chapter_count) + ' chương)' if chapter_count else ''}",
            "acc",
        )

    def _show_scanned_books(self):
        if not self._adb or not self._adb.device:
            messagebox.showwarning("", "Kết nối BlueStacks trước")
            return

        win = tk.Toplevel(self)
        win.title("Quét truyện từ màn hình – MTC")
        win.geometry("1040x620")
        win.configure(bg=BG)
        win.attributes("-topmost", True)

        top = tk.Frame(win, bg=BG)
        top.pack(fill="x", padx=8, pady=6)
        _lbl(top, "Quét trực tiếp danh sách truyện đang mở trên BlueStacks", FG2,
             FONT_BOLD, bg=BG).pack(side="left")
        count_lbl = _lbl(top, "", FG3, ("Segoe UI", 8), bg=BG)
        count_lbl.pack(side="right")

        tree_wrap = tk.Frame(win, bg=BG)
        tree_wrap.pack(fill="both", expand=True, padx=8, pady=(0, 6))
        cols = ("tags", "name", "author", "score", "ch", "status")
        tree = ttk.Treeview(tree_wrap, columns=cols, show="headings", selectmode="browse")
        tree.heading("tags", text="Tag")
        tree.heading("name", text="Tên truyện")
        tree.heading("author", text="Tác giả")
        tree.heading("score", text="Điểm")
        tree.heading("ch", text="Chương")
        tree.heading("status", text="Trạng thái")
        tree.column("tags", width=180, anchor="w", stretch=False)
        tree.column("name", width=420, anchor="w")
        tree.column("author", width=180, anchor="w")
        tree.column("score", width=70, anchor="center", stretch=False)
        tree.column("ch", width=70, anchor="center", stretch=False)
        tree.column("status", width=110, anchor="center", stretch=False)
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
            tags = " ".join(book.get("tags") or []) or "—"
            author = book.get("author") or book.get("api_author") or "—"
            rating = book.get("rating_text") or "—"
            chapter_count = book.get("chapter_count") or book.get("chapter_text") or "—"
            lines = [
                book.get("title") or "—",
                f"Tag: {tags}",
                f"Tác giả: {author}",
                f"Điểm: {rating}   Chương: {chapter_count}",
            ]
            if book.get("chapter_count"):
                lines.append(f"Số chương hiện có: {book['chapter_count']}")
            if book.get("status_name"):
                lines.append(f"Trạng thái: {book['status_name']}")
            if book.get("bookmark_count"):
                lines.append(f"Theo dõi: {book['bookmark_count']}")
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

        ttk.Button(actions, text="Quét lại", style="G.TButton",
                   command=lambda: _load_scan()).pack(side="left")
        ttk.Button(actions, text="Dùng truyện đã chọn", style="TButton",
                   command=_choose_selected).pack(side="left", padx=(6, 0))

        def _fill(books):
            nonlocal items
            items = books
            for row in tree.get_children():
                tree.delete(row)
            if not books:
                count_lbl.config(text="0 truyện")
                detail_var.set("Không quét được truyện nào từ màn hình hiện tại.")
                return

            for idx, book in enumerate(books):
                tags = " ".join((book.get("tags") or [])[:2]) or "—"
                tree.insert(
                    "", "end", iid=f"scan:{idx}",
                    values=(
                        tags,
                        book.get("title") or "",
                        book.get("author") or book.get("api_author") or "",
                        book.get("rating_text") or "",
                        book.get("chapter_count") or "",
                        book.get("status_name") or "",
                    ),
                    tags=(("odd" if idx % 2 else "even"),),
                )
            tree.tag_configure("odd", background=BG2)
            tree.tag_configure("even", background=BG)
            count_lbl.config(text=f"{len(books)} truyện")
            first = tree.get_children()
            if first:
                tree.selection_set(first[0])
                _on_select()

        def _safe_ui(callback):
            try:
                win.after(0, callback)
            except tk.TclError:
                pass

        def _scan_worker():
            self._lg("Quét danh sách truyện trên màn hình...", "acc")
            try:
                books = self._adb.scan_book_list(log_fn=self._lg)
                if _HAS_REQUESTS and books:
                    sess = self._http_session()
                    user_cache = {}
                    books = [self._enrich_scanned_book(sess, book, user_cache) for book in books]
                _safe_ui(lambda: _fill(books))
            except Exception as e:
                _safe_ui(lambda: (
                    count_lbl.config(text="Lỗi quét"),
                    detail_var.set(f"Không quét được danh sách truyện.\n\n{e}"),
                ))

        def _load_scan():
            count_lbl.config(text="Đang quét...")
            detail_var.set("Đang quét danh sách truyện và đối chiếu metadata...")
            for row in tree.get_children():
                tree.delete(row)
            threading.Thread(target=_scan_worker, daemon=True).start()

        tree.bind("<<TreeviewSelect>>", _on_select)
        tree.bind("<Double-1>", lambda _: _choose_selected())

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
            messagebox.showwarning("", "Kết nối BlueStacks trước"); return
        self._lg("Mở tab Khám Phá...", "acc")
        def _w():
            w, h = self._adb.screen_size()
            # Tap "Khám Phá" tab (usually bottom-left area)
            self._adb.tap(w // 4, h - 60)
            time.sleep(0.8)
            self._lg("Đã tap vào Khám Phá", "ok")
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
                self._book_var.set(book.get("name",""))
                ch = book.get("latest_index", book.get("chapter_count",0))
                self._ch_to.set(str(ch))
                self._lg(f"Chọn: {book.get('name','')} ({ch} ch)", "acc")
                win.destroy()

        tree.bind("<Double-1>", _on_select)

        cb.bind("<<ComboboxSelected>>", lambda _: _load(1))
        se.bind("<Return>", lambda _: _load(1))

        _load(1)
