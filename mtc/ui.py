"""ui.py – MTC Novel Downloader GUI (BlueStacks mode)."""
import os, threading, queue, time, logging
from pathlib import Path

import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from .config import (
    BG, BG2, BORDER, BLUE, BLUE2, BHOV, FG, FG2, FG3,
    GREEN, YELLOW, RED, ORANGE,
    FONT, FONT_BOLD, FONT_HEAD, FONT_MONO,
    APK_PATH, log,
)
from . import api
from .adb import AdbController
from .pipeline import download_via_adb
from .utils import safe_name


# ── Helpers ───────────────────────────────────────────────────────────────────
def _ef(parent, var, w=14, show=""):
    fr = tk.Frame(parent, bg=BG, highlightthickness=1,
                  highlightbackground=BORDER, highlightcolor=BLUE)
    e = tk.Entry(fr, textvariable=var, bg=BG, fg=FG,
                 font=FONT, bd=0, width=w, show=show, insertbackground=FG)
    e.pack(ipady=5, padx=6)
    e.bind("<FocusIn>",  lambda _: fr.config(highlightbackground=BLUE))
    e.bind("<FocusOut>", lambda _: fr.config(highlightbackground=BORDER))
    return fr

def _lbl(parent, text, color=FG2, font=FONT, **kw):
    kw.setdefault("bg", BG)
    return tk.Label(parent, text=text, fg=color, font=font, **kw)


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("MTC Novel Downloader – BlueStacks")
        self.geometry("1100x700")
        self.minsize(900, 580)
        self.configure(bg=BG)

        # State
        self._session = api.make_session()
        self._books   = []
        self._sel     = None
        self._page    = 1
        self._lpage   = 1
        self._q       = queue.Queue()
        self._thread  = None
        self._stop    = False

        # ADB
        self._adb_path = AdbController.find_adb()
        self._adb      = None

        self._style()
        self._ui()
        self._poll()
        self.after(400, self._do_list)
        self.after(600, self._auto_connect)

    # ── Style ─────────────────────────────────────────────────────────────
    def _style(self):
        s = ttk.Style(self)
        s.theme_use("clam")
        s.configure(".", background=BG, foreground=FG, font=FONT, borderwidth=0)
        s.configure("TFrame",   background=BG)
        s.configure("TLabel",   background=BG, foreground=FG)
        s.configure("TButton",  background=ORANGE, foreground="#fff",
                    font=FONT_BOLD, padding=(14,7), relief="flat")
        s.map("TButton",
              background=[("active","#e8630a"),("pressed","#e8630a")],
              relief=[("pressed","flat")])
        s.configure("G.TButton", background=BG, foreground=BLUE,
                    font=FONT_BOLD, padding=(10,6), relief="flat")
        s.map("G.TButton",
              background=[("active",BHOV),("pressed",BHOV)],
              foreground=[("active",BLUE2)])
        s.configure("Sd.TButton", background=BG2, foreground=FG,
                    font=FONT, padding=(6,4), relief="flat")
        s.map("Sd.TButton", background=[("active",BORDER)])
        s.configure("TScrollbar", background=BORDER, troughcolor=BG2,
                    borderwidth=0, arrowcolor=FG3)
        s.map("TScrollbar", background=[("active",FG3)])
        s.configure("Horizontal.TProgressbar",
                    troughcolor=BORDER, background=ORANGE,
                    borderwidth=0, thickness=4)
        s.configure("Treeview", background=BG, foreground=FG,
                    fieldbackground=BG, rowheight=30, borderwidth=0, font=FONT)
        s.configure("Treeview.Heading", background=BG2, foreground=FG2,
                    font=FONT_BOLD, borderwidth=0, relief="flat", padding=(6,6))
        s.map("Treeview",
              background=[("selected",BHOV)],
              foreground=[("selected",BLUE)])

    # ── UI Layout ─────────────────────────────────────────────────────────
    def _ui(self):
        # Top bar
        tb = tk.Frame(self, bg=BG, height=52)
        tb.pack(fill="x"); tb.pack_propagate(False)
        tk.Frame(tb, bg=BORDER, height=1).place(relx=0,rely=1,relwidth=1,anchor="sw")
        _lbl(tb, "MTC Novel Downloader", FG, ("Segoe UI",12,"bold")).pack(
              side="left", padx=20, pady=10)
        self._status_chip = tk.Label(tb, text="⏳ Đang kết nối...", bg=YELLOW,
                                      fg="#fff", font=FONT_BOLD, padx=12, pady=3)
        self._status_chip.pack(side="right", padx=20, pady=10)

        main = tk.Frame(self, bg=BG)
        main.pack(fill="both", expand=True)
        left = tk.Frame(main, bg=BG2, width=400)
        left.pack(side="left", fill="y"); left.pack_propagate(False)
        tk.Frame(main, bg=BORDER, width=1).pack(side="left", fill="y")
        right = tk.Frame(main, bg=BG)
        right.pack(side="left", fill="both", expand=True)

        self._sidebar(left)
        self._main_panel(right)

    # ── Sidebar ───────────────────────────────────────────────────────────
    def _sidebar(self, p):
        sr = tk.Frame(p, bg=BG2)
        sr.pack(fill="x", padx=12, pady=(12,6))
        sb = tk.Frame(sr, bg=BG, highlightthickness=1,
                      highlightbackground=BORDER, highlightcolor=BLUE)
        sb.pack(side="left", fill="x", expand=True)
        _lbl(sb, "🔍", FG2).pack(side="left", padx=(6,0))
        self._sq = tk.StringVar()
        se = tk.Entry(sb, textvariable=self._sq, bg=BG, fg=FG,
                      font=FONT, bd=0, insertbackground=FG)
        se.pack(side="left", fill="x", expand=True, ipady=6, padx=4)
        se.bind("<Return>", lambda _: self._search())
        se.bind("<FocusIn>",  lambda _: sb.config(highlightbackground=BLUE))
        se.bind("<FocusOut>", lambda _: sb.config(highlightbackground=BORDER))
        ttk.Button(sr, text="Tìm", command=self._search, width=5,
                   style="Sd.TButton").pack(side="left", padx=(6,0))

        hr = tk.Frame(p, bg=BG2)
        hr.pack(fill="x", padx=12, pady=(2,0))
        _lbl(hr, "TRUYỆN", FG3, ("Segoe UI",8,"bold"), bg=BG2).pack(side="left")
        self._stl = _lbl(hr, "", FG3, ("Segoe UI",8), bg=BG2)
        self._stl.pack(side="right")

        tf = tk.Frame(p, bg=BG2)
        tf.pack(fill="both", expand=True)
        cols = ("id","name","ch")
        self._tree = ttk.Treeview(tf, columns=cols,
                                   show="headings", selectmode="browse")
        self._tree.heading("id",   text="ID",         anchor="center")
        self._tree.heading("name", text="Tên truyện")
        self._tree.heading("ch",   text="Ch.",        anchor="center")
        self._tree.column("id",   width=55,  anchor="center", stretch=False)
        self._tree.column("name", width=275, anchor="w")
        self._tree.column("ch",   width=46,  anchor="center", stretch=False)
        self._tree.tag_configure("o", background=BG2)
        self._tree.tag_configure("e", background=BG)
        vsb = ttk.Scrollbar(tf, orient="vertical", command=self._tree.yview)
        self._tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        self._tree.pack(side="left", fill="both", expand=True)
        self._tree.bind("<<TreeviewSelect>>", self._on_sel)

        pg = tk.Frame(p, bg=BG2)
        pg.pack(fill="x", padx=12, pady=8)
        ttk.Button(pg, text="‹", style="Sd.TButton", width=3,
                   command=self._prev).pack(side="left")
        self._pglbl = _lbl(pg, "—", FG2, bg=BG2)
        self._pglbl.pack(side="left", padx=8)
        ttk.Button(pg, text="›", style="Sd.TButton", width=3,
                   command=self._next).pack(side="left")

    # ── Main Panel ────────────────────────────────────────────────────────
    def _main_panel(self, p):
        # Connection
        df = tk.LabelFrame(p, text=" BlueStacks / ADB ", bg=BG, fg=FG2,
                           font=("Segoe UI",8,"bold"), bd=1, relief="groove")
        df.pack(fill="x", padx=20, pady=(14,0))

        dr = tk.Frame(df, bg=BG)
        dr.pack(fill="x", padx=10, pady=(8,4))
        _lbl(dr, "ADB:").pack(side="left")
        self._adb_path_var = tk.StringVar(
            value=self._adb_path or "(chưa tìm thấy – cài BlueStacks)")
        _ef(dr, self._adb_path_var, 30).pack(side="left", padx=(4,8))
        ttk.Button(dr, text="Quét thiết bị", style="Sd.TButton",
                   command=self._scan_devices).pack(side="left")
        self._conn_status = _lbl(dr, "")
        self._conn_status.pack(side="left", padx=10)

        dr2 = tk.Frame(df, bg=BG)
        dr2.pack(fill="x", padx=10, pady=(0,4))
        _lbl(dr2, "Thiết bị:").pack(side="left")
        self._dev_var = tk.StringVar()
        self._dev_cb = ttk.Combobox(dr2, textvariable=self._dev_var,
                                     state="readonly", width=28, font=FONT)
        self._dev_cb.pack(side="left", padx=(4,8))
        self._dev_cb.bind("<<ComboboxSelected>>", self._on_dev_select)
        ttk.Button(dr2, text="Cài APK", style="Sd.TButton",
                   command=self._install_apk).pack(side="left")
        self._apk_lbl = _lbl(dr2, "")
        self._apk_lbl.pack(side="left", padx=8)

        # Book info
        tk.Frame(p, bg=BORDER, height=1).pack(fill="x", padx=20, pady=(10,0))
        self._book_lbl = _lbl(p, "← Chọn truyện từ danh sách bên trái",
                               FG2, FONT_HEAD, wraplength=580, justify="left",
                               anchor="w")
        self._book_lbl.pack(fill="x", padx=20, pady=(10,0))

        # Controls
        cf = tk.Frame(p, bg=BG)
        cf.pack(fill="x", padx=20, pady=(8,0))
        lc = dict(bg=BG, fg=FG2, font=FONT)
        tk.Label(cf, text="Từ chương:", **lc).grid(row=0, column=0,
                                                    sticky="w", pady=4)
        self._ch_from = tk.StringVar(value="1")
        _ef(cf, self._ch_from, 6).grid(row=0, column=1,
                                        sticky="w", padx=(4,16), pady=4)
        tk.Label(cf, text="Đến chương:", **lc).grid(row=0, column=2,
                                                     sticky="w", pady=4)
        self._ch_to = tk.StringVar()
        _ef(cf, self._ch_to, 6).grid(row=0, column=3,
                                      sticky="w", padx=(4,0), pady=4)
        tk.Label(cf, text="Lưu vào:", **lc).grid(row=1, column=0,
                                                   sticky="w", pady=4)
        of = tk.Frame(cf, bg=BG)
        of.grid(row=1, column=1, columnspan=3, sticky="ew", pady=4)
        self._out_dir = tk.StringVar(value=str(Path.cwd() / "downloads"))
        _ef(of, self._out_dir, 30).pack(side="left")
        ttk.Button(of, text="...", style="G.TButton", width=3,
                   command=self._browse).pack(side="left", padx=(6,0))
        cf.columnconfigure(3, weight=1)

        # Info
        info_f = tk.Frame(p, bg="#fff8e1", highlightthickness=1,
                          highlightbackground="#fdd835")
        info_f.pack(fill="x", padx=20, pady=(8,0))
        tk.Label(info_f,
                 text="ℹ️  Chạy app MTC.apk trên BlueStacks → tự động đọc text "
                      "màn hình → lưu TXT.\nYêu cầu: BlueStacks đang chạy, ADB "
                      "bật (Settings → Advanced → ADB).",
                 bg="#fff8e1", fg="#5d4037", font=("Segoe UI",8),
                 justify="left", anchor="w", wraplength=580).pack(padx=10, pady=8)

        # Progress
        pf = tk.Frame(p, bg=BG)
        pf.pack(fill="x", padx=20, pady=(8,2))
        self._bar = ttk.Progressbar(pf, mode="determinate",
                                     style="Horizontal.TProgressbar")
        self._bar.pack(fill="x")
        self._bar_lbl = tk.StringVar()
        tk.Label(pf, textvariable=self._bar_lbl, bg=BG, fg=FG2,
                 font=FONT).pack(anchor="w", pady=(2,0))

        # Buttons
        bf = tk.Frame(p, bg=BG)
        bf.pack(fill="x", padx=20, pady=(4,6))
        self._btn_start = ttk.Button(bf, text="▶  Bắt đầu tải",
                                      command=self._start_download)
        self._btn_start.pack(side="left")
        self._btn_stop = ttk.Button(bf, text="Dừng", style="G.TButton",
                                     command=self._stop_download,
                                     state="disabled")
        self._btn_stop.pack(side="left", padx=(8,0))
        ttk.Button(bf, text="Mở thư mục", style="G.TButton",
                   command=self._open_folder).pack(side="right")

        # Log
        tk.Frame(p, bg=BORDER, height=1).pack(fill="x", padx=20)
        lh = tk.Frame(p, bg=BG)
        lh.pack(fill="x", padx=20, pady=(6,3))
        _lbl(lh, "Nhật ký", FG2, FONT_BOLD).pack(side="left")
        ttk.Button(lh, text="Xoá", style="G.TButton",
                   command=self._clear_log).pack(side="right")
        lf = tk.Frame(p, bg=BG)
        lf.pack(fill="both", expand=True, padx=20, pady=(0,12))
        self._log = tk.Text(lf, bg=BG2, fg=FG2, font=FONT_MONO, bd=0,
                             wrap="word", state="disabled", highlightthickness=1,
                             highlightbackground=BORDER, selectbackground=BHOV)
        vsb = ttk.Scrollbar(lf, orient="vertical", command=self._log.yview)
        self._log.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        self._log.pack(side="left", fill="both", expand=True)
        for tag, color in [("ok",GREEN),("w",YELLOW),("err",RED),
                           ("acc",BLUE),("dim",FG3),("ora",ORANGE)]:
            self._log.tag_configure(tag, foreground=color)

    # ── Log ───────────────────────────────────────────────────────────────
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

    # ── Auto-connect BlueStacks ───────────────────────────────────────────
    def _auto_connect(self):
        if not self._adb_path:
            self._status_chip.config(text="✖ ADB không tìm thấy", bg=RED)
            self._lg("ADB không tìm thấy. Cài BlueStacks hoặc Android SDK.","err")
            return
        self._lg(f"ADB: {self._adb_path}", "acc")
        threading.Thread(target=self._do_auto_connect, daemon=True).start()

    def _do_auto_connect(self):
        self._adb = AdbController(self._adb_path)
        self._adb.start_server()
        devs = self._adb.devices()
        if not devs:
            self._adb.connect("127.0.0.1:5555")
            time.sleep(1)
            devs = self._adb.devices()
        if devs:
            self._adb.device = devs[0]["serial"]
            items = [d["serial"] for d in devs]
            self.after(0, lambda: self._on_connected(devs, items))
        else:
            self.after(0, self._on_no_device)

    def _on_connected(self, devs, items):
        self._dev_cb["values"] = items
        self._dev_cb.set(items[0])
        self._status_chip.config(text=f"✔ {items[0]}", bg=GREEN)
        self._conn_status.config(text=f"✔ {len(devs)} thiết bị", fg=GREEN)
        self._lg(f"Kết nối OK: {items[0]}", "ok")
        pkg = self._adb.get_installed_package()
        self._apk_lbl.config(
            text=f"✔ {pkg}" if pkg else "Chưa cài APK",
            fg=GREEN if pkg else YELLOW)

    def _on_no_device(self):
        self._status_chip.config(text="✖ Không có thiết bị", bg=RED)
        self._conn_status.config(text="Không tìm thấy", fg=RED)
        self._lg("Không tìm thấy BlueStacks. Kiểm tra:", "err")
        self._lg("  1. BlueStacks đang chạy?", "err")
        self._lg("  2. Settings → Advanced → ADB = ON", "err")

    # ── Device ────────────────────────────────────────────────────────────
    def _scan_devices(self):
        adb_bin = self._adb_path_var.get().strip()
        if not adb_bin or adb_bin.startswith("("):
            messagebox.showwarning("", "Cài BlueStacks trước hoặc nhập ADB.")
            return
        self._adb = AdbController(adb_bin)
        self._adb.start_server()
        devs = self._adb.devices()
        if devs:
            self._on_connected(devs, [d["serial"] for d in devs])
        else:
            self._on_no_device()

    def _on_dev_select(self, _=None):
        idx = self._dev_cb.current()
        devs = self._adb.devices() if self._adb else []
        if 0 <= idx < len(devs):
            self._adb.device = devs[idx]["serial"]
            self._lg(f"Đã chọn: {self._adb.device}", "acc")

    def _install_apk(self):
        if not self._adb or not self._adb.device:
            messagebox.showwarning("", "Kết nối BlueStacks trước"); return
        if not APK_PATH.exists():
            messagebox.showerror("", f"Không tìm thấy MTC.apk\n{APK_PATH}")
            return
        self._apk_lbl.config(text="Đang cài...", fg=YELLOW)
        def _w():
            ok = self._adb.install_apk(APK_PATH, self._lg)
            self.after(0, lambda: self._apk_lbl.config(
                text="✔ Đã cài" if ok else "✖ Lỗi", fg=GREEN if ok else RED))
        threading.Thread(target=_w, daemon=True).start()

    # ── Book list ─────────────────────────────────────────────────────────
    def _do_list(self):
        self._stl.config(text="Đang tải...")
        threading.Thread(target=self._fetch, args=(None,), daemon=True).start()

    def _search(self):
        q = self._sq.get().strip() or None
        self._page = 1
        threading.Thread(target=self._fetch, args=(q,), daemon=True).start()

    def _fetch(self, q):
        try:
            data  = api.search_books(self._session, q, self._page) if q \
                    else api.list_books(self._session, self._page, 30)
            books = data.get("data", [])
            pagi  = data.get("pagination", {}) or {}
            self._books = books
            self._lpage = pagi.get("last", 1)
            total = pagi.get("total", len(books))
            self.after(0, lambda: self._fill(books, total))
        except Exception as e:
            self.after(0, lambda: self._lg(f"Lỗi danh sách: {e}", "err"))

    def _fill(self, books, total):
        for r in self._tree.get_children():
            self._tree.delete(r)
        for i, b in enumerate(books):
            ch = b.get("latest_index", b.get("chapter_count", 0))
            self._tree.insert("", "end", iid=str(b["id"]),
                              values=(b["id"], b.get("name",""), ch),
                              tags=("o" if i % 2 else "e",))
        self._pglbl.config(text=f"Trang {self._page}/{self._lpage}")
        self._stl.config(text=f"{total} truyện")

    def _on_sel(self, _=None):
        sel = self._tree.selection()
        if not sel:
            return
        bid  = int(sel[0])
        book = next((b for b in self._books if b["id"] == bid), None)
        if not book:
            return
        self._sel = book
        n  = book.get("name", "")
        ch = book.get("latest_index", book.get("chapter_count", 0))
        self._book_lbl.config(text=f"📖 {n}  [{ch} chương]", fg=FG)
        self._ch_to.set(str(ch))
        self._lg(f"Chọn: {n}", "acc")

    def _prev(self):
        if self._page > 1:
            self._page -= 1; self._do_list()

    def _next(self):
        if self._page < self._lpage:
            self._page += 1; self._do_list()

    # ── Download ──────────────────────────────────────────────────────────
    def _start_download(self):
        if not self._sel:
            messagebox.showwarning("", "Chọn truyện từ danh sách"); return
        if not self._adb or not self._adb.device:
            messagebox.showwarning("", "Kết nối BlueStacks trước"); return
        if self._thread and self._thread.is_alive():
            messagebox.showinfo("", "Đang chạy..."); return
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
            args=(self._sel["name"], Path(self._out_dir.get()), start, end),
            daemon=True,
        )
        self._thread.start()

    def _stop_download(self):
        self._stop = True
        self._lg("Đang dừng...", "w")

    def _worker(self, book_name, out_dir, start, end):
        self._lg(f"Bắt đầu: «{book_name}»", "ora")
        try:
            def _progress(done, total):
                if total > 0:
                    pct = min(int(done / total * 100), 100)
                    self.after(0, lambda p=pct, m=f"[{done}/{total}]":
                               (self._bar.config(value=p),
                                self._bar_lbl.set(m)))
            result = download_via_adb(
                adb=self._adb, book_name=book_name,
                ch_start=start, ch_end=end, output_dir=out_dir,
                log_fn=self._lg, stop_flag=lambda: self._stop,
                progress_cb=_progress,
            )
            if result.get("success"):
                self._lg(f"Hoàn thành! ✔{result['ok']}  ✖{result['fail']}","ok")
                self._lg(f"Lưu tại: {result['output']}")
            else:
                self._lg(f"Lỗi: {result.get('reason','')}", "err")
        except Exception as e:
            self._lg(f"Lỗi: {e}", "err")
        finally:
            self.after(0, lambda: (
                self._btn_start.config(state="normal"),
                self._btn_stop.config(state="disabled"),
                self._bar.config(value=100)))

    # ── Misc ──────────────────────────────────────────────────────────────
    def _browse(self):
        d = filedialog.askdirectory()
        if d:
            self._out_dir.set(d)

    def _open_folder(self):
        out = Path(self._out_dir.get())
        if self._sel:
            sub = out / safe_name(self._sel["name"])
            if sub.exists():
                out = sub
        out.mkdir(parents=True, exist_ok=True)
        os.startfile(str(out))
