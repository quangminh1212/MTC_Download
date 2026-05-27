import json
from pathlib import Path
from manual_verify_thuong_sinh import maybe_decrypt, clean_text

src = Path(r"C:\Dev\MTC_Download\logs\chapter_debug")
out = Path(r"C:\Dev\MTC_Download\logs\chapter_debug_preview.txt")
ids = [15426215, 15405674, 15624081]
parts = []
for cid in ids:
    data = json.loads((src / f"{cid}.json").read_text(encoding='utf-8'))['data']
    plain, dec = maybe_decrypt(data.get('content') or '')
    cleaned = clean_text(plain)
    parts.append(f"=== {cid} | {data.get('name')} | decrypted={dec} | len={len(cleaned)} ===\n{cleaned[:1500]}\n")
out.write_text('\n'.join(parts), encoding='utf-8')
print(str(out))
