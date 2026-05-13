from pathlib import Path
for path in [r'C:\Dev\MTC_Download\mtc_extracted\classes.dex', r'C:\Dev\MTC_Download\mtc_extracted\lib\arm64-v8a\libapp.so']:
    b=Path(path).read_bytes()
    for pat in [b'","mac"', b'"mac"', b'app_key', b'reader.or', b'CFB-128', b'aesDecrypt', b'deserializeContent']:
        i=b.find(pat)
        print('FILE',path,'PAT',pat,'OFF',i)
        if i!=-1:
            s=max(0,i-220); e=min(len(b),i+420)
            chunk=b[s:e]
            txt=''.join(chr(x) if 32<=x<127 else '\n' for x in chunk)
            print(txt)
            print('---')
