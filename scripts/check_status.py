"""Check download status and parse exported books."""
import sys, json, os, re
from pathlib import Path
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

ROOT = Path(__file__).resolve().parent.parent
BOOKS_JSON = ROOT / 'data' / 'all_books.json'
DOWNLOADS = ROOT / 'downloads'
EXPORT_DIR = ROOT / 'exports'  # where to save pulled txt

with open(BOOKS_JSON, encoding='utf-8') as f:
    books = json.load(f)

print(f'Total books in all_books.json: {len(books)}')
print()

for b in books:
    name = b['name']
    dl_path = DOWNLOADS / name
    exists = dl_path.is_dir()
    ch_count = len(list(dl_path.glob('*.txt'))) if exists else 0
    status = 'OK' if ch_count >= b['chapter_count'] * 0.9 else ('PARTIAL' if ch_count > 0 else 'TODO')
    print(f'  [{b["id"]:7d}] {name[:55]:55} total={b["chapter_count"]:4d} dl={ch_count:4d} {status}')
