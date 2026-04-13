"""
Brute-force the AES key by testing all candidate strings from libapp.so
against a live encrypted chapter from the API.

Strategy:
1. Fetch a chapter from a known public book
2. Extract IV and ciphertext
3. Test all printable ASCII strings (len 16, 24, 32) from libapp.so as keys
4. For each candidate: try AES-CBC decryption
5. Check if result is valid UTF-8

Also tests base64-decoded 16/24/32-byte values of base64 strings found in the binary.
"""

import os
import sys
import json
import base64
import requests
import struct
import time
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad
import urllib3
urllib3.disable_warnings()

API = "https://android.lonoapp.net/api"
SESS = requests.Session()
SESS.verify = False
SESS.timeout = 15

LIBAPP_PATH = r"C:\Dev\MTC_Download\libapp_extracted\libapp.so"

# -------------------------------------------------------
# Step 1: Get a fresh chapter from the API
# -------------------------------------------------------

def get_public_chapter():
    """Get book list, pick first book, get its first chapter ID."""
    print("[1] Getting public books...")
    r = SESS.get(f"{API}/books", params={"page": 1, "pageSize": 20})
    r.raise_for_status()
    d = r.json()
    
    # Find the data - might be nested
    if isinstance(d, dict):
        books = d.get("data", d.get("books", d.get("list", [])))
        if isinstance(books, dict):
            books = books.get("data", books.get("list", []))
    else:
        books = d
    
    print(f"    Got {len(books)} books")
    if not books:
        raise ValueError("No books found")
    
    # Take first book
    book = books[0]
    book_id = book.get("id") or book.get("book_id")
    print(f"    Using book: {book_id} - {str(book.get('title', ''))[:50]}")
    
    # Get chapter list
    print(f"[2] Getting chapter list for book {book_id}...")
    r = SESS.get(f"{API}/books/{book_id}/chapters", params={"page": 1, "pageSize": 5})
    r.raise_for_status()
    d = r.json()
    
    chapters = None
    if isinstance(d, dict):
        for key in ['data', 'chapters', 'list']:
            val = d.get(key)
            if isinstance(val, list):
                chapters = val
                break
            if isinstance(val, dict):
                for k2 in ['data', 'chapters', 'list']:
                    val2 = val.get(k2)
                    if isinstance(val2, list):
                        chapters = val2
                        break
            if chapters:
                break
    
    if not chapters:
        print(f"    Could not parse chapters. Response: {json.dumps(d, ensure_ascii=False)[:500]}")
        raise ValueError("No chapters found")
    
    ch = chapters[0]
    ch_id = ch.get("id") or ch.get("chapter_id")
    print(f"    Using chapter: {ch_id} - {str(ch.get('title', ''))[:50]}")
    return ch_id

def use_known_chapter():
    """Use already-known chapter IDs."""
    return 21589884  # From book 139039, used in previous sessions

def fetch_chapter(ch_id):
    """Fetch and parse chapter encryption data."""
    print(f"[3] Fetching chapter {ch_id}...")
    r = SESS.get(f"{API}/chapters/{ch_id}")
    r.raise_for_status()
    d = r.json()
    
    # Navigate to content
    content = None
    if isinstance(d, dict):
        data = d.get("data", d)
        if isinstance(data, dict):
            content = data.get("content")
        else:
            content = d.get("content")
    
    if not content:
        raise ValueError(f"No content in response: {json.dumps(d)[:500]}")
    
    print(f"    Content (b64 len): {len(content)}")
    
    # Decode and extract IV + ciphertext
    outer = base64.b64decode(content + "==")
    print(f"    Outer len: {len(outer)}")
    print(f"    First 10 bytes: {outer[:10]!r}")
    
    sep = b'","value":"'
    pos = outer.find(sep)
    if pos == -1:
        raise ValueError(f"Could not find separator in outer. First 100: {outer[:100]!r}")
    
    iv16 = outer[7:23]  # First 16 bytes of iv_field
    ct_b64 = outer[pos + 11:-2]  # base64 ciphertext
    ct = base64.b64decode(ct_b64 + b"==")
    
    print(f"    IV (hex): {iv16.hex()}")
    print(f"    CT length: {len(ct)} bytes (mod16={len(ct)%16})")
    
    return iv16, ct

# -------------------------------------------------------
# Step 2: Extract key candidates from libapp.so
# -------------------------------------------------------

