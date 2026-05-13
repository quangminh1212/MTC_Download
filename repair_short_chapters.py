import json
from pathlib import Path
from mtc_downloader import MTCDownloader
from download_completed_to_mtc import write_chapter, chapter_filename, clean_filename

ROOT = Path(r'C:\Dev\MTC')
report = json.loads(Path(r'C:\Dev\MTC_Download\logs\short_chapter_remote_check.json').read_text(encoding='utf-8'))
d = MTCDownloader()

repair_targets = {
    112190: {84},
    100738: {3, 4, 5, 7, 11, 21},
    102223: {2},
}

results = []
for book in report:
    bid = book['book_id']
    wanted = repair_targets.get(bid)
    if not wanted:
        continue
    book_dir = ROOT / clean_filename(book['book_name'])
    chapters = (d.get_chapters(bid, page=1, limit=2000) or {}).get('data') or []
    by_idx = {int(c.get('index') or 0): c for c in chapters if c.get('index')}
    book_results = []
    for item in book['checks']:
        idx = int(item['chapter'])
        if idx not in wanted:
            continue
        ch = by_idx.get(idx)
        if not ch:
            book_results.append({'chapter': idx, 'status': 'missing_remote_index'})
            continue
        detail = (d.get_chapter_content(ch['id']) or {}).get('data') or {}
        content = detail.get('content') or detail.get('body') or ''
        if not content:
            book_results.append({'chapter': idx, 'status': 'empty_remote'})
            continue
        fname = chapter_filename(ch, idx)
        fpath = book_dir / fname
        if not fpath.exists():
            # fallback: find existing file with same chapter index
            matches = sorted(book_dir.glob(f'Chương {idx}*.txt'))
            if matches:
                fpath = matches[0]
        display_name = detail.get('name') or ch.get('name') or f'Chương {idx}'
        before = fpath.stat().st_size if fpath.exists() else None
        write_chapter(fpath, book['book_name'], display_name, content)
        after = fpath.stat().st_size if fpath.exists() else None
        book_results.append({
            'chapter': idx,
            'path': str(fpath),
            'before_size': before,
            'after_size': after,
            'remote_len': len(content),
            'status': 'repaired',
        })
    results.append({
        'book_id': bid,
        'book_name': book['book_name'],
        'results': book_results,
    })

out = Path(r'C:\Dev\MTC_Download\logs\short_chapter_repair_results.json')
out.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding='utf-8')
print(str(out))
