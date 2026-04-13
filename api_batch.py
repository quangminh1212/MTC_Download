#!/usr/bin/env python3
"""api_batch.py – Download all 397 novels from all_books.json via API.

Usage:
    python api_batch.py                  # Download all books
    python api_batch.py --limit 5        # Only first 5 books
    python api_batch.py --start-id 140000  # Skip books with id < 140000
    python api_batch.py --force          # Re-download even if chapters exist
    python api_batch.py --book "Chiến"   # Download specific book (partial name match)
    
Progress is saved to api_batch_state.json (resume-safe).
Output log is appended to api_batch.log.
"""
import sys, json, time, os, argparse, traceback
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.stderr.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, str(Path(__file__).resolve().parent))

from mtc.pipeline import download_via_api, _HAS_API_DEPS
from mtc.utils import safe_name
from mtc.config import OUTPUT_DIR

BOOKS_JSON  = Path('all_books.json')
STATE_FILE  = Path('api_batch_state.json')
LOG_FILE    = Path('api_batch.log')

def ts():
    return time.strftime('%H:%M:%S')

def log(msg: str, also_file=True):
    line = f'[{ts()}] {msg}'
    print(line, flush=True)
    if also_file:
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(line + '\n')

def count_saved(book_name: str) -> int:
    import re
    d = OUTPUT_DIR / safe_name(book_name)
    if not d.is_dir():
        return 0
    return sum(1 for f in d.glob('*.txt')
               if re.match(r'^\d{6}_', f.name) and f.stat().st_size > 100)

def load_state() -> dict:
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text(encoding='utf-8'))
        except Exception:
            pass
    return {}

def save_state(state: dict):
    STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding='utf-8')

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--limit',    type=int, default=9999, help='Max books to process')
    p.add_argument('--start-id', type=int, default=0,    help='Skip books with id < N')
    p.add_argument('--force',    action='store_true',     help='Re-download even if chapters exist')
    p.add_argument('--book',     type=str, default='',    help='Partial name filter')
    args = p.parse_args()

    if not _HAS_API_DEPS:
        log('ERROR: API deps not available (install requests pycryptodome ftfy)')
        return 1

    books = json.loads(BOOKS_JSON.read_text(encoding='utf-8'))
    log(f'Loaded {len(books)} books from {BOOKS_JSON}')

    # Apply filters
    if args.start_id:
        books = [b for b in books if b['id'] >= args.start_id]
        log(f'  After --start-id {args.start_id}: {len(books)} books')

    if args.book:
        q = args.book.lower()
        books = [b for b in books if q in b['name'].lower()]
        log(f'  After --book filter: {len(books)} books')

    books = books[:args.limit]
    log(f'  Will process: {len(books)} books\n')

    state = load_state()
    processed = ok_total = fail_total = skip_total = 0

    for idx, book in enumerate(books, 1):
        bid   = book['id']
        bname = book['name']
        bch   = book.get('chapter_count', 0)

        # Skip if state says done and not force
        if not args.force and state.get(str(bid)) == 'ok':
            saved = count_saved(bname)
            if saved > 0:
                log(f'[{idx}/{len(books)}] SKIP (state=ok, {saved} ch saved): {bname}')
                skip_total += 1
                continue

        # Skip if enough chapters already saved
        saved = count_saved(bname)
        if not args.force and saved > 0 and (bch == 0 or saved >= int(bch * 0.95)):
            log(f'[{idx}/{len(books)}] SKIP ({saved}/{bch} ch): {bname}')
            state[str(bid)] = 'ok'
            save_state(state)
            skip_total += 1
            continue

        log(f'\n[{idx}/{len(books)}] #{bid} {bname} ({bch} chapters, {saved} saved)')

        try:
            result = download_via_api(
                book_name=bname,
                book_id=bid,
                ch_end=bch if bch > 0 else None,
                log_fn=lambda msg: log(f'  {msg}'),
            )
            ok  = result.get('ok', 0)
            fail = result.get('fail', 0)

            if result.get('success'):
                log(f'  => OK: {ok} chapters saved, {fail} failed')
                state[str(bid)] = 'ok'
                ok_total += 1
            else:
                reason = result.get('reason', '?')
                log(f'  => FAIL: {reason} (ok={ok} fail={fail})')
                state[str(bid)] = f'fail:{reason}'
                fail_total += 1

        except Exception as e:
            log(f'  => EXCEPTION: {e}')
            log('  ' + traceback.format_exc().replace('\n', '\n  '))
            state[str(bid)] = f'exception:{e}'
            fail_total += 1

        save_state(state)
        processed += 1

        # Small delay between books to be polite to the server
        if processed < len(books):
            time.sleep(0.5)

    log(f'\n{"="*60}')
    log(f'DONE: {processed} processed, {ok_total} OK, {fail_total} FAIL, {skip_total} SKIP')
    log(f'State saved to {STATE_FILE}')
    log(f'Log saved to {LOG_FILE}')
    return 0

if __name__ == '__main__':
    sys.exit(main())
