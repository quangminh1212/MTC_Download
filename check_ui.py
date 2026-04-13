import sys, re
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
with open('ui_dump.xml', encoding='utf-8', errors='replace') as f:
    data = f.read()
# All text and content-desc values
items = re.findall(r'(?:text|content-desc)="([^"]+)"', data)
seen = set()
print("=== All visible text ===")
for i in items:
    c = i.strip()
    if c and c not in seen:
        seen.add(c)
        print(repr(c[:100]))
nodes = re.findall(r'content-desc="([^"]{3,})"', data)
print(f"\nTotal nodes with content-desc (3+): {len(nodes)}")
