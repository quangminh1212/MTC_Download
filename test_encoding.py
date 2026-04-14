import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from download.api import create_session, fetch_chapter_text

s = create_session()
text = fetch_chapter_text(s, {"id": 26500054})
print(f"Title: {text.splitlines()[0][:80]}")
print(f"Length: {len(text)}")
sample = text[350:550]
print(f"Sample: {sample}")
if "vá»±c" in text or "Ã" in text:
    print("FAIL: mojibake still present")
else:
    print("PASS: encoding looks correct")
