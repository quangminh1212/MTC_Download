import json
import sys
from pathlib import Path

from download_completed_to_mtc import MTCDownloader, clean_filename, chapter_filename, write_chapter, get_all_chapters

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

BOOK_ID = 127805
BOOK_NAME = 'Tiền Hạo Kiếp Tây Du'
BOOK_DIR = Path(r'C:\Dev\MTC') / BOOK_NAME

def main():
    d = MTCDownloader()
    BOOK_DIR.mkdir(parents=True, exist_ok=True)
    chapters = get_all_chapters(d, BOOK_ID)
    print(f'total_chapters={len(chapters)}')
    wrote = 0
    missing = 0
    for i, ch in enumerate(chapters, 1):
        fname = chapter_filename(ch, i)
        fpath = BOOK_DIR / fname
        if fpath.exists() and fpath.stat().st_size > 200:
            continue
        missing += 1
        cid = ch.get('id')
        detail = d.get_chapter_content(cid)
        data = (detail or {}).get('data') or {}
        content = data.get('content') or data.get('body') or ''
        if not content:
            print(f'miss_content: index={i} chapter_id={cid} file={fname}')
            continue
        display_name = data.get('name') or ch.get('name') or f'Chương {i}'
        write_chapter(fpath, BOOK_NAME, display_name, content)
        wrote += 1
        print(f'wrote: {fname}')
    print(f'missing_checked={missing}')
    print(f'wrote_total={wrote}')

if __name__ == '__main__':
    main()
