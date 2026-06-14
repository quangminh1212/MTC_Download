import base64, json, requests, re, hashlib, itertools, math
from pathlib import Path
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad

URL='https://android.lonoapp.net/api/chapters/13071362'
HEAD={'User-Agent':'MTC/Android','Accept':'application/json'}
BASE=b'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/='
VI_WORDS=['Tony','Tèo','bóng','đá','huấn luyện','trận đấu','cầu thủ','Chương','thằng','ông','không','được','và','là','của','một']

def get_payload():
    j=requests.get(URL,headers=HEAD,timeout=30).json()['data']['content']
    raw=base64.b64decode(j)
    a=raw.find(b'{"iv":"'); b=raw.find(b'","value":"'); c=raw.rfind(b'"}')
    return raw[a+7:b], raw[b+11:c]

def clean_iv_variants(ivraw):
    variants=[]
    # observed: positions 6..17 are non-b64 noise; keep first 6 + tail 18 => 24 b64 chars
    cuts=[(6,18),(5,17),(7,19),(0,12),(12,24)]
    for s,e in cuts:
        x=ivraw[:s]+ivraw[e:]
        variants.append(('cut_%d_%d'% (s,e),x))
    variants.append(('basechars', bytes([x for x in ivraw if x in BASE])))
    # all subsequences of length 24 preserving prefix/tail chunks likely too many; try sliding remove 12 bytes
    for s in range(0, len(ivraw)-11):
        variants.append((f'remove12@{s}', ivraw[:s]+ivraw[s+12:]))
    out=[]; seen=set()
    for name,x in variants:
        for pad in [b'', b'=', b'==', b'===']:
            try:
                d=base64.b64decode(x+pad, validate=False)
                if len(d)==16 and d not in seen:
                    seen.add(d); out.append((name,x,d))
            except Exception: pass
        if len(x)==16 and x not in seen:
            seen.add(x); out.append((name,x,x))
    return out

def score_text(b):
    try: t=b.decode('utf-8')
    except Exception: return -999, None
    if '\ufffd' in t: return -100, t
    printable=sum(1 for ch in t if ch.isprintable() or ch in '\r\n\t')/max(1,len(t))
    vi=sum(3 for w in VI_WORDS if w.lower() in t.lower())
    letters=sum(1 for ch in t[:2000] if ch.isalpha() or ch.isspace())/max(1,min(len(t),2000))
    return printable*100+letters*50+vi, t

def collect_candidates():
    blobs=[]
    for p in [r'C:\Dev\MTC_Download\mtc_extracted\lib\arm64-v8a\libapp.so', r'C:\Dev\MTC_Download\mtc_extracted\classes.dex', r'C:\Dev\MTC_Download\mtc_extracted\classes2.dex', r'C:\Dev\MTC_Download\mtc_extracted\classes3.dex']:
        pp=Path(p)
        if pp.exists(): blobs.append((p,pp.read_bytes()))
    cand=[]
    literals=['reader.or','reader.org','novelfever','lonoapp','android.lonoapp.net','api.lonoapp.net','MTC/Android','app_key','ChapterDao','aesDecrypt','decryptContent','getChapterDetailsEncrypt','com.novelfever.app.android','CFB-128','AES/CBC/PKCS7Padding','AES/CBC/PKCS5Padding']
    for lit in literals:
        sb=lit.encode()
        for k in [sb, hashlib.md5(sb).digest(), hashlib.sha1(sb).digest()[:16], hashlib.sha256(sb).digest(), hashlib.sha256(sb).digest()[:16], hashlib.sha256(sb).digest()[:24]]:
            cand.append(('lit',lit,k))
    for path,b in blobs:
        # printable strings near keywords and all lengths 16/24/32
        for m in re.finditer(rb'[\x20-\x7e]{4,96}', b):
            s=m.group()
            sl=s.lower()
            if any(k in sl for k in [b'key',b'aes',b'decrypt',b'reader',b'lono',b'novel',b'chapter',b'app']):
                ss=s.decode('latin1','ignore')
                raw=s
                if len(raw) in (16,24,32): cand.append(('str',ss,raw))
                for k in [hashlib.md5(raw).digest(), hashlib.sha1(raw).digest()[:16], hashlib.sha256(raw).digest(), hashlib.sha256(raw).digest()[:16], hashlib.sha256(raw).digest()[:24]]:
                    cand.append(('hashstr',ss,k))
        for m in re.finditer(rb'[0-9a-fA-F]{32,64}', b):
            h=m.group().decode()
            if len(h)%2==0:
                try:
                    hb=bytes.fromhex(h)
                    if len(hb) in (16,24,32): cand.append(('hex',h,hb))
                    cand += [('md5hex',h,hashlib.md5(h.encode()).digest()),('sha256hex',h,hashlib.sha256(h.encode()).digest())]
                except Exception: pass
    seen=set(); out=[]
    for typ,src,k in cand:
        if len(k) in (16,24,32) and k not in seen:
            seen.add(k); out.append((typ,src,k))
    return out

def try_all():
    ivraw,valb64=get_payload()
    ct=base64.b64decode(valb64)
    print('ivraw',ivraw,'len',len(ivraw),'ct',len(ct))
    ivs=clean_iv_variants(ivraw)
    print('ivs',[(n,x,len(d),d.hex()) for n,x,d in ivs[:20]],'total',len(ivs))
    keys=collect_candidates()
    print('keys',len(keys))
    modes=[]
    best=[]
    for iname,istr,iv in ivs:
        for typ,src,key in keys:
            attempts=[]
            for mode in ['CBC','CFB','CTR','OFB']:
                try:
                    if mode=='CBC': pt=AES.new(key,AES.MODE_CBC,iv).decrypt(ct)
                    elif mode=='CFB': pt=AES.new(key,AES.MODE_CFB,iv,segment_size=128).decrypt(ct)
                    elif mode=='OFB': pt=AES.new(key,AES.MODE_OFB,iv).decrypt(ct)
                    elif mode=='CTR':
                        from Crypto.Util import Counter
                        ctr=Counter.new(128, initial_value=int.from_bytes(iv,'big'))
                        pt=AES.new(key,AES.MODE_CTR,counter=ctr).decrypt(ct)
                    attempts.append((mode,pt))
                except Exception: pass
            for mode,pt in attempts:
                for label,buf in [('raw',pt)]:
                    bufs=[(label,buf)]
                    try: bufs.append(('unpad',unpad(buf,16)))
                    except Exception: pass
                    for lab,b in bufs:
                        sc,t=score_text(b[:5000])
                        if sc>120:
                            best.append((sc,mode,lab,iname,typ,src,key.hex(),t[:800]))
                            print('HIT?',sc,mode,lab,iname,typ,src,key.hex(),repr(t[:300]))
                            if any(w.lower() in t.lower() for w in ['tony','tèo','bóng','chương']):
                                Path('decrypt_success.txt').write_text(t,encoding='utf-8')
                                print('SUCCESS written decrypt_success.txt')
                                return
    best=sorted(best, reverse=True)[:20]
    print('BEST',len(best))
    for row in best: print(row[:7],repr(row[7][:300] if row[7] else ''))

if __name__=='__main__': try_all()
