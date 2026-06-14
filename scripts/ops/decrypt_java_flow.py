import requests, base64
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad

HEAD={'User-Agent':'MTC/Android','Accept':'application/json'}

def decrypt(cid):
    s=requests.get(f'https://android.lonoapp.net/api/chapters/{cid}',headers=HEAD,timeout=30).json()['data']['content']
    raw=base64.b64decode(s)
    a=raw.find(b'{"iv":"'); b=raw.find(b'","value":"'); c=raw.find(b'","mac"')
    if c==-1:
        c=raw.rfind(b'"}')
    iv_b64=raw[a+7:b]
    val_b64=raw[b+11:c]
    iv=AES.block_size
    iv=base64.b64decode(iv_b64)[:16]
    ct=base64.b64decode(val_b64)
    key=s.encode('ascii')[17:33]
    pt=AES.new(key,AES.MODE_CBC,iv).decrypt(ct)
    try:
        txt=unpad(pt,16).decode('utf-8')
    except Exception:
        txt=pt.decode('utf-8','replace')
    return key,iv,txt

for cid in [13071362,13071370,13071381]:
    try:
        key,iv,txt=decrypt(cid)
        print('CID',cid)
        print('KEY',key, key.hex())
        print('IV',iv.hex())
        print(txt[:1200])
        print('\n---\n')
    except Exception as e:
        print('CID',cid,'ERR',repr(e))
