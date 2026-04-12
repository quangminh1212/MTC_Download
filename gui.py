#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gui.py â€“ MTC Novel Downloader GUI
Google Driveâ€“style light interface, uses android.lonoapp.net API (same as MTC.apk)
"""
import sys, io, os, json, threading, queue, time
from pathlib import Path

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

import tkinter as tk
from tkinter import ttk, filedialog, messagebox

# â”€â”€ Palette: Google Drive light â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
BG      = "#ffffff"
BG2     = "#f8f9fa"
BORDER  = "#dadce0"
ACCENT  = "#1a73e8"
ACCENT2 = "#1557b0"
BG_HOV  = "#e8f0fe"
FG      = "#202124"
FG2     = "#5f6368"
FG3     = "#80868b"
GREEN   = "#137333"
YELLOW  = "#f29900"
RED     = "#c5221f"

F       = ("Segoe UI", 9)
FB      = ("Segoe UI", 9,  "bold")
FH      = ("Segoe UI", 11, "bold")
FM      = ("Consolas", 8)

# â”€â”€ Import core â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
try:
    import downloader as dl
    _ok = True
except ImportError:
    _ok = False


# â”€â”€ Helpers â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
def _e(parent, var, w=14, show=""):
    """Styled borderless Entry inside a highlight frame."""
    fr = tk.Frame(parent, bg=BG, highlightthickness=1,
                  highlightbackground=BORDER, highlightcolor=ACCENT)
    ent = tk.Entry(fr, textvariable=var, bg=BG, fg=FG,
                   font=F, bd=0, width=w, show=show, insertbackground=FG)
    ent.pack(ipady=5, padx=6)
    ent.bind("<FocusIn>",  lambda _: fr.config(highlightbackground=ACCENT))
    ent.bind("<FocusOut>", lambda _: fr.config(highlightbackground=BORDER))
    return fr


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("MTC Novel Downloader")
        self.geometry("1140x720")
        self.minsize(920, 600)
        self.configure(bg=BG)

        # â”€â”€ State â”€â”€
        self._session   = dl.make_session() if _ok else None
        self._token     = None
        self._app_key   = None
        self._books     = []
        self._sel       = None
        self._page      = 1
        self._last_page = 1
        self._q         = queue.Queue()
        self._thread    = None
        self._stop      = False

        self._style()
        self._ui()
        self._poll()
        self.after(400, self._do_list)

    # â”€â”€ Style â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    def _style(self):
        s = ttk.Style(self)
        s.theme_use("clam")
        s.configure(".", background=BG, foreground=FG,
                    font=F, borderwidth=0)
        s.configure("TFrame",  background=BG)
        s.configure("S.TFrame",background=BG2)
        s.configure("TLabel",  background=BG, foreground=FG)
        s.configure("D.TLabel",background=BG, foreground=FG2)
        s.configure("S.TLabel",background=BG2,foreground=FG)
        # Blue primary button
        s.configure("TButton", background=ACCENT, foreground="#fff",
                    font=FB, padding=(14,7), relief="flat", borderwidth=0)
        s.map("TButton",
              background=[("active",ACCENT2),("pressed",ACCENT2)],
              relief=[("pressed","flat")])
        # Ghost (text) button
        s.configure("G.TButton", background=BG, foreground=ACCENT,
                    font=FB, padding=(10,6), relief="flat", borderwidth=0)
        s.map("G.TButton",
              background=[("active",BG_HOV),("pressed",BG_HOV)],
              foreground=[("active",ACCENT2)])
        # Side ghost
        s.configure("Sd.TButton", background=BG2, foreground=FG,
                    font=F, padding=(6,4), relief="flat", borderwidth=0)
        s.map("Sd.TButton", background=[("active",BORDER)])
        # Entry
        s.configure("TEntry", fieldbackground=BG, foreground=FG,
                    insertcolor=FG, borderwidth=1, relief="flat", padding=(6,5))
        # Scrollbar
        s.configure("TScrollbar", background=BORDER, troughcolor=BG2,
                    borderwidth=0, arrowcolor=FG3, gripcount=0)
        s.map("TScrollbar", background=[("active",FG3)])
        # Progressbar
        s.configure("Horizontal.TProgressbar",
                    troughcolor=BORDER, background=ACCENT,
                    borderwidth=0, thickness=4)
        # Treeview
        s.configure("Treeview", background=BG, foreground=FG,
                    fieldbackground=BG, rowheight=30, borderwidth=0, font=F)
        s.configure("Treeview.Heading", background=BG2, foreground=FG2,
                    font=FB, borderwidth=0, relief="flat", padding=(6,6))
        s.map("Treeview",
              background=[("selected",BG_HOV)],
              foreground=[("selected",ACCENT)])

    # â”€â”€ UI â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    def _ui(self):
        # Top bar
        tb = tk.Frame(self, bg=BG, height=52)
        tb.pack(fill="x")
        tb.pack_propagate(False)
        tk.Frame(tb, bg=BORDER, height=1).place(relx=0,rely=1,relwidth=1,anchor="sw")
        tk.Label(tb, text="MTC Novel Downloader",
                 bg=BG, fg=FG, font=("Segoe UI",12,"bold")).pack(side="left",padx=20,pady=10)
        tk.Label(tb, text="â€” android.lonoapp.net", bg=BG, fg=FG2, font=F).pack(
                 side="left",pady=10)
        # Auth status chip
        self._chip_var = tk.StringVar(value="ChÆ°a Ä‘Äƒng nháº­p")
        self._chip = tk.Label(tb, textvariable=self._chip_var,
                              bg=BG2, fg=FG2, font=FB,
                              padx=12, pady=4, relief="flat")
        self._chip.pack(side="right", padx=20, pady=10)

        # Main split
        main = tk.Frame(self, bg=BG)
        main.pack(fill="both", expand=True)

        left = tk.Frame(main, bg=BG2, width=440)
        left.pack(side="left", fill="y")
        left.pack_propagate(False)
        tk.Frame(main, bg=BORDER, width=1).pack(side="left", fill="y")

        right = tk.Frame(main, bg=BG)
        right.pack(side="left", fill="both", expand=True)

        self._left(left)
        self._right(right)

    # â”€â”€ Left sidebar â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    def _left(self, p):
        # Search
        sr = tk.Frame(p, bg=BG2)
        sr.pack(fill="x", padx=12, pady=(14,6))

        sb = tk.Frame(sr, bg=BG, highlightthickness=1,
                      highlightbackground=BORDER, highlightcolor=ACCENT)
        sb.pack(side="left", fill="x", expand=True)
        tk.Label(sb, text="ðŸ”", bg=BG, fg=FG2, font=F).pack(side="left",padx=(8,0))
        self._sq = tk.StringVar()
        se = tk.Entry(sb, textvariable=self._sq, bg=BG, fg=FG,
                      font=F, bd=0, insertbackground=FG)
        se.pack(side="left", fill="x", expand=True, ipady=6, padx=4)
        se.bind("<Return>", lambda _: self._search())
        se.bind("<FocusIn>",  lambda _: sb.config(highlightbackground=ACCENT))
        se.bind("<FocusOut>", lambda _: sb.config(highlightbackground=BORDER))
        ttk.Button(sr, text="TÃ¬m", command=self._search, width=5).pack(
                   side="left", padx=(6,0))

        # Header row
        hr = tk.Frame(p, bg=BG2)
        hr.pack(fill="x", padx=12, pady=(2,0))
        tk.Label(hr, text="DANH SÃCH", bg=BG2, fg=FG3,
                 font=("Segoe UI",8,"bold")).pack(side="left")
        self._stl = tk.Label(hr, text="", bg=BG2, fg=FG3,
                              font=("Segoe UI",8))
        self._stl.pack(side="right")

        # Tree
        tf = tk.Frame(p, bg=BG2)
        tf.pack(fill="both", expand=True)
        cols = ("id","name","ch")
        self._tree = ttk.Treeview(tf, columns=cols,
                                   show="headings", selectmode="browse")
        self._tree.heading("id",   text="ID",    anchor="center")
        self._tree.heading("name", text="TÃªn truyá»‡n")
        self._tree.heading("ch",   text="Ch.",   anchor="center")
        self._tree.column("id",   width=65, anchor="center", stretch=False)
        self._tree.column("name", width=290, anchor="w")
        self._tree.column("ch",   width=50,  anchor="center", stretch=False)
        self._tree.tag_configure("o", background="#f8f9fa")
        self._tree.tag_configure("e", background=BG)
        vsb = ttk.Scrollbar(tf, orient="vertical", command=self._tree.yview)
        self._tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        self._tree.pack(side="left", fill="both", expand=True)
        self._tree.bind("<<TreeviewSelect>>", self._on_sel)

        # Pagination
        pg = tk.Frame(p, bg=BG2)
        pg.pack(fill="x", padx=12, pady=8)
        ttk.Button(pg, text="â€¹", style="Sd.TButton", width=3,
                   command=self._prev).pack(side="left")
        self._pglbl = tk.Label(pg, text="â€”", bg=BG2, fg=FG2, font=F)
        self._pglbl.pack(side="left", padx=8)
        ttk.Button(pg, text="â€º", style="Sd.TButton", width=3,
                   command=self._next).pack(side="left")

    # â”€â”€ Right panel â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    def _right(self, p):
        # â”€â”€ Login section â”€â”€
        lf = tk.LabelFrame(p, text=" TÃ i khoáº£n MTC  (dÃ¹ng email/pass á»©ng dá»¥ng MTC) ",
                           bg=BG, fg=FG2, font=("Segoe UI",8,"bold"),
                           bd=1, relief="groove", labelanchor="nw")
        lf.pack(fill="x", padx=20, pady=(16,0))

        lr = tk.Frame(lf, bg=BG)
        lr.pack(fill="x", padx=10, pady=10)

        tk.Label(lr, text="Email:", bg=BG, fg=FG2, font=F).pack(side="left")
        self._email = tk.StringVar()
        _e(lr, self._email, 22).pack(side="left", padx=(4,12))

        tk.Label(lr, text="Máº­t kháº©u:", bg=BG, fg=FG2, font=F).pack(side="left")
        self._pwd = tk.StringVar()
        _e(lr, self._pwd, 16, show="â€¢").pack(side="left", padx=(4,12))

        ttk.Button(lr, text="ÄÄƒng nháº­p", command=self._login).pack(side="left")

        self._auth_lbl = tk.Label(lr, text="", bg=BG, fg=FG3, font=F)
        self._auth_lbl.pack(side="left", padx=10)

        # Key row (shown after login if key found)
        self._key_row = tk.Frame(lf, bg=BG)
        self._key_row.pack(fill="x", padx=10, pady=(0,8))
        tk.Label(self._key_row, text="APP_KEY phÃ¡t hiá»‡n:", bg=BG, fg=FG2,
                 font=F).pack(side="left")
        self._key_var = tk.StringVar()
        _e(self._key_row, self._key_var, 40).pack(side="left", padx=4)
        self._key_row.pack_forget()  # hidden initially

        # â”€â”€ Book info â”€â”€
        tk.Frame(p, bg=BORDER, height=1).pack(fill="x", padx=20, pady=(12,0))
        info = tk.Frame(p, bg=BG)
        info.pack(fill="x", padx=20, pady=(10,0))
        self._t_name = tk.Label(info, text="â† Chá»n truyá»‡n tá»« danh sÃ¡ch",
                                 bg=BG, fg=FG2, font=FH,
                                 anchor="w", wraplength=580, justify="left")
        self._t_name.pack(fill="x")
        self._t_meta = tk.Label(info, text="", bg=BG, fg=FG2, font=F, anchor="w")
        self._t_meta.pack(fill="x", pady=(3,0))
        self._t_syn  = tk.Label(info, text="", bg=BG, fg=FG2, font=F,
                                 anchor="nw", wraplength=580, justify="left")
        self._t_syn.pack(fill="x", pady=(4,0))

        # â”€â”€ Download controls â”€â”€
        tk.Frame(p, bg=BORDER, height=1).pack(fill="x", padx=20, pady=(12,0))
        cf = tk.Frame(p, bg=BG)
        cf.pack(fill="x", padx=20, pady=(10,0))

        lc = {"bg":BG, "fg":FG2, "font":F}
        tk.Label(cf, text="Tá»« chÆ°Æ¡ng:", **lc).grid(row=0,column=0,sticky="w",pady=4)
        self._fr = tk.StringVar(value="1")
        _e(cf,self._fr,6).grid(row=0,column=1,sticky="w",padx=(4,16),pady=4)
        tk.Label(cf,text="Äáº¿n chÆ°Æ¡ng:",**lc).grid(row=0,column=2,sticky="w",pady=4)
        self._to = tk.StringVar(value="")
        _e(cf,self._to,6).grid(row=0,column=3,sticky="w",padx=(4,0),pady=4)

        tk.Label(cf,text="LÆ°u vÃ o:",**lc).grid(row=1,column=0,sticky="w",pady=4)
        of = tk.Frame(cf, bg=BG)
        of.grid(row=1,column=1,columnspan=3,sticky="ew",pady=4)
        self._out = tk.StringVar(value=str(Path.cwd()/"downloads"))
        _e(of,self._out,30).pack(side="left")
        ttk.Button(of,text="Thay Ä‘á»•i",style="G.TButton",
                   command=self._browse).pack(side="left",padx=(6,0))

        tk.Label(cf,text="Delay (s):",**lc).grid(row=2,column=0,sticky="w",pady=4)
        self._delay = tk.StringVar(value="0.5")
        _e(cf,self._delay,6).grid(row=2,column=1,sticky="w",padx=(4,0),pady=4)
        cf.columnconfigure(3, weight=1)

        # â”€â”€ Progress â”€â”€
        pf = tk.Frame(p, bg=BG)
        pf.pack(fill="x", padx=20, pady=(8,4))
        self._bar = ttk.Progressbar(pf, mode="determinate",
                                    style="Horizontal.TProgressbar")
        self._bar.pack(fill="x")
        self._bar_lbl = tk.StringVar()
        tk.Label(pf, textvariable=self._bar_lbl, bg=BG,
                 fg=FG2, font=F).pack(anchor="w", pady=(2,0))

        # â”€â”€ Buttons â”€â”€
        bf = tk.Frame(p, bg=BG)
        bf.pack(fill="x", padx=20, pady=(4,8))
        self._btn_dl = ttk.Button(bf, text="Táº£i xuá»‘ng", command=self._start)
        self._btn_dl.pack(side="left")
        self._btn_stop = ttk.Button(bf, text="Dá»«ng", style="G.TButton",
                                     command=self._stopdl, state="disabled")
        self._btn_stop.pack(side="left", padx=(8,0))
        ttk.Button(bf,text="Má»Ÿ thÆ° má»¥c",style="G.TButton",
                   command=self._open).pack(side="right")

        # â”€â”€ Log â”€â”€
        tk.Frame(p, bg=BORDER, height=1).pack(fill="x", padx=20)
        lh = tk.Frame(p, bg=BG)
        lh.pack(fill="x", padx=20, pady=(8,4))
        tk.Label(lh,text="Nháº­t kÃ½",bg=BG,fg=FG2,font=FB).pack(side="left")
        ttk.Button(lh,text="XoÃ¡",style="G.TButton",
                   command=self._clrlog).pack(side="right")
        lf2 = tk.Frame(p, bg=BG)
        lf2.pack(fill="both", expand=True, padx=20, pady=(0,16))
        self._log = tk.Text(lf2, bg=BG2, fg=FG2, font=FM,
                             bd=0, wrap="word", state="disabled",
                             highlightthickness=1, highlightbackground=BORDER,
                             selectbackground=BG_HOV)
        lvsb = ttk.Scrollbar(lf2, orient="vertical", command=self._log.yview)
        self._log.configure(yscrollcommand=lvsb.set)
        lvsb.pack(side="right", fill="y")
        self._log.pack(side="left", fill="both", expand=True)
        self._log.tag_configure("ok",  foreground=GREEN)
        self._log.tag_configure("w",   foreground=YELLOW)
        self._log.tag_configure("err", foreground=RED)
        self._log.tag_configure("acc", foreground=ACCENT)
        self._log.tag_configure("dim", foreground=FG3)

    # â”€â”€ Log â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    def _lg(self, msg, tag=""):
        self._q.put((msg, tag))

    def _poll(self):
        try:
            while True:
                msg, tag = self._q.get_nowait()
                self._log.config(state="normal")
                self._log.insert("end", f"{time.strftime('%H:%M:%S')}  ", "dim")
                self._log.insert("end", msg+"\n", tag or None)
                self._log.see("end")
                self._log.config(state="disabled")
        except queue.Empty:
            pass
        self.after(80, self._poll)

    def _clrlog(self):
        self._log.config(state="normal")
        self._log.delete("1.0","end")
        self._log.config(state="disabled")

    # â”€â”€ Auth â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    def _login(self):
        if not _ok: return
        em = self._email.get().strip()
        pw = self._pwd.get().strip()
        if not em or not pw:
            messagebox.showwarning("Thiáº¿u thÃ´ng tin","Nháº­p email vÃ  máº­t kháº©u MTC")
            return
        self._auth_lbl.config(text="Äang Ä‘Äƒng nháº­p...", fg=YELLOW)
        self.update_idletasks()

        def _w():
            auth = dl.login(em, pw)
            if not auth:
                self.after(0, lambda: (
                    self._auth_lbl.config(text="âœ– ÄÄƒng nháº­p tháº¥t báº¡i", fg=RED),
                    self._chip_var.set("ChÆ°a Ä‘Äƒng nháº­p"),
                    self._chip.config(fg=FG2),
                    self._lg("ÄÄƒng nháº­p tháº¥t báº¡i â€” kiá»ƒm tra email/máº­t kháº©u","err"),
                ))
                return

            self._token   = auth.get("token")
            self._app_key = auth.get("key")
            self._session = dl.make_session(self._token)

            # After login, probe chapter content type
            chapters_probe = None
            try:
                # Get first chapter ID
                chs = dl.get_all_chapters(self._session,
                                           list(dl.list_books(self._session,1,5)
                                                .get("data",[])[0:1])
                                           and dl.list_books(self._session,1,5)
                                           .get("data",[])[0]["id"] if True else 0)
                if chs:
                    chapters_probe = dl.probe_chapter_content(self._session, chs[0]["id"])
            except Exception:
                pass

            # Fetch profile for any extra keys
            profile = dl.fetch_user_profile(self._session)

            key_found = bool(self._app_key)
            if not key_found and profile:
                import base64 as _b64
                for v in profile.values():
                    if isinstance(v, str) and len(v) > 20:
                        try:
                            raw = _b64.b64decode(v.replace("base64:","")+  "==")
                            if len(raw) in (16,24,32):
                                self._app_key = v
                                key_found = True
                                break
                        except Exception:
                            pass

            def _done():
                status = f"âœ” {em.split('@')[0]}"
                self._chip_var.set(status)
                self._chip.config(fg=GREEN)
                self._auth_lbl.config(fg=GREEN,
                    text=f"ÄÄƒng nháº­p thÃ nh cÃ´ng  |  token: {'âœ”' if self._token else 'âœ–'}")

                self._lg(f"ÄÄƒng nháº­p thÃ nh cÃ´ng: {em}", "ok")
                self._lg(f"  Token: {'âœ” cÃ³' if self._token else 'âœ– khÃ´ng'}")
                self._lg(f"  APP_KEY: {'âœ” tÃ¬m tháº¥y!' if self._app_key else 'âœ– khÃ´ng cÃ³ trong response'}")
                self._lg(f"  Profile fields: {list(profile.keys()) if profile else 'khÃ´ng láº¥y Ä‘Æ°á»£c'}")

                if chapters_probe:
                    enc = chapters_probe.get("encrypted", True)
                    self._lg(f"  Content sau login: {'ÄÃƒ MÃƒ HOÃ' if enc else 'â­ PLAIN TEXT!'}", 
                             "w" if enc else "ok")
                    self._lg(f"  Sample: {chapters_probe.get('sample','')[:80]!r}", "dim")

                if self._app_key:
                    self._key_var.set(self._app_key)
                    self._key_row.pack(fill="x", padx=10, pady=(0,8))
                    self._lg(f"  KEY: {self._app_key[:40]}...", "ok")
                else:
                    self._lg("  Server KHÃ”NG tráº£ key trong response â€” ná»™i dung váº«n cáº§n giáº£i mÃ£", "w")
                    self._lg("  â†’ Náº¿u báº¡n biáº¿t APP_KEY, nháº­p vÃ o Ã´ APP_KEY bÃªn dÆ°á»›i", "dim")

            self.after(0, _done)

        threading.Thread(target=_w, daemon=True).start()

    # â”€â”€ Books â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    def _do_list(self):
        if not _ok: return
        self._stl.config(text="Äang táº£i...")
        threading.Thread(target=self._fetch, args=(None,), daemon=True).start()

    def _search(self):
        q = self._sq.get().strip() or None
        self._page = 1
        self._stl.config(text="Äang táº£i...")
        threading.Thread(target=self._fetch, args=(q,), daemon=True).start()

    def _fetch(self, q):
        try:
            if q:
                data = dl.search_books(self._session, q, self._page)
            else:
                data = dl.list_books(self._session, self._page, 30)
            books = data.get("data", [])
            pagi  = data.get("pagination", {}) or {}
            total = pagi.get("total", len(books))
            lp    = pagi.get("last_page", 1)
            self._books = books
            self._last_page = lp
            self.after(0, lambda: self._fill(books, total, lp))
        except Exception as e:
            self.after(0, lambda: (
                self._lg(f"Lá»—i táº£i danh sÃ¡ch: {e}", "err"),
                self._stl.config(text="Lá»—i"),
            ))

    def _fill(self, books, total, lp):
        for r in self._tree.get_children():
            self._tree.delete(r)
        for i, b in enumerate(books):
            ch = b.get("latest_index", b.get("chapter_count", 0))
            self._tree.insert("","end", iid=str(b["id"]),
                              values=(b["id"], b.get("name",""), ch),
                              tags=("o" if i%2 else "e",))
        self._pglbl.config(text=f"Trang {self._page}/{lp}")
        self._stl.config(text=f"{total} truyá»‡n")

    def _on_sel(self, _=None):
        sel = self._tree.selection()
        if not sel: return
        bid  = int(sel[0])
        book = next((b for b in self._books if b["id"]==bid), None)
        if book:
            self._sel = book
            n  = book.get("name","")
            ch = book.get("latest_index", book.get("chapter_count",0))
            st = book.get("status_name","")
            rt = book.get("review_score",0)
            rv = book.get("review_count",0)
            syn = (book.get("synopsis") or "")[:280]
            self._t_name.config(text=n, fg=FG)
            self._t_meta.config(
                text=f"ID {book['id']}  Â·  {ch} chÆ°Æ¡ng  Â·  {st}  Â·  â˜… {rt}/5  ({rv} Ä‘Ã¡nh giÃ¡)")
            self._t_syn.config(text=syn)
            self._to.set(str(ch))
            self._lg(f"Chá»n: {n}", "acc")

    def _prev(self):
        if self._page > 1:
            self._page -= 1
            self._do_list()

    def _next(self):
        if self._page < self._last_page:
            self._page += 1
            self._do_list()

    # â”€â”€ Download â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    def _start(self):
        if not self._sel:
            messagebox.showwarning("ChÆ°a chá»n","Chá»n truyá»‡n tá»« danh sÃ¡ch"); return
        if self._thread and self._thread.is_alive():
            messagebox.showinfo("Äang cháº¡y","CÃ³ tiáº¿n trÃ¬nh Ä‘ang cháº¡y"); return
        try:
            start = int(self._fr.get() or 1)
            end   = int(self._to.get()) if self._to.get().strip() else None
            delay = float(self._delay.get() or 0.5)
        except ValueError:
            messagebox.showerror("Lá»—i","ChÆ°Æ¡ng/Delay pháº£i lÃ  sá»‘"); return

        # Use key from key field if set
        app_key = self._key_var.get().strip() or self._app_key or None

        self._btn_dl.config(state="disabled")
        self._btn_stop.config(state="normal")
        self._stop = False
        self._bar["value"] = 0
        self._bar_lbl.set("")

        self._thread = threading.Thread(
            target=self._worker,
            args=(self._sel, Path(self._out.get()), start, end, delay, app_key),
            daemon=True)
        self._thread.start()

    def _stopdl(self):
        self._stop = True
        self._lg("Äang dá»«ng...","w")

    def _worker(self, book, out_dir, start, end, delay, app_key):
        name    = book["name"]
        book_id = book["id"]
        self._lg(f"Báº¯t Ä‘áº§u táº£i: Â«{name}Â»", "acc")
        if app_key:
            self._lg(f"Giáº£i mÃ£: âœ” APP_KEY={app_key[:30]}...", "ok")
        else:
            self._lg("Giáº£i mÃ£: KhÃ´ng cÃ³ APP_KEY â€” ghi placeholder náº¿u content mÃ£ hoÃ¡", "w")
        try:
            out_dir.mkdir(parents=True, exist_ok=True)
            bdir  = out_dir / dl.safe_name(name)
            bdir.mkdir(parents=True, exist_ok=True)
            pf    = bdir / ".progress.json"

            done = set()
            if pf.exists():
                try:
                    done = set(json.loads(pf.read_text("utf-8")).get("done",[]))
                    self._lg(f"Resume: {len(done)} chÆ°Æ¡ng Ä‘Ã£ cÃ³")
                except Exception:
                    pass

            self._lg("Láº¥y danh sÃ¡ch chÆ°Æ¡ng...")
            chs = dl.get_all_chapters(self._session, book_id)
            self._lg(f"Tá»•ng {len(chs)} chÆ°Æ¡ng")

            if end is None:
                end = chs[-1].get("index", len(chs)) if chs else 1

            to_dl = [c for c in chs
                     if start <= c.get("index",0) <= end
                     and c["id"] not in done
                     and not c.get("is_locked")]
            n = len(to_dl)
            self._lg(f"Sáº½ táº£i {n} chÆ°Æ¡ng (ch.{start}â€“{end})")

            nok = nenc = nfail = 0
            for i, ch in enumerate(to_dl, 1):
                if self._stop:
                    self._lg("Dá»«ng bá»Ÿi ngÆ°á»i dÃ¹ng","w"); break
                nm  = ch.get("name", f"ChÆ°Æ¡ng {ch.get('index',i)}")
                idx = ch.get("index", i)
                pct = int(i/n*100)
                self.after(0, lambda p=pct, m=f"[{i}/{n}]  {nm}":
                           (self._bar.config(value=p), self._bar_lbl.set(m)))

                ch_data = dl.get_chapter(self._session, ch["id"], delay)
                if not ch_data:
                    self._lg(f"  âœ– {nm}","err"); nfail+=1; continue

                raw  = ch_data.get("content","")
                text = dl.process_content(raw, app_key)

                cf = bdir / f"{idx:06d}_{dl.safe_name(nm)}.txt"
                dl.write_chapter_file(cf, ch_data, text)
                done.add(ch["id"])
                pf.write_text(json.dumps({"done":list(done)},ensure_ascii=False),
                              encoding="utf-8")

                if text:
                    nok+=1; self._lg(f"  âœ” {nm}","ok")
                else:
                    nenc+=1; self._lg(f"  âš  {nm} (mÃ£ hoÃ¡)","w")

            dl.merge_to_single_file(bdir, name)
            self._lg("â”€"*40,"dim")
            self._lg(f"Xong!  âœ”{nok}  âš {nenc}(mÃ£ hoÃ¡)  âœ–{nfail}(lá»—i)",
                     "ok" if nenc==0 else "w")
            self._lg(f"ThÆ° má»¥c: {bdir}")
        except Exception as e:
            self._lg(f"Lá»—i: {e}","err")
        finally:
            self.after(0, self._done)

    def _done(self):
        self._btn_dl.config(state="normal")
        self._btn_stop.config(state="disabled")
        self._bar["value"] = 100

    # â”€â”€ Misc â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    def _browse(self):
        d = filedialog.askdirectory(title="Chá»n thÆ° má»¥c lÆ°u")
        if d: self._out.set(d)

    def _open(self):
        folder = Path(self._out.get())
        if self._sel:
            sub = folder / dl.safe_name(self._sel["name"])
            if sub.exists(): folder = sub
        folder.mkdir(parents=True, exist_ok=True)
        os.startfile(str(folder))


if __name__ == "__main__":
    App().mainloop()

