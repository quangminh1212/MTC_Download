from pathlib import Path
import re
ROOT=Path(r'C:\Dev\MTC\Siêu Dự Bị')

# Better cleanup for residual garbage at beginning of chapter files
chapter_pattern=re.compile(r'(Ch\w*\s*\d+\s*:)', re.IGNORECASE)

def clean_head(text):
    # normalize mojibake from mis-decoded utf8
    for enc in ['latin1','cp1252']:
        try:
            candidate=text.encode(enc,errors='ignore').decode('utf-8',errors='ignore')
            if candidate.count('Ã') < text.count('Ã'):
                text=candidate
        except Exception:
            pass

    # locate probable real start
    markers=['Chương ','Chuong ','Thành phố ','Biến cố','Tony Tèo','Trường Sa','Phút thứ','-PULL OVER']
    idx=None
    for m in markers:
        i=text.find(m)
        if i!=-1:
            idx=i if idx is None else min(idx,i)
    # regex marker like "Chuong 16:" with broken accents removed
    m=chapter_pattern.search(text)
    if m:
        i=m.start()
        idx=i if idx is None else min(idx,i)

    if idx is not None and 0 < idx < 800:
        text=text[idx:]

    # remove obvious binary garbage runs at start line
    lines=text.splitlines()
    if lines:
        first=lines[0]
        bad_ratio=sum(1 for ch in first if ord(ch)<32 and ch not in '\t\r\n')/max(1,len(first))
        if bad_ratio>0.05 or any(x in first for x in ['(>R','긲','}pyng','}päy','Biáº','TrÆ°']):
            # drop first line if second line looks valid
            if len(lines)>1 and len(lines[1].strip())>0:
                lines=lines[1:]
        text='\n'.join(lines)

    # normalize excessive blank lines at top
    text=text.lstrip('\ufeff\n\r\t ')
    return text

fixed=0
for p in ROOT.glob('Chương *.txt'):
    s=p.read_text(encoding='utf-8',errors='replace')
    t=clean_head(s)
    if t!=s:
        p.write_text(t,encoding='utf-8')
        fixed+=1
print('fixed_head',fixed)
