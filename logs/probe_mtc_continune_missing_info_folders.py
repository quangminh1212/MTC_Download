import json
from pathlib import Path

ROOT = Path(r"C:\dev\mtc_continune")
AUDIT = Path(r"C:\Dev\MTC_Download\logs\mtc_continune_local_audit.json")
OUT = Path(r"C:\Dev\MTC_Download\logs\mtc_continune_missing_info_folder_probe.json")
issues = json.loads(AUDIT.read_text(encoding="utf-8"))["issues"]
folders = [r["folder"] for r in issues if r.get("status") == "missing_info"]
rows = []
for name in folders:
    folder = ROOT / name
    files = [p for p in folder.iterdir()] if folder.exists() else []
    txt = [p for p in files if p.is_file() and p.suffix.lower() == ".txt"]
    row = {
        "folder": name,
        "exists": folder.exists(),
        "file_count": sum(1 for p in files if p.is_file()),
        "dir_count": sum(1 for p in files if p.is_dir()),
        "txt_count": len(txt),
        "first_files": [p.name for p in files[:20]],
    }
    samples = []
    for p in txt[:3]:
        try:
            text = p.read_text(encoding="utf-8", errors="replace")[:800]
        except Exception as e:
            text = f"ERROR: {e}"
        samples.append({"file": p.name, "size": p.stat().st_size, "sample": text})
    row["samples"] = samples
    rows.append(row)
OUT.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
print(str(OUT))
for r in rows:
    print(f"{r['folder']} files={r['file_count']} txt={r['txt_count']} dirs={r['dir_count']}")
