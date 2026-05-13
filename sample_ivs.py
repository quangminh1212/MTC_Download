import requests,base64
s=requests.Session(); s.headers.update({'User-Agent':'MTC/Android','Accept':'application/json'})
for i in range(8):
    j=s.get('https://android.lonoapp.net/api/chapters/13071362',timeout=20).json()['data']['content']
    raw=base64.b64decode(j)
    a=raw.find(b'{"iv":"'); b=raw.find(b'","value":"')
    iv=raw[a+7:b]
    base=b'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/='
    bad=[(k,x) for k,x in enumerate(iv) if x not in base]
    print('len',len(iv),'bad',len(bad),'badpos',bad[:12])
    print(iv)
