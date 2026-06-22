import json, sys, re
from pathlib import Path
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
root=Path(r'C:\Dev\MTC')
pat=re.compile(r'(?i)(?:chương|chuong)\s*(\d+)')
books=['Marvel Ta Là Tiểu Chiến Sỹ Họ Stark','Nhị Thứ Nguyên Thần Tượng Âm Nhạc','Devil\'S Path Quỷ Giới Và Nhẫn Giới','Siêu Dự Bị']
for b in books:
    d=root/b
    idxs=[]
    for p in d.glob('*.txt'):
        m=pat.search(p.name)
        if m:
            idxs.append((int(m.group(1)),p.name,p.stat().st_size))
    idxs.sort(key=lambda x:x[0])
    nums=[x[0] for x in idxs]
    print('\n===',b,'===')
    print('count',len(nums),'min',min(nums) if nums else None,'max',max(nums) if nums else None)
    # print gaps in 1..expected from known
    if b=='Marvel Ta Là Tiểu Chiến Sỹ Họ Stark':
        exp=122
    elif b=='Nhị Thứ Nguyên Thần Tượng Âm Nhạc': exp=376
    elif b=="Devil'S Path Quỷ Giới Và Nhẫn Giới": exp=322
    else: exp=121
    missing=[i for i in range(1,exp+1) if i not in set(nums)]
    extra=[i for i in sorted(set(nums)) if i>exp]
    print('missing_first',missing[:20],'missing_count',len(missing))
    print('extra_gt_expected_first',extra[:20],'extra_count',len(extra))
    # show around important ranges
    ranges=[(28,36),(44,58),(166,176),(90,124)]
    for a,b2 in ranges:
        subset=[x for x in idxs if a<=x[0]<=b2]
        if subset:
            print(f'--{a}-{b2}--')
            for idx,name,size in subset[:60]:
                print(idx,'|',name,'|',size)
