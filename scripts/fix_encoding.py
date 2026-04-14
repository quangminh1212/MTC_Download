"""
fix_encoding.py – Quét & sửa lỗi encoding (mojibake) cho file text trong folder.

Hỗ trợ:
  - Double-encoded UTF-8 qua CP1252 hoặc Latin-1
  - Triple-encoded UTF-8
  - File không phải UTF-8 (tự detect encoding)
  - Quét đệ quy tất cả subfolder

Cách dùng:
  python fix_encoding.py <folder>              # Chỉ quét, báo lỗi
  python fix_encoding.py <folder> --fix        # Quét và sửa lỗi
  python fix_encoding.py <folder> --fix --backup  # Sửa + tạo file .bak
  python fix_encoding.py <folder> --ext .txt .html # Chỉ quét file .txt và .html
"""

import argparse
import os
import re
import shutil
import sys
from pathlib import Path

# ── Vietnamese character set ─────────────────────────────────────────────
VIET_LOWER = set("àảãáạăằẳẵắặâầẩẫấậèẻẽéẹêềểễếệìỉĩíịòỏõóọôồổỗốộơờởỡớợùủũúụưừửữứựỳỷỹýỵđ")
VIET_UPPER = set(c.upper() for c in VIET_LOWER)
VIET_CHARS = VIET_LOWER | VIET_UPPER

# Regex patterns for common mojibake produced by double-encoding Vietnamese UTF-8
# through CP1252 or Latin-1. These sequences are extremely rare in normal text.
MOJIBAKE_PATTERNS = re.compile(
    r"[\u00C3][\u0080-\u00BF]"  # Ã + continuation byte  (from C3 xx)
    r"|\u00C4[\u0080-\u00BF]"   # Ä + byte  (from C4 xx)
    r"|\u00C5[\u0080-\u00BF]"   # Å + byte  (from C5 xx)
    r"|\u00C6[\u00A0-\u00BF]"   # Æ + byte  (from C6 xx)
    r"|\u00C2[\u00A0-\u00BF]"   # Â + byte  (from C2 xx)
    r"|\u00E1[\u00BA\u00BB][\u0080-\u00BF]"  # á»x / áºx patterns
    r"|\u00C3[\u0080-\u009F]"   # Ã + C1 ctrl (triple-encoding indicator)
)


def count_vietnamese(text: str) -> int:
    """Count Vietnamese-specific diacritics in text."""
    return sum(1 for c in text if c in VIET_CHARS)


def count_mojibake(text: str) -> int:
    """Count mojibake pattern occurrences in text."""
    return len(MOJIBAKE_PATTERNS.findall(text))


def text_quality_score(text: str) -> float:
    """Score text quality: higher = cleaner Vietnamese text.

    Positive from Vietnamese chars, negative from mojibake patterns.
    """
    return count_vietnamese(text) - count_mojibake(text) * 3


def try_fix_double_encoding(text: str, codec: str = "cp1252") -> str | None:
    """Attempt to fix double-encoded UTF-8 text.

    Returns fixed text if successful, None if not applicable.
    """
    try:
        fixed = text.encode(codec).decode("utf-8")
        if fixed != text and text_quality_score(fixed) > text_quality_score(text):
            return fixed
    except (UnicodeDecodeError, UnicodeEncodeError):
        pass
    return None


def try_fix_line(line: str) -> tuple[str, str]:
    """Try to fix a single line. Returns (fixed_line, method_used).

    Iteratively decodes up to 4 rounds, comparing the FINAL result
    against the ORIGINAL input (handles double, triple, etc. encoding).
    """
    if not line.strip() or all(ord(c) < 128 for c in line):
        return line, ""

    # Strategy 1: Iterative decode (handles double/triple/quad encoding)
    current = line
    passes = 0
    codecs_used = []

    for _ in range(4):
        changed = False
        for codec in ("latin-1", "cp1252"):
            try:
                candidate = current.encode(codec).decode("utf-8")
                if candidate != current:
                    current = candidate
                    codecs_used.append(codec)
                    passes += 1
                    changed = True
                    break
            except (UnicodeDecodeError, UnicodeEncodeError):
                continue
        if not changed:
            break

    if passes > 0 and current != line:
        # Check final result vs original using quality score
        if text_quality_score(current) > text_quality_score(line):
            codec_label = "|".join(dict.fromkeys(codecs_used))
            return current, f"{passes}x-{codec_label}"

    # Strategy 2: Mixed content - try fixing segments
    if count_mojibake(line) > 0:
        fixed_line = _fix_segments(line)
        if fixed_line != line and text_quality_score(fixed_line) > text_quality_score(line):
            return fixed_line, "segment-fix"

    return line, ""


