#!/usr/bin/env python3
"""
Download novels with automatic decryption if key is available.
Usage: python download_and_decrypt.py "Tên Truyện"
"""
import sys
import json
import base64
from pathlib import Path
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad
import re

# Import existing modules
from mtc.api import create_session, search_books, get_book_info, get_chapters, get_chapter_content
from mtc.utils import safe_name, ensure_dir

def load_encryption_key():
    """Load encryption key if available."""
    key_files = ['WORKING_KEY.txt', 'APP_KEY.txt', 'data/app_key.txt']

    for key_file in key_files:
        path = Path(key_file)
        if path.exists():
            content = path.read_text(encoding='utf-8')
            # Extract base64 key
            match = re.search(r'base64:([A-Za-z0-9+/=]+)', content)
            if match:
                return f"base64:{match.group(1)}"

    return None

def decrypt_content(encrypted_b64, app_key):
    """Decrypt Laravel encrypted content."""
    try:
        encrypted_json = json.loads(base64.b64decode(encrypted_b64))
        iv = base64.b64decode(encrypted_json['iv'])
        encrypted_value = base64.b64decode(encrypted_json['value'])

        if app_key.startswith('base64:'):
            key = base64.b64decode(app_key[7:])
        else:
            key = app_key.encode()

        cipher = AES.new(key, AES.MODE_CBC, iv)
        decrypted = unpad(cipher.decrypt(encrypted_value), AES.block_size)
        return decrypted.decode('utf-8')
    except:
        return None

def download_book_with_decrypt(book_name, output_dir=None):
    """Download book and decrypt if key available."""
    if output_dir is None:
        output_dir = Path('extract/novels')

    # Load encryption key
    app_key = load_encryption_key()
    if app_key:
        print(f"[+] Found encryption key: {app_key[:30]}...")
    else:
        print("[!] No encryption key found - content will be encrypted")
        print("[!] See HUONG_DAN_TIM_KEY.md for instructions")

    # Create session
    session = create_session()

    # Search book
    print(f"\n[*] Searching for: {book_name}")
    results = search_books(session, book_name)

    if not results:
        print(f"[-] Book not found: {book_name}")
        return False

    book = results[0]
    book_id = book['id']
    book_title = book['name']

    print(f"[+] Found: {book_title} (ID: {book_id})")

    # Get chapters
    chapters = get_chapters(session, book_id)
    if not chapters:
        print("[-] No chapters found")
        return False

    print(f"[+] Total chapters: {len(chapters)}")

    # Create output directory
    book_dir = ensure_dir(output_dir / safe_name(book_title))

    # Download chapters
    success_count = 0
    decrypted_count = 0

    for i, chapter in enumerate(chapters, 1):
        ch_id = chapter['id']
        ch_title = chapter.get('title', f"Chương {i}")

        print(f"[{i}/{len(chapters)}] {ch_title}...", end=' ')

        # Get content
        content = get_chapter_content(session, book_id, ch_id)

        if not content:
            print("FAILED")
            continue

        # Try to decrypt if key available
        if app_key:
            # Check if content is encrypted
            match = re.search(r'(eyJ[A-Za-z0-9+/=]+)', content)
            if match:
                encrypted_b64 = match.group(1)
                decrypted = decrypt_content(encrypted_b64, app_key)

                if decrypted:
                    content = decrypted
                    decrypted_count += 1
                    print("OK (decrypted)")
                else:
                    print("OK (encrypted - decrypt failed)")
            else:
                print("OK (plain text)")
        else:
            print("OK (encrypted)")

        # Save
        ch_file = book_dir / f"{i:04d}_{safe_name(ch_title)}.txt"
        ch_file.write_text(content, encoding='utf-8')
        success_count += 1

    print(f"\n[+] Download complete!")
    print(f"    Total: {success_count}/{len(chapters)} chapters")
    if app_key:
        print(f"    Decrypted: {decrypted_count} chapters")
    print(f"    Location: {book_dir}")

    return True

def main():
    if len(sys.argv) < 2:
        print("Usage: python download_and_decrypt.py <book_name>")
        print("Example: python download_and_decrypt.py 'Võ Luyện Đỉnh Phong'")
        return

    book_name = " ".join(sys.argv[1:])

    print("=" * 60)
    print("MTC Novel Downloader with Auto-Decryption")
    print("=" * 60)

    download_book_with_decrypt(book_name)

if __name__ == "__main__":
    main()
