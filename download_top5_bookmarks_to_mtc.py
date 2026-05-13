#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json, re, sys, time, base64, html
from pathlib import Path
import requests
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad

EMAIL=sys.argv[1]
PASSWORD=sys.argv[2]
ROOT=Path(r'C:\Dev\MTC')
BASE='https://android.lonoapp.net/api'
TOP_N=int(sys.argv[3]) if len(sys.argv)>3 else 5
DELAY=float(sys.argv[4]) if len(sys.argv)>4 else 0.2
MANIFEST=Path(r'C:\Dev\MTC_Download\logs\bookmarked_books_manifest.json')
LOG=Path(r'C:\Dev\MTC_Download\logs\download_top_bookmarks_to_mtc.json')

INVALID='<>:"/\\|?*[]()'
TAG_RE = re.compile(r'<[^>]+>')
WS_RE = re.compile(r'[ \t\r\f\v]+')
PAYLOAD_RE = re.compile(r'^[A-Za-z0-9+/=]+$')
MARKER_RE = re.compile(r'eyJpdiI6|"iv":"|"value":"')

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
    name=name.replace('+',' ')
    name=re.sub(r'[-–—]+',' ',name)
    name=re.sub(r'\s+',' ',name).strip().rstrip('.')
    return name[:170] or 'unknown'

def chapter_filename(idx, title):
    t = safe(title)
    return f'{t}.txt' if t else f'Chuong {idx}.txt'

def get_json(session, url, params=None, retries=4):
    for i in range(retries):
        try:
            r=session.get(url, params=params, timeout=35)
            r.encoding='utf-8'
            if r.status_code==429:
                time.sleep(3+i*2)
                continue
            r.raise_for_status()
            return r.json()
        except Exception:
            if i==retries-1: raise
            time.sleep(2+i*2)

ROOT.mkdir(parents=True, exist_ok=True)
books=json.loads(MANIFEST.read_text(encoding='utf-8'))['books'][:TOP_N]
s=requests.Session()
s.headers.update({'User-Agent':'MTC/Android','Accept':'application/json','Content-Type':'application/json'})
login=s.post(BASE+'/auth/login', json={'email':EMAIL,'password':PASSWORD,'device_name':'OpenClaw Windows'}, timeout=30)
login.encoding='utf-8'
print('login', login.status_code, flush=True)
login.raise_for_status()
token=login.json()['data']['token']
s.headers.update({'Authorization':f'Bearer {token}'})
report=[]
for bi,b in enumerate(books,1):
    bid=int(b['id'])
    name=b['name']
    folder=ROOT/safe(name)
    folder.mkdir(parents=True, exist_ok=True)
    print(f'[{bi}/{len(books)}] {bid} {name}', flush=True)
    detail=get_json(s, BASE+f'/books/{bid}')
    (folder/'info.json').write_text(json.dumps(detail.get('data',detail), ensure_ascii=False, indent=2), encoding='utf-8')
    chapters_json=get_json(s, BASE+'/chapters', params={'filter[book_id]':bid,'page':1,'limit':100})
    chapters=chapters_json.get('data') or []
    (folder/'chapters_manifest.json').write_text(json.dumps(chapters, ensure_ascii=False, indent=2), encoding='utf-8')
    ok=0; fail=[]
    for idx,ch in enumerate(chapters,1):
        cid=ch.get('id')
        title=(ch.get('name') or '').strip()
        out=folder/chapter_filename(idx, title)
        if out.exists() and out.stat().st_size>20:
            ok+=1
            continue
        try:
            cj=get_json(s, BASE+f'/chapters/{cid}')
            data=cj.get('data',{})
            cname=(data.get('name') or title or f'Chuong {idx}').strip()
            encrypted = data.get('content') or ''
            content = clean_text(maybe_decrypt(encrypted))
            text=f"{cname}\n\n{content}\n"
            if MARKER_RE.search(text):
                raise ValueError('encrypted marker remains after decrypt')
            out.write_text(text, encoding='utf-8')
            ok+=1
        except Exception as e:
            fail.append({'index':idx,'id':cid,'name':title,'error':str(e)[:300]})
        if idx%25==0 or idx==len(chapters):
            print(f'  chapters {idx}/{len(chapters)} ok={ok} fail={len(fail)}', flush=True)
        time.sleep(DELAY)
    report.append({'id':bid,'name':name,'folder':str(folder),'expected':len(chapters),'ok':ok,'fail':len(fail)})
    LOG.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
print('done', flush=True)
