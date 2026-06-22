import json
import re
from pathlib import Path

ROOT = Path(r"C:\Dev\MTC")
OUT = Path(r"C:\Dev\MTC_Download\logs\mtc_local_chapter_continuity.json")
IGNORE = {".git", ".githooks", ".vscode", "git"}
PAT = re.compile(r"(?i)(?:chương|chuong)\s*(\d+)")


def main():
    report = []
    for d in sorted([p for p in ROOT.iterdir() if p.is_dir() and p.name not in IGNORE], key=lambda p: p.name.lower()):
        nums = []
        files = []
        for p in d.glob("*.txt"):
            m = PAT.search(p.name)
            if not m:
                continue
            try:
                n = int(m.group(1))
            except Exception:
                continue
            nums.append(n)
            files.append((n, p.name))
        if not nums:
            continue
        uniq = sorted(set(nums))
        positive = [n for n in uniq if n > 0]
        max_idx = max(uniq)
        min_positive = min(positive) if positive else None
        missing = []
        if positive:
            present = set(positive)
            for i in range(1, max(positive) + 1):
                if i not in present:
                    missing.append(i)
        dup_map = {}
        for n, fname in files:
            dup_map.setdefault(n, []).append(fname)
        dupes = {k: v for k, v in dup_map.items() if len(v) > 1}
        row = {
            "folder": d.name,
            "chapter_file_count": len(files),
            "unique_index_count": len(uniq),
            "min_index": min(uniq),
            "max_index": max_idx,
            "has_chapter_0": 0 in uniq,
            "missing_count_1_to_max": len(missing),
            "missing_first200": missing[:200],
            "duplicate_index_count": len(dupes),
            "duplicate_indexes_first50": sorted(list(dupes))[:50],
            "status": "continuous_1_to_max" if not missing and not dupes else "has_gaps_or_duplicates",
        }
        report.append(row)
    out = {
        "total_story_folders": len(report),
        "report": report,
    }
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(OUT)


if __name__ == "__main__":
    main()
