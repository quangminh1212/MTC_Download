import json
import re
from pathlib import Path
from download_completed_to_mtc import clean_filename

BOOKS = [
    {"id": 112190, "name": "Biển Vô Tận: Toàn Chức Vua Câu Cá", "expected": 181},
    {"id": 121843, "name": "Bắt Đầu Từ Kiếm Ma", "expected": 344},
    {"id": 100677, "name": "Công Cuộc Bị 999 Em Gái Chinh Phục", "expected": 1106},
    {"id": 127805, "name": "Tiền Hạo Kiếp Tây Du", "expected": 51},
]
ROOT=Path(r'C:\Dev\MTC')
pat=re.compile(r'(?i)(?:chương|chuong)\s*(\d+)')
report=[]
for b in BOOKS:
    d=ROOT/clean_filename(b['name'])
    rows=[]; seen={}
    if d.exists():
        for p in d.glob('*.txt'):
            m=pat.search(p.name)
            if m:
                n=int(m.group(1)); seen[n]=p.stat().st_size
                rows.append({'chapter':n,'name':p.name,'size':p.stat().st_size})
    missing=[i for i in range(1,b['expected']+1) if i not in seen]
    small=[r for r in sorted(rows,key=lambda x:x['chapter']) if r['size']<5000]
    report.append({'id':b['id'],'name':b['name'],'expected':b['expected'],'folder':str(d),'files':len(rows),'missing':missing[:50],'missing_count':len(missing),'small_count':len(small),'small_first':small[:20]})
out=Path(r'C:\Dev\MTC_Download\logs\target_books_gap_report.json')
out.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(str(out))
