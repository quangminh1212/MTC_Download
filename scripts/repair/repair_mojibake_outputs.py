from pathlib import Path
import re
ROOT=Path(r'C:\Dev\MTC\Siêu Dự Bị')

def fix_mojibake(s):
    # remove leading binary garbage before common chapter markers
    markers=['Chương ', 'ChÆ°Æ¡ng ', 'Tony', 'Biến ', 'Biáº¿n ']
    best=None
    for m in markers:
        i=s.find(m)
        if i!=-1:
            best=i if best is None else min(best,i)
    if best is not None and 0 < best < 200:
        s=s[best:]
    # common UTF-8 read as latin1/cp1252 then saved as unicode
    candidates=[s]
    for enc in ['latin1','cp1252']:
        try:
            candidates.append(s.encode(enc, errors='ignore').decode('utf-8', errors='ignore'))
        except Exception:
            pass
    def score(t):
        bad=sum(t.count(x) for x in ['Ã','Æ','áº','á»','Ä','Â','â'])
        good=sum(t.count(x) for x in ['ư','ơ','đ','ă','ê','ô','á','à','ế','ệ','ộ','ờ','ữ','Đ','Ư','Ơ'])
        return good*5-bad*10+len(t)/10000
    return max(candidates,key=score)

fixed=0
for p in ROOT.glob('Chương *.txt'):
    try:
        s=p.read_text(encoding='utf-8',errors='replace')
        t=fix_mojibake(s)
        if t!=s:
            p.write_text(t,encoding='utf-8')
            fixed+=1
    except Exception as e:
        print('ERR',p,e)
print('fixed',fixed)
