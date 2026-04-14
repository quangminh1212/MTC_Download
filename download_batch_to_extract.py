#!/usr/bin/env python3
"""Download multiple novels to extract folder."""
import sys
from pathlib import Path
from mtc.downloader import download_batch, load_catalog, refresh_catalog

# Set output to extract folder
EXTRACT_DIR = Path(__file__).parent / "extract" / "novels"

def main():
    print(f"📥 Tải truyện vào: {EXTRACT_DIR}")
    print("=" * 60)
    
    # Check arguments
    refresh = "--refresh" in sys.argv
    completed_only = "--completed" in sys.argv
    limit = None
    
    if "--limit" in sys.argv:
        idx = sys.argv.index("--limit")
        if idx + 1 < len(sys.argv):
            limit = int(sys.argv[idx + 1])
    
    # Load or refresh catalog
    if refresh:
        print("🔄 Đang cập nhật catalog...")
        books = refresh_catalog(log_fn=print)
    else:
        books = load_catalog()
        if not books:
            print("❌ Catalog trống! Chạy với --refresh để cập nhật.")
            return
    
    print(f"📚 Tìm thấy {len(books)} truyện trong catalog")
    
    # Apply limit
    if limit:
        books = books[:limit]
        print(f"   Giới hạn: {limit} truyện đầu tiên")
    
    # Filter by status
    status_filter = "hoàn thành" if completed_only else None
    if completed_only:
        print("   Chỉ tải truyện hoàn thành")
    
    print("\n" + "=" * 60)
    
    # Download
    result = download_batch(
        books,
        output_dir=EXTRACT_DIR,
        log_fn=print,
        skip_existing=True,
        status_filter=status_filter,
    )
    
    print("\n" + "=" * 60)
    print("📊 Kết quả:")
    print(f"   Tổng số: {result['total']}")
    print(f"   ✅ Thành công: {result['ok']}")
    print(f"   ❌ Thất bại: {result['fail']}")
    print(f"   ⊘ Bỏ qua: {result['skipped']}")


if __name__ == "__main__":
    main()
