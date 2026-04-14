import os
import sys

def encode_safe(obj):
    return str(obj).encode('utf-8', 'replace').decode('utf-8')

sys.stdout.reconfigure(encoding='utf-8')

for name in os.listdir('exports'):
    if name.endswith('.txt'):
        path = os.path.join('exports', name)
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read(4000)
            
        print("======== ", name, " ========")
        print(encode_safe(repr(content[:1500])))
        break
