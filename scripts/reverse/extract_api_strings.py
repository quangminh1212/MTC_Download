import re
from pathlib import Path

b=Path(r'C:\Dev\MTC_Download\mtc_extracted\lib\arm64-v8a\libapp.so').read_bytes()
# printable strings only
for m in re.finditer(rb'[\x20-\x7e]{4,}', b):
    s=m.group().decode('latin1')
    if '/' in s and ('api' in s.lower() or 'chapter' in s.lower() or 'book' in s.lower() or 'key' in s.lower() or 'content' in s.lower()):
        if len(s) <= 180:
            print(m.start(), s)
