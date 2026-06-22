import requests,base64
s=requests.Session(); s.headers.update({'User-Agent':'MTC/Android','Accept':'application/json'})
vals=[]
for i in range(40):
    j=s.get('https://android.lonoapp.net/api/chapters/13071362',timeout=20).json()['data']['content']
    raw=base64.b64decode(j)
    a=raw.find(b'{"iv":"'); b=raw.find(b'","value":"')
    iv=raw[a+7:b]
    vals.append(iv)
print('samples',len(vals),'lenset',sorted({len(v) for v in vals}))
base=set(b'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=')
for pos in range(36):
    bytes_at=[v[pos] for v in vals]
    ok=sum(1 for x in bytes_at if x in base)
    uniq=len(set(bytes_at))
    print(pos,'base%',round(ok/len(vals),2),'uniq',uniq,'vals',bytes_at[:8])
