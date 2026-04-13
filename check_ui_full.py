"""check_ui_full.py - Show all nodes including ones without text."""
import sys, re, xml.etree.ElementTree as ET
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

with open('ui_dump.xml', encoding='utf-8', errors='replace') as f:
    data = f.read()

try:
    root = ET.fromstring(data)
except ET.ParseError as e:
    print(f'Parse error: {e}')
    sys.exit(1)

print("=== ALL CLICKABLE NODES ===")
for node in root.iter():
    if node.get('clickable') != 'true':
        continue
    cls    = node.get('class', '').split('.')[-1]
    text   = (node.get('text', '') or '').strip()
    desc   = (node.get('content-desc', '') or '').strip()
    bounds = node.get('bounds', '')
    print(f"  [{cls}] text={repr(text[:50]):<55} desc={repr(desc[:50]):<55} {bounds}")

print("\n=== ALL VIEWS WITH BOUNDS IN CONTENT AREA (y>120) ===")
for node in root.iter():
    if node.get('class') not in ('android.view.View', 'android.widget.ImageView'):
        continue
    bounds = node.get('bounds', '')
    rect = re.match(r'\[(\d+),(\d+)\]\[(\d+),(\d+)\]', bounds)
    if not rect:
        continue
    x1, y1, x2, y2 = int(rect.group(1)), int(rect.group(2)), int(rect.group(3)), int(rect.group(4))
    if y1 < 120:
        continue
    if (x2-x1) < 10 or (y2-y1) < 10:
        continue
    text = (node.get('text', '') or '').strip()
    desc = (node.get('content-desc', '') or '').strip()
    clk  = node.get('clickable', 'false')
    print(f"  [{clk}] ({x1},{y1})-({x2},{y2})  text={repr(text[:30]):<35} desc={repr(desc[:40]):<45}")
