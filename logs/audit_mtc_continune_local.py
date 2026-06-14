import json, re
from pathlib import Path

root = Path(r"C:\dev\mtc_continune")
chap_re = re.compile(r"(?i)^Chương\s+(\d+)\b.*\.txt$")
ignore = {".git", ".claude", ".vscode", "_bad_quarantine"}
known_short_by_id = {(142817, 55), (142817, 56), (137995, 580)}
rows = []
scanned = 0
for folder in root.iterdir():
    if not folder.is_dir() or folder.name in ignore:
        continue
    info = folder / "info.json"
    if not info.exists():
        rows.append({"folder": folder.name, "status": "missing_info"})
        continue
    scanned += 1
    try:
        meta = json.loads(info.read_text(encoding="utf-8"))
    except Exception as e:
        rows.append({"folder": folder.name, "status": "bad_info", "error": str(e)})
        continue
    expected = int(meta.get("chapter_count") or meta.get("latest_index") or len(meta.get("chapters") or []) or 0)
    chapters = meta.get("chapters") or []
    remote_indexes = []
    for i, ch in enumerate(chapters, 1):
        try:
            remote_indexes.append(int(ch.get("index") or i))
        except Exception:
            remote_indexes.append(i)
    if not remote_indexes and expected:
        remote_indexes = list(range(1, expected + 1))
    local = []
    small = []
    empty = []
    for p in folder.glob("*.txt"):
        m = chap_re.match(p.name)
        if not m:
            continue
        idx = int(m.group(1))
        local.append(idx)
        size = p.stat().st_size
        if size == 0:
            empty.append(idx)
        elif size < 500 and (int(meta.get("id") or 0), idx) not in known_short_by_id:
            small.append(idx)
    lset = set(local)
    rset = set(remote_indexes)
    missing = sorted(rset - lset)
    dup = len(local) - len(lset)
    if missing or dup or small or empty or (expected and len(lset) < expected):
        rows.append({
            "folder": folder.name,
            "book_id": meta.get("id"),
            "book_name": meta.get("name"),
            "link": meta.get("link"),
            "expected": expected,
            "remote_manifest_count": len(rset),
            "local_count": len(lset),
            "missing": missing[:300],
            "missing_count": len(missing),
            "duplicates": dup,
            "small": small[:100],
            "small_count": len(small),
            "empty": empty[:100],
            "empty_count": len(empty),
        })

out = Path(r"C:\Dev\MTC_Download\logs\mtc_continune_local_audit.json")
out.write_text(json.dumps({"scanned": scanned, "issues": rows}, ensure_ascii=False, indent=2), encoding="utf-8")
print(str(out))
print("scanned", scanned)
print("issues", len(rows))
for r in rows[:80]:
    if r.get("status"):
        print(f"{r['folder']} status={r['status']}")
    else:
        print("{folder} id={book_id} local={local_count} expected={expected} missing={missing_count} small={small_count} empty={empty_count} dup={duplicates}".format(**r))
