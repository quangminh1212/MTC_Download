import requests,base64
HEAD={'User-Agent':'MTC/Android','Accept':'application/json'}
for cid in [13071362,13071370,13071381,13071383,13071385]:
    j=requests.get(f'https://android.lonoapp.net/api/chapters/{cid}',headers=HEAD,timeout=20).json()['data']['content']
    raw=base64.b64decode(j)
    a=raw.find(b'{"iv":"'); b=raw.find(b'","value":"'); c=raw.rfind(b'"}')
    iv=raw[a+7:b]
    print(cid,'iv_raw',iv)
    print('  prefix6',iv[:6],'tail18',iv[18:],'joined',(iv[:6]+iv[18:]))
