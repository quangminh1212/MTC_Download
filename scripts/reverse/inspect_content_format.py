import requests,base64
s=requests.Session(); s.headers.update({'User-Agent':'MTC/Android','Accept':'application/json'})
for cid in [13071362,13071363,13071364,13071365]:
    j=s.get(f'https://android.lonoapp.net/api/chapters/{cid}',timeout=20).json()['data']
    raw=base64.b64decode(j['content'])
    a=raw.find(b'{"iv":"')
    b=raw.find(b'","value":"')
    c=raw.rfind(b'"}')
    print('cid',cid,'rawlen',len(raw),'a,b,c',a,b,c)
    iv=raw[a+7:b] if a!=-1 and b!=-1 else b''
    val=raw[b+11:c] if b!=-1 and c!=-1 else b''
    print('iv_len',len(iv),'iv_printable_ratio',sum(32<=x<127 for x in iv)/max(1,len(iv)))
    print('iv_hex',iv.hex())
    print('val_len',len(val),'val_prefix',val[:50])
