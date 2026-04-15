import base64
from pathlib import Path

sample_file = Path(r"extract\novels\Chiến Lược Gia Thiên Tài\Chương 1.txt")
with open(sample_file, 'r', encoding='utf-8') as f:
    lines = f.readlines()
    encrypted_content = lines[2].strip() if len(lines) > 2 else ""

print("Original base64 first 100:", encrypted_content[:100])
try:
    missing_padding = len(encrypted_content) % 4
    if missing_padding:
        encrypted_content += '='* (4 - missing_padding)
    decoded = base64.b64decode(encrypted_content)
    print("Decoded length:", len(decoded))
    print("Decoded first 100 repr:")
    print(repr(decoded[:100]))
except Exception as e:
    print("Error:", e)
