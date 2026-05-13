#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import base64
import html
import json
import re
import sys
import time
from pathlib import Path
from typing import Any

from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad

from download_completed_to_mtc import MTCDownloader, clean_filename, chapter_filename

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

ROOT = Path(r'C:\Dev\MTC')
TAG_RE = re.compile(r'<[^>]+>')
WS_RE = re.compile(r'[ \t\r\f\v]+')
PAYLOAD_RE = re.compile(r'^[A-Za-z0-9+/=]+$')
# Hard encrypted residue markers (should never remain after successful decrypt)
MARKER_RE = re.compile(r'eyJpdiI6|"iv":"|"value":"')
CONTROL_RE = re.compile(r'[\x00-\x08\x0b\x0c\x0e-\x1f]')


def b64d(data):
    if isinstance(data, str):
        data = data.encode('ascii', 'ignore')
    data = data.strip()
    data += b'=' * ((4 - len(data) % 4) % 4)
    return base64.b64decode(data)


def clean_iv_b64(iv_b64: bytes) -> bytes:
    base = b'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/='
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
    raise ValueError('unable to decode iv')


def decrypt_content_field(content_b64: str) -> str:
    content_bytes_ascii = content_b64.encode('ascii', 'ignore')
    raw = b64d(content_b64)
    a = raw.find(b'"iv":"')
    b = raw.find(b'","value":"')
    c = raw.find(b'"value":"')
    if a < 0 or b < 0 or c < 0:
        raise ValueError('encrypted payload markers not found')
    iv_b64 = raw[a + len(b'"iv":"'):b]
    c += len(b'"value":"')
    d = raw.find(b'","mac"', c)
    if d < 0:
        d = raw.rfind(b'"}')
    if d < 0:
        raise ValueError('encrypted value end marker not found')
    val_b64 = raw[c:d]
    key = content_bytes_ascii[17:33]
    iv16 = clean_iv_b64(iv_b64)
    value_raw = b64d(val_b64)
    pt = AES.new(key, AES.MODE_CBC, iv16).decrypt(value_raw)
    try:
        pt = unpad(pt, 16)
    except Exception:
        pass
    return pt.decode('utf-8', errors='replace').replace('\x00', '').lstrip('\ufeff').strip()


def maybe_decrypt(content: str) -> tuple[str, bool]:
    s = str(content or '').strip()
    # Usually content is one long base64 string containing JSON iv/value/mac.
    if len(s) > 100 and PAYLOAD_RE.fullmatch(s):
        try:
            raw = b64d(s)
            if b'"iv":"' in raw and b'"value":"' in raw:
                return decrypt_content_field(s), True
        except Exception:
            raise
    return s, False


def clean_text(value: Any) -> str:
    text = html.unescape(str(value or ''))
    text = text.replace('<br />', '\n').replace('<br/>', '\n').replace('<br>', '\n')
    text = re.sub(r'</p\s*>', '\n\n', text, flags=re.I)
    text = TAG_RE.sub('', text)
    lines = []
    for line in text.splitlines():
        line = WS_RE.sub(' ', line).strip()
        lines.append(line)
    out = []
    blanks = 0
    for line in lines:
        if not line:
            blanks += 1
            if blanks <= 1:
                out.append('')
        else:
            blanks = 0
            out.append(line)
    return '\n'.join(out).strip()


def normalize_chapter_title(name: str, index: int) -> str:
    s = html.unescape(str(name or f'Chương {index}')).strip()
    s = re.sub(r'^\s*(?:chương|chuong)\s*(\d+)\s*[:.\-–—]?\s*', lambda m: f'Chương {m.group(1)}: ', s, flags=re.I)
    if not re.match(r'^Chương\s+\d+', s, re.I):
        s = f'Chương {index}: {s}'
    return s.strip(' .') + ('' if s.rstrip().endswith(('!', '?')) else ('.' if s.rstrip().endswith('.') else ''))

def sanitize_path_component(s: str) -> str:
    s = str(s or '')
    s = CONTROL_RE.sub('', s)
    s = s.replace('�', '')
    s = re.sub(r'\s+', ' ', s).strip()
    return s


