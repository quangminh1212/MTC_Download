#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import base64, html, json, re, sys, time
from pathlib import Path
import requests
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad

EMAIL=sys.argv[1]
PASSWORD=sys.argv[2]
BOOK_ID=int(sys.argv[3])
BOOK_NAME=sys.argv[4]
ROOT=Path(r'C:\Dev\MTC')
BASE='https://android.lonoapp.net/api'
DELAY=0.15

PAYLOAD_RE = re.compile(r'^[A-Za-z0-9+/=]+$')
TAG_RE = re.compile(r'<[^>]+>')
WS_RE = re.compile(r'[ \t\r\f\v]+')
INVALID='<>:"/\\|?*[]()+'

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
        raw = b64d(s)
        if b'"iv":"' in raw and b'"value":"' in raw:
            return decrypt_content_field(s)
    return s

def clean_text(value) -> str:
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

def safe(name:str)->str:
    if not name: return 'unknown'
    for c in INVALID: name=name.replace(c,' ')
    name=re.sub(r'[-–—]+',' ',name)
    name=re.sub(r'\s+',' ',name).strip().rstrip('.')
    return name[:180] or 'unknown'

s=requests.Session()
s.headers.update({'User-Agent':'MTC/Android','Accept':'application/json','Content-Type':'application/json'})
login=s.post(BASE+'/auth/login', json={'email':EMAIL,'password':PASSWORD,'device_name':'OpenClaw Windows'}, timeout=30)
login.encoding='utf-8'
print('login', login.status_code, flush=True)
login.raise_for_status()
token=login.json()['data']['token']
s.headers.update({'Authorization':f'Bearer {token}'})

folder=ROOT/safe(BOOK_NAME)
if folder.exists():
    import shutil; shutil.rmtree(folder)
folder.mkdir(parents=True, exist_ok=True)

j=s.get(BASE+'/chapters', params={'filter[book_id]':BOOK_ID,'page':1,'limit':100}, timeout=30)
j.encoding='utf-8'; j.raise_for_status()
chapters=(j.json().get('data') or [])
(folder/'chapters_manifest.json').write_text(json.dumps(chapters, ensure_ascii=False, indent=2), encoding='utf-8')
print('chapters', len(chapters), flush=True)
for idx,ch in enumerate(chapters,1):
    cid=ch.get('id')
    title=(ch.get('name') or f'Chương {idx}').strip()
    out=folder/f"{safe(title)}.txt"
    r=s.get(BASE+f'/chapters/{cid}', timeout=30)
    r.encoding='utf-8'; r.raise_for_status()
    data=r.json().get('data',{})
    cname=(data.get('name') or title).strip()
    body=clean_text(maybe_decrypt(data.get('content') or ''))
    out.write_text(f"{cname}\n\n{body}\n", encoding='utf-8')
    if idx<=3:
        print('sample_file', out.name)
        print(body[:300].replace('\n',' '))
    if idx%25==0 or idx==len(chapters):
        print(f'progress {idx}/{len(chapters)}', flush=True)
    time.sleep(DELAY)
print('done', folder, flush=True)
