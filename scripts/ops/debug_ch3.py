from mtc_downloader import MTCDownloader
import base64, re, sys
if hasattr(sys.stdout,'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
d=MTCDownloader()
r=d.get_chapter_content(14318241)
data=(r or {}).get('data') or {}
c=(data.get('content') or data.get('body') or '').strip()
print('name', data.get('name'))
print('len', len(c))
print('is_b64', bool(re.fullmatch(r'[A-Za-z0-9+/=]+', c)))
raw=base64.b64decode(c + '='*((4-len(c)%4)%4))
print('has_markers', b'"iv":"' in raw, b'"value":"' in raw)
print(raw[:120])
