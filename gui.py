#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gui.py – MTC Novel Downloader GUI
Google Drive–style clean light interface
"""
import sys, io, os, json, threading, queue, time
from pathlib import Path

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

import tkinter as tk
from tkinter import ttk, filedialog, messagebox

# ── Palette (Google Drive light) ─────────────────────────────────────────
BG        = "#ffffff"
BG_SIDE   = "#f8f9fa"
BG_HOVER  = "#e8f0fe"
BORDER    = "#dadce0"
ACCENT    = "#1a73e8"   # Google blue
ACCENT_H  = "#1557b0"
FG        = "#202124"
FG2       = "#5f6368"
FG3       = "#80868b"
GREEN     = "#137333"
YELLOW    = "#f29900"
RED       = "#c5221f"
ROW_ODD   = "#f8f9fa"
ROW_EVEN  = "#ffffff"
SEL       = "#e8f0fe"

FONT   = ("Segoe UI", 9)
FONT_B = ("Segoe UI", 9, "bold")
FONT_H = ("Segoe UI", 11, "bold")
FONT_M = ("Consolas", 8)

# ── Imports ──────────────────────────────────────────────────────────────
try:
    import downloader as dl
    _dl_ok = True
except ImportError:
    _dl_ok = False

try:
    from scraper import Scraper, SOURCE_BASE
    _sc_ok = True
except ImportError:
    _sc_ok = False


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("MTC Novel Downloader")
        self.geometry("1120x700")
        self.minsize(900, 580)
        self.configure(bg=BG)

        # State
        self._api_session = dl.make_session() if _dl_ok else None
        self._scraper     = Scraper() if _sc_ok else None
        self._books       = []
        self._sel_book    = None
        self._last_page   = 1
        self._log_q       = queue.Queue()
        self._dl_thread   = None
        self._stop_flag   = False
        self._use_web     = tk.BooleanVar(value=True)  # use web scraper

        self._style()
        self._build()
        self._poll_log()
        self.after(300, self._search)

    # ── ttk Style ─────────────────────────────────────────────────────────
    def _style(self):
        s = ttk.Style(self)
        s.theme_use("clam")
        # Base
        s.configure(".",
                    background=BG, foreground=FG,
                    font=FONT, borderwidth=0,
                    focuscolor=ACCENT, highlightthickness=0)
        # Frames
        s.configure("TFrame",    background=BG)
        s.configure("Side.TFrame", background=BG_SIDE)
        # Labels
        s.configure("TLabel",     background=BG, foreground=FG)
        s.configure("Dim.TLabel", background=BG, foreground=FG2)
        s.configure("Side.TLabel",background=BG_SIDE, foreground=FG)
        s.configure("SideDim.TLabel", background=BG_SIDE, foreground=FG2)
        # Primary button (Google blue)
        s.configure("TButton",
                    background=ACCENT, foreground="#ffffff",
                    font=FONT_B, padding=(14, 7),
                    borderwidth=0, relief="flat")
        s.map("TButton",
              background=[("active", ACCENT_H), ("pressed", ACCENT_H)],
              relief=[("pressed", "flat")])
        # Ghost button
        s.configure("Ghost.TButton",
                    background=BG, foreground=ACCENT,
                    font=FONT_B, padding=(10, 6),
                    borderwidth=1, relief="flat")
        s.map("Ghost.TButton",
              background=[("active", BG_HOVER), ("pressed", BG_HOVER)],
              foreground=[("active", ACCENT_H)])
        # Side button
        s.configure("Side.TButton",
                    background=BG_SIDE, foreground=FG,
                    font=FONT, padding=(8, 5),
                    borderwidth=0, relief="flat")
        s.map("Side.TButton",
              background=[("active", BORDER)])
        # Entry
        s.configure("TEntry",
                    fieldbackground=BG, foreground=FG,
                    insertcolor=FG, borderwidth=1,
                    relief="flat", padding=(8, 5))
        # Scrollbar
        s.configure("TScrollbar",
                    background=BORDER, troughcolor=BG_SIDE,
                    borderwidth=0, arrowcolor=FG3, gripcount=0)
        s.map("TScrollbar", background=[("active", FG3)])
        # Progress
        s.configure("Horizontal.TProgressbar",
                    troughcolor=BORDER, background=ACCENT,
                    borderwidth=0, thickness=4)
        # Treeview
        s.configure("Treeview",
                    background=BG, foreground=FG,
                    fieldbackground=BG, rowheight=30,
                    borderwidth=0, font=FONT)
        s.configure("Treeview.Heading",
                    background=BG_SIDE, foreground=FG2,
                    font=FONT_B, borderwidth=0, relief="flat",
                    padding=(6, 6))
        s.map("Treeview",
              background=[("selected", SEL)],
              foreground=[("selected", ACCENT)])
        # Separator
        s.configure("TSeparator", background=BORDER)

    # ── Layout ────────────────────────────────────────────────────────────
    def _build(self):
        # ─ Top bar ─
        topbar = tk.Frame(self, bg=BG, height=56)
        topbar.pack(fill="x", side="top")
        topbar.pack_propagate(False)
        # Bottom border
        tk.Frame(topbar, bg=BORDER, height=1).place(relx=0, rely=1.0,
                                                     relwidth=1, anchor="sw")
        tk.Label(topbar, text="MTC Novel Downloader",
                 bg=BG, fg=FG, font=("Segoe UI", 12, "bold")).pack(
                 side="left", padx=20, pady=12)
        tk.Label(topbar, text="v2.0", bg=BG, fg=FG2, font=FONT).pack(
                 side="left", pady=12)

        # ─ Main area (sidebar + content) ─
        main = tk.Frame(self, bg=BG)
        main.pack(fill="both", expand=True)

        # Left sidebar
        side = tk.Frame(main, bg=BG_SIDE, width=460)
        side.pack(side="left", fill="y")
        side.pack_propagate(False)
        tk.Frame(main, bg=BORDER, width=1).pack(side="left", fill="y")

        # Right content
        right = tk.Frame(main, bg=BG)
        right.pack(side="left", fill="both", expand=True)

        self._build_sidebar(side)
        self._build_right(right)

    # ── Sidebar ───────────────────────────────────────────────────────────
    def _build_sidebar(self, parent):
        # Search row
        search_row = tk.Frame(parent, bg=BG_SIDE)
        search_row.pack(fill="x", padx=12, pady=(14, 8))

        # Search box with border
        search_box = tk.Frame(search_row, bg=BG, highlightthickness=1,
                              highlightbackground=BORDER,
                              highlightcolor=ACCENT)
        search_box.pack(fill="x", side="left", expand=True)
        tk.Label(search_box, text="🔍", bg=BG, fg=FG2,
                 font=("Segoe UI", 9)).pack(side="left", padx=(8, 0))
        self._search_var = tk.StringVar()
        e = tk.Entry(search_box, textvariable=self._search_var,
                     bg=BG, fg=FG, font=FONT, bd=0,
                     insertbackground=FG, relief="flat")
        e.pack(side="left", fill="x", expand=True, ipady=6, padx=4)
        e.bind("<Return>", lambda _: self._search())
        search_box.bind("<FocusIn>",
                        lambda _: search_box.config(highlightbackground=ACCENT))
        e.bind("<FocusIn>",
               lambda _: search_box.config(highlightbackground=ACCENT))
        e.bind("<FocusOut>",
               lambda _: search_box.config(highlightbackground=BORDER))

        ttk.Button(search_row, text="Tìm", command=self._search,
                   width=5).pack(side="left", padx=(6, 0))

        # Section label
        hdr = tk.Frame(parent, bg=BG_SIDE)
        hdr.pack(fill="x", padx=12, pady=(4, 0))
        tk.Label(hdr, text="DANH SÁCH TRUYỆN", bg=BG_SIDE,
                 fg=FG3, font=("Segoe UI", 8, "bold")).pack(side="left")
        self._status_lbl = tk.Label(hdr, text="...", bg=BG_SIDE,
                                    fg=FG3, font=("Segoe UI", 8))
        self._status_lbl.pack(side="right")

        # Treeview
        tree_f = tk.Frame(parent, bg=BG_SIDE)
        tree_f.pack(fill="both", expand=True, padx=0, pady=(6, 0))

        cols = ("id", "name", "ch")
        self._tree = ttk.Treeview(tree_f, columns=cols,
                                   show="headings", selectmode="browse")
        self._tree.heading("id",   text="ID",    anchor="center")
        self._tree.heading("name", text="Tên truyện")
        self._tree.heading("ch",   text="Ch.",    anchor="center")
        self._tree.column("id",   width=65,  anchor="center", stretch=False)
        self._tree.column("name", width=310, anchor="w")
        self._tree.column("ch",   width=48,  anchor="center", stretch=False)
        self._tree.tag_configure("odd",  background=ROW_ODD)
        self._tree.tag_configure("even", background=ROW_EVEN)

        vsb = ttk.Scrollbar(tree_f, orient="vertical", command=self._tree.yview)
        self._tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        self._tree.pack(side="left", fill="both", expand=True)
        self._tree.bind("<<TreeviewSelect>>", self._on_select)

        # Pagination
        pg = tk.Frame(parent, bg=BG_SIDE)
        pg.pack(fill="x", padx=12, pady=8)
        ttk.Button(pg, text="‹", style="Side.TButton", width=3,
                   command=self._prev_page).pack(side="left")
        self._page_lbl = tk.Label(pg, text="—", bg=BG_SIDE,
                                   fg=FG2, font=FONT)
        self._page_lbl.pack(side="left", padx=8)
        ttk.Button(pg, text="›", style="Side.TButton", width=3,
                   command=self._next_page).pack(side="left")

    # ── Right panel ───────────────────────────────────────────────────────
    def _build_right(self, parent):
        # Info card
        info = tk.Frame(parent, bg=BG)
        info.pack(fill="x", padx=24, pady=(20, 0))

        self._lbl_title = tk.Label(info, text="Chọn truyện từ danh sách →",
                                   bg=BG, fg=FG2, font=FONT_H,
                                   anchor="w", wraplength=560, justify="left")
        self._lbl_title.pack(fill="x")

        meta = tk.Frame(info, bg=BG)
        meta.pack(fill="x", pady=(4, 0))
        self._lbl_meta = tk.Label(meta, text="", bg=BG, fg=FG2, font=FONT,
                                   anchor="w")
        self._lbl_meta.pack(side="left")

        self._lbl_syn = tk.Label(info, text="", bg=BG, fg=FG2, font=FONT,
                                  anchor="nw", wraplength=560, justify="left")
        self._lbl_syn.pack(fill="x", pady=(6, 0))

        # Divider
        tk.Frame(parent, bg=BORDER, height=1).pack(fill="x", padx=24,
                                                    pady=(16, 0))

        # ── Download controls ──
        ctrl = tk.Frame(parent, bg=BG)
        ctrl.pack(fill="x", padx=24, pady=(14, 0))

        tk.Label(ctrl, text="Nguồn nội dung", bg=BG,
                 fg=FG2, font=("Segoe UI", 8, "bold")).grid(
                 row=0, column=0, columnspan=4, sticky="w", pady=(0, 6))

        # Web source toggle
        web_f = tk.Frame(ctrl, bg=BG)
        web_f.grid(row=1, column=0, columnspan=4, sticky="w", pady=(0, 10))
        tk.Checkbutton(web_f, text="Tải qua web (tiemtruyenchu.com) — đọc được luôn",
                       variable=self._use_web, bg=BG, fg=FG,
                       font=FONT, activebackground=BG,
                       selectcolor=BG, command=self._toggle_auth,
                       cursor="hand2").pack(side="left")

        # Auth row (shown when web mode on)
        self._auth_frame = tk.Frame(ctrl, bg=BG)
        self._auth_frame.grid(row=2, column=0, columnspan=4, sticky="ew",
                               pady=(0, 10))
        tk.Label(self._auth_frame, text="User:", bg=BG, fg=FG2,
                 font=FONT).pack(side="left")
        self._user_var = tk.StringVar()
        tk.Entry(self._auth_frame, textvariable=self._user_var,
                 bg=BG_SIDE, fg=FG, bd=0, font=FONT,
                 highlightthickness=1, highlightbackground=BORDER,
                 width=18).pack(side="left", padx=(4, 10), ipady=4)
        tk.Label(self._auth_frame, text="Pass:", bg=BG, fg=FG2,
                 font=FONT).pack(side="left")
        self._pass_var = tk.StringVar()
        tk.Entry(self._auth_frame, textvariable=self._pass_var,
                 show="•", bg=BG_SIDE, fg=FG, bd=0, font=FONT,
                 highlightthickness=1, highlightbackground=BORDER,
                 width=14).pack(side="left", padx=(4, 10), ipady=4)
        ttk.Button(self._auth_frame, text="Đăng nhập", style="Ghost.TButton",
                   command=self._do_login).pack(side="left")
        self._auth_status = tk.Label(self._auth_frame, text="Chưa đăng nhập",
                                      bg=BG, fg=FG3, font=FONT)
        self._auth_status.pack(side="left", padx=8)

        # Row: from/to/output
        lbl_cfg = {"bg": BG, "fg": FG2, "font": FONT}

        tk.Label(ctrl, text="Từ chương", **lbl_cfg).grid(
            row=3, column=0, sticky="w", pady=(0, 6))
        self._from_var = tk.StringVar(value="1")
        self._entry(ctrl, self._from_var, w=6).grid(
            row=3, column=1, sticky="w", padx=(6, 16), pady=(0, 6))

        tk.Label(ctrl, text="Đến chương", **lbl_cfg).grid(
            row=3, column=2, sticky="w", pady=(0, 6))
        self._to_var = tk.StringVar(value="")
        self._entry(ctrl, self._to_var, w=6).grid(
            row=3, column=3, sticky="w", padx=(6, 0), pady=(0, 6))

        tk.Label(ctrl, text="Lưu vào", **lbl_cfg).grid(
            row=4, column=0, sticky="w", pady=(0, 6))
        out_f = tk.Frame(ctrl, bg=BG)
        out_f.grid(row=4, column=1, columnspan=3, sticky="ew", pady=(0, 6))
        self._out_var = tk.StringVar(value=str(Path.cwd() / "downloads"))
        self._entry(out_f, self._out_var, w=32).pack(side="left")
        ttk.Button(out_f, text="Thay đổi", style="Ghost.TButton",
                   command=self._browse).pack(side="left", padx=(6, 0))

        tk.Label(ctrl, text="Delay (giây)", **lbl_cfg).grid(
            row=5, column=0, sticky="w", pady=(0, 10))
        self._delay_var = tk.StringVar(value="0.5")
        self._entry(ctrl, self._delay_var, w=6).grid(
            row=5, column=1, sticky="w", padx=(6, 0), pady=(0, 10))

        ctrl.columnconfigure(1, weight=0)
        ctrl.columnconfigure(3, weight=1)

        # Progress
        prog_f = tk.Frame(parent, bg=BG)
        prog_f.pack(fill="x", padx=24, pady=(0, 6))
        self._progress = ttk.Progressbar(prog_f, mode="determinate",
                                          style="Horizontal.TProgressbar")
        self._progress.pack(fill="x")
        self._prog_var = tk.StringVar(value="")
        tk.Label(prog_f, textvariable=self._prog_var,
                 bg=BG, fg=FG2, font=FONT).pack(anchor="w", pady=(2, 0))

        # Buttons
        btn_f = tk.Frame(parent, bg=BG)
        btn_f.pack(fill="x", padx=24, pady=(0, 12))
        self._btn_dl = ttk.Button(btn_f, text="Tải xuống",
                                   command=self._start_dl)
        self._btn_dl.pack(side="left")
        self._btn_stop = ttk.Button(btn_f, text="Dừng", style="Ghost.TButton",
                                     command=self._stop_dl, state="disabled")
        self._btn_stop.pack(side="left", padx=(8, 0))
        ttk.Button(btn_f, text="Mở thư mục", style="Ghost.TButton",
                   command=self._open_folder).pack(side="right")

        # Log
        tk.Frame(parent, bg=BORDER, height=1).pack(fill="x", padx=24)
        log_hdr = tk.Frame(parent, bg=BG)
        log_hdr.pack(fill="x", padx=24, pady=(8, 4))
        tk.Label(log_hdr, text="Nhật ký", bg=BG, fg=FG2,
                 font=FONT_B).pack(side="left")
        ttk.Button(log_hdr, text="Xoá", style="Ghost.TButton",
                   command=self._clear_log).pack(side="right")

        log_f = tk.Frame(parent, bg=BG)
        log_f.pack(fill="both", expand=True, padx=24, pady=(0, 16))
        self._log_txt = tk.Text(log_f, bg=BG_SIDE, fg=FG2,
                                 font=FONT_M, bd=0, wrap="word",
                                 state="disabled",
                                 highlightthickness=1,
                                 highlightbackground=BORDER,
                                 selectbackground=SEL)
        vsb = ttk.Scrollbar(log_f, orient="vertical",
                             command=self._log_txt.yview)
        self._log_txt.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        self._log_txt.pack(side="left", fill="both", expand=True)
        self._log_txt.tag_configure("ok",   foreground=GREEN)
        self._log_txt.tag_configure("warn", foreground=YELLOW)
        self._log_txt.tag_configure("err",  foreground=RED)
        self._log_txt.tag_configure("acc",  foreground=ACCENT)
        self._log_txt.tag_configure("dim",  foreground=FG3)

    # ── Helpers ────────────────────────────────────────────────────────────
    def _entry(self, parent, var, w=12):
        f = tk.Frame(parent, bg=BG, highlightthickness=1,
                     highlightbackground=BORDER, highlightcolor=ACCENT)
        e = tk.Entry(f, textvariable=var, bg=BG, fg=FG,
                     font=FONT, bd=0, width=w,
                     insertbackground=FG, relief="flat")
        e.pack(ipady=5, padx=6)
        e.bind("<FocusIn>",  lambda _: f.config(highlightbackground=ACCENT))
        e.bind("<FocusOut>", lambda _: f.config(highlightbackground=BORDER))
        return f

    def _toggle_auth(self):
        pass  # auth frame always visible

    # ── Log ───────────────────────────────────────────────────────────────
    def _log(self, msg: str, tag: str = ""):
        self._log_q.put((msg, tag))

    def _poll_log(self):
        try:
            while True:
                msg, tag = self._log_q.get_nowait()
                self._log_txt.config(state="normal")
                ts = time.strftime("%H:%M:%S")
                self._log_txt.insert("end", f"{ts}  ", "dim")
                self._log_txt.insert("end", msg + "\n", tag or None)
                self._log_txt.see("end")
                self._log_txt.config(state="disabled")
        except queue.Empty:
            pass
        self.after(80, self._poll_log)

    def _clear_log(self):
        self._log_txt.config(state="normal")
        self._log_txt.delete("1.0", "end")
        self._log_txt.config(state="disabled")

    # ── Auth ──────────────────────────────────────────────────────────────
    def _do_login(self):
        if not _sc_ok:
            self._log("scraper.py not found", "err"); return
        user = self._user_var.get().strip()
        pwd  = self._pass_var.get().strip()
        if not user or not pwd:
            messagebox.showwarning("Thiếu thông tin", "Nhập tài khoản và mật khẩu")
            return
        self._auth_status.config(text="Đang đăng nhập...", fg=YELLOW)
        self.update_idletasks()
        def _worker():
            ok = self._scraper.login(user, pwd)
            tag = "ok" if ok else "err"
            msg = f"Đăng nhập {'thành công' if ok else 'thất bại'} ({user})"
            self.after(0, lambda: self._auth_status.config(
                text="✔ Đã đăng nhập" if ok else "✖ Thất bại",
                fg=GREEN if ok else RED))
            self._log(msg, tag)
        threading.Thread(target=_worker, daemon=True).start()

    # ── Book list ─────────────────────────────────────────────────────────
    def _search(self, reset=True):
        if not _dl_ok: return
        if reset:
            self._page_var = getattr(self, "_page_var", tk.IntVar(value=1))
            self._page_var.set(1)
        self._status_lbl.config(text="Đang tải...")
        q = self._search_var.get().strip() or None
        threading.Thread(target=self._fetch_books, args=(q,), daemon=True).start()

    def _fetch_books(self, query=None):
        try:
            page = getattr(self, "_page_var", None)
            pg   = page.get() if page else 1
            if query:
                data = dl.search_books(self._api_session, query, pg)
            else:
                data = dl.list_books(self._api_session, pg, 30)
            books = data.get("data", [])
            pagi  = data.get("pagination", {}) or {}
            self._books = books
            total = pagi.get("total", len(books))
            lp    = pagi.get("last_page", 1)
            self.after(0, lambda: self._fill_tree(books, pg, lp, total))
        except Exception as e:
            self.after(0, lambda: (
                self._log(f"Lỗi tải danh sách: {e}", "err"),
                self._status_lbl.config(text="Lỗi"),
            ))

    def _fill_tree(self, books, page, lp, total):
        for row in self._tree.get_children():
            self._tree.delete(row)
        for i, b in enumerate(books):
            tag = "odd" if i % 2 else "even"
            ch  = b.get("latest_index", b.get("chapter_count", 0))
            self._tree.insert("", "end", iid=str(b["id"]),
                              values=(b["id"], b.get("name",""), ch),
                              tags=(tag,))
        self._last_page = lp
        self._page_lbl.config(text=f"Trang {page} / {lp}")
        self._status_lbl.config(text=f"{total} truyện")
        if not hasattr(self, "_page_var"):
            self._page_var = tk.IntVar(value=1)
        self._page_var.set(page)

    def _on_select(self, _=None):
        sel = self._tree.selection()
        if not sel: return
        bid  = int(sel[0])
        book = next((b for b in self._books if b["id"] == bid), None)
        if book:
            self._sel_book = book
            self._show_info(book)

    def _show_info(self, book):
        name    = book.get("name", "")
        ch      = book.get("latest_index", book.get("chapter_count", 0))
        status  = book.get("status_name", "")
        rating  = book.get("review_score", 0)
        reviews = book.get("review_count", 0)
        syn     = (book.get("synopsis") or "")[:300]
        self._lbl_title.config(text=name, fg=FG)
        self._lbl_meta.config(
            text=f"ID {book['id']}  ·  {ch} chương  ·  {status}  ·  ★ {rating}/5  ({reviews} đánh giá)")
        self._lbl_syn.config(text=syn)
        self._to_var.set(str(ch))
        self._log(f"Đã chọn: {name}", "acc")

    def _prev_page(self):
        if not hasattr(self, "_page_var"): return
        if self._page_var.get() > 1:
            self._page_var.set(self._page_var.get() - 1)
            self._search(reset=False)

    def _next_page(self):
        if not hasattr(self, "_page_var"): return
        if self._page_var.get() < self._last_page:
            self._page_var.set(self._page_var.get() + 1)
            self._search(reset=False)

    # ── Download ──────────────────────────────────────────────────────────
    def _start_dl(self):
        if not self._sel_book:
            messagebox.showwarning("Chưa chọn", "Hãy chọn truyện từ danh sách")
            return
        if self._dl_thread and self._dl_thread.is_alive():
            messagebox.showinfo("Đang chạy", "Có tiến trình đang tải, hãy dừng trước")
            return
        use_web = self._use_web.get()
        if use_web and not (_sc_ok and self._scraper and self._scraper.is_logged_in()):
            if messagebox.askyesno(
                "Chưa đăng nhập",
                "Chưa đăng nhập vào tiemtruyenchu.com.\n"
                "Chuyển sang tải qua API? (nội dung có thể bị mã hoá)"
            ):
                use_web = False
            else:
                return

        try:
            start = int(self._from_var.get() or 1)
            end   = int(self._to_var.get()) if self._to_var.get().strip() else None
            delay = float(self._delay_var.get() or 0.5)
        except ValueError:
            messagebox.showerror("Lỗi", "Chương / Delay phải là số hợp lệ"); return

        out = Path(self._out_var.get())
        self._btn_dl.config(state="disabled")
        self._btn_stop.config(state="normal")
        self._stop_flag = False
        self._progress["value"] = 0
        self._prog_var.set("")

        self._dl_thread = threading.Thread(
            target=self._dl_worker,
            args=(self._sel_book, out, start, end, delay, use_web),
            daemon=True,
        )
        self._dl_thread.start()

    def _stop_dl(self):
        self._stop_flag = True
        self._log("Đang dừng...", "warn")

    def _dl_worker(self, book, out_dir, start, end, delay, use_web):
        slug      = book.get("slug", "")
        book_id   = book["id"]
        book_name = book["name"]

        self._log(f"Bắt đầu tải: «{book_name}»", "acc")
        try:
            out_dir.mkdir(parents=True, exist_ok=True)
            book_dir = out_dir / dl.safe_name(book_name)
            book_dir.mkdir(parents=True, exist_ok=True)
            prog_f   = book_dir / ".progress.json"

            # Progress file
            done_ids = set()
            if prog_f.exists():
                try:
                    done_ids = set(
                        json.loads(prog_f.read_text("utf-8")).get("done", []))
                    self._log(f"Resume: {len(done_ids)} chương đã có")
                except Exception:
                    pass

            # Chapter list
            if use_web:
                # Get chapters from web source
                self._log("Lấy danh sách chương từ web...")
                chapters = self._scraper.get_chapter_urls(slug,
                            total_hint=book.get("latest_index", 100))
                self._log(f"Web: tìm thấy {len(chapters)} chương")
            else:
                # Get chapters from API
                self._log("Lấy danh sách chương từ API...")
                chapters = dl.get_all_chapters(self._api_session, book_id)
                self._log(f"API: {len(chapters)} chương")

            if end is None:
                end = chapters[-1].get("index", len(chapters)) if chapters else 1

            to_dl = [c for c in chapters
                     if start <= c.get("index", 0) <= end]

            if use_web:
                # Filter already done by URL key
                pass
            else:
                to_dl = [c for c in to_dl
                         if c["id"] not in done_ids and not c.get("is_locked")]

            n = len(to_dl)
            self._log(f"Sẽ tải {n} chương (ch.{start}–{end})")
            n_ok = n_enc = n_fail = 0

            for i, ch in enumerate(to_dl, 1):
                if self._stop_flag:
                    self._log("Dừng bởi người dùng", "warn"); break

                name = ch.get("name", f"Chương {ch.get('index', i)}")
                idx  = ch.get("index", i)
                pct  = int(i / n * 100)
                self.after(0, lambda p=pct, m=f"[{i}/{n}]  {name}":
                           (self._progress.config(value=p),
                            self._prog_var.set(m)))

                if use_web:
                    url  = ch.get("url", "")
                    text = self._scraper.get_chapter_text(url, delay)
                    ch_data = {"id": idx, "name": name,
                               "index": idx, "word_count": 0}
                else:
                    ch_data = dl.get_chapter(self._api_session, ch["id"], delay)
                    if not ch_data:
                        self._log(f"  ✖ {name}", "err")
                        n_fail += 1; continue
                    raw  = ch_data.get("content", "")
                    text = dl.process_content(raw)

                ch_file = book_dir / f"{idx:06d}_{dl.safe_name(name)}.txt"
                dl.write_chapter_file(ch_file, ch_data, text)

                if not use_web:
                    done_ids.add(ch["id"])
                    prog_f.write_text(
                        json.dumps({"done": list(done_ids)}, ensure_ascii=False),
                        encoding="utf-8")

                if text:
                    n_ok += 1
                    self._log(f"  ✔ {name}", "ok")
                else:
                    n_enc += 1
                    self._log(f"  ⚠ {name}  (mã hoá / chưa login)", "warn")

            # Merge
            dl.merge_to_single_file(book_dir, book_name)
            self._log("─" * 40, "dim")
            self._log(f"Xong!  ✔{n_ok}  ⚠{n_enc}  ✖{n_fail}", "ok")
            self._log(f"Thư mục: {book_dir}")
        except Exception as e:
            self._log(f"Lỗi: {e}", "err")
        finally:
            self.after(0, self._dl_done)

    def _dl_done(self):
        self._btn_dl.config(state="normal")
        self._btn_stop.config(state="disabled")
        self._progress["value"] = 100

    # ── Misc ──────────────────────────────────────────────────────────────
    def _browse(self):
        d = filedialog.askdirectory(title="Chọn thư mục lưu")
        if d: self._out_var.set(d)

    def _open_folder(self):
        folder = Path(self._out_var.get())
        if self._sel_book:
            sub = folder / dl.safe_name(self._sel_book["name"])
            if sub.exists():
                folder = sub
        folder.mkdir(parents=True, exist_ok=True)
        os.startfile(str(folder))


if __name__ == "__main__":
    App().mainloop()
