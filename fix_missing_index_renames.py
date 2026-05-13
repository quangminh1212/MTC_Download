import re, shutil, json, sys
from pathlib import Path
if hasattr(sys.stdout,'reconfigure'): sys.stdout.reconfigure(encoding='utf-8', errors='replace')
ROOT=Path(r'C:\Dev\MTC')
pat=re.compile(r'^(Chương\s+)(\d+)(\b.*\.txt)$', re.I)
changes=[]

def renumber_range(folder, start, end, delta):
    d=ROOT/folder
    files=[]
    for p in d.glob('*.txt'):
        m=pat.match(p.name)
        if not m: continue
        idx=int(m.group(2))
        if start<=idx<=end:
            files.append((idx,p,m))
    # avoid collisions: if shifting down, process ascending via temp; if up, descending via temp
    temp=[]
    for idx,p,m in files:
        tp=p.with_name(f'__tmp_renumber_{idx}_{p.name}')
        p.rename(tp)
        temp.append((idx,tp,m))
    for idx,tp,m in temp:
        new_idx=idx+delta
        new_name=f'{m.group(1)}{new_idx}{m.group(3)}'
        dest=d/new_name
        if dest.exists():
            raise RuntimeError(f'collision {dest}')
        tp.rename(dest)
        changes.append({'folder':folder,'old':tp.name,'new':dest.name,'op':'renumber'})

def rename_one(folder, old_name, new_name):
    d=ROOT/folder
    old=d/old_name
    new=d/new_name
    if old.exists() and not new.exists():
        old.rename(new)
        changes.append({'folder':folder,'old':old_name,'new':new_name,'op':'rename_one'})

# Remote metadata confirms these are display chapter numbers, but local filenames used remote index.
rename_one("Devil'S Path Quỷ Giới Và Nhẫn Giới", "Chương 33 Quỷ Nhân làng Sương Mù Zabuza tiếp theo.txt", "Chương 32 Quỷ Nhân làng Sương Mù Zabuza tiếp theo.txt")
renumber_range('Marvel Ta Là Tiểu Chiến Sỹ Họ Stark', 54, 129, -7)
renumber_range('Nhị Thứ Nguyên Thần Tượng Âm Nhạc', 173, 377, -1)

# Remove old bracket/dash duplicates when normalized counterpart exists; keep normalized file.
for d in ROOT.iterdir():
    if not d.is_dir() or d.name=='.git': continue
    for p in list(d.glob('*.txt')):
        norm=p.name.replace('(','').replace(')','').replace('[','').replace(']','').replace('-',' ').replace('–',' ').replace('—',' ')
        norm=re.sub(r'\s+',' ',norm).strip()
        q=d/norm
        if q != p and q.exists():
            # keep q; delete p only if sizes are close or q is non-empty
            if q.stat().st_size >= max(200, int(p.stat().st_size*0.90)):
                p.unlink()
                changes.append({'folder':d.name,'old':p.name,'new':q.name,'op':'delete_duplicate_normalized'})

out=Path(r'C:\Dev\MTC_Download\logs\fix_missing_index_renames.json')
out.write_text(json.dumps(changes,ensure_ascii=False,indent=2),encoding='utf-8')
print(str(out))
print('changes',len(changes))
