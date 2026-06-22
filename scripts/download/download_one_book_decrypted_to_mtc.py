#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import base64, html, json, re, sys, time
from pathlib import Path
import requests
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad
from download_completed_to_mtc import chapter_filename, safe_book_dir_name, write_chapter

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

args = sys.argv[1:]
if len(args) >= 4 and not str(args[0]).isdigit():
    EMAIL = args[0]
    PASSWORD = args[1]
    BOOK_ID = int(args[2])
    BOOK_NAME = args[3]
elif len(args) >= 2:
    EMAIL = None
    PASSWORD = None
    BOOK_ID = int(args[0])
    BOOK_NAME = args[1]
else:
    raise SystemExit('Usage: download_one_book_decrypted_to_mtc.py [email password] <book_id> <book_name>')
ROOT=Path(r'C:\Dev\MTC')
BASE='https://android.lonoapp.net/api'
DELAY=0.15

PAYLOAD_RE = re.compile(r'^[A-Za-z0-9+/=]+$')
TAG_RE = re.compile(r'<[^>]+>')
WS_RE = re.compile(r'[ \t\r\f\v]+')
CONTROL_RE = re.compile(r'[\x00-\x08\x0b\x0c\x0e-\x1f]')
CHAPTER_LINE_RE = re.compile(r'^\s*(?:ch\S{0,8})\s*\d+\s*[:.\-–—]?', re.I)
ENCRYPTED_MARKER_RE = re.compile(r'eyJpdiI6|"iv":"|"value":"')
CHAPTER_FILE_RE = re.compile(r'^Chương\s+(\d+)\b.*\.txt$', re.I)

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

def maybe_decrypt(content: str) -> str:
    s = str(content or '').strip()
    if len(s) > 100 and PAYLOAD_RE.fullmatch(s):
        try:
            raw = b64d(s)
            if b'"iv":"' in raw and b'"value":"' in raw:
                return decrypt_content_field(s)
        except Exception:
            return s
    return s

def clean_text(value) -> str:
    text = html.unescape(str(value or ''))
    text = CONTROL_RE.sub('', text).replace('�', '')
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

def strip_leading_duplicate_title(body: str, chapter_index: int) -> str:
    lines = body.splitlines()
    while lines and not lines[0].strip():
        lines.pop(0)
    if not lines:
        return ''
    first = lines[0].strip()
    if CHAPTER_LINE_RE.match(first) or re.search(rf'\b{chapter_index}\b', first):
        lines.pop(0)
        while lines and not lines[0].strip():
            lines.pop(0)
    return '\n'.join(lines).strip()

def strip_corrupted_title_prefix(body: str, title: str) -> str:
    plain_title = re.sub(r'^\s*(?:ch\S{0,8})\s*\d+\s*[:.\-–—]?\s*', '', title, flags=re.I).strip()
    if not plain_title:
        return body
    body_work = body
    hay = body_work[:240].lower()
    words = plain_title.split()
    for start in range(0, min(4, len(words))):
        candidate = ' '.join(words[start:]).strip()
        if len(candidate) < 12:
            continue
        pos = hay.find(candidate.lower())
        if 0 <= pos <= 40:
            body_work = body_work[pos + len(candidate):].lstrip(' .,:;!?")]-\n\r\t')
            break
    return body_work.strip()

def safe(name:str)->str:
    return safe_book_dir_name(name or 'unknown')

def cleanup_same_index_files(folder: Path, chapter_index: int, keep: Path) -> None:
    for path in folder.glob('*.txt'):
        if path == keep:
            continue
        match = CHAPTER_FILE_RE.match(path.name)
        if not match:
            continue
        if int(match.group(1)) != int(chapter_index):
            continue
        if keep.exists() and keep.stat().st_size >= path.stat().st_size:
            path.unlink(missing_ok=True)

def validate_chapter_body(body: str) -> str:
    text = str(body or '').strip()
    if not text:
        raise ValueError('empty chapter body')
    if ENCRYPTED_MARKER_RE.search(text):
        raise ValueError('encrypted payload remains after decode')
    return text

def fetch_all_chapters(session: requests.Session):
    rows=[]
    page=1
    while True:
        response=session.get(BASE+'/chapters', params={'filter[book_id]':BOOK_ID,'page':page,'limit':100}, timeout=30)
        response.encoding='utf-8'
        response.raise_for_status()
        payload=response.json()
        items=payload.get('data') or []
        if not items:
            break
        rows.extend(items)
        pagination = payload.get('pagination') or {}
        current = pagination.get('current') or page
        last = pagination.get('last') or current
        if current >= last or len(items) < 100:
            break
        page += 1
        time.sleep(DELAY)
    return rows

s=requests.Session()
s.headers.update({'User-Agent':'MTC/Android','Accept':'application/json','Content-Type':'application/json'})
if EMAIL and PASSWORD:
    login=s.post(BASE+'/auth/login', json={'email':EMAIL,'password':PASSWORD,'device_name':'OpenClaw Windows'}, timeout=30)
    login.encoding='utf-8'
    print('login', login.status_code, flush=True)
    login.raise_for_status()
    token=login.json()['data']['token']
    s.headers.update({'Authorization':f'Bearer {token}'})
else:
    print('login skipped (public mode)', flush=True)

folder=ROOT/safe(BOOK_NAME)
folder.mkdir(parents=True, exist_ok=True)

book_detail = s.get(BASE+f'/books/{BOOK_ID}', timeout=30)
book_detail.encoding='utf-8'
book_detail.raise_for_status()
(folder/'info.json').write_text(
    json.dumps(book_detail.json().get('data', {}), ensure_ascii=False, indent=2),
    encoding='utf-8',
)

chapters=fetch_all_chapters(s)
(folder/'chapters_manifest.json').write_text(json.dumps(chapters, ensure_ascii=False, indent=2), encoding='utf-8')
print('chapters', len(chapters), flush=True)
failed = []
for idx,ch in enumerate(chapters,1):
    try:
        cid=ch.get('id')
        title=(ch.get('name') or f'Chương {idx}').strip()
        out=folder/chapter_filename(ch, idx)
        cleanup_same_index_files(folder, idx, out)
        if out.exists() and out.stat().st_size > 200:
            if idx%25==0 or idx==len(chapters):
                print(f'progress {idx}/{len(chapters)} skip-existing', flush=True)
            continue
        r=s.get(BASE+f'/chapters/{cid}', timeout=30)
        r.encoding='utf-8'
        r.raise_for_status()
        data=r.json().get('data',{})
        cname=(data.get('name') or title).strip()
        body=clean_text(maybe_decrypt(data.get('content') or ''))
        body=strip_leading_duplicate_title(body, idx)
        body=strip_corrupted_title_prefix(body, cname)
        body=validate_chapter_body(body)
        write_chapter(out, BOOK_NAME, out.stem, body)
        cleanup_same_index_files(folder, idx, out)
        if idx<=3:
            print('sample_file', out.name)
            print(body[:300].replace('\n',' '))
        if idx%25==0 or idx==len(chapters):
            print(f'progress {idx}/{len(chapters)}', flush=True)
    except Exception as exc:
        failed.append({'index': idx, 'chapter_id': ch.get('id'), 'name': ch.get('name'), 'error': str(exc)[:300]})
        print(f'chapter_error {idx}/{len(chapters)} id={ch.get("id")} error={exc}', flush=True)
    time.sleep(DELAY)

if failed:
    print(f'done_with_errors {folder} failed={len(failed)}', flush=True)
    for row in failed[:20]:
        print(json.dumps(row, ensure_ascii=False), flush=True)
    raise SystemExit(2)

print('done', folder, flush=True)
