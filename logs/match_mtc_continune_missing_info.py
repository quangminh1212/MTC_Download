import html, json, re, sys, time
from pathlib import Path
sys.path.insert(0, r"C:\Dev\MTC_Download\scripts")
from mtc_downloader import MTCDownloader

ROOT = Path(r"C:\dev\mtc_continune")
AUDIT = Path(r"C:\Dev\MTC_Download\logs\mtc_continune_local_audit.json")
OUT = Path(r"C:\Dev\MTC_Download\logs\mtc_continune_missing_info_matches.json")
INVALID = '<>:"/\\|?*!'
STRIP_PUNCT_RE = re.compile(r"[^\w\sÀ-ỹà-ỹĐđ]+", re.UNICODE)
WS_RE = re.compile(r"\s+")

def norm(s):
    s = html.unescape(str(s or ""))
    s = STRIP_PUNCT_RE.sub(" ", s)
    for ch in INVALID:
        s = s.replace(ch, " ")
    return WS_RE.sub(" ", s).strip(" .").lower()

d = MTCDownloader()
books = []
page = 1
while True:
    data = d.get_books(limit=100, page=page)
    rows = (data or {}).get("data") or []
    if not rows:
        break
    books.extend(rows)
    if len(rows) < 100:
        break
    page += 1
    time.sleep(0.1)
by_norm = {}
for b in books:
    by_norm.setdefault(norm(b.get("name")), []).append(b)
issues = json.loads(AUDIT.read_text(encoding="utf-8"))["issues"]
missing = [r["folder"] for r in issues if r.get("status") == "missing_info"]
results = []
for folder in missing:
    cands = by_norm.get(norm(folder), [])
    row = {"folder": folder, "matches": []}
    for b in cands:
        row["matches"].append({"id": b.get("id"), "name": b.get("name"), "chapter_count": b.get("chapter_count"), "latest_index": b.get("latest_index"), "status_name": b.get("status_name")})
    results.append(row)
OUT.write_text(json.dumps({"book_count": len(books), "results": results}, ensure_ascii=False, indent=2), encoding="utf-8")
print(str(OUT))
print("books", len(books), "missing", len(missing), "matched", sum(1 for r in results if r['matches']))
