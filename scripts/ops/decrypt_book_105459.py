import requests, base64, json, os, re
from pathlib import Path
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad

API='https://android.lonoapp.net/api'
HEAD={'User-Agent':'MTC/Android','Accept':'application/json'}
BOOK_ID=105459
OUT_DIR=Path(r'C:\Dev\MTC\Siêu Dự Bị')
OUT_DIR.mkdir(parents=True, exist_ok=True)


def b64d(data):
    if isinstance(data,str):
        data=data.encode('ascii','ignore')
    data=data.strip()
    data += b'=' * ((4 - len(data) % 4) % 4)
    return base64.b64decode(data)


def safe_name(s):
    s=s.strip()
    s=re.sub(r'[\\/:*?"<>|]+',' ',s)
    s=re.sub(r'\s+',' ',s)
    return s[:180]


def decrypt_content_field(content_b64):
    # Java flow from DownloadAllActivity$4.decryptContent
    content_bytes_ascii=content_b64.encode('ascii','ignore')
    raw=b64d(content_b64)

    p_iv_start=b'"iv":"'
    p_iv_end=b'","value":"'
    p_val_start=b'"value":"'
    p_val_end=b'","mac"'

    a=raw.find(p_iv_start)
    b=raw.find(p_iv_end)
    if a<0 or b<0:
        return None, 'no iv marker'
    iv_b64=raw[a+len(p_iv_start):b]

    c=raw.find(p_val_start)
    if c<0:
        return None, 'no value marker'
    c += len(p_val_start)
    d=raw.find(p_val_end, c)
    if d<0:
        d=raw.rfind(b'"}')
        if d<0:
            return None, 'no value end marker'
    val_b64=raw[c:d]

    iv_raw=b64d(iv_b64)
    iv16=iv_raw[:16]

    value_raw=b64d(val_b64)

    # key = 16 bytes from content ascii at offset 17 (from reversed Java)
    if len(content_bytes_ascii) < 33:
        return None, 'content too short for key slice'
    key=content_bytes_ascii[17:33]

    cipher=AES.new(key, AES.MODE_CBC, iv16)
    pt=cipher.decrypt(value_raw)
    try:
        pt=unpad(pt,16)
    except Exception:
        pass

    # decode robustly
    text=None
    for enc in ('utf-8','utf-8-sig','cp1258','latin1'):
        try:
            t=pt.decode(enc)
            text=t
            break
        except Exception:
            continue
    if text is None:
        text=pt.decode('utf-8','replace')

    # cleanup some leading binary garbage if present
    text=text.replace('\x00','')
    text=text.lstrip('\ufeff').strip()

    return text, None


def fetch_chapters(book_id):
    url=f'{API}/chapters?filter%5Bbook_id%5D={book_id}&filter%5Btype%5D=published&limit=50000'
    r=requests.get(url,headers=HEAD,timeout=30)
    r.raise_for_status()
    data=r.json().get('data') or []
    # API ignores page/limit and returns full list; de-dupe by id.
    seen=set(); out=[]
    for ch in data:
        cid=ch.get('id')
        if cid in seen:
            continue
        seen.add(cid); out.append(ch)
    return out


def fetch_chapter_detail(cid):
    r=requests.get(f'{API}/chapters/{cid}',headers=HEAD,timeout=30)
    r.raise_for_status()
    return r.json().get('data') or {}


def main():
    chapters=fetch_chapters(BOOK_ID)
    chapters=sorted(chapters,key=lambda x:(x.get('index') or 0, x.get('id') or 0))

    ok=0
    fail=0
    report=[]
    for ch in chapters:
        cid=ch.get('id')
        idx=ch.get('index')
        name=ch.get('name') or f'Chapter {cid}'
        try:
            detail=fetch_chapter_detail(cid)
            content_b64=detail.get('content')
            if not content_b64:
                fail+=1
                report.append((cid,idx,name,'no content'))
                print('FAIL',cid,name,'no content', flush=True)
                continue
            text,err=decrypt_content_field(content_b64)
            if err or not text:
                fail+=1
                report.append((cid,idx,name,err or 'empty text'))
                print('FAIL',cid,name,err or 'empty text', flush=True)
                continue

            fname=f'Chương {idx} {safe_name(name)}.txt' if idx is not None else f'Chương {cid} {safe_name(name)}.txt'
            out=OUT_DIR / fname
            out.write_text(text,encoding='utf-8')
            ok+=1
            report.append((cid,idx,name,f'OK -> {out.name} ({len(text)} chars)'))
            print('OK',cid,name,out.name, len(text), flush=True)
        except Exception as e:
            fail+=1
            report.append((cid,idx,name,f'ERR {e}'))
            print('ERR',cid,name,repr(e), flush=True)
            continue

    rep=OUT_DIR / '_decrypt_report.txt'
    with rep.open('w',encoding='utf-8') as f:
        f.write(f'Book {BOOK_ID}: ok={ok}, fail={fail}\n')
        for row in report:
            f.write(str(row)+'\n')

    print(f'DONE ok={ok} fail={fail} report={rep}', flush=True)

if __name__=='__main__':
    main()
