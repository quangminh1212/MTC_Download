import re
from pathlib import Path

p=Path(r'C:\Dev\MTC_Download\mtc_extracted\lib\arm64-v8a\libapp.so')
b=p.read_bytes()
strings=[]
for m in re.finditer(rb'[\x20-\x7e]{4,}', b):
    s=m.group().decode('latin1')
    if any(k.lower() in s.lower() for k in ['decrypt','encrypt','aes','chapter','content','iv','value','mac','key','base64','novelfever','lonoapp','android.lonoapp']):
        strings.append((m.start(),s))
for off,s in strings[:1000]:
    print(off, s[:300])
