import sys
from pathlib import Path
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
p = Path(r'C:\Dev\MTC_Download\download_one_completed_live_decrypt.py')
s = p.read_text(encoding='utf-8')
needle = """        try:\n            plain, decrypted = maybe_decrypt(content)\n            title = normalize_chapter_title(data.get('name') or ch.get('name') or f'Chương {i}', i)\n            write_plain_chapter(fpath, title, plain)\n            ok += 1\n            print(f'  OK decrypted={decrypted} written={fpath.name}', flush=True)\n"""
print('found=', needle in s)
