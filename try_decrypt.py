"""
Test decryption theory: iv_field = KEY(16) + IV(16) + marker(4)
This would mean encryption key is embedded in the same response (obfuscation, not security).
"""
import requests, base64, sys
sys.stdout.reconfigure(encoding='utf-8')

try:
    from Crypto.Cipher import AES
    from Crypto.Util.Padding import unpad
    CRYPTO = 'pycryptodome'
except ImportError:
    try:
        from Cryptodome.Cipher import AES
        from Cryptodome.Util.Padding import unpad
        CRYPTO = 'pycryptodome'
    except:
        CRYPTO = None
        print("No crypto library, trying install...")

if not CRYPTO:
    import subprocess
    subprocess.run([sys.executable, '-m', 'pip', 'install', 'pycryptodome', '-q'])
    from Crypto.Cipher import AES
    from Crypto.Util.Padding import unpad
    CRYPTO = 'pycryptodome'

print(f"Using: {CRYPTO}")

BASE = 'https://android.lonoapp.net/api'
HEADERS = {'Accept': 'application/json', 'User-Agent': 'NovelFeverApp/1.0'}

def decrypt_chapter(chapter_id):
    r = requests.get(f'{BASE}/chapters/{chapter_id}', headers=HEADERS, timeout=10)
    data = r.json()['data']
    
    raw_content = data['content']
    content_bytes = base64.b64decode(raw_content + '==')
    
    # Parse JSON structure
    start = b'{"iv":"'
    sep = b'","value":"'
    end = b'"}'
    
    iv_pos = content_bytes.find(start) + len(start)
    val_pos = content_bytes.find(sep, iv_pos)
    end_pos = content_bytes.rfind(end)
    
    iv_raw = content_bytes[iv_pos:val_pos]   # raw bytes of iv field
    value_b64 = content_bytes[val_pos + len(sep):end_pos]
    ciphertext = base64.b64decode(value_b64 + b'==')
    
    print(f"\nChapter {chapter_id}: {data['name']}")
    print(f"IV field: {len(iv_raw)} bytes = {iv_raw.hex()}")
    print(f"Ciphertext: {len(ciphertext)} bytes (= {len(ciphertext)/16:.1f} blocks)")
    
    # Theory 1: KEY = iv_field[0:16], IV = iv_field[16:32]
    hypotheses = [
        ("key=iv[0:16], iv=iv[16:32]",  iv_raw[:16],  iv_raw[16:32]),
        ("key=iv[16:32], iv=iv[0:16]",  iv_raw[16:32], iv_raw[:16]),
        ("key=iv[0:32], iv=iv_field",   iv_raw[:32],   iv_raw[:16]),  # AES-256
        ("key=iv[4:36], iv=iv[0:16]",   iv_raw[4:36],  iv_raw[:16]),  # 32-byte key after offset
        ("key=iv[0:16], iv=iv[20:36]",  iv_raw[:16],   iv_raw[20:36]),
        # Try 32-byte key
        ("key=iv[0:32](AES256), iv=iv[0:16]", iv_raw[:32], iv_raw[:16]),
    ]
    
    for name, key_bytes, iv_bytes in hypotheses:
        if len(key_bytes) not in (16, 24, 32) or len(iv_bytes) != 16:
            continue
        try:
            cipher = AES.new(key_bytes, AES.MODE_CBC, iv_bytes)
            plaintext = cipher.decrypt(ciphertext)
            # Check first 200 bytes for Vietnamese/readable text
            sample = plaintext[:200]
            # Count printable/Vietnamese-looking bytes
            printable = sum(1 for b in sample if 0x20 <= b <= 0x7e)
            # High bytes (Vietnamese UTF-8 uses 0xc0-0xff range)
            highbytes = sum(1 for b in sample if b >= 0x80)
            printable_pct = (printable + highbytes) / len(sample) * 100
            
            print(f"  [{name}]: key={key_bytes.hex()[:16]}... -> {printable_pct:.0f}% readable")
            if printable_pct > 70:
                print(f"    ** POSSIBLE MATCH **")
                try:
                    text = plaintext.rstrip(b'\x00\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0a\x0b\x0c\x0d\x0e\x0f\x10')
                    text = unpad(text, 16)
                    decoded = text[:300].decode('utf-8', errors='replace')
                    print(f"    TEXT: {decoded}")
                except Exception as e:
                    decoded = plaintext[:300].decode('utf-8', errors='replace')
                    print(f"    RAW: {decoded}")
        except Exception as e:
            print(f"  [{name}]: ERROR {e}")
    
    return iv_raw, ciphertext

# Test on known chapter
iv1, ct1 = decrypt_chapter(21589884)

# Fetch a second chapter to see if iv fields differ (confirming random per-chapter key)
print("\n" + "="*60)
r = requests.get(f'{BASE}/chapters?filter[book_id]=139039&limit=3', headers=HEADERS, timeout=10)
chaps = r.json()['data']
for c in chaps[1:3]:
    iv2, ct2 = decrypt_chapter(c['id'])
