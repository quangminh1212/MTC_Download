#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gui.py – MTC Novel Downloader GUI
Google Drive light style.
Two modes:
  • API  – download via android.lonoapp.net (may be encrypted)
  • ADB  – run MTC.apk on device/emulator, extract text via UIAutomator (always readable)
"""
import sys, io, os, json, threading, queue, time
from pathlib import Path

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

import tkinter as tk
from tkinter import ttk, filedialog, messagebox

# ── Palette ──────────────────────────────────────────────────────────────────
BG     = "#ffffff"
BG2    = "#f8f9fa"
BORDER = "#dadce0"
BLUE   = "#1a73e8"
BLUE2  = "#1557b0"
BHOV   = "#e8f0fe"
FG     = "#202124"
FG2    = "#5f6368"
FG3    = "#80868b"
GREEN  = "#137333"
YELLOW = "#f29900"
RED    = "#c5221f"
ORANGE = "#fa7b17"

F  = ("Segoe UI", 9)
FB = ("Segoe UI", 9,  "bold")
FH = ("Segoe UI", 11, "bold")
FM = ("Consolas", 8)

# ── Imports ───────────────────────────────────────────────────────────────────
try:
    import downloader as dl
    _dl = True
except ImportError:
    _dl = False

try:
    from auto import AdbController, download_via_adb, APK_PATH
    _au = True
except ImportError:
    _au = False


# ── Small helpers ─────────────────────────────────────────────────────────────
def _ef(parent, var, w=14, show=""):
    fr = tk.Frame(parent, bg=BG, highlightthickness=1,
                  highlightbackground=BORDER, highlightcolor=BLUE)
    e = tk.Entry(fr, textvariable=var, bg=BG, fg=FG,
                 font=F, bd=0, width=w, show=show, insertbackground=FG)
    e.pack(ipady=5, padx=6)
    e.bind("<FocusIn>",  lambda _: fr.config(highlightbackground=BLUE))
    e.bind("<FocusOut>", lambda _: fr.config(highlightbackground=BORDER))
    return fr

def _lbl(parent, text, color=FG2, font=F, **kw):
    kw.setdefault("bg", BG)
    return tk.Label(parent, text=text, fg=color, font=font, **kw)


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("MTC Novel Downloader")
        self.geometry("1160x740")
        self.minsize(960, 620)
        self.configure(bg=BG)

        # State
        self._session   = dl.make_session() if _dl else None
        self._token     = None
        self._app_key   = None
        self._books     = []
        self._sel       = None
        self._page      = 1
        self._lpage     = 1
        self._q         = queue.Queue()
        self._thread    = None
        self._stop      = False
        self._cur_tab   = "adb"

        # ADB
        self._adb_path  = AdbController.find_adb() if _au else None
        self._adb       = None
        self._adb_devs  = []

        # Tab underline widgets (prevent memory leak)
        self._tab_lines = {}

        self._style()
        self._ui()
        self._poll()
        self.after(400, self._do_list)

    # ── Style ─────────────────────────────────────────────────────────────────
    def _style(self):
        s = ttk.Style(self)
        s.theme_use("clam")
        s.configure(".", background=BG, foreground=FG, font=F, borderwidth=0)
        s.configure("TFrame",   background=BG)
        s.configure("S.TFrame", background=BG2)
        s.configure("TLabel",   background=BG, foreground=FG)
        s.configure("TButton",  background=BLUE, foreground="#fff",
                    font=FB, padding=(14,7), relief="flat")
        s.map("TButton",
              background=[("active",BLUE2),("pressed",BLUE2)],
              relief=[("pressed","flat")])
        s.configure("G.TButton", background=BG, foreground=BLUE,
                    font=FB, padding=(10,6), relief="flat")
        s.map("G.TButton",
              background=[("active",BHOV),("pressed",BHOV)],
              foreground=[("active",BLUE2)])
        s.configure("O.TButton", background=ORANGE, foreground="#fff",
                    font=FB, padding=(14,7), relief="flat")
        s.map("O.TButton",
              background=[("active","#e8630a"),("pressed","#e8630a")],
              relief=[("pressed","flat")])
        s.configure("Sd.TButton", background=BG2, foreground=FG,
                    font=F, padding=(6,4), relief="flat")
        s.map("Sd.TButton", background=[("active",BORDER)])
        s.configure("TEntry", fieldbackground=BG, foreground=FG,
                    insertcolor=FG, borderwidth=1, relief="flat", padding=(6,5))
        s.configure("TScrollbar", background=BORDER, troughcolor=BG2,
                    borderwidth=0, arrowcolor=FG3, gripcount=0)
        s.map("TScrollbar", background=[("active",FG3)])
        s.configure("Horizontal.TProgressbar",
                    troughcolor=BORDER, background=BLUE,
                    borderwidth=0, thickness=4)
        s.configure("Treeview", background=BG, foreground=FG,
                    fieldbackground=BG, rowheight=30, borderwidth=0, font=F)
        s.configure("Treeview.Heading", background=BG2, foreground=FG2,
                    font=FB, borderwidth=0, relief="flat", padding=(6,6))
        s.map("Treeview",
              background=[("selected",BHOV)],
              foreground=[("selected",BLUE)])

    # ── UI ────────────────────────────────────────────────────────────────────
    def _ui(self):
        # Top bar
        tb = tk.Frame(self, bg=BG, height=52)
        tb.pack(fill="x")
        tb.pack_propagate(False)
        tk.Frame(tb, bg=BORDER, height=1).place(relx=0,rely=1,relwidth=1,anchor="sw")
        _lbl(tb, "MTC Novel Downloader", FG, ("Segoe UI",12,"bold")).pack(
              side="left", padx=20, pady=10)
        _lbl(tb, "android.lonoapp.net", FG2).pack(side="left", pady=10)
        self._mode_chip = tk.Label(tb, text="", bg=BLUE, fg="#fff", font=FB,
                                    padx=12, pady=3)
        self._mode_chip.pack(side="right", padx=20, pady=10)

        # Notebook (tabs)
        nb_frame = tk.Frame(self, bg=BORDER)
        nb_frame.pack(fill="x")
        self._tab_btns = {}
        for name, label in [("api","API Mode"), ("adb","ADB / Giả lập (APK thật)")]:
            btn = tk.Button(nb_frame, text=label, bg=BG2, fg=FG2,
                            font=FB, bd=0, padx=16, pady=8, cursor="hand2",
                            activebackground=BHOV, activeforeground=BLUE,
                            command=lambda n=name: self._switch_tab(n))
            btn.pack(side="left")
            self._tab_btns[name] = btn
        tk.Frame(nb_frame, bg=BORDER, height=2).pack(fill="x", side="bottom")

        # Main area
        main = tk.Frame(self, bg=BG)
        main.pack(fill="both", expand=True)

        # Left sidebar (book list) — shared across tabs
        left = tk.Frame(main, bg=BG2, width=430)
        left.pack(side="left", fill="y")
        left.pack_propagate(False)
        tk.Frame(main, bg=BORDER, width=1).pack(side="left", fill="y")

        # Right: API panel
        self._api_panel = tk.Frame(main, bg=BG)
        self._api_panel.place(relx=0, rely=0, relwidth=1, relheight=1)

        # Right: ADB panel
        self._adb_panel = tk.Frame(main, bg=BG)
        self._adb_panel.place(relx=0, rely=0, relwidth=1, relheight=1)
        self._adb_panel.lower()

        self._sidebar(left)
        self._api_tab(self._api_panel)
        self._adb_tab(self._adb_panel)
        self._switch_tab("adb")  # default = ADB mode

    def _switch_tab(self, name: str):
        panels = {"api": self._api_panel, "adb": self._adb_panel}
        labels = {"api": "API Mode", "adb": "APK / ADB Mode"}
        colors = {"api": BLUE, "adb": ORANGE}
        for n, btn in self._tab_btns.items():
            # Remove old underline if exists
            if n in self._tab_lines:
                self._tab_lines[n].destroy()
                del self._tab_lines[n]
            if n == name:
                btn.config(bg=BG, fg=colors[n], relief="flat")
                line = tk.Frame(btn, bg=colors[n], height=2)
                line.place(relx=0, rely=1, relwidth=1, anchor="sw")
                self._tab_lines[n] = line
            else:
                btn.config(bg=BG2, fg=FG2, relief="flat")
            panels[n].lower()
        panels[name].lift()
        self._mode_chip.config(text=labels[name], bg=colors[name])
        self._cur_tab = name

    # ── Sidebar (shared) ──────────────────────────────────────────────────────
    def _sidebar(self, p):
        sr = tk.Frame(p, bg=BG2)
        sr.pack(fill="x", padx=12, pady=(12,6))
        sb = tk.Frame(sr, bg=BG, highlightthickness=1,
                      highlightbackground=BORDER, highlightcolor=BLUE)
        sb.pack(side="left", fill="x", expand=True)
        _lbl(sb, "🔍", FG2).pack(side="left", padx=(6,0))
        self._sq = tk.StringVar()
        se = tk.Entry(sb, textvariable=self._sq, bg=BG, fg=FG,
                      font=F, bd=0, insertbackground=FG)
        se.pack(side="left", fill="x", expand=True, ipady=6, padx=4)
        se.bind("<Return>", lambda _: self._search())
        se.bind("<FocusIn>",  lambda _: sb.config(highlightbackground=BLUE))
        se.bind("<FocusOut>", lambda _: sb.config(highlightbackground=BORDER))
        ttk.Button(sr, text="Tìm", command=self._search, width=5).pack(
                   side="left", padx=(6,0))

        hr = tk.Frame(p, bg=BG2)
        hr.pack(fill="x", padx=12, pady=(2,0))
        _lbl(hr,"TRUYỆN",FG3,("Segoe UI",8,"bold"),bg=BG2).pack(side="left")
        self._stl = _lbl(hr,"",FG3,("Segoe UI",8),bg=BG2)
        self._stl.pack(side="right")

        tf = tk.Frame(p, bg=BG2)
        tf.pack(fill="both", expand=True)
        cols = ("id","name","ch")
        self._tree = ttk.Treeview(tf, columns=cols,
                                   show="headings", selectmode="browse")
        self._tree.heading("id",  text="ID",    anchor="center")
        self._tree.heading("name",text="Tên truyện")
        self._tree.heading("ch",  text="Ch.",   anchor="center")
        self._tree.column("id",  width=62, anchor="center", stretch=False)
        self._tree.column("name",width=295,anchor="w")
        self._tree.column("ch",  width=46, anchor="center", stretch=False)
        self._tree.tag_configure("o", background=BG2)
        self._tree.tag_configure("e", background=BG)
        vsb = ttk.Scrollbar(tf, orient="vertical", command=self._tree.yview)
        self._tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        self._tree.pack(side="left", fill="both", expand=True)
        self._tree.bind("<<TreeviewSelect>>", self._on_sel)

        pg = tk.Frame(p, bg=BG2)
        pg.pack(fill="x", padx=12, pady=8)
        ttk.Button(pg,text="‹",style="Sd.TButton",width=3,
                   command=self._prev).pack(side="left")
        self._pglbl = _lbl(pg,"—",FG2,bg=BG2)
        self._pglbl.pack(side="left", padx=8)
        ttk.Button(pg,text="›",style="Sd.TButton",width=3,
                   command=self._next).pack(side="left")

    # ── API tab ───────────────────────────────────────────────────────────────
    def _api_tab(self, p):
        # Login
        lf = tk.LabelFrame(p, text=" Tài khoản MTC ",
                           bg=BG, fg=FG2, font=("Segoe UI",8,"bold"),
                           bd=1, relief="groove")
        lf.pack(fill="x", padx=20, pady=(14,0))
        lr = tk.Frame(lf, bg=BG)
        lr.pack(fill="x", padx=10, pady=8)
        _lbl(lr,"Email:").pack(side="left")
        self._email = tk.StringVar(value="wuangming12@gmail.com")
        _ef(lr,self._email,22).pack(side="left",padx=(4,12))
        _lbl(lr,"Mật khẩu:").pack(side="left")
        self._pwd = tk.StringVar(value="0438765718")
        _ef(lr,self._pwd,16,show="•").pack(side="left",padx=(4,12))
        ttk.Button(lr,text="Đăng nhập",command=self._login).pack(side="left")
        self._auth_lbl = _lbl(lr,"")
        self._auth_lbl.pack(side="left", padx=10)

        # Book info
        tk.Frame(p, bg=BORDER, height=1).pack(fill="x", padx=20, pady=(10,0))
        inf = tk.Frame(p, bg=BG)
        inf.pack(fill="x", padx=20, pady=(10,0))
        self._tn  = _lbl(inf,"← Chọn truyện từ danh sách",FG2,FH,
                          wraplength=580,justify="left",anchor="w")
        self._tn.pack(fill="x")
        self._tm  = _lbl(inf,"",FG2,anchor="w")
        self._tm.pack(fill="x",pady=(3,0))
        self._tsy = _lbl(inf,"",FG2,wraplength=580,justify="left",anchor="nw")
        self._tsy.pack(fill="x",pady=(4,0))

        # Controls
        tk.Frame(p, bg=BORDER, height=1).pack(fill="x", padx=20, pady=(10,0))
        cf = tk.Frame(p, bg=BG)
        cf.pack(fill="x", padx=20, pady=(10,0))
        lc = dict(bg=BG,fg=FG2,font=F)
        tk.Label(cf,text="Từ chương:",**lc).grid(row=0,column=0,sticky="w",pady=4)
        self._fr=tk.StringVar(value="1")
        _ef(cf,self._fr,6).grid(row=0,column=1,sticky="w",padx=(4,16),pady=4)
        tk.Label(cf,text="Đến chương:",**lc).grid(row=0,column=2,sticky="w",pady=4)
        self._to=tk.StringVar()
        _ef(cf,self._to,6).grid(row=0,column=3,sticky="w",padx=(4,0),pady=4)
        tk.Label(cf,text="Lưu vào:",**lc).grid(row=1,column=0,sticky="w",pady=4)
        of=tk.Frame(cf,bg=BG)
        of.grid(row=1,column=1,columnspan=3,sticky="ew",pady=4)
        self._out=tk.StringVar(value=str(Path.cwd()/"downloads"))
        _ef(of,self._out,30).pack(side="left")
        ttk.Button(of,text="...",style="G.TButton",width=3,
                   command=self._browse).pack(side="left",padx=(6,0))
        tk.Label(cf,text="Delay (s):",**lc).grid(row=2,column=0,sticky="w",pady=4)
        self._delay=tk.StringVar(value="0.5")
        _ef(cf,self._delay,6).grid(row=2,column=1,sticky="w",padx=(4,0),pady=4)
        cf.columnconfigure(3,weight=1)

        self._bar_api, self._barlbl_api = self._prog_row(p)
        self._btn_api, self._stop_api   = self._btn_row(p, self._start_api, self._stop_dl)
        self._mklog(p, "api")

    # ── ADB tab ───────────────────────────────────────────────────────────────
    def _adb_tab(self, p):
        # Device section
        df = tk.LabelFrame(p, text=" ADB Device / Android Emulator ",
                           bg=BG, fg=FG2, font=("Segoe UI",8,"bold"),
                           bd=1, relief="groove")
        df.pack(fill="x", padx=20, pady=(14,0))

        dr = tk.Frame(df, bg=BG)
        dr.pack(fill="x", padx=10, pady=(8,4))
        _lbl(dr,"ADB:").pack(side="left")
        self._adb_path_var = tk.StringVar(value=self._adb_path or "(chưa tìm thấy)")
        _ef(dr,self._adb_path_var,28).pack(side="left",padx=(4,8))
        ttk.Button(dr,text="Tìm ADB",style="Sd.TButton",
                   command=self._find_all_adb).pack(side="left",padx=(0,4))
        ttk.Button(dr,text="Quét thiết bị",
                   command=self._scan_devices).pack(side="left")
        self._adb_status = _lbl(dr,"")
        self._adb_status.pack(side="left",padx=10)

        dr2 = tk.Frame(df, bg=BG)
        dr2.pack(fill="x", padx=10, pady=(0,4))
        _lbl(dr2,"Thiết bị:").pack(side="left")
        self._dev_var = tk.StringVar()
        self._dev_cb  = ttk.Combobox(dr2, textvariable=self._dev_var,
                                      state="readonly", width=30, font=F)
        self._dev_cb.pack(side="left",padx=(4,8))
        self._dev_cb.bind("<<ComboboxSelected>>", self._on_device_select)
        ttk.Button(dr2,text="Cài APK",
                   command=self._install_apk).pack(side="left")
        self._apk_status = _lbl(dr2,"")
        self._apk_status.pack(side="left",padx=8)

        # Emulator connect row
        dr3 = tk.Frame(df, bg=BG)
        dr3.pack(fill="x", padx=10, pady=(0,8))
        _lbl(dr3,"Kết nối giả lập:").pack(side="left")
        self._emu_host = tk.StringVar(value="127.0.0.1:5555")
        _ef(dr3,self._emu_host,16).pack(side="left",padx=(4,8))
        ttk.Button(dr3,text="Connect",style="Sd.TButton",
                   command=self._connect_emulator).pack(side="left")
        self._emu_status = _lbl(dr3, "")
        self._emu_status.pack(side="left",padx=8)

        # ADB controls
        tk.Frame(p, bg=BORDER, height=1).pack(fill="x", padx=20, pady=(8,0))

        # Book info from list
        self._adb_book_lbl = _lbl(p, "← Chọn truyện từ sidebar",
                                   FG2, FH, wraplength=600,
                                   justify="left", anchor="w")
        self._adb_book_lbl.pack(fill="x", padx=20, pady=(8,0))

        cf = tk.Frame(p, bg=BG)
        cf.pack(fill="x", padx=20, pady=(8,0))
        lc = dict(bg=BG,fg=FG2,font=F)
        tk.Label(cf,text="Từ chương:",**lc).grid(row=0,column=0,sticky="w",pady=4)
        self._adb_fr=tk.StringVar(value="1")
        _ef(cf,self._adb_fr,6).grid(row=0,column=1,sticky="w",padx=(4,16),pady=4)
        tk.Label(cf,text="Đến chương:",**lc).grid(row=0,column=2,sticky="w",pady=4)
        self._adb_to=tk.StringVar()
        _ef(cf,self._adb_to,6).grid(row=0,column=3,sticky="w",padx=(4,0),pady=4)
        tk.Label(cf,text="Lưu vào:",**lc).grid(row=1,column=0,sticky="w",pady=4)
        of2=tk.Frame(cf,bg=BG)
        of2.grid(row=1,column=1,columnspan=3,sticky="ew",pady=4)
        self._adb_out=tk.StringVar(value=str(Path.cwd()/"downloads"))
        _ef(of2,self._adb_out,30).pack(side="left")
        ttk.Button(of2,text="...",style="G.TButton",width=3,
                   command=lambda: self._browse2(self._adb_out)).pack(side="left",padx=(6,0))
        cf.columnconfigure(3,weight=1)

        # Info box
        info_f = tk.Frame(p, bg="#fff8e1", highlightthickness=1,
                          highlightbackground="#fdd835")
        info_f.pack(fill="x", padx=20, pady=(8,0))
        tk.Label(info_f,
                 text="ℹ️  Chế độ ADB chạy app MTC thật trên điện thoại/giả lập.\n"
                      "Hỗ trợ: LDPlayer, BlueStacks, Nox, MEmu, Android Studio AVD.\n"
                      "Yêu cầu: Bật USB Debugging, kết nối ADB. App tự điều hướng, đọc text → lưu TXT.",
                 bg="#fff8e1", fg="#5d4037", font=("Segoe UI",8),
                 justify="left", anchor="w", wraplength=620).pack(padx=10,pady=8)

        self._bar_adb, self._barlbl_adb = self._prog_row(p)
        self._btn_adb, self._stop_adb   = self._btn_row(p, self._start_adb, self._stop_dl,
                                                          primary_style="O.TButton",
                                                          primary_text="▶  Bắt đầu tự động tải")
        self._mklog(p, "adb")

    # ── Shared widget factories ───────────────────────────────────────────────
    def _prog_row(self, parent):
        pf = tk.Frame(parent, bg=BG)
        pf.pack(fill="x", padx=20, pady=(8,2))
        bar = ttk.Progressbar(pf, mode="determinate",
                               style="Horizontal.TProgressbar")
        bar.pack(fill="x")
        lv = tk.StringVar()
        tk.Label(pf, textvariable=lv, bg=BG, fg=FG2, font=F).pack(
                 anchor="w", pady=(2,0))
        return bar, lv

    def _btn_row(self, parent, start_cmd, stop_cmd,
                 primary_style="TButton",
                 primary_text="Tải xuống"):
        bf = tk.Frame(parent, bg=BG)
        bf.pack(fill="x", padx=20, pady=(4,6))
        b1 = ttk.Button(bf, text=primary_text, style=primary_style,
                         command=start_cmd)
        b1.pack(side="left")
        b2 = ttk.Button(bf, text="Dừng", style="G.TButton",
                         command=stop_cmd, state="disabled")
        b2.pack(side="left", padx=(8,0))
        ttk.Button(bf, text="Mở thư mục", style="G.TButton",
                   command=self._open_folder).pack(side="right")
        return b1, b2

    def _mklog(self, parent, tag: str):
        tk.Frame(parent, bg=BORDER, height=1).pack(fill="x", padx=20)
        lh = tk.Frame(parent, bg=BG)
        lh.pack(fill="x", padx=20, pady=(6,3))
        _lbl(lh, "Nhật ký", FG2, FB).pack(side="left")
        ttk.Button(lh, text="Xoá", style="G.TButton",
                   command=self._clrlog).pack(side="right")
        lf = tk.Frame(parent, bg=BG)
        lf.pack(fill="both", expand=True, padx=20, pady=(0,12))
        txt = tk.Text(lf, bg=BG2, fg=FG2, font=FM, bd=0, wrap="word",
                       state="disabled", highlightthickness=1,
                       highlightbackground=BORDER, selectbackground=BHOV)
        vsb = ttk.Scrollbar(lf, orient="vertical", command=txt.yview)
        txt.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        txt.pack(side="left", fill="both", expand=True)
        txt.tag_configure("ok",  foreground=GREEN)
        txt.tag_configure("w",   foreground=YELLOW)
        txt.tag_configure("err", foreground=RED)
        txt.tag_configure("acc", foreground=BLUE)
        txt.tag_configure("dim", foreground=FG3)
        txt.tag_configure("ora", foreground=ORANGE)
        if tag == "adb":
            self._log_adb = txt
        else:
            self._log_api = txt

    # ── Log ───────────────────────────────────────────────────────────────────
    def _lg(self, msg, tag=""):
        self._q.put((msg, tag))

    def _poll(self):
        try:
            while True:
                msg, tag = self._q.get_nowait()
                # Write to the log widget of current tab
                w = self._log_adb if self._cur_tab == "adb" else self._log_api
                if w:
                    w.config(state="normal")
                    w.insert("end", f"{time.strftime('%H:%M:%S')}  ", "dim")
                    w.insert("end", msg+"\n", tag or None)
                    w.see("end")
                    w.config(state="disabled")
        except queue.Empty:
            pass
        self.after(80, self._poll)

    def _clrlog(self):
        for w in (getattr(self,"_log_api",None),
                  getattr(self,"_log_adb",None)):
            if w:
                w.config(state="normal")
                w.delete("1.0","end")
                w.config(state="disabled")

    # ── Book list ─────────────────────────────────────────────────────────────
    def _do_list(self):
        if not _dl: return
        self._stl.config(text="Đang tải...")
        threading.Thread(target=self._fetch, args=(None,), daemon=True).start()

    def _search(self):
        q = self._sq.get().strip() or None
        self._page = 1
        threading.Thread(target=self._fetch, args=(q,), daemon=True).start()

    def _fetch(self, q):
        try:
            if q:
                data = dl.search_books(self._session, q, self._page)
            else:
                data = dl.list_books(self._session, self._page, 30)
            books = data.get("data",[])
            pagi  = data.get("pagination",{}) or {}
            self._books  = books
            self._lpage  = pagi.get("last", 1)
            total = pagi.get("total",len(books))
            self.after(0, lambda: self._fill(books, total, self._lpage))
        except Exception as e:
            self.after(0, lambda: self._lg(f"Lỗi danh sách: {e}","err"))

    def _fill(self, books, total, lp):
        for r in self._tree.get_children():
            self._tree.delete(r)
        for i,b in enumerate(books):
            ch = b.get("latest_index",b.get("chapter_count",0))
            self._tree.insert("","end",iid=str(b["id"]),
                              values=(b["id"],b.get("name",""),ch),
                              tags=("o" if i%2 else "e",))
        self._pglbl.config(text=f"Trang {self._page}/{lp}")
        self._stl.config(text=f"{total} truyện")

    def _on_sel(self, _=None):
        sel = self._tree.selection()
        if not sel: return
        bid  = int(sel[0])
        book = next((b for b in self._books if b["id"]==bid), None)
        if not book: return
        self._sel = book
        n   = book.get("name","")
        ch  = book.get("latest_index",book.get("chapter_count",0))
        st  = book.get("status_name","")
        rt  = book.get("review_score",0)
        rv  = book.get("review_count",0)
        syn = (book.get("synopsis") or "")[:250]
        # Update API tab
        self._tn.config(text=n, fg=FG)
        self._tm.config(text=f"ID {book['id']}  ·  {ch} chương  ·  {st}  ·  ★{rt} ({rv})")
        self._tsy.config(text=syn)
        self._to.set(str(ch))
        # Update ADB tab
        self._adb_book_lbl.config(text=f"Truyện: {n}  [{ch} chương]", fg=FG)
        self._adb_to.set(str(ch))
        self._lg(f"Chọn: {n}", "acc")

    def _prev(self):
        if self._page > 1:
            self._page -= 1
            self._do_list()

    def _next(self):
        if self._page < self._lpage:
            self._page += 1
            self._do_list()

    # ── API Login ─────────────────────────────────────────────────────────────
    def _login(self):
        if not _dl: return
        em = self._email.get().strip()
        pw = self._pwd.get().strip()
        if not em or not pw:
            messagebox.showwarning("","Nhập email và mật khẩu"); return
        self._auth_lbl.config(text="Đang đăng nhập...", fg=YELLOW)
        def _w():
            auth = dl.login(em, pw)
            if not auth:
                self.after(0, lambda: self._auth_lbl.config(
                    text="✖ Thất bại", fg=RED))
                self._lg("Đăng nhập thất bại","err"); return
            self._token   = auth.get("token")
            self._app_key = auth.get("key")
            self._session = dl.make_session(self._token)
            self.after(0, lambda: self._auth_lbl.config(
                text=f"✔ {em.split('@')[0]}" +
                     ("  +KEY!" if self._app_key else ""), fg=GREEN))
            self._lg(f"Đăng nhập OK: {em}  key={'✔' if self._app_key else '✖'}","ok")
        threading.Thread(target=_w, daemon=True).start()

    # ── ADB device ────────────────────────────────────────────────────────────
    def _find_all_adb(self):
        """Show dialog listing all found ADB binaries."""
        if not _au:
            messagebox.showerror("","auto.py not found"); return
        found = AdbController.find_all_adb()
        if not found:
            messagebox.showinfo("ADB",
                "Không tìm thấy ADB.\n"
                "Hãy cài Android SDK platform-tools hoặc emulator "
                "(LDPlayer, BlueStacks, Nox, MEmu).")
            return
        # Show selection
        items = [f"{f['source']}: {f['path']}" for f in found]
        if len(items) == 1:
            self._adb_path_var.set(found[0]["path"])
            self._lg(f"ADB: {found[0]['source']} → {found[0]['path']}", "ok")
            return
        # Simple selection popup
        win = tk.Toplevel(self)
        win.title("Chọn ADB")
        win.geometry("500x200")
        win.configure(bg=BG)
        _lbl(win, "Tìm thấy nhiều ADB:", FG, FB).pack(padx=10,pady=(10,5))
        lb = tk.Listbox(win, font=F, bg=BG2, selectbackground=BHOV)
        for item in items:
            lb.insert("end", item)
        lb.pack(fill="both", expand=True, padx=10, pady=5)
        lb.select_set(0)
        def _pick():
            idx = lb.curselection()
            if idx:
                self._adb_path_var.set(found[idx[0]]["path"])
                self._lg(f"ADB: {found[idx[0]]['source']} → {found[idx[0]]['path']}", "ok")
            win.destroy()
        ttk.Button(win, text="Chọn", command=_pick).pack(pady=(0,10))

    def _scan_devices(self):
        adb_bin = self._adb_path_var.get().strip()
        if not adb_bin or adb_bin.startswith("("):
            messagebox.showwarning("","Vui lòng chọn đường dẫn ADB trước.\n"
                                   "Nhấn 'Tìm ADB' hoặc nhập đường dẫn thủ công.")
            return
        if not _au:
            messagebox.showerror("","Module auto.py không tải được"); return
        self._adb = AdbController(adb_bin)
        self._adb.start_server()
        devs = self._adb.devices()
        self._adb_devs = devs
        if devs:
            items = [f"{d['serial']} ({d['type']})" for d in devs]
            self._dev_cb["values"] = items
            self._dev_cb.set(items[0])
            self._adb.device = devs[0]["serial"]
            self._adb_status.config(
                text=f"✔ {len(devs)} thiết bị", fg=GREEN)
            self._lg(f"Tìm thấy {len(devs)} thiết bị: "
                     f"{[d['serial'] for d in devs]}", "ok")
            # Check if MTC installed
            pkg = self._adb.get_installed_package()
            if pkg:
                self._apk_status.config(text=f"✔ Đã cài: {pkg}", fg=GREEN)
            else:
                self._apk_status.config(text="Chưa cài APK", fg=YELLOW)
        else:
            self._adb_status.config(text="Không có thiết bị", fg=RED)
            self._lg("Không tìm thấy thiết bị.\n"
                     "  → Kiểm tra: Emulator đang chạy? USB Debugging bật?\n"
                     "  → Thử 'Connect' với cổng 127.0.0.1:5555 (hoặc 62001 cho Nox)", "err")

    def _on_device_select(self, _=None):
        """When a device is selected from the combo box."""
        idx = self._dev_cb.current()
        if idx >= 0 and idx < len(self._adb_devs):
            self._adb.device = self._adb_devs[idx]["serial"]
            self._lg(f"Đã chọn: {self._adb.device}", "acc")
            # Re-check APK status
            pkg = self._adb.get_installed_package()
            if pkg:
                self._apk_status.config(text=f"✔ Đã cài: {pkg}", fg=GREEN)
            else:
                self._apk_status.config(text="Chưa cài APK", fg=YELLOW)

    def _connect_emulator(self):
        """Connect to emulator via ADB TCP."""
        host = self._emu_host.get().strip()
        if not host:
            messagebox.showwarning("","Nhập địa chỉ (vd: 127.0.0.1:5555)"); return
        adb_bin = self._adb_path_var.get().strip()
        if not adb_bin or adb_bin.startswith("("):
            messagebox.showwarning("","Vui lòng chọn ADB trước"); return
        if not _au:
            return
        if not self._adb:
            self._adb = AdbController(adb_bin)
            self._adb.start_server()
        self._emu_status.config(text="Đang kết nối...", fg=YELLOW)
        def _w():
            ok = self._adb.connect(host)
            if ok:
                self.after(0, lambda: self._emu_status.config(
                    text=f"✔ Đã kết nối {host}", fg=GREEN))
                self._lg(f"Connected to {host}", "ok")
                # Auto-scan
                self.after(500, self._scan_devices)
            else:
                self.after(0, lambda: self._emu_status.config(
                    text=f"✖ Không kết nối được", fg=RED))
                self._lg(f"Failed to connect to {host}", "err")
        threading.Thread(target=_w, daemon=True).start()

    def _install_apk(self):
        if not self._adb:
            messagebox.showwarning("","Quét thiết bị trước"); return
        if not APK_PATH.exists():
            messagebox.showerror("","Không tìm thấy file MTC.apk\n"
                                 f"Kiểm tra: {APK_PATH}"); return
        self._apk_status.config(text="Đang cài...", fg=YELLOW)
        def _w():
            ok = self._adb.install_apk(APK_PATH, self._lg)
            self.after(0, lambda: self._apk_status.config(
                text="✔ Đã cài" if ok else "✖ Thất bại",
                fg=GREEN if ok else RED))
        threading.Thread(target=_w, daemon=True).start()

    # ── Download ──────────────────────────────────────────────────────────────
    def _busy(self):
        return bool(self._thread and self._thread.is_alive())

    def _start_api(self):
        if not self._sel:
            messagebox.showwarning("","Chọn truyện từ danh sách"); return
        if self._busy():
            messagebox.showinfo("","Đang tải..."); return
        try:
            start = int(self._fr.get() or 1)
            end   = int(self._to.get()) if self._to.get().strip() else None
            delay = float(self._delay.get() or 0.5)
        except ValueError:
            messagebox.showerror("","Số không hợp lệ"); return

        self._btn_api.config(state="disabled")
        self._stop_api.config(state="normal")
        self._stop = False
        self._bar_api["value"] = 0
        self._barlbl_api.set("")
        self._thread = threading.Thread(
            target=self._api_worker,
            args=(self._sel, Path(self._out.get()), start, end, delay,
                  self._app_key),
            daemon=True)
        self._thread.start()

    def _start_adb(self):
        if not self._sel:
            messagebox.showwarning("","Chọn truyện từ sidebar trước"); return
        if not self._adb or not self._adb.device:
            messagebox.showwarning("","Quét và chọn thiết bị ADB trước"); return
        if self._busy():
            messagebox.showinfo("","Đang chạy..."); return
        try:
            start = int(self._adb_fr.get() or 1)
            end   = int(self._adb_to.get()) if self._adb_to.get().strip() else None
        except ValueError:
            messagebox.showerror("","Số không hợp lệ"); return

        self._btn_adb.config(state="disabled")
        self._stop_adb.config(state="normal")
        self._stop = False
        self._bar_adb["value"] = 0
        self._barlbl_adb.set("")

        book_name = self._sel.get("name","")
        self._thread = threading.Thread(
            target=self._adb_worker,
            args=(book_name, Path(self._adb_out.get()), start, end),
            daemon=True)
        self._thread.start()

    def _stop_dl(self):
        self._stop = True
        self._lg("Đang dừng...","w")

    def _api_worker(self, book, out_dir, start, end, delay, app_key):
        name    = book["name"]
        book_id = book["id"]
        self._lg(f"Bắt đầu tải (API): «{name}»","acc")
        try:
            out_dir.mkdir(parents=True, exist_ok=True)
            bdir = out_dir / dl.safe_name(name)
            bdir.mkdir(parents=True, exist_ok=True)
            pf   = bdir / ".progress.json"
            done = set()
            if pf.exists():
                try: done = set(json.loads(pf.read_text("utf-8")).get("done",[]))
                except: pass

            chs = dl.get_all_chapters(self._session, book_id)
            self._lg(f"Tổng {len(chs)} chương")
            if end is None:
                end = chs[-1].get("index",len(chs)) if chs else 1
            to_dl = [c for c in chs
                     if start <= c.get("index",0) <= end
                     and c["id"] not in done
                     and not c.get("is_locked")]
            n  = len(to_dl)
            nok = nenc = nfail = 0
            for i, ch in enumerate(to_dl, 1):
                if self._stop: self._lg("Dừng","w"); break
                nm  = ch.get("name",f"Chương {ch.get('index',i)}")
                idx = ch.get("index",i)
                pct = int(i/n*100)
                self.after(0, lambda p=pct, m=f"[{i}/{n}]  {nm}":
                           (self._bar_api.config(value=p),
                            self._barlbl_api.set(m)))
                cd = dl.get_chapter(self._session, ch["id"], delay)
                if not cd: nfail+=1; self._lg(f"  ✖ {nm}","err"); continue
                text = dl.process_content(cd.get("content",""), app_key)
                cf   = bdir / f"{idx:06d}_{dl.safe_name(nm)}.txt"
                dl.write_chapter_file(cf, cd, text)
                done.add(ch["id"])
                pf.write_text(json.dumps({"done":list(done)},ensure_ascii=False),"utf-8")
                if text: nok+=1; self._lg(f"  ✔ {nm}","ok")
                else:    nenc+=1; self._lg(f"  ⚠ {nm} (mã hoá)","w")
            dl.merge_to_single_file(bdir, name)
            self._lg(f"Xong!  ✔{nok}  ⚠{nenc}  ✖{nfail}",
                     "ok" if nenc==0 else "w")
        except Exception as e:
            self._lg(f"Lỗi: {e}","err")
        finally:
            self.after(0, lambda: (
                self._btn_api.config(state="normal"),
                self._stop_api.config(state="disabled"),
                self._bar_api.config(value=100)))

    def _adb_worker(self, book_name, out_dir, start, end):
        self._lg(f"Bắt đầu ADB: «{book_name}»","ora")
        self._lg("  → App sẽ tự chạy trên thiết bị và đọc text màn hình")
        try:
            def _progress(done, total):
                if total > 0:
                    pct = int(done / total * 100)
                    self.after(0, lambda p=pct, m=f"[{done}/{total}]":
                               (self._bar_adb.config(value=p),
                                self._barlbl_adb.set(m)))

            result = download_via_adb(
                adb        = self._adb,
                book_name  = book_name,
                ch_start   = start,
                ch_end     = end,
                output_dir = out_dir,
                log        = lambda m: self._lg(m),
                stop_flag  = lambda: self._stop,
                progress_cb= _progress,
            )
            if result.get("success"):
                self._lg(f"Hoàn thành!  ✔{result['ok']}  ✖{result['fail']}", "ok")
                self._lg(f"Lưu tại: {result['output']}")
            else:
                self._lg(f"Thất bại: {result.get('reason','')}","err")
        except Exception as e:
            self._lg(f"Lỗi ADB: {e}","err")
        finally:
            self.after(0, lambda: (
                self._btn_adb.config(state="normal"),
                self._stop_adb.config(state="disabled"),
                self._bar_adb.config(value=100)))

    # ── Misc ──────────────────────────────────────────────────────────────────
    def _browse(self):
        d = filedialog.askdirectory()
        if d: self._out.set(d)

    def _browse2(self, var):
        d = filedialog.askdirectory()
        if d: var.set(d)

    def _open_folder(self):
        tab = self._cur_tab
        out = Path(self._adb_out.get() if tab=="adb" else self._out.get())
        if self._sel and _dl:
            sub = out / dl.safe_name(self._sel["name"])
            if sub.exists(): out = sub
        out.mkdir(parents=True, exist_ok=True)
        if sys.platform == "win32":
            os.startfile(str(out))
        else:
            import subprocess
            subprocess.run(["xdg-open", str(out)])


if __name__ == "__main__":
    App().mainloop()
