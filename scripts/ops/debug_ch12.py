from mtc_downloader import MTCDownloader
from download_one_completed_live_decrypt import maybe_decrypt, clean_text, normalize_chapter_title
import sys
if hasattr(sys.stdout,'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

d=MTCDownloader()
r=d.get_chapter_content(14326584)
data=(r or {}).get('data') or {}
content=(data.get('content') or data.get('body') or '')
plain,decrypted=maybe_decrypt(content)
print('title=', normalize_chapter_title(data.get('name'), 12))
print('decrypted=', decrypted)
print('plain_prefix=')
print(plain[:1200])
print('--- cleaned prefix ---')
print(clean_text(plain)[:1200])
