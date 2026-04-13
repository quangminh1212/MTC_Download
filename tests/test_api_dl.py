"""Quick API download test with first 2 chapters of a small book."""
import sys, json
from pathlib import Path
_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from mtc.pipeline import _api_session, _resolve_book, _fetch_chapter_list, _fetch_api_chapter_text

# First book in data/all_books.json: Chiến Lược Gia Thiên Tài (id=153347, 21 chapters)
books = json.load(open(_ROOT / 'data' / 'all_books.json', encoding='utf-8'))
book = books[0]
print(f"Testing: id={book['id']} name={book['name']} ch={book['chapter_count']}")

session = _api_session()

# Resolve book
print("Resolving via API...")
bdata = _resolve_book(session, book['name'], book_id=book['id'])
if not bdata:
    print("FAIL: could not resolve book")
    sys.exit(1)
print(f"  Found: id={bdata.get('id')} name={bdata.get('name')}")

# Fetch chapter list
print("Fetching chapter list...")
chapters = _fetch_chapter_list(session, bdata['id'])
print(f"  Got {len(chapters)} chapters")

if not chapters:
    print("FAIL: no chapters")
    sys.exit(1)

# Fetch first 2 chapters
for ch in chapters[:2]:
    idx = ch.get('index', 0)
    cid = ch.get('id')
    print(f"\n  Chapter {idx} (id={cid})")
    try:
        title, text = _fetch_api_chapter_text(session, ch)
        print(f"    title: {title}")
        print(f"    length: {len(text)} chars")
        print(f"    preview: {text[:100]!r}")
    except Exception as e:
        print(f"    ERROR: {e}")

print("\nDone.")
