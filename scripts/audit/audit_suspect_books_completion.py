import json
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, r"C:\Dev\MTC_Download")
from mtc_downloader import MTCDownloader

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(r"C:\Dev\MTC")
OUT = Path(r"C:\Dev\MTC_Download\logs\suspect_books_completion_audit.json")
PAT = re.compile(r"(?i)(?:chương|chuong)\s*(\d+)")
TARGETS = [
    "Bạch Quả Chi Đồng Nhân Thiếu Niên Ca Hành Quyển 1 end",
    "Bắt Đầu Cùng Chị Dâu Nương Tựa Lẫn Nhau",
    "Bắt Đầu Từ Lập Trình Viên",
    "Biển Vô Tận Toàn Chức Vua Câu Cá",
    "Công Cuộc Bị 999 Em Gái Chinh Phục",
    "Đại La Thiên Tôn",
    "Đưa Nước Việt Vươn Tầm Thế Giới phần 1 Khải Hoàn Nhất Lộ",
    "Minecraft Thế Giới Sinh Tồn",
    "Siêu Dự Bị",
    "Tận Thế Xuyên Việt Giả",
]

# From latest successful remote audit; avoids relying on broken search.
KNOWN_IDS = {
    "Bạch Quả Chi Đồng Nhân Thiếu Niên Ca Hành Quyển 1 end": 104077,
    "Bắt Đầu Cùng Chị Dâu Nương Tựa Lẫn Nhau": 128485,
    "Bắt Đầu Từ Lập Trình Viên": 128191,
    "Biển Vô Tận Toàn Chức Vua Câu Cá": 112190,
    "Công Cuộc Bị 999 Em Gái Chinh Phục": 100677,
    "Đại La Thiên Tôn": 105059,
    "Đưa Nước Việt Vươn Tầm Thế Giới phần 1 Khải Hoàn Nhất Lộ": 129421,
    "Minecraft Thế Giới Sinh Tồn": 119624,
    "Siêu Dự Bị": 120283,
    "Tận Thế Xuyên Việt Giả": 123252,
}


def local_map(folder: Path):
    out = {}
    for p in folder.glob("*.txt"):
        m = PAT.search(p.name)
        if m:
            out.setdefault(int(m.group(1)), []).append(p.name)
    return out


def get_all_chapters(d, book_id):
    rows = []
    page = 1
    while True:
        data = d.get_chapters(book_id, page=page, limit=500)
        arr = (data or {}).get("data") or []
        if not arr:
            break
        rows.extend(arr)
        if len(arr) < 500:
            break
        page += 1
        time.sleep(0.05)
    return rows


def main():
    d = MTCDownloader()
    report = []
    for folder_name in TARGETS:
        folder = ROOT / folder_name
        lm = local_map(folder)
        lidx = sorted(lm)
        book_id = KNOWN_IDS[folder_name]
        detail = (d.get_book_detail(book_id) or {}).get("data") or {}
        chapters = get_all_chapters(d, book_id)
        remote = {}
        for i, ch in enumerate(chapters, 1):
            try:
                idx = int(ch.get("index") or ch.get("number") or i)
            except Exception:
                idx = i
            remote[idx] = ch
        ridx = sorted(remote)
        missing = sorted(set(ridx) - set(lidx))
        extra = sorted(set(lidx) - set(ridx))
        last_remote_idx = max(ridx) if ridx else None
        last_remote = remote.get(last_remote_idx) if last_remote_idx else None
        last_local_idx = max(lidx) if lidx else None
        last_local_files = lm.get(last_local_idx, []) if last_local_idx else []
        row = {
            "folder": folder_name,
            "book_id": book_id,
            "remote_name": detail.get("name"),
            "remote_status": detail.get("status_name"),
            "remote_status_code": detail.get("status"),
            "remote_chapter_count": detail.get("chapter_count"),
            "remote_latest_index": detail.get("latest_index"),
            "remote_index_count": len(ridx),
            "local_unique_count": len(lidx),
            "local_file_count": sum(len(v) for v in lm.values()),
            "local_last_index": last_local_idx,
            "local_last_files": last_local_files,
            "remote_last_index": last_remote_idx,
            "remote_last_name": (last_remote or {}).get("name"),
            "missing_count": len(missing),
            "missing": missing,
            "extra_count": len(extra),
            "extra": extra,
            "is_complete_vs_remote": not missing and not extra,
        }
        report.append(row)
        print(folder_name, "complete_vs_remote", row["is_complete_vs_remote"], "missing", missing, "status", row["remote_status"])
        time.sleep(0.1)
    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(OUT)


if __name__ == "__main__":
    main()
