import json, re, sys, time
from pathlib import Path
sys.path.insert(0, r"C:\Dev\MTC_Download\scripts")
sys.path.insert(0, r"C:\Dev\MTC_Download\scripts\download")
from mtc_downloader import MTCDownloader
from download_completed_to_mtc import chapter_filename

ROOT = Path(r"C:\dev\mtc_continune")
OUT = Path(r"C:\Dev\MTC_Download\logs\mtc_continune_verified_missing_info_map.json")
chap_re = re.compile(r"(?i)^Chương\s+(\d+)\b.*\.txt$")
seed = {
"Biên Soạn Tiểu Thuyết Bọn Hắn Đều Cho Là Ta Là Nhân Vật Chính": [150294],
"Huyền Huyễn Nguyên Lai Ta Là Tuyệt Thế Võ Thần": [107396],
"Hàn Môn Kiêu Sĩ": [105732,130141,140643,139039],
"Hàn Môn Quật Khởi Ta Võ Đạo Nghịch Tập Kiếp Sống": [136469],
"Hàn Đông Tận Thế Một Cỗ Xe Buýt Lưu Lãng Toàn Cầu": [145025],
"Hải Dương Cầu Sinh Từ Bè Gỗ Bắt Đầu Đăng Nhập": [106599],
"Hải Dương Tai Biến Bắt Đầu Thức Tỉnh Sss Cấp Thiên Phú": [148026,143709],
"Hải Đảo Toàn Dân Thả Câu Ta Độc Lấy Được Sử Thi Thiên Phú": [132616],
"Hệ Thống Tu Luyện Ức Vạn Lần": [150359],
"Hồng Lâu Xuân": [145729],
"Hồng Thủy Tận Thế Ta Tại Huyền Vũ Trên Lưng Xây Gia Viên": [145981],
"Không Biết Hàng Lâm Ta Có Vô Địch Lĩnh Vực": [122242],
"Không Thể Trường Sinh Ta Không Thể Làm Gì Khác Ngoài Vô Hạn Chuyển Thế": [137995],
"Khắc Mệnh Tu Hành Từ Cẩm Y Vệ Bắt Đầu Trường Sinh": [136646],
"Kim Bảng Hiện Thế Trẫm Hoàng Hậu Dĩ Nhiên Là Võ Tắc Thiên": [111955],
"Kinh Ngạc Của Ta Hoa Quả Toàn Bộ Là Thiên Tài Địa Bảo": [144380],
"Ký Túc Xá Cầu Sinh Ta Bị Mặc Định Của Hệ Thống Toàn Tuyển D": [138039],
"Toàn Dân Cầu Sinh Không Có Kim Thủ Chỉ Cũng Muốn Cẩu Được": [146340],
"Từ Tiên Lại Vững Vàng Thành Đại Thiên Tôn": [147101],
}

def local_info(folder: Path):
    idxs=[]
    names=[]
    for p in folder.glob('*.txt'):
        m=chap_re.match(p.name)
        if not m:
            continue
        idxs.append(int(m.group(1)))
        names.append(p.name)
    idxs=sorted(set(idxs))
    return idxs, set(names)

def remote_summary(d, bid: int):
    page=1
    count=0
    indexes=set()
    first_file=None
    last_file=None
    name_hits=0
    while True:
        data=d.get_chapters(bid,page=page,limit=100)
        arr=(data or {}).get('data') or []
        if not arr:
            break
        arr=sorted(arr, key=lambda c:int(c.get('index') or 0))
        for i, ch in enumerate(arr, 1):
            idx = int(ch.get('index') or ((page-1)*100+i))
            indexes.add(idx)
            fn = chapter_filename(ch, idx)
            if first_file is None:
                first_file = fn
            last_file = fn
            if fn in local_names:
                name_hits += 1
        count += len(arr)
        if len(arr) < 100:
            break
        page += 1
        time.sleep(0.05)
    return count, indexes, first_file, last_file, name_hits

d=MTCDownloader()
results=[]
for folder_name, ids in seed.items():
    folder=ROOT/folder_name
    local_idxs, local_names = local_info(folder)
    candidates=[]
    for bid in ids:
        detail=(d.get_book_detail(bid) or {}).get('data') or {}
        remote_count, remote_indexes, first_remote, last_remote, name_hits = remote_summary(d,bid)
        missing = sorted(remote_indexes - set(local_idxs))
        extra = sorted(set(local_idxs) - remote_indexes)
        candidates.append({
            'book_id': bid,
            'book_name': detail.get('name'),
            'chapter_count': detail.get('chapter_count'),
            'latest_index': detail.get('latest_index'),
            'remote_count': remote_count,
            'local_count': len(local_idxs),
            'missing_count': len(missing),
            'extra_count': len(extra),
            'name_hits': name_hits,
            'first_remote_file': first_remote,
            'last_remote_file': last_remote,
            'first_local_file': min(local_names) if local_names else None,
            'missing_first50': missing[:50],
            'extra_first50': extra[:50],
        })
    candidates.sort(key=lambda r:(-r['name_hits'], r['missing_count']+r['extra_count'], abs((r['remote_count'] or 0)-len(local_idxs))))
    results.append({'folder': folder_name, 'chosen': candidates[0] if candidates else None, 'candidates': candidates})
OUT.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding='utf-8')
print(str(OUT))
for r in results:
    c=r['chosen'] or {}
    print(f"{r['folder']} -> {c.get('book_id')} {c.get('book_name')} local={c.get('local_count')} remote={c.get('remote_count')} missing={c.get('missing_count')} extra={c.get('extra_count')} hits={c.get('name_hits')}")
