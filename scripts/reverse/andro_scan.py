from androguard.misc import AnalyzeAPK, AnalyzeDex
from pathlib import Path
import sys, re
apk=Path(r'C:\Dev\MTC_Download\MTC.apk')
print('loading apk', apk)
a,d,dx=AnalyzeAPK(str(apk))
needles=['decryptContent','aesDecrypt','getChapterDetailsEncrypt','CANNOT_DECODE_CONTENT_DATA','app_key','chapter_detail','chapters']
for needle in needles:
    print('\n=== NEEDLE',needle,'===')
    hits=[]
    # strings
    for s in dx.get_strings():
        val=s.get_value()
        if needle.lower() in val.lower():
            hits.append(('string',val,s))
            print('STRING',repr(val))
            for xref in s.get_xref_from():
                try:
                    cls=xref[0].get_class_name(); meth=xref[1].get_name(); desc=xref[1].get_descriptor()
                    print('  from',cls,meth,desc)
                except Exception as e: print('  xref?',xref,e)
    if not hits:
        print('no string hits')

print('\n=== methods named decrypt/content/aes ===')
for m in dx.get_methods():
    mm=m.get_method()
    name=mm.get_name(); cls=mm.get_class_name()
    full=(cls+'->'+name+mm.get_descriptor()).lower()
    if any(k in full for k in ['decrypt','aes','chapter','content']):
        print(cls, name, mm.get_descriptor())
