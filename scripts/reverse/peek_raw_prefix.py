import requests,base64
s=requests.Session(); s.headers.update({'User-Agent':'MTC/Android','Accept':'application/json'})
for i in range(10):
    j=s.get('https://android.lonoapp.net/api/chapters/13071362',timeout=20).json()['data']['content']
    raw=base64.b64decode(j)
    print('--- sample',i,'len',len(raw))
    print('first 120 hex:', raw[:120].hex())
    print('first 120 repr:', raw[:120])
