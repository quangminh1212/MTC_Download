import concurrent.futures as cf
import subprocess, sys
from pathlib import Path
BASE=Path(r"C:\Dev\MTC_Download")
ids=[100775,100931]
py=sys.executable
book=BASE/'download_all_missing_books.py'

def run_one(book_id):
    cmd=[py, str(book), '--book-id', str(book_id), '--delay', '0.05', '--workers', '3', '--batch-size', '12']
    p=subprocess.run(cmd, cwd=str(BASE), text=True, encoding='utf-8', errors='replace', capture_output=True)
    return book_id, p.returncode, '\n'.join((p.stdout or '').splitlines()[-8:]), '\n'.join((p.stderr or '').splitlines()[-8:])

with open(BASE/'logs'/'retry_two_timeout.log','w',encoding='utf-8') as f:
    with cf.ThreadPoolExecutor(max_workers=2) as ex:
        for book_id, rc, out, err in ex.map(run_one, ids):
            f.write(f'ID={book_id} RC={rc}\nSTDOUT:\n{out}\nSTDERR:\n{err}\n---\n')
            f.flush()
