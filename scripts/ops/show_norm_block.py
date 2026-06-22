import sys
from pathlib import Path
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
p = Path(r'C:\Dev\MTC_Download\download_one_completed_live_decrypt.py')
s = p.read_text(encoding='utf-8')
start = s.index('def normalize_chapter_title(')
end = s.index('def write_plain_chapter(')
print(s[start:end])
