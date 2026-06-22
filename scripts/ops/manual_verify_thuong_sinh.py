#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import base64
import html
import json
import re
from pathlib import Path
from typing import Any

from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad

from mtc_downloader import MTCDownloader

ROOT = Path(r"C:\Dev\MTC\Thương Sinh Giang Đạo")
LOG = Path(r"C:\Dev\MTC_Download\logs\thuong_sinh_manual_verify.json")
PAYLOAD_RE = re.compile(r'^[A-Za-z0-9+/=]+$')
TAG_RE = re.compile(r'<[^>]+>')
WS_RE = re.compile(r'[ \t\r\f\v]+')
MARKER_RE = re.compile(r'eyJpdiI6|"iv":"|"value":"')
CONTROL_RE = re.compile(r'[\x00-\x08\x0b\x0c\x0e-\x1f]')
CH_RE = re.compile(r'(?i)(?:chương|chuong)\s*(\d+)')


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
    if len(s) > 100 and PAYLOAD_RE.fullmatch(s):
        raw = b64d(s)
        if b'"iv":"' in raw and b'"value":"' in raw:
            return decrypt_content_field(s), True
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


def parse_local_body(path: Path) -> str:
    txt = path.read_text(encoding='utf-8', errors='replace')
    lines = txt.splitlines()
    if len(lines) >= 6:
        body = '\n'.join(lines[6:]).strip()
    else:
        body = txt.strip()
    body = body.replace('�', '')
    body = CONTROL_RE.sub('', body)
    return body.strip()


def local_path_for(index: int) -> Path | None:
    hits = list(ROOT.glob(f'Chương {index} *.txt')) + list(ROOT.glob(f'Chuong {index} *.txt')) + list(ROOT.glob(f'Chương {index}.txt')) + list(ROOT.glob(f'Chuong {index}.txt'))
    return hits[0] if hits else None


def chapter_status(index: int, api_name: str, remote_plain: str, local_path: Path | None) -> dict:
    remote_clean = clean_text(remote_plain)
    remote_len = len(remote_clean)
    row = {
        'chapter': index,
        'api_name': api_name,
        'remote_len': remote_len,
        'local_exists': bool(local_path),
        'local_name': local_path.name if local_path else None,
    }
    if not local_path or not local_path.exists():
        row['status'] = 'missing'
        return row
    local_body = parse_local_body(local_path)
    local_len = len(local_body)
    row['local_len'] = local_len
    row['local_size'] = local_path.stat().st_size
    row['local_preview'] = local_body[:180]
    row['remote_preview'] = remote_clean[:180]
    same_prefix = local_body[:120].strip() == remote_clean[:120].strip() if local_body and remote_clean else False
    ratio = (local_len / remote_len) if remote_len else 0
    row['same_prefix_120'] = same_prefix
    row['ratio'] = round(ratio, 4)
    if remote_len < 50:
        row['status'] = 'remote_too_short'
    elif local_len < 50:
        row['status'] = 'local_too_short'
    elif ratio < 0.6:
        row['status'] = 'truncated'
    elif not same_prefix and ratio < 0.9:
        row['status'] = 'mismatch'
    else:
        row['status'] = 'ok'
    return row


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--book-id', type=int, default=110512)
    ap.add_argument('--start', type=int, default=1)
    ap.add_argument('--end', type=int, default=20)
    args = ap.parse_args()

    d = MTCDownloader()
    chapters = (d.get_chapters(args.book_id, page=1, limit=2000) or {}).get('data') or []
    by_index = {}
    for ch in chapters:
        try:
            idx = int(ch.get('index'))
        except Exception:
            continue
        by_index[idx] = ch

    results = []
    for idx in range(args.start, args.end + 1):
        ch = by_index.get(idx)
        if not ch:
            results.append({'chapter': idx, 'status': 'missing_remote_meta'})
            continue
        detail = (d.get_chapter_content(ch['id']) or {}).get('data') or {}
        content = detail.get('content') or detail.get('body') or ''
        plain, decrypted = maybe_decrypt(content)
        row = chapter_status(idx, detail.get('name') or ch.get('name') or f'Chương {idx}', plain, local_path_for(idx))
        row['decrypted'] = decrypted
        row['chapter_id'] = ch['id']
        results.append(row)
        print(f"chapter={idx} status={row['status']} local={row.get('local_len')} remote={row.get('remote_len')}")

    LOG.parent.mkdir(parents=True, exist_ok=True)
    LOG.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding='utf-8')
    print(str(LOG))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
