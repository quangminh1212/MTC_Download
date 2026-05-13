from pathlib import Path
b=Path(r'C:\Dev\MTC_Download\mtc_extracted\lib\arm64-v8a\libapp.so').read_bytes()
for pat in [b'generateSign', b'_signPrefix', b'_signSuffix', b'X-Signature', b'/setting?sign=', b'/setting', b'?sign=', b'getChapterDetailsEncrypt', b'_getChapterDetails', b'chapterDetails', b'AES encryption key null or is empty.', b'AES encryption key is null or empty.', b'_decryptBlock', b'aesDecryptBlock', b'decryptContent']:
    i=b.find(pat)
    print('\nPAT',pat,'OFF',i)
    if i!=-1:
        s=max(0,i-900); e=min(len(b),i+1400)
        chunk=b[s:e]
        txt=''.join(chr(x) if 32<=x<127 else '\n' for x in chunk)
        print(txt)
