"""Show the rotation IIFE for x1 and compute the hash."""
import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

with open('app_bundle.js', 'r', encoding='utf-8') as f:
    js = f.read()

# Rotation IIFE ends at pos=21512 ("})(x1,650736)")
# Let's show the code AROUND that position
print('=== Context around pos 21512 (x1 rotation end) ===')
# Show 2000 chars BEFORE pos 21512
start = max(0, 21512-2000)
print(js[start:21512+50])
