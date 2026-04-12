#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MTC Novel Downloader - GUI
Dark theme desktop interface built with tkinter
"""
import sys, io, os, json, threading, queue, time
from pathlib import Path

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

import tkinter as tk
from tkinter import ttk, filedialog, messagebox

# ── Colours ──────────────────────────────────────────────────────────────────
BG      = "#0f1117"
BG2     = "#1a1d2e"
BG3     = "#252840"
ACCENT  = "#6c63ff"
ACCENT2 = "#4f46e5"
FG      = "#e2e8f0"
FG2     = "#94a3b8"
GREEN   = "#22c55e"
YELLOW  = "#f59e0b"
RED     = "#ef4444"
BORDER  = "#2d3148"

FONT_TITLE = ("Segoe UI", 13, "bold")
FONT_HEAD  = ("Segoe UI", 10, "bold")
FONT_BODY  = ("Segoe UI", 9)
FONT_MONO  = ("Consolas", 9)

# ── Import downloader logic ────────────────────────────────────────────────
try:
    import downloader as dl
    _dl_ok = True
except ImportError:
    _dl_ok = False

# ── Helpers ───────────────────────────────────────────────────────────────
def make_session(token=None):
    return dl.make_session(token) if _dl_ok else None

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("MTC Novel Downloader")
        self.geometry("1100x700")
        self.minsize(900, 600)
        self.configure(bg=BG)
        self._set_icon()

        # State
        self.session   = make_session() if _dl_ok else None
        self.books     = []
        self.sel_book  = None
        self.log_q     = queue.Queue()
        self.dl_thread = None

        self._style()
        self._build_ui()
        self._after_log()   # start log polling

        # load first page on start
        self.after(200, lambda: self._search())

    # ── Window icon ──────────────────────────────────────────────────────
    def _set_icon(self):
        try:
            self.iconbitmap(default="")
        except Exception:
            pass

    # ── ttk style ─────────────────────────────────────────────────────────
    def _style(self):
        s = ttk.Style(self)
        s.theme_use("clam")
        s.configure(".",           background=BG,  foreground=FG,
                    font=FONT_BODY, borderwidth=0)
        s.configure("TFrame",      background=BG)
        s.configure("Card.TFrame", background=BG2)
        s.configure("TLabel",      background=BG,  foreground=FG)
        s.configure("Dim.TLabel",  background=BG,  foreground=FG2)
        s.configure("Card.TLabel", background=BG2, foreground=FG)
        s.configure("TButton",     background=ACCENT, foreground="#ffffff",
                    padding=(12,6), font=FONT_HEAD, borderwidth=0,
                    focusthickness=0, relief="flat")
        s.map("TButton",
              background=[("active", ACCENT2), ("pressed", ACCENT2)],
              relief=[("pressed","flat")])
        s.configure("Ghost.TButton", background=BG3, foreground=FG,
                    padding=(10,5), borderwidth=0, relief="flat")
        s.map("Ghost.TButton",
              background=[("active", BORDER), ("pressed", BORDER)])
        s.configure("TEntry", fieldbackground=BG3, foreground=FG,
                    insertcolor=FG, borderwidth=1, relief="flat",
                    padding=(8,6))
        s.configure("TScrollbar", background=BG3, troughcolor=BG2,
                    borderwidth=0, arrowcolor=FG2)
        s.configure("Horizontal.TProgressbar",
                    troughcolor=BG3, background=ACCENT,
                    borderwidth=0, thickness=6)
        s.configure("Treeview",
                    background=BG2, foreground=FG,
                    fieldbackground=BG2, rowheight=32,
                    borderwidth=0, font=FONT_BODY)
        s.configure("Treeview.Heading",
                    background=BG3, foreground=FG2,
                    font=FONT_HEAD, borderwidth=0, relief="flat")
        s.map("Treeview",
              background=[("selected", ACCENT2)],
              foreground=[("selected", "#ffffff")])

    # ── UI layout ─────────────────────────────────────────────────────────
    def _build_ui(self):
        # ─ Title bar ─
        hdr = tk.Frame(self, bg=BG2, height=56)
        hdr.pack(fill="x", side="top")
        hdr.pack_propagate(False)

        tk.Label(hdr, text="📚", bg=BG2, fg=ACCENT,
                 font=("Segoe UI Emoji", 20)).pack(side="left", padx=(18,6), pady=8)
        tk.Label(hdr, text="MTC Novel Downloader",
                 bg=BG2, fg=FG, font=FONT_TITLE).pack(side="left", pady=8)
        tk.Label(hdr, text="v2.0  •  android.lonoapp.net",
                 bg=BG2, fg=FG2, font=FONT_BODY).pack(side="left", padx=12, pady=8)

        # ─ Main paned ─
        paned = tk.PanedWindow(self, orient="horizontal",
                               bg=BG, sashwidth=4, sashrelief="flat",
                               sashpad=0, bd=0)
        paned.pack(fill="both", expand=True, padx=0, pady=0)

        # LEFT: book browser
        left = tk.Frame(paned, bg=BG, width=520)
        paned.add(left, minsize=400)

        # RIGHT: details + download
        right = tk.Frame(paned, bg=BG, width=560)
        paned.add(right, minsize=380)

        self._build_left(left)
        self._build_right(right)

    # ── LEFT panel ────────────────────────────────────────────────────────
    def _build_left(self, parent):
        # Search bar
        top = tk.Frame(parent, bg=BG, padx=14, pady=12)
        top.pack(fill="x")

        self.search_var = tk.StringVar()
        entry = ttk.Entry(top, textvariable=self.search_var, font=FONT_BODY)
        entry.pack(side="left", fill="x", expand=True, ipady=3)
        entry.bind("<Return>", lambda _: self._search())
        entry.insert(0, "Tìm truyện...")
        entry.bind("<FocusIn>",  lambda e: (entry.get() == "Tìm truyện..." and
                                             (self.search_var.set(""), entry.config(foreground=FG))))
        entry.bind("<FocusOut>", lambda e: (not self.search_var.get() and
                                             (self.search_var.set("Tìm truyện..."), entry.config(foreground=FG2))))
        entry.config(foreground=FG2)

        ttk.Button(top, text="Tìm", command=self._search).pack(side="left", padx=(8,0))
        ttk.Button(top, text="Tất cả", style="Ghost.TButton",
                   command=lambda: (self.search_var.set(""), self._search())).pack(side="left", padx=(6,0))

        # Separator line
        tk.Frame(parent, bg=BORDER, height=1).pack(fill="x")

        # Treeview
        tree_frame = tk.Frame(parent, bg=BG)
        tree_frame.pack(fill="both", expand=True, padx=14, pady=(10,0))

        cols = ("id", "name", "ch", "status")
        self.tree = ttk.Treeview(tree_frame, columns=cols, show="headings",
                                  selectmode="browse")
        self.tree.heading("id",     text="ID",      anchor="center")
        self.tree.heading("name",   text="Tên truyện")
        self.tree.heading("ch",     text="Chương",  anchor="center")
        self.tree.heading("status", text="Trạng thái")
        self.tree.column("id",     width=75,  anchor="center", stretch=False)
        self.tree.column("name",   width=270, anchor="w")
        self.tree.column("ch",     width=65,  anchor="center", stretch=False)
        self.tree.column("status", width=90,  anchor="center", stretch=False)

        vsb = ttk.Scrollbar(tree_frame, orient="vertical",   command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        self.tree.pack(side="left", fill="both", expand=True)
        self.tree.bind("<<TreeviewSelect>>", self._on_select)
        self.tree.bind("<Double-1>",         self._on_select)

        # Alternating row colours
        self.tree.tag_configure("odd",  background="#1e2135")
        self.tree.tag_configure("even", background=BG2)

        # Pagination
        pg = tk.Frame(parent, bg=BG, padx=14, pady=10)
        pg.pack(fill="x")
        self.page_var  = tk.IntVar(value=1)
        self.total_var = tk.StringVar(value="")

        ttk.Button(pg, text="◀", style="Ghost.TButton", width=3,
                   command=self._prev_page).pack(side="left")
        tk.Label(pg, textvariable=self.total_var,
                 bg=BG, fg=FG2, font=FONT_BODY).pack(side="left", padx=8)
        ttk.Button(pg, text="▶", style="Ghost.TButton", width=3,
                   command=self._next_page).pack(side="left")

        self.status_bar = tk.Label(pg, text="Đang tải...", bg=BG, fg=FG2,
                                   font=FONT_BODY, anchor="e")
        self.status_bar.pack(side="right")

    # ── RIGHT panel ───────────────────────────────────────────────────────
    def _build_right(self, parent):
        parent.grid_rowconfigure(1, weight=1)
        parent.columnconfigure(0, weight=1)

        # ── Book info card ──
        self.info_frame = tk.Frame(parent, bg=BG2, bd=0)
        self.info_frame.pack(fill="x", padx=14, pady=(14,0))

        self.lbl_title    = tk.Label(self.info_frame, text="← Chọn truyện từ danh sách",
                                     bg=BG2, fg=FG2, font=FONT_TITLE,
                                     anchor="w", wraplength=480, justify="left")
        self.lbl_title.pack(fill="x", padx=14, pady=(14,4))

        meta = tk.Frame(self.info_frame, bg=BG2)
        meta.pack(fill="x", padx=14, pady=(0,4))

        self.lbl_id     = self._meta_label(meta, "ID: —")
        self.lbl_ch     = self._meta_label(meta, "Chương: —")
        self.lbl_status = self._meta_label(meta, "Trạng thái: —")
        self.lbl_rating = self._meta_label(meta, "Đánh giá: —")

        self.lbl_synopsis = tk.Label(self.info_frame, text="",
                                     bg=BG2, fg=FG2, font=FONT_BODY,
                                     anchor="nw", wraplength=460,
                                     justify="left")
        self.lbl_synopsis.pack(fill="x", padx=14, pady=(2,14))

        # ── Download controls card ──
        ctrl = tk.Frame(parent, bg=BG2)
        ctrl.pack(fill="x", padx=14, pady=(10,0))

        tk.Label(ctrl, text="TẢI XUỐNG", bg=BG2, fg=ACCENT,
                 font=("Segoe UI", 8, "bold")).pack(anchor="w", padx=14, pady=(12,4))

        row1 = tk.Frame(ctrl, bg=BG2)
        row1.pack(fill="x", padx=14, pady=(0,8))

        self._field_label(row1, "Từ chương:")
        self.from_var = tk.StringVar(value="1")
        ttk.Entry(row1, textvariable=self.from_var, width=7).pack(side="left", padx=(4,16))

        self._field_label(row1, "Đến chương:")
        self.to_var = tk.StringVar(value="")
        ttk.Entry(row1, textvariable=self.to_var, width=7).pack(side="left", padx=(4,0))
        tk.Label(row1, text="(để trống = tất cả)", bg=BG2, fg=FG2,
                 font=FONT_BODY).pack(side="left", padx=8)

        row2 = tk.Frame(ctrl, bg=BG2)
        row2.pack(fill="x", padx=14, pady=(0,8))

        self._field_label(row2, "Lưu vào:")
        self.out_var = tk.StringVar(value=str(Path.cwd() / "downloads"))
        ttk.Entry(row2, textvariable=self.out_var, width=30).pack(side="left", padx=(4,6))
        ttk.Button(row2, text="...", style="Ghost.TButton", width=3,
                   command=self._browse_output).pack(side="left")

        row3 = tk.Frame(ctrl, bg=BG2)
        row3.pack(fill="x", padx=14, pady=(0,12))

        self._field_label(row3, "Delay (s):")
        self.delay_var = tk.StringVar(value="0.5")
        ttk.Entry(row3, textvariable=self.delay_var, width=6).pack(side="left", padx=(4,16))

        self._field_label(row3, "APP_KEY:")
        self.key_var = tk.StringVar(value="")
        ttk.Entry(row3, textvariable=self.key_var, width=28).pack(side="left", padx=(4,0))

        # Progress bar
        prog_f = tk.Frame(ctrl, bg=BG2)
        prog_f.pack(fill="x", padx=14, pady=(0,4))
        self.progress = ttk.Progressbar(prog_f, mode="determinate",
                                        style="Horizontal.TProgressbar")
        self.progress.pack(fill="x")

        prog_label_f = tk.Frame(ctrl, bg=BG2)
        prog_label_f.pack(fill="x", padx=14, pady=(2,10))
        self.prog_var = tk.StringVar(value="")
        tk.Label(prog_label_f, textvariable=self.prog_var, bg=BG2,
                 fg=FG2, font=FONT_BODY).pack(side="left")

        # Buttons
        btn_f = tk.Frame(ctrl, bg=BG2)
        btn_f.pack(fill="x", padx=14, pady=(0,14))

        self.btn_dl   = ttk.Button(btn_f, text="▶  TẢI CHƯƠNG",
                                   command=self._start_download)
        self.btn_dl.pack(side="left")
        self.btn_stop = ttk.Button(btn_f, text="■  Dừng", style="Ghost.TButton",
                                   command=self._stop_download, state="disabled")
        self.btn_stop.pack(side="left", padx=(8,0))
        ttk.Button(btn_f, text="📂 Mở thư mục", style="Ghost.TButton",
                   command=self._open_folder).pack(side="right")

        # ── Log panel ──
        log_head = tk.Frame(parent, bg=BG)
        log_head.pack(fill="x", padx=14, pady=(10,4))
        tk.Label(log_head, text="LOG", bg=BG, fg=ACCENT,
                 font=("Segoe UI", 8, "bold")).pack(side="left")
        ttk.Button(log_head, text="Xoá", style="Ghost.TButton",
                   command=self._clear_log).pack(side="right")

        log_frame = tk.Frame(parent, bg=BG)
        log_frame.pack(fill="both", expand=True, padx=14, pady=(0,14))

        self.log_text = tk.Text(log_frame, bg="#0a0c14", fg=FG2,
                                font=FONT_MONO, bd=0, wrap="word",
                                state="disabled", insertbackground=FG,
                                selectbackground=ACCENT2)
        log_vsb = ttk.Scrollbar(log_frame, orient="vertical",
                                 command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=log_vsb.set)
        log_vsb.pack(side="right", fill="y")
        self.log_text.pack(side="left", fill="both", expand=True)

        # Log colour tags
        self.log_text.tag_configure("INFO",    foreground=FG2)
        self.log_text.tag_configure("OK",      foreground=GREEN)
        self.log_text.tag_configure("WARN",    foreground=YELLOW)
        self.log_text.tag_configure("ERROR",   foreground=RED)
        self.log_text.tag_configure("ACCENT",  foreground=ACCENT)
        self.log_text.tag_configure("DIM",     foreground="#4a5568")

    # ── Small helper widgets ──────────────────────────────────────────────
    def _meta_label(self, parent, text):
        lbl = tk.Label(parent, text=text, bg=BG2, fg=FG2, font=FONT_BODY)
        lbl.pack(side="left", padx=(0,16))
        return lbl

    def _field_label(self, parent, text):
        tk.Label(parent, text=text, bg=BG2, fg=FG2, font=FONT_BODY).pack(side="left")

    # ── Log helpers ───────────────────────────────────────────────────────
    def _log(self, msg, tag="INFO"):
        self.log_q.put((msg, tag))

    def _after_log(self):
        try:
            while True:
                msg, tag = self.log_q.get_nowait()
                self.log_text.config(state="normal")
                ts = time.strftime("%H:%M:%S")
                self.log_text.insert("end", f"[{ts}] ", "DIM")
                self.log_text.insert("end", msg + "\n", tag)
                self.log_text.see("end")
                self.log_text.config(state="disabled")
        except queue.Empty:
            pass
        self.after(80, self._after_log)

    def _clear_log(self):
        self.log_text.config(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.config(state="disabled")

    # ── Book browsing ─────────────────────────────────────────────────────
    def _search(self, reset_page=True):
        if not _dl_ok:
            self._log("downloader.py not found!", "ERROR"); return
        if reset_page:
            self.page_var.set(1)
        self.status_bar.config(text="Đang tải...")
        q = self.search_var.get().strip()
        if q in ("", "Tìm truyện..."):
            q = None
        threading.Thread(target=self._fetch_books, args=(q,), daemon=True).start()

    def _fetch_books(self, query=None):
        try:
            page = self.page_var.get()
            if query:
                data = dl.search_books(self.session, query, page)
            else:
                data = dl.list_books(self.session, page, 30)
            books = data.get("data", [])
            pagi  = data.get("pagination", {}) or {}
            self.books = books
            total = pagi.get("total", len(books))
            lp    = pagi.get("last_page", 1)
            self.after(0, lambda: self._populate_tree(books, page, lp, total))
        except Exception as e:
            self.after(0, lambda: self._log(f"Lỗi tải danh sách: {e}", "ERROR"))
            self.after(0, lambda: self.status_bar.config(text="Lỗi"))

    def _populate_tree(self, books, page, last_page, total):
        for row in self.tree.get_children():
            self.tree.delete(row)
        for i, b in enumerate(books):
            tag = "odd" if i % 2 else "even"
            name = b.get("name", "")
            ch   = b.get("latest_index", b.get("chapter_count", 0))
            st   = b.get("status_name", "")
            self.tree.insert("", "end", iid=str(b["id"]),
                             values=(b["id"], name, ch, st), tags=(tag,))
        self.total_var.set(f"Trang {page}/{last_page}  ({total} truyện)")
        self._last_page = last_page
        self.status_bar.config(text=f"{len(books)} truyện")

    def _on_select(self, _=None):
        sel = self.tree.selection()
        if not sel: return
        book_id = int(sel[0])
        book = next((b for b in self.books if b["id"] == book_id), None)
        if book:
            self._show_book(book)

    def _show_book(self, book):
        self.sel_book = book
        name     = book.get("name", "")
        ch       = book.get("latest_index", book.get("chapter_count", 0))
        status   = book.get("status_name", "")
        rating   = book.get("review_score", 0)
        reviews  = book.get("review_count", 0)
        synopsis = book.get("synopsis", "") or ""
        if len(synopsis) > 280:
            synopsis = synopsis[:280] + "…"

        self.lbl_title.config(text=name)
        self.lbl_id.config(    text=f"ID: {book['id']}")
        self.lbl_ch.config(    text=f"Chương: {ch}")
        self.lbl_status.config(text=status)
        self.lbl_rating.config(text=f"★ {rating}/5  ({reviews})")
        self.lbl_synopsis.config(text=synopsis)
        self.to_var.set(str(ch))
        self._log(f"Đã chọn: {name}  [{ch} chương]", "ACCENT")

    def _prev_page(self):
        if self.page_var.get() > 1:
            self.page_var.set(self.page_var.get() - 1)
            self._search(reset_page=False)

    def _next_page(self):
        lp = getattr(self, "_last_page", 1)
        if self.page_var.get() < lp:
            self.page_var.set(self.page_var.get() + 1)
            self._search(reset_page=False)

    # ── Download ──────────────────────────────────────────────────────────
    def _start_download(self):
        if not _dl_ok:
            self._log("downloader.py not found!", "ERROR"); return
        if not self.sel_book:
            messagebox.showwarning("Chưa chọn truyện", "Hãy chọn một truyện từ danh sách.")
            return
        if self.dl_thread and self.dl_thread.is_alive():
            messagebox.showinfo("Đang tải", "Có tiến trình đang chạy, hãy dừng trước.")
            return

        try:
            start = int(self.from_var.get() or 1)
            end   = int(self.to_var.get()) if self.to_var.get().strip() else None
            delay = float(self.delay_var.get() or 0.5)
        except ValueError:
            messagebox.showerror("Lỗi", "Chương / Delay phải là số hợp lệ."); return

        out     = Path(self.out_var.get())
        app_key = self.key_var.get().strip() or None

        self.btn_dl.config(state="disabled")
        self.btn_stop.config(state="normal")
        self._stop_flag = False
        self.progress["value"] = 0
        self.prog_var.set("")

        self.dl_thread = threading.Thread(
            target=self._dl_worker,
            args=(self.sel_book, out, start, end, delay, app_key),
            daemon=True,
        )
        self.dl_thread.start()

    def _stop_download(self):
        self._stop_flag = True
        self._log("Đang dừng...", "WARN")

    def _dl_worker(self, book, output_dir, start_ch, end_ch, delay, app_key):
        """Run download in background thread with GUI progress callbacks."""
        book_id   = book["id"]
        book_name = book["name"]
        self._log(f"Bắt đầu tải: {book_name}", "ACCENT")

        try:
            output_dir.mkdir(parents=True, exist_ok=True)
            book_dir       = output_dir / dl.safe_name(book_name)
            book_dir.mkdir(parents=True, exist_ok=True)
            progress_file  = book_dir / ".progress.json"

            # Load progress
            downloaded_ids = set()
            if progress_file.exists():
                try:
                    data = json.loads(progress_file.read_text("utf-8"))
                    downloaded_ids = set(data.get("done", []))
                    self._log(f"Resume: {len(downloaded_ids)} chương đã có", "INFO")
                except Exception:
                    pass

            # Chapter list
            self._log("Đang lấy danh sách chương...", "INFO")
            all_chapters = dl.get_all_chapters(self.session, book_id)
            total = len(all_chapters)
            self._log(f"Tổng {total} chương", "INFO")

            if end_ch is None:
                end_ch = total

            to_download = [
                c for c in all_chapters
                if start_ch <= c.get("index", 0) <= end_ch
                and c["id"] not in downloaded_ids
                and not c.get("is_locked")
            ]

            n = len(to_download)
            if n == 0:
                self._log("Không có chương mới cần tải.", "WARN")
                self.after(0, self._dl_done)
                return

            self._log(f"Sẽ tải {n} chương (từ {start_ch} → {end_ch})", "OK")
            n_ok = n_enc = n_fail = 0

            for i, ch in enumerate(to_download, 1):
                if getattr(self, "_stop_flag", False):
                    self._log("Đã dừng bởi người dùng.", "WARN")
                    break

                ch_name = ch.get("name", f"Chương {ch.get('index')}")
                pct     = int(i / n * 100)
                self.after(0, lambda p=pct, m=f"[{i}/{n}] {ch_name}":
                           (self.progress.config(value=p), self.prog_var.set(m)))

                ch_data = dl.get_chapter(self.session, ch["id"], delay)
                if not ch_data:
                    self._log(f"  FAIL: {ch_name}", "ERROR")
                    n_fail += 1
                    continue

                raw  = ch_data.get("content", "")
                text = dl.process_content(raw, app_key)

                ch_file = book_dir / f"{ch.get('index',i):06d}_{dl.safe_name(ch_name)}.txt"
                dl.write_chapter_file(ch_file, ch_data, text)
                downloaded_ids.add(ch["id"])

                progress_file.write_text(
                    json.dumps({"done": list(downloaded_ids)}, ensure_ascii=False),
                    encoding="utf-8",
                )

                if text:
                    n_ok  += 1
                    self._log(f"  ✔ {ch_name}", "OK")
                else:
                    n_enc += 1
                    self._log(f"  ⚠ {ch_name}  [mã hoá]", "WARN")

            # Merge
            dl.merge_to_single_file(book_dir, book_name)

            self._log("─" * 48, "DIM")
            self._log(f"XONG  ✔{n_ok}  ⚠{n_enc}(mã hoá)  ✖{n_fail}(lỗi)", "OK")
            self._log(f"Lưu tại: {book_dir}", "INFO")

        except Exception as e:
            self._log(f"Lỗi: {e}", "ERROR")

        finally:
            self.after(0, self._dl_done)

    def _dl_done(self):
        self.btn_dl.config(state="normal")
        self.btn_stop.config(state="disabled")
        self.progress["value"] = 100

    # ── Misc ──────────────────────────────────────────────────────────────
    def _browse_output(self):
        d = filedialog.askdirectory(title="Chọn thư mục lưu truyện")
        if d:
            self.out_var.set(d)

    def _open_folder(self):
        folder = Path(self.out_var.get())
        if self.sel_book:
            sub = folder / dl.safe_name(self.sel_book["name"])
            if sub.exists():
                folder = sub
        folder.mkdir(parents=True, exist_ok=True)
        os.startfile(str(folder))


# ── Entry ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = App()
    app.mainloop()
