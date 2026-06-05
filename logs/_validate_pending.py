import sys, os
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
root = Path(r"C:\Dev\MTC")
markers = ["eyJpdiI6", '"iv":"', '"value":"']
def has_ctrl(s):
    return any(ord(ch) < 32 and ch not in "\n\r\t" for ch in s)
for name in os.listdir(root):
    d = root / name
    if not d.is_dir() or name == ".git":
        continue
    txts = sorted(d.glob("*.txt"))
    jsons = sorted(d.glob("*.json"))
    if not txts and not jsons:
        continue
    info_ok = (d / "info.json").exists()
    bad_marker = bad_fffd = bad_ctrl = 0
    for p in txts:
        t = p.read_text(encoding="utf-8", errors="replace")
        if any(m in t for m in markers):
            bad_marker += 1
        if "\ufffd" in t:
            bad_fffd += 1
        if has_ctrl(t):
            bad_ctrl += 1
    status = "OK"
    issues = []
    if not info_ok:
        issues.append("NO_INFO_JSON")
    if bad_marker:
        issues.append(f"ENCRYPTED={bad_marker}")
    if bad_fffd:
        issues.append(f"FFFD={bad_fffd}")
    if bad_ctrl:
        issues.append(f"CTRL={bad_ctrl}")
    if issues:
        status = " ".join(issues)
    print(f"{name}\ttxt={len(txts)}\tjson={len(jsons)}\tinfo={info_ok}\t{status}")