def _fix_segments(text: str) -> str:
    """Try to fix encoding segment by segment for mixed-encoding text."""
    result = []
    i = 0
    while i < len(text):
        # Find a run of non-ASCII characters
        if ord(text[i]) > 127:
            j = i
            while j < len(text) and (ord(text[j]) > 127 or text[j] in " "):
                j += 1
            segment = text[i:j]
            for codec in ("cp1252", "latin-1"):
                try:
                    fixed = segment.encode(codec).decode("utf-8")
                    if text_quality_score(fixed) > text_quality_score(segment):
                        segment = fixed
                        break
                except (UnicodeDecodeError, UnicodeEncodeError):
                    continue
            result.append(segment)
            i = j
        else:
            result.append(text[i])
            i += 1
    return "".join(result)


def detect_file_encoding(filepath: Path) -> str:
    """Detect if file is valid UTF-8 or needs encoding conversion."""
    raw = filepath.read_bytes()

    # Check for BOM
    if raw.startswith(b"\xef\xbb\xbf"):
        return "utf-8-sig"
    if raw.startswith(b"\xff\xfe"):
        return "utf-16-le"
    if raw.startswith(b"\xfe\xff"):
        return "utf-16-be"

    # Try UTF-8
    try:
        raw.decode("utf-8")
        return "utf-8"
    except UnicodeDecodeError:
        pass

    # Try common Vietnamese encodings
    for enc in ("cp1252", "latin-1", "cp1258"):
        try:
            text = raw.decode(enc)
            if count_vietnamese(text) > 0:
                return enc
        except (UnicodeDecodeError, UnicodeEncodeError):
            continue

    return "unknown"


class EncodingChecker:
    """Check and fix encoding issues in text files."""

    def __init__(self, extensions: list[str] = None, backup: bool = False):
        self.extensions = extensions or [".txt"]
        self.backup = backup
        self.stats = {
            "scanned": 0,
            "issues": 0,
            "fixed": 0,
            "errors": 0,
            "skipped": 0,
        }

    def scan_folder(self, folder: Path, fix: bool = False) -> list[dict]:
        """Scan folder recursively for encoding issues.

        Returns list of issue reports.
        """
        results = []
        folder = Path(folder)

        if not folder.is_dir():
            print(f"❌ Không tìm thấy folder: {folder}")
            return results

        # Collect all matching files recursively
        files = []
        for ext in self.extensions:
            files.extend(folder.rglob(f"*{ext}"))
        files.sort()

        if not files:
            print(f"⚠️  Không tìm thấy file {', '.join(self.extensions)} trong {folder}")
            return results

        print(f"📂 Quét {len(files)} file trong {folder}")
        print("=" * 70)

        for filepath in files:
            result = self._check_file(filepath, fix=fix)
            if result:
                results.append(result)

        self._print_summary()
        return results

    def _check_file(self, filepath: Path, fix: bool = False) -> dict | None:
        """Check a single file for encoding issues."""
        self.stats["scanned"] += 1
        rel_path = filepath

        # Detect encoding
        encoding = detect_file_encoding(filepath)

        if encoding == "unknown":
            self.stats["errors"] += 1
            print(f"  ❓ {rel_path} — không xác định được encoding")
            return {"file": str(filepath), "issue": "unknown-encoding", "fixed": False}

        # Read file
        try:
            if encoding in ("utf-16-le", "utf-16-be"):
                text = filepath.read_text(encoding=encoding)
                encoding_issue = "utf16"
            elif encoding != "utf-8" and encoding != "utf-8-sig":
                # File is not UTF-8 — this is an issue
                raw = filepath.read_bytes()
                text = raw.decode(encoding)
                encoding_issue = f"wrong-encoding-{encoding}"
            else:
                text = filepath.read_text(encoding="utf-8")
                encoding_issue = None
        except Exception as e:
            self.stats["errors"] += 1
            print(f"  ❌ {rel_path} — lỗi đọc file: {e}")
            return {"file": str(filepath), "issue": f"read-error: {e}", "fixed": False}

        # Check for replacement characters
        replacement_count = text.count("\ufffd")

        # Check for mojibake by trying line-by-line fix
        lines = text.split("\n")
        issues_found = []
        fixed_lines = []
        fix_methods = set()

        for line_num, line in enumerate(lines, 1):
            fixed_line, method = try_fix_line(line)
            if method:
                issues_found.append((line_num, line.strip()[:60], fixed_line.strip()[:60], method))
                fix_methods.add(method)
            fixed_lines.append(fixed_line)

        # Determine overall status
        has_issues = bool(issues_found) or encoding_issue or replacement_count > 0

        if not has_issues:
            return None  # File is clean

        self.stats["issues"] += 1

        # Report
        issue_types = []
        if encoding_issue:
            issue_types.append(f"encoding={encoding}")
        if issues_found:
            issue_types.append(f"mojibake={len(issues_found)} dòng")
        if replacement_count:
            issue_types.append(f"ký tự lỗi (U+FFFD)={replacement_count}")

        print(f"\n  ⚠️  {rel_path}")
        print(f"     Vấn đề: {', '.join(issue_types)}")

        # Show sample issues (max 3)
        for i, (ln, before, after, method) in enumerate(issues_found[:3]):
            print(f"     Dòng {ln} [{method}]:")
            print(f"       ❌ {before}")
            print(f"       ✅ {after}")
        if len(issues_found) > 3:
            print(f"     ... và {len(issues_found) - 3} dòng khác")

        result = {
            "file": str(filepath),
            "issue": ", ".join(issue_types),
            "mojibake_lines": len(issues_found),
            "replacement_chars": replacement_count,
            "methods": list(fix_methods),
            "fixed": False,
        }

        # Fix if requested
        if fix and (issues_found or encoding_issue):
            try:
                if self.backup:
                    bak = filepath.with_suffix(filepath.suffix + ".bak")
                    shutil.copy2(filepath, bak)

                fixed_text = "\n".join(fixed_lines)
                filepath.write_text(fixed_text, encoding="utf-8")
                self.stats["fixed"] += 1
                result["fixed"] = True
                print(f"     ✅ Đã sửa! ({len(issues_found)} dòng)")
            except Exception as e:
                self.stats["errors"] += 1
                print(f"     ❌ Lỗi khi sửa: {e}")

        return result

    def _print_summary(self):
        """Print scan summary."""
        s = self.stats
        print()
        print("=" * 70)
        print(f"📊 KẾT QUẢ:")
        print(f"   Đã quét:   {s['scanned']} file")
        print(f"   Có lỗi:    {s['issues']} file")
        print(f"   Đã sửa:    {s['fixed']} file")
        print(f"   Lỗi đọc:   {s['errors']} file")
        print("=" * 70)


