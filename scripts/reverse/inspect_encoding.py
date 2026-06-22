from pathlib import Path
import glob

cands = sorted(glob.glob(r"C:\Dev\MTC\Si*"))
print('candidates:', cands)
if not cands:
    raise SystemExit('No candidates')
book = Path(cands[0])
files = sorted(book.glob('*.txt'))
print('book:', book)
print('files:', len(files))
if not files:
    raise SystemExit('No txt files')
f = files[0]
b = f.read_bytes()
head = b[:500]
print('first file:', f)
print('size:', len(b))
print('head hex:', head[:120].hex())
for enc in ['utf-8', 'utf-8-sig', 'cp1258', 'cp1252', 'latin1']:
    try:
        s = head.decode(enc)
        print(f'ENC {enc} OK sample:')
        print(s[:300].replace('\n','\\n'))
    except Exception as e:
        print(f'ENC {enc} err: {e}')
