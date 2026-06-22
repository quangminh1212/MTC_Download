import base64, requests, hashlib, re
from pathlib import Path
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad
from Crypto.Util import Counter
HEAD={'User-Agent':'MTC/Android','Accept':'application/json'}
blob1='04925be9fb01afc6fb4d3e7d4990010f813408ab106c4f09cb7ee07868cc136fff3357f624a21bed5263ba3a7a27483ebf6671dbef7abb30ebee084e58a0b077ad42a5a0989d1ee71b1b9bc0455fb0d2c3'
blob2='d35e472036bc4fb7e13c785ed201e065f98fcfa6f6f40def4f92b9ec7893ec28fcd412b1f1b32e27'

def payload(cid):
    j=requests.get(f'https://android.lonoapp.net/api/chapters/{cid}',headers=HEAD,timeout=30).json()['data']['content']
    raw=base64.b64decode(j + '='*((4-len(j)%4)%4))
    a=raw.find(b'{"iv":"'); b=raw.find(b'","value":"'); c=raw.rfind(b'"}')
    ivraw=raw[a+7:b]; val=raw[b+11:c]
    iv=base64.b64decode(ivraw[:6]+ivraw[18:])
    ct=base64.b64decode(val + b'='*((4-len(val)%4)%4))
    return iv,ct

def score(buf):
    for trans in [lambda x:x, lambda x:base64.b64decode(x+ b'='*((4-len(x)%4)%4)) if re.fullmatch(rb'[A-Za-z0-9+/=\r\n]+', x[:200]) else b'']:
        try: b=trans(buf)
        except: continue
        for u in [False, True]:
            try:
                x=unpad(b,16) if u else b
                t=x[:5000].decode('utf-8')
            except: continue
            low=t.lower()
            sc=sum(w in low for w in ['tony','tèo','bóng','không','được','chương','trận','huấn luyện'])*20 + sum(ch.isalpha() or ch.isspace() for ch in t[:1000])/10
            if sc>120: return sc,t
    return -1,None

def key_candidates():
    c=[]
    raw_hexes=[blob1,blob2]
    # split blobs every 16/24/32 bytes windows over hex bytes
    for h in raw_hexes:
        hb=bytes.fromhex(h)
        for n in [16,24,32]:
            for i in range(0,len(hb)-n+1): c.append((f'blobwin{n}@{i}',h,hb[i:i+n]))
        for material in [h.encode(), hb, base64.b64encode(hb)]:
            c += [('md5',h,hashlib.md5(material).digest()),('sha1-16',h,hashlib.sha1(material).digest()[:16]),('sha256',h,hashlib.sha256(material).digest()),('sha256-16',h,hashlib.sha256(material).digest()[:16]),('sha256-24',h,hashlib.sha256(material).digest()[:24])]
    literals=['QeiqkD56tI2QTBZP','reader.or','app_key','lonoapp','novelfever','android.lonoapp.net','generateSign','_signPrefix','_signSuffix','X-Signature']
    for s in literals:
        b=s.encode();
        if len(b) in [16,24,32]: c.append(('literal',s,b))
        c += [('md5lit',s,hashlib.md5(b).digest()),('sha256lit',s,hashlib.sha256(b).digest()),('sha256lit16',s,hashlib.sha256(b).digest()[:16]),('sha256lit24',s,hashlib.sha256(b).digest()[:24])]
    seen=set(); out=[]
    for a,b,k in c:
        if len(k) in [16,24,32] and k not in seen:
            seen.add(k); out.append((a,b,k))
    return out

iv,ct=payload(13071362)
print('iv',iv.hex(),'ct',len(ct),'keys',len(key_candidates()))
for name,src,key in key_candidates():
    for mode in ['CBC','CFB8','CFB128','OFB','CTR']:
        try:
            if mode=='CBC': pt=AES.new(key,AES.MODE_CBC,iv).decrypt(ct)
            elif mode=='CFB8': pt=AES.new(key,AES.MODE_CFB,iv,segment_size=8).decrypt(ct)
            elif mode=='CFB128': pt=AES.new(key,AES.MODE_CFB,iv,segment_size=128).decrypt(ct)
            elif mode=='OFB': pt=AES.new(key,AES.MODE_OFB,iv).decrypt(ct)
            elif mode=='CTR':
                ctr=Counter.new(128, initial_value=int.from_bytes(iv,'big'))
                pt=AES.new(key,AES.MODE_CTR,counter=ctr).decrypt(ct)
            sc,t=score(pt)
            if sc>120:
                print('FOUND',sc,name,src[:80],mode,key.hex())
                print(t[:1000])
                Path('decrypt_success.txt').write_text(t,encoding='utf-8')
                raise SystemExit
        except Exception: pass
print('not found')
