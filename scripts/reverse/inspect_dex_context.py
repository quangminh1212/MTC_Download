from pathlib import Path
b=Path(r'C:\Dev\MTC_Download\mtc_extracted\classes.dex').read_bytes()
for pat in [b'decryptContent',b'https://android.lonoapp.net/api/chapters/',b'KEY_APP_KEY',b'"iv":"',b'","value":"']:
    i=b.find(pat)
    print('PAT',pat,'OFF',i)
    if i!=-1:
        s=max(0,i-500); e=min(len(b),i+1200)
        chunk=b[s:e]
        txt=''.join(chr(x) if 32<=x<127 else '\n' for x in chunk)
        print(txt)
        print('---')
