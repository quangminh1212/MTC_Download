import base64
import json
from pathlib import Path

sample_file = Path(r"extract\novels\Chiến Lược Gia Thiên Tài\Chương 1.txt")
with open(sample_file, 'r', encoding='utf-8') as f:
    lines = f.readlines()
    if len(lines) > 2:
        text = lines[2].strip()
    else:
        text = ""

text = text.replace(' ', '').replace('\n', '').replace('\r', '').strip()
print("Cleaned text length:", len(text))
try:
    missing_padding = len(text) % 4
    if missing_padding: text += '=' * (4 - missing_padding)
    raw = base64.b64decode(text)
    print("Decoded length:", len(raw))
    print("Has binary chars?", not raw.isascii())
    data = json.loads(raw)
    print("Keys:", data.keys())
    print("IV base64 encoded length:", len(data['iv']))
except Exception as e:
    print("Error:", e)
