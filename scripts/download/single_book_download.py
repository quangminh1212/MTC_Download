import sys
from pathlib import Path
from download_completed_to_mtc import MTCDownloader, get_all_chapters, chapter_filename, write_chapter, clean_filename

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

BOOK_ID = 127805
OUT_ROOT = Path(r'C:\Dev\MTC_single')

def main():
    d = MTCDownloader()
    detail = d.get_book_detail(BOOK_ID)
    book = (detail or {}).get('data') or {}
    name = clean_filename(book.get('name') or f'book_{BOOK_ID}')
    book_dir = OUT_ROOT / name
    book_dir.mkdir(parents=True, exist_ok=True)
    (book_dir / 'info.json').write_text(__import__('json').dumps(book, ensure_ascii=False, indent=2), encoding='utf-8')
    chapters = get_all_chapters(d, BOOK_ID)
    print(f'book={name}')
    print(f'chapters_total={len(chapters)}')
    ok = 0
    miss = 0
    for i, ch in enumerate(chapters, 1):
        cid = ch.get('id')
        detail = d.get_chapter_content(cid)
        data = (detail or {}).get('data') or {}
        content = data.get('content') or data.get('body') or ''
        if not content:
            miss += 1
            print(f'miss: {i} id={cid}')
            continue
        display_name = data.get('name') or ch.get('name') or f'Chương {i}'
        fname = chapter_filename(ch, i)
        write_chapter(book_dir / fname, name, display_name, content)
        ok += 1
        if ok % 10 == 0 or ok == len(chapters):
            print(f'ok={ok}/{len(chapters)} last={fname}')
    print(f'final_ok={ok}')
    print(f'final_miss={miss}')
    print(f'out={book_dir}')

if __name__ == '__main__':
    main()
