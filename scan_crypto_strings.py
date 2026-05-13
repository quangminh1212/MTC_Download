from pathlib import Path
import re
for path in [r'C:\Dev\MTC_Download\mtc_extracted\lib\arm64-v8a\libapp.so', r'C:\Dev\MTC_Download\mtc_extracted\classes.dex', r'C:\Dev\MTC_Download\mtc_extracted\classes2.dex', r'C:\Dev\MTC_Download\mtc_extracted\classes3.dex']:
    b=Path(path).read_bytes(); print('\nFILE',path)
    pats=[b'AES',b'aes',b'CBC',b'CFB',b'PKCS',b'pointycastle',b'encrypt',b'decrypt',b'app_key',b'iv',b'value',b'ChapterDao',b'content_page',b'flutter_secure']
    for pat in pats:
        offs=[]; start=0
        while True:
            i=b.find(pat,start)
            if i<0: break
            offs.append(i); start=i+1
            if len(offs)>=20: break
        if offs: print(pat, offs[:20])
    count=0
    for m in re.finditer(rb'[\x20-\x7e]{3,160}', b):
        s=m.group().decode('latin1','ignore')
        if any(k in s.lower() for k in ['aes','cipher','cbc','cfb','pkcs','pointycastle','encrypt','decrypt','app_key','secret','iv','value','chapterdao','content_page']):
            print(m.start(), repr(s[:160]))
            count+=1
            if count>300: break
