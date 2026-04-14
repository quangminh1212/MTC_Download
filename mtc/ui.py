"""ui.py – Tkinter GUI for MTC Novel Downloader (API-only)."""
import threading
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
from pathlib import Path

from .config import (
    BG, BG2, BORDER, BLUE, BLUE2, BHOV, FG, FG2, FG3,
    GREEN, YELLOW, RED, ORANGE,
    FONT, FONT_BOLD, FONT_HEAD, FONT_MONO,
    OUTPUT_DIR, TOKEN_FILE, log,
)
from .downloader import (
    download_book,
    download_batch,
    load_catalog,
    refresh_catalog,
)
from .utils import safe_name, merge_to_single_file


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("MTC Novel Downloader v2.0")
        self.geometry("800x600")
        self.configure(bg=BG)
        self._stop = False
        self._running = False

        self._build_ui()

    # ── Build UI ────────────────────────────────────────────────────────────
    def _build_ui(self):
        # Header
        hdr = tk.Frame(self, bg=BLUE, height=48)
        hdr.pack(fill=tk.X)
        tk.Label(
            hdr, text="📚 MTC Novel Downloader", font=FONT_HEAD,
            bg=BLUE, fg="white",
        ).pack(side=tk.LEFT, padx=16, pady=8)

        token_status = "✔ Token" if TOKEN_FILE.exists() else "✖ No token"
        tk.Label(
            hdr, text=token_status, font=FONT, bg=BLUE, fg="white",
        ).pack(side=tk.RIGHT, padx=16)

        # Input area
        inp = tk.Frame(self, bg=BG, padx=16, pady=12)
        inp.pack(fill=tk.X)

        tk.Label(inp, text="Tên truyện:", font=FONT_BOLD, bg=BG, fg=FG).grid(
            row=0, column=0, sticky="w"
        )
        self._book_var = tk.StringVar()
        self._book_entry = tk.Entry(
            inp, textvariable=self._book_var, font=FONT, width=50
        )
        self._book_entry.grid(row=0, column=1, padx=8, sticky="ew")

        tk.Label(inp, text="Từ ch:", font=FONT, bg=BG, fg=FG2).grid(
            row=0, column=2
        )
        self._start_var = tk.StringVar(value="1")
        tk.Entry(inp, textvariable=self._start_var, font=FONT, width=6).grid(
            row=0, column=3
        )

        tk.Label(inp, text="Đến ch:", font=FONT, bg=BG, fg=FG2).grid(
            row=0, column=4
        )
        self._end_var = tk.StringVar()
        tk.Entry(inp, textvariable=self._end_var, font=FONT, width=6).grid(
            row=0, column=5
        )

        inp.columnconfigure(1, weight=1)

        # Buttons
        btn_row = tk.Frame(self, bg=BG, padx=16, pady=4)
        btn_row.pack(fill=tk.X)

        self._dl_btn = tk.Button(
            btn_row, text="⚡ Tải truyện", font=FONT_BOLD,
            bg=BLUE, fg="white", activebackground=BLUE2,
            relief="flat", padx=16, pady=6,
            command=self._on_download,
        )
        self._dl_btn.pack(side=tk.LEFT, padx=(0, 8))

        self._batch_btn = tk.Button(
            btn_row, text="📦 Tải tất cả", font=FONT_BOLD,
            bg=GREEN, fg="white", relief="flat", padx=16, pady=6,
            command=self._on_batch,
        )
        self._batch_btn.pack(side=tk.LEFT, padx=(0, 8))

        self._refresh_btn = tk.Button(
            btn_row, text="🔄 Cập nhật catalog", font=FONT,
            bg=BG2, fg=FG, relief="flat", padx=12, pady=6,
            command=self._on_refresh,
        )
        self._refresh_btn.pack(side=tk.LEFT, padx=(0, 8))

        self._stop_btn = tk.Button(
            btn_row, text="⏹ Dừng", font=FONT,
            bg=RED, fg="white", relief="flat", padx=12, pady=6,
            command=self._on_stop, state=tk.DISABLED,
        )
        self._stop_btn.pack(side=tk.LEFT)

        # Status bar
        self._status_var = tk.StringVar(value="Sẵn sàng")
        tk.Label(
            btn_row, textvariable=self._status_var, font=FONT,
            bg=BG, fg=FG2,
        ).pack(side=tk.RIGHT)

        # Log area
        log_frame = tk.Frame(self, bg=BG, padx=16, pady=8)
        log_frame.pack(fill=tk.BOTH, expand=True)

        self._log = scrolledtext.ScrolledText(
            log_frame, font=FONT_MONO, bg="#1e1e1e", fg="#d4d4d4",
            insertbackground="#d4d4d4", relief="flat", wrap=tk.WORD,
            state=tk.DISABLED, height=20,
        )
        self._log.pack(fill=tk.BOTH, expand=True)

        # Catalog count
        books = load_catalog()
        self._status_var.set(f"Sẵn sàng  ·  Catalog: {len(books)} truyện")

    # ── Logging ─────────────────────────────────────────────────────────────
    def _log_msg(self, msg: str):
        def _append():
            self._log.configure(state=tk.NORMAL)
            self._log.insert(tk.END, msg + "\n")
            self._log.see(tk.END)
            self._log.configure(state=tk.DISABLED)
        self.after(0, _append)

    def _set_status(self, msg: str):
        self.after(0, lambda: self._status_var.set(msg))

    def _set_running(self, running: bool):
        self._running = running
        self._stop = False
        state = tk.DISABLED if running else tk.NORMAL
        stop_state = tk.NORMAL if running else tk.DISABLED
        self.after(0, lambda: self._dl_btn.configure(state=state))
        self.after(0, lambda: self._batch_btn.configure(state=state))
        self.after(0, lambda: self._refresh_btn.configure(state=state))
        self.after(0, lambda: self._stop_btn.configure(state=stop_state))

    def _on_stop(self):
        self._stop = True
        self._set_status("Đang dừng...")

    # ── Single download ─────────────────────────────────────────────────────
    def _on_download(self):
        name = self._book_var.get().strip()
        if not name:
            messagebox.showwarning("Thiếu thông tin", "Nhập tên truyện!")
            return

        ch_start = int(self._start_var.get() or "1")
        ch_end_str = self._end_var.get().strip()
        ch_end = int(ch_end_str) if ch_end_str else None

        self._set_running(True)
        self._set_status(f"Đang tải: {name}...")

        def _worker():
            try:
                result = download_book(
                    book_name=name,
                    ch_start=ch_start,
                    ch_end=ch_end,
                    log_fn=self._log_msg,
                    stop_flag=lambda: self._stop,
                )
                if result["success"]:
                    self._set_status(f"✔ Xong: {result['ok']} chương")
                else:
                    self._set_status(f"✖ {result.get('reason', 'Lỗi')}")
            except Exception as exc:
                self._log_msg(f"Lỗi: {exc}")
                self._set_status(f"✖ Lỗi: {exc}")
            finally:
                self._set_running(False)

        threading.Thread(target=_worker, daemon=True).start()

    # ── Batch download ──────────────────────────────────────────────────────
    def _on_batch(self):
        books = load_catalog()
        if not books:
            messagebox.showwarning("Catalog trống", "Chạy 'Cập nhật catalog' trước!")
            return

        self._set_running(True)
        self._set_status(f"Đang tải {len(books)} truyện...")

        def _worker():
            try:
                result = download_batch(
                    books,
                    log_fn=self._log_msg,
                    stop_flag=lambda: self._stop,
                )
                self._set_status(
                    f"Xong! ✔{result['ok']}  ✖{result['fail']}  ⊘{result['skipped']}"
                )
            except Exception as exc:
                self._log_msg(f"Lỗi: {exc}")
                self._set_status(f"✖ Lỗi: {exc}")
            finally:
                self._set_running(False)

        threading.Thread(target=_worker, daemon=True).start()

    # ── Refresh catalog ─────────────────────────────────────────────────────
    def _on_refresh(self):
        self._set_running(True)
        self._set_status("Đang cập nhật catalog...")

        def _worker():
            try:
                books = refresh_catalog(log_fn=self._log_msg)
                self._set_status(f"Catalog: {len(books)} truyện")
            except Exception as exc:
                self._log_msg(f"Lỗi: {exc}")
                self._set_status(f"✖ Lỗi refresh: {exc}")
            finally:
                self._set_running(False)

        threading.Thread(target=_worker, daemon=True).start()
