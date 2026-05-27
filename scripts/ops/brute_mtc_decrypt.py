import re, base64, json, requests, hashlib
from pathlib import Path
try:
    from Crypto.Cipher import AES
    from Crypto.Util.Padding import unpad
except Exception as e:
    print('NO_CRYPTO', e); raise

b=Path(r'C:\Dev\MTC_Download\mtc_extracted\lib\arm64-v8a\libapp.so').read_bytes()
# hex constants likely keys/signatures
hexes=sorted(set(m.group().decode() for m in re.finditer(rb'[0-9a-f]{32,128}', b)), key=len)
texts=[]
for m in re.finditer(rb'[\x20-\x7e]{6,80}', b):
    s=m.group().decode('latin1')
    if any(k in s.lower() for k in ['reader','app_key','novelfever','lonoapp','key','secret']):
        texts.append(s)

r=requests.get('https://android.lonoapp.net/api/chapters/13071362',headers={'User-Agent':'MTC/Android','Accept':'application/json'},timeout=20).json()
raw=base64.b64decode(r['data']['content'])
a=raw.find(b'{"iv":"'); bpos=raw.find(b'","value":"'); c=raw.rfind(b'"}')
iv_raw=raw[a+7:bpos]
val_b64=raw[bpos+11:c]
# iv field is polluted with non-base64 bytes; keep valid base64 chars
iv_clean=iv_raw[:6] + iv_raw[18:]
value=base64.b64decode(val_b64)
ivs=[]
for ivs_b in [iv_raw, iv_clean]:
    try:
        d=base64.b64decode(ivs_b + b'=' * ((4 - len(ivs_b) % 4) % 4), validate=False)
        if len(d)==16: ivs.append(('b64',d))
    except Exception: pass
    if len(ivs_b)==16: ivs.append(('raw',ivs_b))
print('iv_raw',iv_raw, 'iv_clean', iv_clean, 'ivs', [(n,len(v)) for n,v in ivs], 'value',len(value), 'hexes',len(hexes))

candidates=[]
for h in hexes:
    if len(h) % 2:
        continue
    hb=bytes.fromhex(h)
    if len(hb) in (16,24,32): candidates.append(('hex',h,hb))
    for digest in [hashlib.md5(h.encode()).digest(), hashlib.sha256(h.encode()).digest()]:
        candidates.append(('hashhex',h,digest[:16] if len(digest)>=16 else digest))
        candidates.append(('hashhex256',h,digest[:32] if len(digest)>=32 else digest))
for s in texts:
    sb=s.encode('utf-8','ignore')
    if len(sb) in (16,24,32): candidates.append(('str',s,sb))
    candidates.append(('md5str',s,hashlib.md5(sb).digest()))
    candidates.append(('sha256str',s,hashlib.sha256(sb).digest()))
# common from nearby string
for s in ['reader.or','reader.org','novelfever','lonoapp','android.lonoapp.net','app_key']:
    sb=s.encode()
    candidates += [('md5lit',s,hashlib.md5(sb).digest()),('sha256lit',s,hashlib.sha256(sb).digest())]

seen=set(); uniq=[]
for typ,src,k in candidates:
    if len(k) not in (16,24,32): continue
    kk=(k,src[:40])
    if kk not in seen:
        seen.add(kk); uniq.append((typ,src,k))
print('candidates',len(uniq))
for iname,iv in ivs:
  for mode in ['CBC']:
    for typ,src,key in uniq:
      try:
        pt=AES.new(key,AES.MODE_CBC,iv).decrypt(value)
        for final in [pt]:
          try: txt=unpad(final,16).decode('utf-8')
          except Exception:
            try: txt=final.decode('utf-8')
            except Exception: continue
          low=txt.lower()
          if any(w in low for w in ['tony','tèo','bóng','huấn luyện','trận đấu','chương']):
            print('FOUND',iname,typ,src,'keyhex',key.hex())
            print(txt[:1000])
            raise SystemExit
      except Exception: pass
print('NOT_FOUND')
print('sample hex constants:')
for h in hexes[:80]: print(len(h),h)
