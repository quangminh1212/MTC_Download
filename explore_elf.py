"""
Step 1: Find ELF .rodata section in libapp.so (much smaller than full binary).
Step 2: Fetch chapters from 2 DIFFERENT books to see if they use the same key.
Step 3: Scan .rodata with stride=1 for both AES-128 and AES-256.
"""
import sys, base64, hmac, hashlib, requests, struct
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from Crypto.Cipher import AES

def get_chapter_data(cid):
    r = requests.get(f'https://android.lonoapp.net/api/chapters/{cid}', timeout=15)
    d = r.json()
    if 'data' not in d:
        print(f'  FAILED for {cid}: {d}')
        return None
    chap = d['data']
    content_str = chap['content']
    book_id = chap.get('book_id')
    pad = '=' * (-len(content_str) % 4)
    outer = base64.b64decode(content_str + pad)
    sep = b'","value":"'
    p2 = outer.find(sep); vs = p2 + len(sep)
    ct_end = outer.find(b'"', vs)
    iv_raw = outer[7:p2]; val_b64 = outer[vs:ct_end]
    mac_s = outer.find(b'"mac":"'); mac_e = outer.find(b'"', mac_s+7)
    mac_hex = outer[mac_s+7:mac_e].decode('ascii')
    ct = base64.b64decode(val_b64 + b'==')
    return {'iv_raw': iv_raw, 'val_b64': val_b64, 'mac_hex': mac_hex, 
            'ct': ct, 'ct_last': ct[-16:], 'ct_prev': ct[-32:-16], 'book_id': book_id}

# Book 1: already known
print('=== Fetching chapters from 2 different books ===')
print('Chapter 21589884 (known book)...')
c1 = get_chapter_data(21589884)
print(f'  book_id={c1["book_id"]}, mac={c1["mac_hex"][:20]}...')

# Book 2: Try a different book listing
# First, find chapters from another book via /api/books
print('\nSearching for another book...')
rb = requests.get('https://android.lonoapp.net/api/books?limit=5', timeout=15)
print(f'  /api/books status={rb.status_code}')
if rb.status_code == 200:
    bd = rb.json()
    print(f'  keys={list(bd.keys() if isinstance(bd, dict) else ["array"])}')
    if isinstance(bd, dict) and 'data' in bd:
        books = bd['data']
        if isinstance(books, list):
            print(f'  {len(books)} books')
            for b in books[:3]:
                print(f'    id={b.get("id")} name={str(b.get("name",""))[:40]}')
    print(f'  raw (first 300): {str(bd)[:300]}')

# Try fetching a chapter from a slightly different ID range (likely same or different book)
print('\nChapter 21598093...')
c2 = get_chapter_data(21598093)
if c2:
    print(f'  book_id={c2["book_id"]}, mac={c2["mac_hex"][:20]}...')

# Try to find a chapter from the downloads folder (different book)
# The 3 books in downloads/ - let's try fetching book list directly
print('\nLooking for chapters from different books...')
# Check if there's a "book chapters list" API
for book_id in [139039, 50000, 100000, 150000]:
    r = requests.get(f'https://android.lonoapp.net/api/books/{book_id}/chapters?limit=3', timeout=10)
    if r.status_code == 200:
        bchap = r.json()
        print(f'  book {book_id}: status=200 keys={list(bchap.keys() if isinstance(bchap, dict) else [])}')
        if isinstance(bchap, dict) and 'data' in bchap:
            items = bchap['data']
            if isinstance(items, list) and items:
                chap_ids = [x.get('id') for x in items[:2] if x.get('id')]
                print(f'    chapter ids: {chap_ids}')

# ============================================================
# ELF .rodata parsing
# ============================================================
print('\n=== Parsing ELF sections of libapp.so ===')
lib_path = r'.\libapp_extracted\libapp.so'
with open(lib_path, 'rb') as f:
    lib = f.read()

magic = lib[:4]
if magic != b'\x7fELF':
    print('ERROR: not an ELF file')
    sys.exit(1)

bitclass = lib[4]  # 1=32bit, 2=64bit
endian = lib[5]    # 1=little, 2=big
print(f'ELF: class={bitclass}bit endian={"little" if endian==1 else "big"}')

if bitclass == 2:  # 64-bit
    # Elf64_Ehdr: 64 bytes
    e_shoff = struct.unpack_from('<Q', lib, 0x28)[0]   # section header offset
    e_shentsize = struct.unpack_from('<H', lib, 0x3A)[0]
    e_shnum = struct.unpack_from('<H', lib, 0x3C)[0]
    e_shstrndx = struct.unpack_from('<H', lib, 0x3E)[0]
    print(f'  shoff={e_shoff:#x} shentsize={e_shentsize} shnum={e_shnum} shstrndx={e_shstrndx}')
    
    def read_shdr(idx):
        off = e_shoff + idx * e_shentsize
        sh_name   = struct.unpack_from('<I', lib, off)[0]
        sh_type   = struct.unpack_from('<I', lib, off+4)[0]
        sh_flags  = struct.unpack_from('<Q', lib, off+8)[0]
        sh_addr   = struct.unpack_from('<Q', lib, off+16)[0]
        sh_offset = struct.unpack_from('<Q', lib, off+24)[0]
        sh_size   = struct.unpack_from('<Q', lib, off+32)[0]
        return {'name_off': sh_name, 'type': sh_type, 'flags': sh_flags,
                'offset': sh_offset, 'size': sh_size}
    
    # Read string table
    strtab_hdr = read_shdr(e_shstrndx)
    strtab_off = strtab_hdr['offset']
    
    print('\nAll ELF sections:')
    rodata_regions = []
    for i in range(e_shnum):
        hdr = read_shdr(i)
        name_off = hdr['name_off']
        n_end = lib.find(b'\x00', strtab_off + name_off)
        sname = lib[strtab_off+name_off:n_end].decode('ascii', errors='replace')
        sz_kb = hdr['size'] // 1024
        print(f'  [{i:3d}] {sname:20s} off={hdr["offset"]:#010x} size={hdr["size"]:>10d} ({sz_kb:6d}KB) type={hdr["type"]}')
        if sname in ('.rodata', '__TEXT', '__DATA', '.data', '.data.rel.ro', '.got', '.dynstr') or 'const' in sname.lower():
            rodata_regions.append((sname, hdr['offset'], hdr['size']))
    
    print(f'\nCandidate sections for key scanning: {[(n, f"{off:#x}", f"{sz}B") for n,off,sz in rodata_regions]}')
else:
    print(f'32-bit ELF - different parsing needed')
    # Elf32_Ehdr  
    e_shoff = struct.unpack_from('<I', lib, 0x20)[0]
    e_shentsize = struct.unpack_from('<H', lib, 0x2E)[0]
    e_shnum = struct.unpack_from('<H', lib, 0x30)[0]
    e_shstrndx = struct.unpack_from('<H', lib, 0x32)[0]
    print(f'  shoff={e_shoff:#x} shentsize={e_shentsize} shnum={e_shnum} shstrndx={e_shstrndx}')
    rodata_regions = []

print('\nDone.')
