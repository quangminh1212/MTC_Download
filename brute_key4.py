'''
brute_key4.py - FIXED CT extraction.
outer format: {"iv":"<36b>","value":"<b64ct>","mac":"<hex>","tag":""}
Use find('"', vs) to correctly terminate the value field.
'''
import base64, sys, time, requests
from pathlib import Path
from multiprocessing import Pool, cpu_count
from Crypto.Cipher import AES

LIBAPP = r'C:\Dev\MTC_Download\libapp_extracted\libapp.so'
CHAPTER_ID = 21589884

_lib=None; _iv16=None; _ct=None; _last=None; _prev=None

def init(iv_hex, ct_hex):
    global _lib,_iv16,_ct,_last,_prev
    _lib=Path(LIBAPP).read_bytes()
    _iv16=bytes.fromhex(iv_hex); _ct=bytes.fromhex(ct_hex)
    _last=_ct[-16:]; _prev=_ct[-32:-16]

def scan(args):
    start,end,ks=args; res=[]; cnt=0
    lib=_lib; last=_last; prev=_prev; iv=_iv16; ct=_ct
    for i in range(start,end):
        k=lib[i:i+ks]; cnt+=1
        try: raw=AES.new(k,AES.MODE_ECB).decrypt(last)
        except: continue
        pl=bytes(a^b for a,b in zip(raw,prev)); n=pl[-1]
        if n<1 or n>16: continue
        if not all(b==n for b in pl[-n:]): continue
        try:
            pt=AES.new(k,AES.MODE_CBC,iv).decrypt(ct)
            p=pt[-1]
            if p<1 or p>16: continue
            if not all(b==p for b in pt[-p:]): continue
            txt=pt[:-p].decode('utf-8')
        except: continue
        if sum(1 for c in txt if ord(c)>127)<10: continue
        res.append((i,bytes(k),txt[:200]))
    return res,cnt

def fetch():
    r=requests.get(f'https://android.lonoapp.net/api/chapters/{CHAPTER_ID}',timeout=15)
    outer=base64.b64decode(r.json()['data']['content']+'==')
    sep=b'","value":"'; pos=outer.find(sep); vs=pos+len(sep)
    ct_end=outer.find(b'"',vs)  # FIXED: stop at first " after value
    iv16=outer[7:23]
    ct=base64.b64decode(outer[vs:ct_end]+b'==')
    print(f'  outer len:{len(outer)}  sep@{pos}  iv_field:{len(outer[7:pos])}B  ct_end:{ct_end}  ct:{len(ct)}B  ct%16={len(ct)%16}')
    return iv16,ct

if __name__=='__main__':
    sz=Path(LIBAPP).stat().st_size; print(f'lib:{sz:,}B')
    print('Fetching chapter...')
    iv,ct=fetch()
    print(f'IV:{iv.hex()}  CT_len:{len(ct)}')
    n=max(1,cpu_count()-1); print(f'workers:{n}')
    t0=time.time()
    for ks in [16,24,32]:
        tot=sz-ks+1; print(f'\n{ks}B: {tot:,} pos')
        chunk=max(1,tot//n)
        tasks=[(c*chunk,tot if c==n-1 else (c+1)*chunk,ks) for c in range(n)]
        found=[]; chk=0
        with Pool(n,initializer=init,initargs=(iv.hex(),ct.hex())) as p:
            for r2,c2 in p.imap_unordered(scan,tasks):
                chk+=c2; found.extend(r2)
        t1=time.time()-t0
        print(f'  {t1:.1f}s  {chk/t1:,.0f}/s')
        for off,k,tx in found:
            print(f'  KEY[{ks}B] 0x{off:08x} hex={k.hex()}'); print(f'  text:{tx}')
        if not found: print('  not found')
    print(f'TOTAL:{time.time()-t0:.1f}s')
