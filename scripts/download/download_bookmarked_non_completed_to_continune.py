#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""Download every non-completed bookmarked MTC book to D:\Dev\MTC_Continune.

Uses the account credentials to authenticate, reads the existing bookmark manifest,
selects unfinished books, and downloads them in the same plain-text format used by
the other MTC_Continune downloaders.
"""
from __future__ import annotations

import argparse
import base64
import html
import json
import os
import re
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import requests
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad

SCRIPT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPT_ROOT))
sys.path.insert(0, str(SCRIPT_ROOT / "download"))

from download_all_missing_books import strict_book_name, strict_chapter_filename, strict_component
from download_completed_to_mtc import safe_book_dir_name
from mtc_status_utils import is_completed_status, is_ongoing_status

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(r"D:\Dev\MTC_Continune")
LOG_DIR = Path(r"C:\Dev\MTC_Download\logs")
BASE = "https://android.lonoapp.net/api"
MANIFEST = LOG_DIR / "bookmarked_books_manifest.json"
LOG = LOG_DIR / "download_bookmarked_non_completed_to_continune.json"
STATE = LOG_DIR / "download_bookmarked_non_completed_to_continune_state.json"
DELAY = 0.2
VERIFY_PASSES = 3

INVALID = '<>:"/\\|?*[]()'
TAG_RE = re.compile(r"<[^>]+")
WS_RE = re.compile(r"[ \t\r\f\v]+")
PAYLOAD_RE = re.compile(r"^[A-Za-z0-9+/=]+$")
MARKER_RE = re.compile(r'eyJpdiI6|"iv":"|"value":"')
CHAPTER_RE = re.compile(r"^chapter_(\d{4})_(\d+)\.txt$")
DUPLICATE_DIR = "_duplicate_chapter_files"
_thread_state = threading.local()


def b64d(data):
    if isinstance(data, str):
        data = data.encode("ascii", "ignore")
    data = data.strip()
    data += b"=" * ((4 - len(data) % 4) % 4)
    return base64.b64decode(data)


def clean_iv_b64(iv_b64: bytes) -> bytes:
    base = b"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/="
    candidates = [iv_b64, bytes([x for x in iv_b64 if x in base])]
    for src in list(candidates):
        n = len(src)
        for remove_len in range(1, min(24, n) + 1):
            for start in range(0, n - remove_len + 1):
                candidates.append(src[:start] + src[start + remove_len:])
    seen = set()
    for cand in candidates:
        if cand in seen:
            continue
        seen.add(cand)
        try:
            raw = b64d(cand)
            if len(raw) >= 16:
                return raw[:16]
        except Exception:
            continue
    raise ValueError("unable to decode iv")


def decrypt_content_field(content_b64: str) -> str:
    content_bytes_ascii = content_b64.encode("ascii", "ignore")
    raw = b64d(content_b64)
    a = raw.find(b'"iv":"')
    b = raw.find(b'","value":"')
    c = raw.find(b'"value":"')
    if a < 0 or b < 0 or c < 0:
        raise ValueError("encrypted payload markers not found")
    iv_b64 = raw[a + len(b'"iv":"'):b]
    c += len(b'"value":"')
    d = raw.find(b'","mac"', c)
    if d < 0:
        d = raw.rfind(b'"}')
    if d < 0:
        raise ValueError("encrypted value end marker not found")
    val_b64 = raw[c:d]
    key = content_bytes_ascii[17:33]
    iv16 = clean_iv_b64(iv_b64)
    value_raw = b64d(val_b64)
    pt = AES.new(key, AES.MODE_CBC, iv16).decrypt(value_raw)
    try:
        pt = unpad(pt, 16)
    except Exception:
        pass
    return pt.decode("utf-8", errors="replace").replace("\x00", "").lstrip("\ufeff").strip()


def maybe_decrypt(content: str) -> str:
    value = str(content or "").strip()
    if len(value) > 100 and PAYLOAD_RE.fullmatch(value):
        raw = b64d(value)
        if b'"iv":"' in raw and b'"value":"' in raw:
            return decrypt_content_field(value)
    return value


def clean_text(value) -> str:
    text = html.unescape(str(value or ""))
    text = text.replace("<br />", "\n").replace("<br/>", "\n").replace("<br>", "\n")
    text = re.sub(r"</p\s*>", "\n\n", text, flags=re.I)
    text = TAG_RE.sub("", text)
    lines = []
    for line in text.splitlines():
        line = WS_RE.sub(" ", line).strip()
        lines.append(line)
    out = []
    blanks = 0
    for line in lines:
        if not line:
            blanks += 1
            if blanks <= 1:
                out.append("")
        else:
            blanks = 0
            out.append(line)
    return "\n".join(out).strip()


def safe(name: str) -> str:
    return safe_book_dir_name(name or "unknown")


def book_folder_name(book_id: int, name: str) -> str:
    return safe(name)


def select_unfinished_books(manifest_books, top_n: int | None):
    selected = []
    skipped = []
    for book in manifest_books:
        if is_completed_status(book):
            skipped.append({"id": book.get("id"), "name": book.get("name"), "reason": "completed"})
            continue
        if book.get("status_name") or book.get("status") is not None:
            if not is_ongoing_status(book):
                skipped.append({"id": book.get("id"), "name": book.get("name"), "reason": book.get("status_name") or book.get("status")})
                continue
        selected.append(book)
        if top_n is not None and len(selected) >= top_n:
            break
    return selected, skipped


def technical_chapter_filename(idx: int, chapter_id: int) -> str:
    return f"chapter_{idx:04d}_{chapter_id}.txt"


def mtc_chapter_filename(chapter: dict) -> str:
    return strict_chapter_filename(chapter, chapter["index"])


def format_chapter_text(chapter_name: str, content: str) -> str:
    clean_name = str(chapter_name or "").strip()
    body = clean_text(content)
    header = f"{'=' * 60}\n{clean_name}\n{'=' * 60}\n\n"
    return header + body + ("" if body.endswith("\n") else "\n")


def chapter_index_from_name(name: str):
    match = re.search(r"\d+", name)
    if not match:
        return None
    try:
        return int(match.group(0))
    except Exception:
        return None


def chapter_sort_score(path: Path, canonical_name: str) -> tuple:
    size = path.stat().st_size if path.exists() else 0
    exact = 0 if path.name == canonical_name else 1
    punct = sum(1 for ch in path.name if not (ch.isalnum() or ch.isspace() or ch == "."))
    return (exact, -size, punct, len(path.name))


def is_valid_chapter_file(path: Path) -> bool:
    if not path.exists() or path.stat().st_size <= 20:
        return False
    try:
        sample = path.read_text(encoding="utf-8", errors="ignore")[:2000]
    except Exception:
        return False
    return not MARKER_RE.search(sample)


def move_duplicate_file(path: Path, folder: Path):
    duplicate_dir = folder / DUPLICATE_DIR
    duplicate_dir.mkdir(exist_ok=True)
    target = duplicate_dir / path.name
    if target.exists():
        stem = target.stem
        suffix = target.suffix
        for index in range(2, 1000):
            candidate = duplicate_dir / f"{stem}_{index}{suffix}"
            if not candidate.exists():
                target = candidate
                break
    path.replace(target)
    return target


def reconcile_existing_chapter_files(folder: Path, chapters):
    chapter_map = {int(ch["index"]): ch for ch in chapters}
    by_index = {}
    for path in folder.glob("*.txt"):
        index = chapter_index_from_name(path.name)
        if index is None:
            continue
        by_index.setdefault(index, []).append(path)
    moved = []
    duplicates = []
    for index, paths in by_index.items():
        chapter = chapter_map.get(index)
        if chapter is None:
            continue
        canonical = folder / mtc_chapter_filename(chapter)
        paths = sorted(paths, key=lambda p: chapter_sort_score(p, canonical.name))
        keep = paths[0]
        if keep != canonical and is_valid_chapter_file(keep) and not canonical.exists():
            keep.replace(canonical)
            moved.append({"from": str(keep), "to": str(canonical)})
            keep = canonical
        for extra in paths[1:]:
            duplicates.append(str(move_duplicate_file(extra, folder)))
    return {"moved": moved, "duplicates": duplicates}


def find_technical_file(folder: Path, chapter: dict) -> Path | None:
    candidate = folder / technical_chapter_filename(chapter["index"], chapter["id"])
    return candidate if candidate.exists() else None


def normalize_existing_chapter_files(folder: Path, chapters):
    moved = []
    duplicates = []
    for chapter in chapters:
        canonical = folder / mtc_chapter_filename(chapter)
        technical = find_technical_file(folder, chapter)
        if not technical:
            continue
        if is_valid_chapter_file(canonical):
            duplicates.append(str(move_duplicate_file(technical, folder)))
        elif is_valid_chapter_file(technical):
            technical.replace(canonical)
            moved.append({"from": str(technical), "to": str(canonical)})
        elif canonical.exists():
            duplicates.append(str(move_duplicate_file(technical, folder)))
    return {"moved": moved, "duplicates": duplicates}


def collect_existing_ids(folder: Path, chapters):
    ids = set()
    for chapter in chapters:
        path = folder / mtc_chapter_filename(chapter)
        if is_valid_chapter_file(path):
            ids.add(chapter["id"])
    return ids


def build_unique_chapters(chapters):
    unique = []
    seen = set()
    duplicates = []
    for idx, chapter in enumerate(chapters, 1):
        chapter_id = int(chapter.get("id"))
        if chapter_id in seen:
            duplicates.append(chapter_id)
            continue
        seen.add(chapter_id)
        unique.append({
            "index": idx,
            "id": chapter_id,
            "name": (chapter.get("name") or "").strip(),
        })
    return unique, duplicates


def find_missing_chapters(chapters, existing_ids):
    return [chapter for chapter in chapters if chapter["id"] not in existing_ids]


def get_json(session, url, params=None, retries=4):
    for attempt in range(retries):
        try:
            response = session.get(url, params=params, timeout=35)
            response.encoding = "utf-8"
            if response.status_code == 429:
                time.sleep(3 + attempt * 2)
                continue
            response.raise_for_status()
            return response.json()
        except Exception:
            if attempt == retries - 1:
                raise
            time.sleep(2 + attempt * 2)


def login_with_retry(email: str, password: str, retries=5):
    for attempt in range(retries):
        session = requests.Session()
        session.headers.update({"User-Agent": "MTC/Android", "Accept": "application/json", "Content-Type": "application/json"})
        try:
            response = session.post(
                BASE + "/auth/login",
                json={"email": email, "password": password, "device_name": "OpenClaw Windows"},
                timeout=30,
            )
            response.encoding = "utf-8"
            print("login", response.status_code, flush=True)
            response.raise_for_status()
            token = response.json()["data"]["token"]
            return session, token
        except Exception:
            session.close()
            if attempt == retries - 1:
                raise
            time.sleep(2 + attempt * 2)


def make_session(token: str):
    session = requests.Session()
    from requests.adapters import HTTPAdapter
    adapter = HTTPAdapter(pool_connections=64, pool_maxsize=64, max_retries=0)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    session.headers.update({
        "User-Agent": "MTC/Android",
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    })
    return session


def get_worker_session(token: str):
    state = _thread_state
    if getattr(state, "token", None) != token or getattr(state, "session", None) is None:
        old = getattr(state, "session", None)
        if old is not None:
            try:
                old.close()
            except Exception:
                pass
        state.session = make_session(token)
        state.token = token
    return state.session


def fetch_chapter_text(token: str, chapter, folder: Path):
    session = get_worker_session(token)
    chapter_id = chapter["id"]
    index = chapter["index"]
    title = chapter["name"]
    out = folder / mtc_chapter_filename(chapter)
    if is_valid_chapter_file(out):
        return {"status": "skipped", "id": chapter_id, "index": index}
    temp = out.with_suffix(".txt.tmp")
    try:
        payload = get_json(session, BASE + f"/chapters/{chapter_id}")
        data = payload.get("data", {})
        chapter_name = (data.get("name") or title or f"Chuong {index}").strip()
        encrypted = data.get("content") or ""
        text = format_chapter_text(chapter_name, maybe_decrypt(encrypted))
        if MARKER_RE.search(text):
            raise ValueError("encrypted marker remains after decrypt")
        temp.write_text(text, encoding="utf-8")
        temp.replace(out)
        return {"status": "downloaded", "id": chapter_id, "index": index}
    except Exception as exc:
        try:
            if temp.exists():
                temp.unlink()
        except Exception:
            pass
        return {
            "status": "failed",
            "id": chapter_id,
            "index": index,
            "name": title,
            "error": str(exc)[:300],
        }


def download_book(token: str, folder: Path, chapters, worker_count: int):
    failures = []
    unique_chapters, duplicates = build_unique_chapters(chapters)
    reconciled = reconcile_existing_chapter_files(folder, unique_chapters)
    normalized = normalize_existing_chapter_files(folder, unique_chapters)
    ok_ids = collect_existing_ids(folder, unique_chapters)
    final_missing = []

    for verify_pass in range(1, VERIFY_PASSES + 1):
        missing = find_missing_chapters(unique_chapters, ok_ids)
        if not missing:
            final_missing = []
            break
        with ThreadPoolExecutor(max_workers=max(1, worker_count)) as executor:
            futures = [executor.submit(fetch_chapter_text, token, chapter, folder) for chapter in missing]
            completed = 0
            total = len(futures)
            pass_failures = []
            for future in as_completed(futures):
                result = future.result()
                completed += 1
                if result["status"] in {"downloaded", "skipped"}:
                    ok_ids.add(result["id"])
                else:
                    pass_failures.append(result)
                if completed % 25 == 0 or completed == total:
                    print(
                        f"  pass {verify_pass}: completed {completed}/{total} ok={len(ok_ids)}/{len(unique_chapters)} fail={len(pass_failures)}",
                        flush=True,
                    )
                time.sleep(DELAY)
            failures = pass_failures
        ok_ids = collect_existing_ids(folder, unique_chapters)
        final_missing = find_missing_chapters(unique_chapters, ok_ids)
        if not final_missing:
            break
        print(f"  verify pass {verify_pass} missing={len(final_missing)} retrying", flush=True)
        time.sleep(1)

    if final_missing:
        missing_ids = {chapter["id"] for chapter in final_missing}
        failure_map = {item["id"]: item for item in failures}
        for chapter in final_missing:
            if chapter["id"] not in failure_map:
                failures.append({
                    "status": "failed",
                    "id": chapter["id"],
                    "index": chapter["index"],
                    "name": chapter["name"],
                    "error": "missing after verification pass",
                })
    failures.sort(key=lambda item: item["index"])
    return {
        "ok": len(ok_ids.intersection({chapter["id"] for chapter in unique_chapters})),
        "expected": len(unique_chapters),
        "duplicates": duplicates,
        "reconciled": reconciled,
        "normalized": normalized,
        "failures": failures,
        "missing_ids": [chapter["id"] for chapter in final_missing],
    }


def load_existing_report():
    if not LOG.exists():
        return []
    try:
        return json.loads(LOG.read_text(encoding="utf-8"))
    except Exception:
        return []


def save_report(report):
    LOG.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")


def load_state():
    if STATE.exists():
        try:
            return json.loads(STATE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"done": set(), "failed": set(), "started_at": time.strftime("%Y-%m-%d %H:%M:%S")}


def save_state(state):
    serializable = {
        "done": sorted(int(x) for x in state.get("done", set())),
        "failed": sorted(int(x) for x in state.get("failed", set())),
        "started_at": state.get("started_at"),
    }
    STATE.write_text(json.dumps(serializable, ensure_ascii=False, indent=2), encoding="utf-8")


def parse_args(argv):
    env_email = os.environ.get("MTC_EMAIL")
    env_password = os.environ.get("MTC_PASS")
    first_arg = argv[1] if len(argv) > 1 else ""
    if len(argv) > 2 and not (env_email and env_password and first_arg.isdigit()):
        email = argv[1]
        password = argv[2]
        arg_offset = 3
    else:
        email = env_email
        password = env_password
        arg_offset = 1
    if not email or not password:
        raise SystemExit("usage: python download_bookmarked_non_completed_to_continune.py <email> <password> [top_n] [delay] [workers] [verify_passes]")
    return {
        "email": email,
        "password": password,
        "top_n": int(argv[arg_offset]) if len(argv) > arg_offset and argv[arg_offset].isdigit() else None,
        "delay": float(argv[arg_offset + 1]) if len(argv) > arg_offset + 1 else float(os.environ.get("MTC_DELAY", "0.2")),
        "workers": int(argv[arg_offset + 2]) if len(argv) > arg_offset + 2 else int(os.environ.get("MTC_WORKERS", "8")),
        "verify_passes": int(argv[arg_offset + 3]) if len(argv) > arg_offset + 3 else int(os.environ.get("MTC_VERIFY_PASSES", "3")),
        "book_id": int(argv[arg_offset]) if len(argv) > arg_offset and argv[arg_offset].lstrip("-").isdigit() and int(argv[arg_offset]) > 0 else None,
    }


def main():
    args = parse_args(sys.argv)
    email = args["email"]
    password = args["password"]
    top_n = args["top_n"]
    workers = args["workers"]
    global DELAY, VERIFY_PASSES
    DELAY = args["delay"]
    VERIFY_PASSES = args["verify_passes"]
    ROOT.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    manifest_books = json.loads(MANIFEST.read_text(encoding="utf-8"))["books"]
    books, skipped_books = select_unfinished_books(manifest_books, top_n)
    if skipped_books:
        print(f"skipped non-ongoing/completed books before download: {len(skipped_books)}", flush=True)
    if not books:
        print("no unfinished books to download", flush=True)
        return
    session, token = login_with_retry(email, password)

    state = load_state()
    done_ids = {int(x) for x in state.get("done", set())}
    failed_ids = {int(x) for x in state.get("failed", set())}

    report = load_existing_report()
    report_by_id = {item["id"]: item for item in report if isinstance(item, dict) and "id" in item}

    if args["book_id"]:
        detail = get_json(session, BASE + f"/books/{args['book_id']}")
        book_detail = detail.get("data", detail)
        name = book_detail.get("name") or f"book_{args['book_id']}"
        books = [{"id": args["book_id"], "name": name}]

    for book_index, book in enumerate(books, 1):
        book_id = int(book["id"])
        name = book["name"]
        folder = ROOT / book_folder_name(book_id, name)
        if book_id in done_ids:
            print(f"[{book_index}/{len(books)}] SKIP done {book_id} {name}", flush=True)
            continue
        print(f"[{book_index}/{len(books)}] {book_id} {name}", flush=True)

        if not args["book_id"]:
            detail = get_json(session, BASE + f"/books/{book_id}")
            book_detail = detail.get("data", detail)
        if is_completed_status(book_detail):
            print(f"  skip completed; status={book_detail.get('status_name') or book_detail.get('status')}", flush=True)
            continue
        if not is_ongoing_status(book_detail):
            print(f"  skip non-ongoing status={book_detail.get('status_name') or book_detail.get('status')}", flush=True)
            continue
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "info.json").write_text(json.dumps(book_detail, ensure_ascii=False, indent=2), encoding="utf-8")

        all_chapters = []
        page = 1
        while True:
            page_json = get_json(session, BASE + "/chapters", params={"filter[book_id]": book_id, "page": page, "limit": 100})
            items = page_json.get("data") or []
            if not items:
                break
            all_chapters.extend(items)
            pagination = page_json.get("pagination") or {}
            current = pagination.get("current") or page
            last = pagination.get("last") or current
            if current >= last or len(items) < 100:
                break
            page += 1
            time.sleep(DELAY)

        (folder / "chapters_manifest.json").write_text(json.dumps(all_chapters, ensure_ascii=False, indent=2), encoding="utf-8")
        result = download_book(token, folder, all_chapters, workers)
        entry = {
            "id": book_id,
            "name": name,
            "folder": str(folder),
            "expected": result["expected"],
            "ok": result["ok"],
            "duplicates": result["duplicates"],
            "reconciled": result["reconciled"],
            "normalized": result["normalized"],
            "fail": result["failures"],
            "missing_ids": result["missing_ids"],
            "workers": workers,
            "status": "complete" if result["ok"] == result["expected"] and not result["missing_ids"] else "partial",
            "updated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        }
        report_by_id[book_id] = entry
        ordered = [report_by_id[int(item["id"])] for item in books if int(item["id"]) in report_by_id]
        save_report(ordered)
        if entry["status"] == "complete":
            state["done"].add(book_id)
        else:
            state["failed"].add(book_id)
        save_state(state)
        print(
            f"  final ok={entry['ok']}/{entry['expected']} duplicates={len(entry['duplicates'])} missing={len(entry['missing_ids'])}",
            flush=True,
        )

    print("done", flush=True)


if __name__ == "__main__":
    main()
