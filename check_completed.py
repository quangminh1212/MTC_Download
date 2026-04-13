import json, sys
sys.stdout.reconfigure(encoding='utf-8')
with open('data/all_books.json', encoding='utf-8') as f:
    books = json.load(f)

completed = [b for b in books if b.get('status_name', '') == 'Hoàn thành' or b.get('state') == 'completed' or b.get('status') == 2]

print(f"Found {len(completed)} completed books.")
for b in completed[:12]:
    print(f"{b['id']}: {b['name']} ({b['chapter_count']} ch) - status_name: {b.get('status_name')}")
