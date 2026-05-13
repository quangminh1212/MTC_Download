import requests, hashlib, itertools
URLS=[
    'https://android.lonoapp.net/api/setting',
    'https://android.lonoapp.net/api/settings',
    'https://api.lonoapp.net/api/setting',
    'https://api.lonoapp.net/api/settings',
]
HEAD={'User-Agent':'MTC/Android','Accept':'application/json'}
blob1='04925be9fb01afc6fb4d3e7d4990010f813408ab106c4f09cb7ee07868cc136fff3357f624a21bed5263ba3a7a27483ebf6671dbef7abb30ebee084e58a0b077ad42a5a0989d1ee71b1b9bc0455fb0d2c3'
blob2='d35e472036bc4fb7e13c785ed201e065f98fcfa6f6f40def4f92b9ec7893ec28fcd412b1f1b32e27'
seeds=['1','test','abc123','android','MTC','novelfever','lonoapp',blob1,blob2]
vals=[]
for s in seeds:
    vals += [s, hashlib.md5(s.encode()).hexdigest(), hashlib.sha1(s.encode()).hexdigest(), hashlib.sha256(s.encode()).hexdigest()]
seen=[]
for x in vals:
    if x not in seen: seen.append(x)
vals=seen
for u in URLS:
    print('\nURL',u)
    # plain
    for kind,headers,params in [
        ('plain',HEAD,{}),
        ('sign-param',HEAD,{'sign':'1'}),
    ]:
        try:
            r=requests.get(u,headers=headers,params=params,timeout=20)
            print(kind,r.status_code,r.text[:300])
        except Exception as e:
            print(kind,'ERR',e)
    # brute some sign headers/params
    for sig in vals[:40]:
        tries=[
            ({**HEAD,'X-Signature':sig},{}),
            (HEAD,{'sign':sig}),
            ({**HEAD,'X-Signature':sig,'sign':sig},{}),
        ]
        for headers,params in tries:
            try:
                r=requests.get(u,headers=headers,params=params,timeout=15)
                txt=r.text[:250]
                if r.status_code!=404 and 'Không tìm thấy tài nguyên chỉ định' not in txt:
                    print('HIT',sig[:24],r.status_code,params,txt)
                    raise SystemExit
            except Exception:
                pass
print('DONE')
