#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import base64
import json
import re
import sys
from pathlib import Path
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

ROOT = Path(r'C:\Dev\MTC\Tiền Hạo Kiếp Tây Du')
REPORT = ROOT / '_decrypt_report.txt'


def b64d(data):
    if isinstance(data, str):
        data = data.encode('ascii', 'ignore')
    data = data.strip()
    data += b'=' * ((4 - len(data) % 4) % 4)
    return base64.b64decode(data)


def clean_iv_b64(iv_b64: bytes) -> bytes:
    base = b'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/='
    candidates = []
    # Original and base64-only filtered forms.
    candidates.append(iv_b64)
    candidates.append(bytes([x for x in iv_b64 if x in base]))
    # Try removing inserted noise runs. Valid Laravel IV base64 normally decodes to 16 bytes.
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
    raise ValueError(f'unable to decode iv len={len(iv_b64)} raw={iv_b64[:60]!r}')


def decrypt_content_field(content_b64: str):
    content_bytes_ascii = content_b64.encode('ascii', 'ignore')
    raw = b64d(content_b64)
    p_iv_start = b'"iv":"'
    p_iv_end = b'","value":"'
    p_val_start = b'"value":"'
    p_val_end = b'","mac"'

    a = raw.find(p_iv_start)
    b = raw.find(p_iv_end)
    if a < 0 or b < 0:
        return None, 'no iv marker'
    iv_b64 = raw[a + len(p_iv_start):b]

    c = raw.find(p_val_start)
    if c < 0:
        return None, 'no value marker'
    c += len(p_val_start)
    d = raw.find(p_val_end, c)
    if d < 0:
        d = raw.rfind(b'"}')
        if d < 0:
            return None, 'no value end marker'
    val_b64 = raw[c:d]

    iv16 = clean_iv_b64(iv_b64)
    value_raw = b64d(val_b64)
    if len(content_bytes_ascii) < 33:
        return None, 'content too short for key slice'
    key = content_bytes_ascii[17:33]

    pt = AES.new(key, AES.MODE_CBC, iv16).decrypt(value_raw)
    try:
        pt = unpad(pt, 16)
    except Exception:
        pass

    text = pt.decode('utf-8', errors='replace').replace('\x00', '').lstrip('\ufeff').strip()
    return text, None


def extract_payload(text: str):
    # Files have a human header, then encrypted JSON/base64 payload.
    lines = text.splitlines()
    payload = None
    for line in lines:
        s = line.strip()
        if len(s) > 100 and re.fullmatch(r'[A-Za-z0-9+/=]+', s):
            payload = s
            break
    return payload


def main():
    if not ROOT.exists():
        print(f'ERROR: missing {ROOT}')
        return 2
    ok = 0
    fail = 0
    rows = []
    files = sorted(ROOT.glob('*.txt'))
    for p in files:
        if p.name.startswith('_'):
            continue
        original = p.read_text(encoding='utf-8', errors='replace')
        payload = extract_payload(original)
        if not payload:
            rows.append(f'SKIP already plain or no payload: {p.name}')
            continue
        text, err = decrypt_content_field(payload)
        if err or not text:
            fail += 1
            rows.append(f'FAIL {p.name}: {err or "empty"}')
            print(f'FAIL {p.name}: {err or "empty"}')
            continue
        # Keep existing title header if present, replace encrypted body with plaintext.
        title_lines = original.splitlines()[:3]
        if len(title_lines) >= 3 and set(title_lines[0]) == {'='}:
            final = '\n'.join(title_lines) + '\n\n' + text.strip() + '\n'
        else:
            final = text.strip() + '\n'
        p.write_text(final, encoding='utf-8')
        ok += 1
        rows.append(f'OK {p.name}: {len(text)} chars')
        print(f'OK {p.name}: {len(text)} chars')
    REPORT.write_text(f'ok={ok}\nfail={fail}\n' + '\n'.join(rows) + '\n', encoding='utf-8')
    print(f'DONE ok={ok} fail={fail} report={REPORT}')
    return 0 if fail == 0 else 4


if __name__ == '__main__':
    raise SystemExit(main())
