from androguard.core.dex import DEX
from pathlib import Path
import re

def scan_dex(path):
    print('FILE',path)
    d=DEX(Path(path).read_bytes())
    needles=['decryptContent','aesDecrypt','getChapterDetailsEncrypt','CANNOT_DECODE_CONTENT_DATA','app_key','chapter_detail','chapters','iv','value']
    strings=d.get_strings()
    idxmap={s:i for i,s in enumerate(strings)}
    for needle in needles:
        hits=[(i,s) for i,s in enumerate(strings) if needle.lower() in s.lower()]
        print('\nNEEDLE',needle,'hits',len(hits))
        for i,s in hits[:20]:
            print(' string_idx',i,repr(s))
            lo=max(0,i-8); hi=min(len(strings),i+9)
            for j in range(lo,hi):
                print('   ',j,repr(strings[j]))
    print('\nmethods containing keywords')
    for m in d.get_methods():
        try:
            name=m.get_name(); cls=m.get_class_name(); desc=m.get_descriptor()
            full=(cls+'->'+name+desc).lower()
            if any(k in full for k in ['decrypt','encrypt','chapter','content','reader']):
                print(cls,name,desc)
        except Exception:
            pass

for p in [r'C:\Dev\MTC_Download\mtc_extracted\classes.dex', r'C:\Dev\MTC_Download\mtc_extracted\classes2.dex', r'C:\Dev\MTC_Download\mtc_extracted\classes3.dex']:
    scan_dex(p)
