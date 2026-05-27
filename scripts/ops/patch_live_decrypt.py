from pathlib import Path
p = Path(r'C:\Dev\MTC_Download\download_one_completed_live_decrypt.py')
s = p.read_text(encoding='utf-8')
old1 = """def normalize_chapter_title(name: str, index: int) -> str:
    s = html.unescape(str(name or f'Chương {index}')).strip()
    s = re.sub(r'^\s*(?:chương|chuong)\s*(\d+)\s*[:.\-–—]?\s*', lambda m: f'Chương {m.group(1)}: ', s, flags=re.I)
    if not re.match(r'^Chương\s+\d+', s, re.I):
        s = f'Chương {index}: {s}'
    return s.strip(' .') + ('' if s.rstrip().endswith(('!', '?')) else ('.' if s.rstrip().endswith('.') else ''))

"""
new1 = old1 + """def sanitize_path_component(s: str) -> str:
    s = str(s or '')
    s = CONTROL_RE.sub('', s)
    s = s.replace('�', '')
    s = re.sub(r'\s+', ' ', s).strip()
    return s

"""
old2 = """        try:
            plain, decrypted = maybe_decrypt(content)
            title = normalize_chapter_title(data.get('name') or ch.get('name') or f'Chương {i}', i)
            write_plain_chapter(fpath, title, plain)
            ok += 1
            print(f'  OK decrypted={decrypted} written={fpath.name}', flush=True)
"""
new2 = """        try:
            plain, decrypted = maybe_decrypt(content)
            idx = int(ch.get('index') or i)
            title = normalize_chapter_title(data.get('name') or ch.get('name') or f'Chương {idx}', idx)
            safe_fname = sanitize_path_component(chapter_filename(ch, i))
            safe_title = sanitize_path_component(title)
            safe_fpath = book_dir / safe_fname
            write_plain_chapter(safe_fpath, safe_title, plain)
            ok += 1
            print(f'  OK decrypted={decrypted} written={safe_fpath.name}', flush=True)
"""
if old1 not in s:
    raise SystemExit('old1 not found')
if old2 not in s:
    raise SystemExit('old2 not found')
s = s.replace(old1, new1, 1)
s = s.replace(old2, new2, 1)
p.write_text(s, encoding='utf-8')
print('patched', str(p))
