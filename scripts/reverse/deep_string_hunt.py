from pathlib import Path
import re
paths=[
 r'C:\Dev\MTC_Download\mtc_extracted\classes.dex',
 r'C:\Dev\MTC_Download\mtc_extracted\classes2.dex',
 r'C:\Dev\MTC_Download\mtc_extracted\classes3.dex',
 r'C:\Dev\MTC_Download\mtc_extracted\lib\arm64-v8a\libapp.so',
]
keywords=['lonoapp','novelfever','/api/','chapter','content','decrypt','encrypt','app_key','key','setting','settings','sign','signature','token','reader','mac','iv','value']
for p in paths:
    b=Path(p).read_bytes()
    print('\n===',p,'===')
    found=[]
    for m in re.finditer(rb'[\x20-\x7e]{6,220}', b):
        s=m.group().decode('latin1','ignore')
        sl=s.lower()
        if any(k in sl for k in keywords):
            found.append((m.start(),s))
    # prioritize endpoint-like strings
    rank=[]
    for off,s in found:
        sl=s.lower()
        score=0
        if 'http' in sl: score+=10
        if '/api/' in sl: score+=8
        if 'setting' in sl: score+=6
        if 'sign' in sl: score+=6
        if 'app_key' in sl: score+=7
        if 'decrypt' in sl or 'encrypt' in sl: score+=5
        if 'chapter' in sl: score+=5
        if 'mac' in sl or 'iv' in sl or 'value' in sl: score+=4
        rank.append((score,off,s))
    rank=sorted(rank,key=lambda x:(-x[0],x[1]))
    for sc,off,s in rank[:400]:
        print(f'[{sc:02d}] {off} {s[:220]}')
