import concurrent.futures as cf
import subprocess, sys, time
from pathlib import Path

BASE=Path(r"C:\Dev\MTC_Download")
ids=[int(x) for x in "100231,100234,100336,100368,100471,100507,100525,100557,100558,100771,100775,100816,100918,100931,101033,101037,101050,101119,101140,101409,101628,101739,101812,101863".split(',')]
py=sys.executable
log=BASE/'logs'/'retry_failed_first.log'
full=BASE/'download_hidden_parallel.py'
book=BASE/'download_all_missing_books.py'

def run_one(book_id):
    cmd=[py, str(book), '--book-id', str(book_id), '--delay', '0.05', '--workers', '4', '--batch-size', '16']
    p=subprocess.run(cmd, cwd=str(BASE), text=True, encoding='utf-8', errors='replace', capture_output=True)
    return book_id, p.returncode, '\n'.join((p.stdout or '').splitlines()[-3:]), '\n'.join((p.stderr or '').splitlines()[-3:])

with log.open('w', encoding='utf-8') as f:
    f.write(f'retry_failed_count={len(ids)}\\n')
    with cf.ThreadPoolExecutor(max_workers=4) as ex:
        for book_id, rc, out, err in ex.map(run_one, ids):
            f.write(f'ID={book_id} RC={rc}\\nSTDOUT:\\n{out}\\nSTDERR:\\n{err}\\n---\\n')
            f.flush()
    f.write('RETRY_FAILED_DONE\\n')
    f.flush()
subprocess.Popen([py, str(full), '--status', 'completed', '--order', 'small', '--delay', '0.05', '--book-workers', '4', '--chapter-workers', '4', '--batch-size', '16'], cwd=str(BASE), stdout=open(BASE/'logs'/'hidden_parallel_stdout.log','w',encoding='utf-8'), stderr=open(BASE/'logs'/'hidden_parallel_stderr.log','w',encoding='utf-8'))