def extract_string_candidates(libapp_path, lengths=(16, 24, 32)):
    """Extract all printable ASCII strings of exactly len from libapp.so."""
    print(f"\n[4] Reading libapp.so...")
    with open(libapp_path, "rb") as f:
        data = f.read()
    print(f"    Size: {len(data):,} bytes")
    
    candidates = set()
    
    for target_len in lengths:
        count = 0
        for i in range(len(data) - target_len):
            chunk = data[i:i + target_len]
            # Check: all bytes are printable ASCII (32-126)
            if all(32 <= b <= 126 for b in chunk):
                # Check neighboring bytes - real strings in code often have null-terminator or non-ASCII neighbors
                # But don't filter too strictly - try all printable sequences
                candidates.add((target_len, chunk))
                count += 1
        print(f"    Found {count:,} printable {target_len}-byte candidates")
    
    # Also extract base64 strings that decode to 16/24/32 bytes
    base64_chars = set(b'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=')
    for b64_len in (24, 32, 44):  # 24->16, 32->18, 44->32 bytes
        for i in range(len(data) - b64_len):
            chunk = data[i:i + b64_len]
            if all(b in base64_chars for b in chunk):
                try:
                    decoded = base64.b64decode(chunk)
                    if len(decoded) in (16, 24, 32):
                        candidates.add((len(decoded), decoded))
                except:
                    pass
    
    print(f"    Total unique candidates: {len(candidates):,}")
    return list(candidates)

# -------------------------------------------------------
# Step 3: Test each candidate
# -------------------------------------------------------

def test_candidate(key_bytes, iv, ct):
    """Return plaintext if key decrypts ct to valid UTF-8, else None."""
    try:
        cipher = AES.new(key_bytes, AES.MODE_CBC, iv)
        plain = unpad(cipher.decrypt(ct), 16)
        text = plain.decode("utf-8")
        return text
    except:
        return None

def brute_force(candidates, iv, ct):
    """Test all candidates. Return (key_bytes, plaintext) if found."""
    print(f"\n[5] Testing {len(candidates):,} candidates...")
    start = time.time()
    
    found = []
    for i, (key_len, key_bytes) in enumerate(candidates):
        if i % 10000 == 0 and i > 0:
            elapsed = time.time() - start
            rate = i / elapsed
            eta = (len(candidates) - i) / rate
            print(f"    {i:,}/{len(candidates):,} tested @ {rate:.0f}/s, ETA: {eta:.0f}s")
        
        result = test_candidate(key_bytes, iv, ct)
        if result is not None:
            print(f"\n[!!!] FOUND KEY!")
            print(f"      Key length: {key_len} bytes")
            print(f"      Key hex: {key_bytes.hex()}")
            print(f"      Key str: {repr(key_bytes)}")
            print(f"      Plaintext start: {result[:200]!r}")
            found.append((key_bytes, result))
    
    elapsed = time.time() - start
    print(f"\n    Done: {len(candidates):,} tested in {elapsed:.1f}s ({len(candidates)/elapsed:.0f}/s)")
    return found

# -------------------------------------------------------
# Main
# -------------------------------------------------------

def main():
    # Get encrypted chapter data
    try:
        ch_id = get_public_chapter()
    except Exception as e:
        print(f"Failed to get public chapter: {e}")
        print("Using known chapter ID...")
        ch_id = use_known_chapter()
    
    try:
        iv, ct = fetch_chapter(ch_id)
    except Exception as e:
        print(f"Failed to fetch chapter: {e}")
        sys.exit(1)
    
    # Extract candidates
    if not os.path.exists(LIBAPP_PATH):
        print(f"libapp.so not found at {LIBAPP_PATH}")
        print("Please run: adb -s emulator-5554 pull /data/app/com.novelfever*/base.apk ...")
        sys.exit(1)
    
    candidates = extract_string_candidates(LIBAPP_PATH)
    
    # Brute force
    found = brute_force(candidates, iv, ct)
    
    if found:
        print(f"\n{'='*60}")
        print(f"SUCCESS! Found {len(found)} key(s)!")
        for key_bytes, plain in found:
            print(f"  Key: {key_bytes.hex()}")
            print(f"  As string: {repr(key_bytes)}")
            print(f"  Plaintext: {plain[:500]}")
    else:
        print("\nNo key found in printable ASCII candidates.")
        print("Consider: raw binary 16/32-byte sequences from libapp.so")

if __name__ == "__main__":
    main()
