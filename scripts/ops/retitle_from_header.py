import json
import re
from pathlib import Path

ROOT = Path(r"C:\Dev\MTC")
OUT = Path(r"C:\Dev\MTC_Download\logs\retitle_from_header_report.json")
IGNORE = {".git", ".githooks", ".vscode", "git"}
PLAIN_RE = re.compile(r"^(?i:chương|chuong)\s+(\d+)\.txt$")
HEADER_RE = re.compile(r"(?i)^(?:chương|chuong)\s*(\d+)\s*[:.\-–—]?\s*(.+)$")
INVALID_RE = re.compile(r"[<>:\"/\\|?*!]")
STRIP_RE = re.compile(r"[\(\)\[\]\{\}\+,\-–—]+")


def clean_title(s: str) -> str:
    s = INVALID_RE.sub(" ", s or "")
    s = STRIP_RE.sub(" ", s)
    s = re.sub(r"^[\s\.:;,_]+|[\s\.:;,_]+$", "", s)
    s = re.sub(r"\s+", " ", s).strip(" .")
    return s


def main():
    bad = []
    renamed = []
    conflicts = []
    for d in sorted([p for p in ROOT.iterdir() if p.is_dir() and p.name not in IGNORE], key=lambda p: p.name.lower()):
        for f in d.glob("*.txt"):
            m = PLAIN_RE.match(f.name)
            if not m:
                continue
            idx = int(m.group(1))
            lines = f.read_text(encoding="utf-8", errors="replace").splitlines()
            cand = ""
            for line in lines[:15]:
                mm = HEADER_RE.match(line.strip())
                if mm and int(mm.group(1)) == idx:
                    cand = clean_title(mm.group(2))
                    break
            if not cand:
                bad.append(str(f))
                continue
            dst = f.with_name(f"Chương {idx} {cand}.txt")
            if dst.exists() and dst.resolve() != f.resolve():
                conflicts.append({"src": str(f), "dst": str(dst)})
                continue
            f.rename(dst)
            renamed.append({"from": str(f), "to": str(dst)})
    OUT.write_text(json.dumps({
        "renamed_count": len(renamed),
        "unresolved_count": len(bad),
        "conflict_count": len(conflicts),
        "renamed": renamed,
        "unresolved": bad,
        "conflicts": conflicts,
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print(OUT)
    print("renamed", len(renamed), "unresolved", len(bad), "conflicts", len(conflicts))


if __name__ == "__main__":
    main()
