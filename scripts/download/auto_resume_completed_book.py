#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Auto-resume downloader for one completed MTC book until full chapter count is reached.

Usage:
  python auto_resume_completed_book.py --book-id 110512 --expected 1405
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(r"C:\Dev\MTC")
SCRIPT = Path(r"C:\Dev\MTC_Download\download_one_completed_live_decrypt.py")


def count_txt(book_dir: Path) -> int:
    if not book_dir.exists():
        return 0
    return sum(1 for p in book_dir.glob("*.txt") if p.is_file() and p.stat().st_size >= 5000)


def detect_book_dir(book_id: int) -> Path:
    # Current pipeline for book 110512 is known folder name.
    # Keep generic fallback by using existing expected path if present.
    known = ROOT / "Thương Sinh Giang Đạo"
    if known.exists() or book_id == 110512:
        return known
    # fallback: pick latest folder with many chapter files
    candidates = []
    for d in ROOT.iterdir():
        if d.is_dir():
            n = sum(1 for p in d.glob("Chương *.txt"))
            candidates.append((n, d))
    candidates.sort(reverse=True, key=lambda t: t[0])
    return candidates[0][1] if candidates else known


def run_once(book_id: int, delay: float, timeout_seconds: int) -> tuple[int, str, str]:
    cmd = [sys.executable, str(SCRIPT), "--book-id", str(book_id), "--delay", str(delay)]
    p = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout_seconds)
    return p.returncode, p.stdout, p.stderr


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--book-id", type=int, required=True)
    ap.add_argument("--expected", type=int, required=True)
    ap.add_argument("--delay", type=float, default=0.15)
    ap.add_argument("--max-attempts", type=int, default=20)
    ap.add_argument("--per-run-timeout", type=int, default=1800, help="seconds")
    ap.add_argument("--sleep-between", type=float, default=3.0)
    ap.add_argument("--log", type=str, default=r"C:\Dev\MTC_Download\logs\auto_resume_110512.log")
    args = ap.parse_args()

    log_path = Path(args.log)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    book_dir = detect_book_dir(args.book_id)
    with log_path.open("a", encoding="utf-8") as log:
        log.write(f"\n=== START auto-resume book_id={args.book_id} expected={args.expected} dir={book_dir} ===\n")

    for attempt in range(1, args.max_attempts + 1):
        have = count_txt(book_dir)
        if have >= args.expected:
            print(f"DONE before run: {have}/{args.expected}")
            return 0

        print(f"attempt={attempt} current={have}/{args.expected} => run downloader")
        try:
            rc, out, err = run_once(args.book_id, args.delay, args.per_run_timeout)
        except subprocess.TimeoutExpired as e:
            out = (e.stdout or "")
            err = (e.stderr or "") + "\n[TIMEOUT]"
            rc = 124

        with log_path.open("a", encoding="utf-8") as log:
            log.write(f"\n--- attempt {attempt} rc={rc} ---\n")
            if out:
                log.write(out)
                if not out.endswith("\n"):
                    log.write("\n")
            if err:
                log.write("[stderr]\n")
                log.write(err)
                if not err.endswith("\n"):
                    log.write("\n")

        have2 = count_txt(book_dir)
        print(f"attempt={attempt} rc={rc} after={have2}/{args.expected}")
        if have2 >= args.expected:
            print("DONE after run")
            return 0

        time.sleep(args.sleep_between)

    final = count_txt(book_dir)
    print(f"NOT_DONE final={final}/{args.expected}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
