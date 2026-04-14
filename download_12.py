import sys, json, time, io
from pathlib import Path

# Add current dir to sys.path so mtc module can be imported
sys.path.insert(0, str(Path(__file__).resolve().parent))

from mtc.pipeline import download_via_api, _HAS_API_DEPS, _api_session, _fetch_chapter_list

def main():
    if not _HAS_API_DEPS:
        print("Missing API dependencies (requests, pycryptodome, ftfy).")
        return

    json_path = Path('data/all_books.json')
    if not json_path.exists():
        print(f"Error: {json_path} not found.")
        return

    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Khởi chạy script download_12.py")
    with open(json_path, encoding='utf-8') as f:
        books = json.load(f)

    # Filter completed books
    completed = [b for b in books if str(b.get('status_name', '')).strip().lower() == 'hoàn thành' 
                                  or str(b.get('state', '')).lower() == 'completed' 
                                  or b.get('status') == 2]
    
    target_books = completed[:12]
    print(f"Bắt đầu tải {len(target_books)} truyện hoàn thành hoàn toàn thông qua API (không cần tọa độ hay lướt trang)...")

    session = _api_session()

    for i, book in enumerate(target_books):
        book_id = book['id']
        book_name = book['name']
        chapter_count = book.get('chapter_count', 0)
        
        print(f"\n{'='*50}\n[{i+1}/{len(target_books)}] #{book_id} - {book_name} ({chapter_count} chương)\n{'='*50}")
        try:
            # Phân tích rootcause trực tiếp từ API trước khi tải
            print(f"> [DEBUG API] Kiểm tra tính trạng bản quyền/VIP của {book_name}...")
            chs = _fetch_chapter_list(session, book_id)
            locked_count = sum(1 for c in chs if c.get('unlock_price', 0) > 0 or c.get('is_locked'))
            
            if locked_count > 0:
                print(f"  [WARNING] Phát hiện {locked_count}/{len(chs)} chương bị khóa (VIP/Paywall).")
                print("  [ROOTCAUSE] Vì chúng ta đang dùng API ẩn danh (không có mã Token đăng nhập chứa khóa VIP của app), server backend lonoapp/MTC sẽ chỉ trả về đoạn Preview ngắn ~500 ký tự cho các chương này thay vì nội dung gốc. Từ chương 100 trở đi thường là VIP. Đây là lý do nội dung tải về bị thiếu sót!")
            
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