def main():
    parser = argparse.ArgumentParser(
        description="Quét & sửa lỗi encoding (mojibake) cho file text",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ví dụ:
  python fix_encoding.py novel_exports              # Quét, chỉ báo lỗi
  python fix_encoding.py novel_exports --fix         # Quét và sửa
  python fix_encoding.py novel_exports --fix --backup # Sửa + backup .bak
  python fix_encoding.py data --ext .txt .json       # Quét file .txt và .json
  python fix_encoding.py . --ext .txt                # Quét toàn bộ project
        """,
    )
    parser.add_argument("folder", help="Folder cần quét (bao gồm subfolder)")
    parser.add_argument("--fix", action="store_true", help="Tự động sửa lỗi encoding")
    parser.add_argument("--backup", action="store_true", help="Tạo file .bak trước khi sửa")
    parser.add_argument(
        "--ext",
        nargs="+",
        default=[".txt"],
        help="Extension file cần quét (mặc định: .txt)",
    )

    args = parser.parse_args()

    folder = Path(args.folder)
    if not folder.is_dir():
        print(f"❌ Folder không tồn tại: {folder}")
        sys.exit(1)

    print()
    print("🔍 ENCODING CHECKER / FIXER")
    print(f"   Folder:     {folder.resolve()}")
    print(f"   Extensions: {', '.join(args.ext)}")
    print(f"   Chế độ:     {'SỬA LỖI' if args.fix else 'CHỈ QUÉT'}")
    if args.backup:
        print(f"   Backup:     Có (.bak)")
    print()

    checker = EncodingChecker(extensions=args.ext, backup=args.backup)
    results = checker.scan_folder(folder, fix=args.fix)

    if not args.fix and results:
        print()
        print("💡 Chạy lại với --fix để tự động sửa lỗi:")
        print(f"   python fix_encoding.py {args.folder} --fix")


if __name__ == "__main__":
    main()
