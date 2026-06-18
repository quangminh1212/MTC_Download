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
EMBEDDED_PAYLOAD_RE = re.compile(r'eyJpdiI6[^\s\u0000-\u001f]+')


MOJIBAKE_FIXES = {
    'Ch\u00c6\u00b0\u00c6\u00a1ng': 'Ch\u01b0\u01a1ng',
    'ch\u00c6\u00b0\u00c6\u00a1ng': 'ch\u01b0\u01a1ng',
    'Ch????ng': 'Ch\u01b0\u01a1ng',
    'ch????ng': 'ch\u01b0\u01a1ng',
    'Ch??ng': 'Ch\u01b0\u01a1ng',
    'ch??ng': 'ch\u01b0\u01a1ng',
    '\u00e2\u20ac\u201c': '\u2013',
    '\u00e2\u20ac\u201d': '\u2014',
}


def _only_b64(token: str) -> str:
    return ''.join(ch for ch in token if ch in 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=')


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
    decrypted_any = False
    for _ in range(4):
        candidate = s.strip()
        # Case 1: the whole string is one Laravel payload.
        if len(candidate) > 100 and (PAYLOAD_RE.fullmatch(candidate) or candidate.startswith('eyJpdiI6')):
            token = candidate if PAYLOAD_RE.fullmatch(candidate) else _only_b64(candidate)
            try:
                raw = b64d(token)
            except Exception:
                raw = b''
            if b'"iv":"' in raw and b'"value":"' in raw:
                s = decrypt_content_field(token).strip()
                decrypted_any = True
                continue
        # Case 2: a Laravel payload is embedded inside otherwise-decrypted text
        # (nested encryption). Decrypt the embedded payload and splice it back in.
        match = EMBEDDED_PAYLOAD_RE.search(s)
        if match:
            token = _only_b64(match.group(0))
            try:
                raw = b64d(token)
            except Exception:
                raw = b''
            if b'"iv":"' in raw and b'"value":"' in raw:
                inner = decrypt_content_field(token).strip()
                s = (s[:match.start()] + inner + s[match.end():]).strip()
                decrypted_any = True
                continue
        break
    return s, decrypted_any



def repair_common_mojibake(value: Any) -> str:
    text = html.unescape(str(value or '')).strip()
    for bad, good in MOJIBAKE_FIXES.items():
        text = text.replace(bad, good)
    return re.sub(r'\s+', ' ', text).strip()


def chapter_title_candidate(data: dict | None, chapter: dict | None, index: int) -> str:
    candidates = []
    for source in (data or {}, chapter or {}):
        for key in ('name', 'title', 'chapter_name', 'chapter_title', 'full_name'):
            value = source.get(key)
            if value:
                candidates.append(value)
        slug = source.get('slug')
        if slug and not re.fullmatch(r'chuong-?0*%s' % int(index), str(slug).strip(), flags=re.I):
            candidates.append(str(slug).replace('-', ' '))
    for candidate in candidates:
        repaired = repair_common_mojibake(candidate)
        if repaired:
            return repaired
    return f'Ch\u01b0\u01a1ng {index}'


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
    s = repair_common_mojibake(name)
    m = re.match(r'^\s*(?:ch\u01b0\u01a1ng|chuong|ch[?]{2,4}ng)\s*0*(\d+)\s*[:.\-\u2013\u2014]?\s*(.*)$', s, flags=re.I)
    if m:
        idx = int(m.group(1))
        suffix = repair_common_mojibake(m.group(2) or '').strip(' .')
        return f'Ch\u01b0\u01a1ng {idx} {suffix}'.strip()
    if not s:
        return f'Ch\u01b0\u01a1ng {index}'
    if not re.match(r'^Ch\u01b0\u01a1ng\s+\d+', s, re.I):
        s = f'Ch\u01b0\u01a1ng {index} {s}'
    return re.sub(r'\s+', ' ', s).strip(' .')

def sanitize_path_component(s: str) -> str:
    s = str(s or '')
    s = CONTROL_RE.sub('', s)
    s = s.replace('�', '')
    s = re.sub(r'\s+', ' ', s).strip()
    return s


def write_plain_chapter(path: Path, title: str, body: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    body = clean_text(body)
    lines = body.splitlines()
    while lines and not lines[0].strip():
        lines.pop(0)
    for _ in range(3):
        if not lines:
            break
        first = lines[0].strip()
        # Drop duplicate/garbled title fragments before the real prose starts.
        looks_like_broken_title = False
        if first == title or MARKER_RE.search(first) or '�' in first:
            looks_like_broken_title = True
        elif len(first) < 160:
            alpha = sum(ch.isalpha() for ch in first)
            weird = sum((ord(ch) < 32) or (ch == '�') for ch in first)
            if weird > 0 or alpha < max(8, len(first) // 3):
                looks_like_broken_title = True
            lowered = first.lower()
            if 'tác giả:' in lowered or 'chuong' in lowered or 'chư' in lowered or 'chương' in lowered:
                looks_like_broken_title = True
        if not looks_like_broken_title:
            break
        lines.pop(0)
        while lines and not lines[0].strip():
            lines.pop(0)
    body = '\n'.join(lines).strip()
    # Remove residual replacement/control chars to keep chapter readable and filename-safe commits clean.
    body = body.replace('�', '')
    body = CONTROL_RE.sub('', body)
    text = f"{'='*60}\n{title}\n{'='*60}\n\n{body}\n"
    if MARKER_RE.search(text):
        raise ValueError('encrypted marker remains after decrypt/clean')
    path.write_text(text, encoding='utf-8')


def write_info_json(book_dir: Path, book: dict, chapters: list[dict]):
    payload = dict(book)
    payload['chapters'] = chapters
    for old_json in book_dir.glob('*.json'):
        if old_json.name != 'info.json':
            old_json.unlink(missing_ok=True)
    (book_dir / 'info.json').write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding='utf-8',
    )


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
        last_error = None
        for attempt in range(1, 4):
            try:
                if attempt > 1:
                    time.sleep(max(args.delay, 0.5))
                    detail = d.get_chapter_content(cid)
                    data = (detail or {}).get('data') or {}
                    content = data.get('content') or data.get('body') or ''
                plain, decrypted = maybe_decrypt(content)
                idx = int(ch.get('index') or i)
                title = normalize_chapter_title(data.get('name') or ch.get('name') or f'Chương {idx}', idx)
                safe_fname = sanitize_path_component(chapter_filename(ch, i))
                safe_title = sanitize_path_component(title)
                safe_fpath = book_dir / safe_fname
                write_plain_chapter(safe_fpath, safe_title, plain)
                ok += 1
                retry_note = f' retry={attempt}' if attempt > 1 else ''
                print(f'  OK decrypted={decrypted}{retry_note} written={safe_fpath.name}', flush=True)
                last_error = None
                break
            except Exception as e:
                last_error = e
                print(f'  RETRYABLE_FAIL attempt={attempt} chapter_id={cid}: {e}', flush=True)
        if last_error is not None:
            fail += 1
            print(f'  FAIL chapter_id={cid}: {last_error}', flush=True)
        time.sleep(args.delay)

    write_info_json(book_dir, book, chapters)
    print(f'final_ok={ok}')
    print(f'final_fail={fail}')
    print(f'out={book_dir}')
    return 0 if fail == 0 and ok == len(chapters) else 4

if __name__ == '__main__':
    raise SystemExit(main())
