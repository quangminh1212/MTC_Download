import sys, json, time
from pathlib import Path

# Add current dir to sys.path so mtc module can be imported
sys.path.insert(0, str(Path(__file__).resolve().parent))

from mtc.pipeline import download_via_api, _HAS_API_DEPS

def main():
    sys.stdout.reconfigure(encoding='utf-8')
    if not _HAS_API_DEPS:
        print("Missing API dependencies (requests, pycryptodome, ftfy).")
        return

    json_path = Path('data/all_books.json')
    if not json_path.exists():
        print(f"Error: {json_path} not found.")
        return

    with open(json_path, encoding='utf-8') as f:
        books = json.load(f)

    # Filter completed books
    completed = [b for b in books if str(b.get('status_name', '')).strip().lower() == 'hoàn thành' 
                                  or str(b.get('state', '')).lower() == 'completed' 
                                  or b.get('status') == 2]
    
    target_books = completed[:12]
    print(f"Bắt đầu tải {len(target_books)} truyện hoàn thành hoàn toàn thông qua API (không cần tọa độ hay lướt trang)...")

    for i, book in enumerate(target_books):
        book_id = book['id']
        book_name = book['name']
        chapter_count = book.get('chapter_count', 0)
        
        print(f"\n{'='*50}\n[{i+1}/{len(target_books)}] #{book_id} - {book_name} ({chapter_count} chương)\n{'='*50}")
        try:
            result = download_via_api(
                book_name=book_name,
                book_id=book_id,
                ch_end=chapter_count if chapter_count > 0 else None,
                log_fn=lambda msg: print(f"  {msg}")
            )
            print(f"> Kết quả tải {book_name}:", result.get('reason', 'Thành công' if result.get('success') else 'Thất bại'))
        except Exception as e:
            print(f"> Lỗi nghiêm trọng khi tải {book_name}: {e}")
        
        # Ngủ một chút giữa các truyện để tránh rate limit
        time.sleep(2)

    print("\nHoàn tất quá trình tải thử 12 truyện hoàn thành.")

if __name__ == '__main__':
    main()
