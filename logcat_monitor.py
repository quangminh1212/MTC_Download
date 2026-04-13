"""
Monitor logcat for HTTP requests while user navigates the app.
This will capture book IDs and chapter IDs from API call URLs.
"""
import subprocess, threading, time, re, sys
sys.stdout.reconfigure(encoding='utf-8')

ADB = r'C:\Program Files\BlueStacks_nxt\HD-Adb.exe'
DEV = '127.0.0.1:5555'

def adb(cmd):
    r = subprocess.run([ADB, '-s', DEV, 'shell', cmd],
                       capture_output=True, text=True, encoding='utf-8', errors='replace')
    return r.stdout.strip()

# Clear logcat first
subprocess.run([ADB, '-s', DEV, 'logcat', '-c'], capture_output=True)
print("Logcat cleared. Now open your app and navigate to one of the target novels.", flush=True)
print("I will capture all network requests for 60 seconds...", flush=True)
print("="*60, flush=True)

# Start logcat capture
proc = subprocess.Popen(
    [ADB, '-s', DEV, 'logcat', '-v', 'raw', '-s', '*:V'],
    stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    text=True, encoding='utf-8', errors='replace'
)

# Also start a broader capture
proc2 = subprocess.Popen(
    [ADB, '-s', DEV, 'logcat', '-v', 'raw'],
    stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    text=True, encoding='utf-8', errors='replace'
)

interesting_lines = []

def capture(p, label):
    for line in p.stdout:
        line = line.strip()
        # Look for anything related to lonoapp, chapters, books, or API calls
        if any(kw in line.lower() for kw in ['lonoapp', 'chapters', '/books/', 'novelfever', 'chapter_id', 'book_id', 'api/', '/api']):
            print(f'[{label}] {line}', flush=True)
            interesting_lines.append((label, line))
        # Also look for HTTP requests
        elif any(kw in line for kw in ['https://', 'GET /', 'POST /', 'HTTP', '200 OK', 'Request']):
            print(f'[{label}] {line}', flush=True)
            interesting_lines.append((label, line))

t1 = threading.Thread(target=capture, args=(proc, 'All'), daemon=True)
t1.start()

try:
    for i in range(60, 0, -5):
        print(f"  ... {i}s remaining. Navigate to a chapter now! ...", flush=True)
        time.sleep(5)
except KeyboardInterrupt:
    pass

proc.terminate()
proc2.terminate()

print("\n" + "="*60)
print(f"Captured {len(interesting_lines)} interesting lines")
if interesting_lines:
    print("Summary:")
    for label, line in interesting_lines:
        print(f"  {line}")

# Parse book/chapter IDs from captured URLs
all_urls = [line for _, line in interesting_lines if 'lonoapp' in line.lower()]
print("\nLonoapp URLs found:")
for url in all_urls:
    # Extract numbers that could be IDs
    ids = re.findall(r'\d{4,}', url)
    print(f"  URL: {url}")
    print(f"  IDs: {ids}")
