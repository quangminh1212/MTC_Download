"""ui.py – MTC Overlay (compact, always-on-top control panel)."""
import os, threading, queue, time, logging
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
        ttk.Button(af, text="Cài APK", style="G.TButton",
                   command=self._install_apk).pack(side="right", padx=(0,4))

        tk.Frame(body, bg=BORDER, height=1).pack(fill="x", pady=4)

        # ── Book name ─────────────────────────────────────────────────────
        _lbl(body, "Tên truyện (để đặt tên thư mục):", FG2).pack(anchor="w")
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
            self._lg(f"APK: {pkg}", "ok")
        else:
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
            tag = "ok" if ok else "err"
            self._lg("✔ Đã cài" if ok else "✖ Lỗi cài APK", tag)
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
