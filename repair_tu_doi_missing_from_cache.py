import html
import json
import re
from pathlib import Path

SRC = Path(r"C:\Dev\MTC_Download\bookmarked_downloads\Từ Đội Sản Xuất Đuổi Đại Xa Bắt Đầu__143452")
OUT = Path(r"C:\Dev\MTC\Từ Đội Sản Xuất Đuổi Đại Xa Bắt Đầu")
NEED = [1343, 1392, 1548, 1582, 1691, 1692, 1697]
INVALID = '<>:"/\\|?*!'
STRIP_RE = re.compile(r"[\(\)\[\]\{\}\+,\-–—]+")
TAG_RE = re.compile(r"<[^>]+>")
TITLE_PREFIX = re.compile(r"^\s*(?:chương|chuong)\s*\d+\s*[:.\-–—]?\s*", re.I)


def clean_filename(s, max_len=170):
    s = html.unescape(str(s or "")).strip()
    s = STRIP_RE.sub(" ", s)
    for ch in INVALID:
        s = s.replace(ch, " ")
    s = re.sub(r"\s+", " ", s).strip(" .")
    return (s or "Untitled")[:max_len].strip(" .")


def clean_text(value):
    text = html.unescape(str(value or ""))
    text = text.replace("<br />", "\n").replace("<br/>", "\n").replace("<br>", "\n")
    text = re.sub(r"</p\s*>", "\n\n", text, flags=re.I)
    text = TAG_RE.sub("", text)
    lines = [re.sub(r"[ \t\r\f\v]+", " ", line).strip() for line in text.splitlines()]
    out = []
    blanks = 0
    for line in lines:
        if line:
            blanks = 0
            out.append(line)
        else:
            blanks += 1
            if blanks <= 1:
                out.append("")
    return "\n".join(out).strip() + "\n"


def extract_data(obj):
    if isinstance(obj, dict):
        data = obj.get("data", obj)
    else:
        data = obj
    if isinstance(data, list):
        data = data[0] if data else {}
    return data if isinstance(data, dict) else {}


def main():
    report = []
    for n in NEED:
        jf = next(SRC.glob(f"chapter_{n}_*.json"))
        data = extract_data(json.loads(jf.read_text(encoding="utf-8")))
        raw_title = data.get("name") or data.get("title") or f"Chương {n}"
        title = TITLE_PREFIX.sub("", str(raw_title)).strip(" :.–—-")
        title = clean_filename(title, 130)
        fname = f"Chương {n} {title}.txt" if title and title != "Untitled" else f"Chương {n}.txt"
        content = data.get("content") or data.get("body") or ""
        text = f"{'=' * 60}\n{raw_title}\n{'=' * 60}\n\n" + clean_text(content)
        path = OUT / fname
        path.write_text(text, encoding="utf-8")
        row = {"idx": n, "json": str(jf), "file": str(path), "size": path.stat().st_size}
        report.append(row)
        print("WROTE", n, path.name, path.stat().st_size)
    log = Path(r"C:\Dev\MTC_Download\logs\repair_tu_doi_missing_from_cache.json")
    log.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print("REPORT", log)


if __name__ == "__main__":
    main()