def write_plain_chapter(path: Path, title: str, body: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    body = clean_text(body)
    # Remove accidental duplicate/garbage title at start of body, then intentionally add clean duplicate at line 5.
    lines = body.splitlines()
    while lines and not lines[0].strip():
        lines.pop(0)
    if lines:
        first = lines[0].strip()
        # Drop duplicate/garbled title fragments before the real prose starts.
        looks_like_broken_title = False
        if first == title or MARKER_RE.search(first) or '�' in first:
            looks_like_broken_title = True
        elif len(first) < 160:
            # short non-prose line at top that resembles a damaged title
            alpha = sum(ch.isalpha() for ch in first)
            weird = sum((ord(ch) < 32) or (ch == '�') for ch in first)
            if weird > 0 or alpha < max(8, len(first) // 3):
                looks_like_broken_title = True
            if 'tác giả:' in first.lower() or 'chuong' in first.lower() or 'chư' in first.lower() or 'chương' in first.lower():
                looks_like_broken_title = True
        if looks_like_broken_title:
            lines.pop(0)
            while lines and not lines[0].strip():
                lines.pop(0)
    body = '\n'.join(lines).strip()
    # Remove residual replacement/control chars to keep chapter readable and filename-safe commits clean.
    body = body.replace('�', '')
    body = CONTROL_RE.sub('', body)
    text = f"{'='*60}\n{title}\n{'='*60}\n\n{title}\n\n{body}\n"
    if MARKER_RE.search(text):
        raise ValueError('encrypted marker remains after decrypt/clean')
    path.write_text(text, encoding='utf-8')


def is_completed(book: dict) -> bool:
    return book.get('status_name') == 'Hoàn thành' or book.get('status') == 2


def get_latest_completed(d: MTCDownloader, exclude_existing=True, limit_pages=10) -> dict | None:
    page = 1
    while page <= limit_pages:
        data = d.get_books(limit=100, page=page)
        rows = (data or {}).get('data') or []
        if not rows:
            break
        for b in rows:
            if not is_completed(b):
                continue
            name = clean_filename(b.get('name') or f"book_{b.get('id')}")
            if exclude_existing and (ROOT / name).exists():
                continue
            return b
        if len(rows) < 100:
            break
        page += 1
        time.sleep(0.2)
    return None


def get_chapters_once_safe(d: MTCDownloader, book_id: int) -> list[dict]:
    data = d.get_chapters(book_id, page=1, limit=100)
    rows = (data or {}).get('data') or []
    # This API sometimes ignores limit and returns all chapters at once (e.g. 1405 rows).
    # In that case do NOT paginate, or it loops forever on identical pages.
    seen = set()
    out = []
    for c in rows:
        cid = c.get('id')
        if cid in seen:
            continue
        seen.add(cid)
        out.append(c)
    def key(c: dict):
        try:
            return int(c.get('index') or c.get('number') or 0)
        except Exception:
            return 0
    return sorted(out, key=key)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--book-id', type=int, default=None)
    ap.add_argument('--delay', type=float, default=0.25)
    args = ap.parse_args()

    ROOT.mkdir(parents=True, exist_ok=True)
    d = MTCDownloader()
    if args.book_id:
        detail = d.get_book_detail(args.book_id)
        book = (detail or {}).get('data') or {}
    else:
        book = get_latest_completed(d)
    if not book:
        print('ERROR: no completed book found')
        return 2
    if not is_completed(book):
        print(f"ERROR: book {book.get('id')} is not completed")
        return 3

    book_id = int(book['id'])
    book_name = clean_filename(book.get('name') or f'book_{book_id}')
    book_dir = ROOT / book_name
    book_dir.mkdir(parents=True, exist_ok=True)
    print(f'book={book_name}')
    print(f'book_id={book_id}')
    print(f'out={book_dir}')

    chapters = get_chapters_once_safe(d, book_id)
    print(f'chapters_total={len(chapters)} expected={book.get("chapter_count") or book.get("latest_index")}')
    ok = fail = 0
    for i, ch in enumerate(chapters, 1):
        cid = ch.get('id')
        fname = chapter_filename(ch, i)
        fpath = book_dir / fname
        if fpath.exists() and fpath.stat().st_size >= 5000:
            ok += 1
            print(f'[{i}/{len(chapters)}] skip existing file={fname}', flush=True)
            continue
        print(f'[{i}/{len(chapters)}] download chapter_id={cid} file={fname}', flush=True)
        detail = d.get_chapter_content(cid)
        data = (detail or {}).get('data') or {}
        content = data.get('content') or data.get('body') or ''
        if not content:
            fail += 1
            print(f'  MISS content chapter_id={cid}')
            time.sleep(args.delay)
            continue
        try:
            plain, decrypted = maybe_decrypt(content)
            idx = int(ch.get('index') or i)
            title = normalize_chapter_title(data.get('name') or ch.get('name') or f'Chương {idx}', idx)
            safe_fname = sanitize_path_component(chapter_filename(ch, i))
            safe_title = sanitize_path_component(title)
            safe_fpath = book_dir / safe_fname
            write_plain_chapter(safe_fpath, safe_title, plain)
            ok += 1
            print(f'  OK decrypted={decrypted} written={safe_fpath.name}', flush=True)
        except Exception as e:
            fail += 1
            print(f'  FAIL chapter_id={cid}: {e}', flush=True)
            break
        time.sleep(args.delay)

    # No info.json/manifest in book folder by design.
    for junk in book_dir.glob('info.json'):
        junk.unlink(missing_ok=True)
    print(f'final_ok={ok}')
    print(f'final_fail={fail}')
    print(f'out={book_dir}')
    return 0 if fail == 0 and ok == len(chapters) else 4

if __name__ == '__main__':
    raise SystemExit(main())
