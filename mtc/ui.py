"""ui.py – MTC Overlay (compact, always-on-top control panel)."""
import os, re, threading, queue, time, logging
from pathlib import Path

import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from .config import (
    BG, BG2, BORDER, BLUE, BLUE2, BHOV, FG, FG2, FG3,
    GREEN, YELLOW, RED, ORANGE,
    FONT, FONT_BOLD, FONT_HEAD, FONT_MONO,
    APK_PATH, OUTPUT_DIR, log,
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
        tk.Label(
            info,
            text="ℹ️  Chế độ hiện tại: chỉ tải bằng ADB.\n"
             "     BlueStacks là bắt buộc cho quét / khám phá / tải chương.",
            bg="#fff8e1",
            fg="#5d4037",
            font=("Segoe UI",8),
            justify="left",
            anchor="w",
        ).pack(padx=8, pady=6)

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
            self._chip.config(text="ADB")
            self._adb_lbl.config(text="chưa có BlueStacks/ADB", fg=YELLOW)
            self._lg("Không tìm thấy ADB. Ở chế độ hiện tại, BlueStacks là bắt buộc.", "w")
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
        self._chip.config(text="ADB")
        self._adb_lbl.config(text=f"đã kết nối: {serial}", fg=GREEN)
        self._lg(f"BlueStacks OK: {serial}", "ok")
        pkg = self._adb.get_installed_package()
        if pkg:
            self._btn_apk.config(text="✔ APK")
            self._lg(f"APK: {pkg}", "ok")
        else:
            self._btn_apk.config(text="Cài APK")
            self._lg("MTC chưa cài. Bấm 'Cài APK'.", "w")

    def _on_fail(self):
        self._chip.config(text="ADB")
        self._adb_lbl.config(text="không thấy BlueStacks", fg=YELLOW)
        self._lg("Không tìm thấy BlueStacks. Không thể tải ở chế độ ADB-only.", "w")

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

        if not (self._adb and self._adb.device):
            messagebox.showwarning("", "Cần BlueStacks/ADB để tải ở chế độ ADB-only")
            return

        self._lg("ADB-only mode: tải truyện trực tiếp qua BlueStacks.", "dim")

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
            result = download_book(
                adb=self._adb, book_name=book_name,
                ch_start=start, ch_end=end, output_dir=out_dir,
                log_fn=self._lg, stop_flag=lambda: self._stop,
                progress_cb=_progress,
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

    def _log_verify_result(self, result):
        reason = (result.get("reason") or "").strip()
        if reason:
            self._lg(reason, "w" if not result.get("success") else "dim")

    def _scan_books_via_adb(self):
        books = self._adb.scan_book_list(max_items=800, max_scrolls=120, log_fn=self._lg)
        if books:
            return books, "màn hiện tại"

        self._lg("ADB chưa thấy card truyện nào; thử mở tab Khám phá...", "w")
        if self._adb.open_explore_tab(self._lg):
            time.sleep(0.8)
            books = self._adb.scan_book_list(max_items=800, max_scrolls=120, log_fn=self._lg)
            if books:
                return books, "tab Khám phá"

        return [], "ADB"

    def _select_book_from_item(self, book):
        title = (book.get("title") or book.get("name") or "").strip()
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
            messagebox.showwarning("", "Cần BlueStacks/ADB để quét danh sách truyện")
            return

        win = tk.Toplevel(self)
        win.title("Quét toàn bộ danh sách truyện – MTC")
        win.geometry("1040x620")
        win.configure(bg=BG)
        win.attributes("-topmost", True)

           top = tk.Frame(win, bg=BG)
           top.pack(fill="x", padx=8, pady=6)
           _lbl(top, "Quét danh sách truyện bằng ADB từ app đang mở", FG2,
               FONT_BOLD, bg=BG).pack(side="left")
        count_lbl = _lbl(top, "", FG3, ("Segoe UI", 8), bg=BG)
        count_lbl.pack(side="right")

        filters = tk.Frame(win, bg=BG)
        filters.pack(fill="x", padx=8, pady=(0, 6))
        _lbl(filters, "🔍", bg=BG).pack(side="left")
        search_var = tk.StringVar()
                se = tk.Entry(filters, textvariable=search_var, bg=BG, fg=FG, font=FONT,
                                            bd=1, relief="solid", width=22, insertbackground=FG)
                se.pack(side="left", padx=4)
                _lbl(filters, "Sắp xếp:", bg=BG).pack(side="left", padx=(10, 4))
                sort_var = tk.StringVar(value="Tên A-Z")
                sort_cb = ttk.Combobox(filters, textvariable=sort_var, state="readonly",
                                                             values=["Tên A-Z", "Nhiều chương", "Điểm cao"],
                                                             width=14, font=FONT)
                sort_cb.pack(side="left")

                tree_wrap = tk.Frame(win, bg=BG)
                tree_wrap.pack(fill="both", expand=True, padx=8, pady=(0, 6))
                cols = ("name", "author", "ch", "score")
                tree = ttk.Treeview(tree_wrap, columns=cols, show="headings", selectmode="browse")
                tree.heading("name", text="Tên truyện")
                tree.heading("author", text="Tác giả")
                tree.heading("ch", text="Chương")
                tree.heading("score", text="Điểm")
                tree.column("name", width=500, anchor="w")
                tree.column("author", width=180, anchor="w")
        tree.column("ch", width=70, anchor="center", stretch=False)
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
        source_label = [""]

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
            chapter_count = book.get("chapter_count") or book.get("chapter_text") or "—"
            lines = [
                book.get("title") or "—",
                f"Tác giả: {book.get('author') or '—'}   Chương: {chapter_count}   Điểm: {rating}",
            ]
            tags = [tag for tag in (book.get("tags") or []) if tag]
            if tags:
                lines.append("Tag: " + ", ".join(tags))
            extras = [line for line in (book.get("extra_lines") or []) if line]
            if extras:
                lines.append("Thông tin: " + " | ".join(extras))
            raw = (book.get("raw_text") or "").strip()
            if raw:
                lines.append("")
                lines.append(raw)
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
        ttk.Button(actions, text="Mở Khám phá rồi quét", style="G.TButton",
                   command=lambda: _goto_explore_and_rescan()).pack(side="left", padx=(6, 0))
        ttk.Button(actions, text="Dùng truyện đã chọn", style="TButton",
                   command=_choose_selected).pack(side="left", padx=(6, 0))

        def _passes_filter(book):
            query = (search_var.get() or "").strip()
            if not query:
                return True

            query_key = self._book_lookup_key(query)
            haystacks = [
                book.get("title") or "",
                book.get("author") or "",
                " ".join(book.get("tags") or []),
                " ".join(book.get("extra_lines") or []),
                book.get("raw_text") or "",
            ]
            return any(query_key in self._book_lookup_key(value) for value in haystacks if value)

        def _sort_books(books):
            mode = sort_var.get()
            if mode == "Nhiều chương":
                return sorted(
                    books,
                    key=lambda book: (int(book.get("chapter_count") or 0), self._book_lookup_key(book.get("title") or "")),
                    reverse=True,
                )
            if mode == "Điểm cao":
                return sorted(
                    books,
                    key=lambda book: (float(book.get("rating") or 0), self._book_lookup_key(book.get("title") or "")),
                    reverse=True,
                )
            return sorted(books, key=lambda book: self._book_lookup_key(book.get("title") or ""))

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
                chapter_value = book.get("chapter_count") or book.get("chapter_text") or ""
                tree.insert(
                    "", "end", iid=f"scan:{idx}",
                    values=(
                        book.get("title") or "",
                        book.get("author") or "",
                        chapter_value,
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

        def _goto_explore_and_rescan():
            def _worker():
                if self._adb.open_explore_tab(self._lg):
                    self._lg("Đã mở tab Khám phá, quét lại...", "ok")
                    _safe_ui(_load_scan)
                else:
                    self._lg("⚠ Không mở được tab Khám phá", "err")

            threading.Thread(target=_worker, daemon=True).start()

        def _scan_worker():
            self._lg("Quét danh sách truyện bằng ADB...", "acc")
            try:
                if not (self._adb and self._adb.device):
                    raise RuntimeError("Không có BlueStacks để quét danh sách")

                books, current_source = self._scan_books_via_adb()

                if not books:
                    self._lg("ADB không thấy card truyện nào trên màn hình hiện tại.", "w")
                    self._lg("Hãy mở tab Khám phá hoặc màn kết quả tìm kiếm rồi bấm quét lại.", "w")

                def _update_full():
                    nonlocal full_items
                    full_items = books
                    source_label[0] = current_source
                    _fill([book for book in full_items if _passes_filter(book)], current_source)
                    if not full_items:
                        detail_var.set("ADB chưa thấy card truyện nào trên màn hình hiện tại.\n\nHãy mở tab Khám phá hoặc màn kết quả tìm kiếm trong app rồi quét lại.")

                _safe_ui(_update_full)
            except Exception as e:
                self._lg(f"ADB scan lỗi: {e}", "w")
                _safe_ui(lambda: (
                    count_lbl.config(text="Lỗi quét"),
                    detail_var.set(f"Không quét được danh sách truyện.\n\n{e}"),
                ))

        def _apply_filter(*_):
            _fill([book for book in full_items if _passes_filter(book)], source_label[0])

        def _load_scan():
            count_lbl.config(text="Đang quét...")
            detail_var.set("Đang quét danh sách truyện bằng ADB trong app...")
            for row in tree.get_children():
                tree.delete(row)
            threading.Thread(target=_scan_worker, daemon=True).start()

        tree.bind("<<TreeviewSelect>>", _on_select)
        tree.bind("<Double-1>", lambda _: _choose_selected())
        search_var.trace_add("write", _apply_filter)
        sort_cb.bind("<<ComboboxSelected>>", _apply_filter)

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

    # ── Danh sách truyện (ADB popup) ─────────────────────────────────────
    def _show_book_list(self):
        self._show_scanned_books()

        tree.bind("<Double-1>", _on_select)

        cb.bind("<<ComboboxSelected>>", lambda _: _load(1))
        se.bind("<Return>", lambda _: _load(1))

        _load(1)
