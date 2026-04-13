"""Find i0, a0, and all rotation IIFEs in the JS."""
import sys, re
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

with open('app_bundle.js', 'r', encoding='utf-8') as f:
    js = f.read()

print('=== a0 function definitions ===')
for m in re.finditer(r'function a0\b', js):
    print(f'  pos={m.start()}: {js[m.start():m.start()+150]}')
print()

print('=== $0 assignments near decrypt ===')
for m in re.finditer(r'\$0\s*=', js):
    print(f'  pos={m.start()}: {js[m.start():m.start()+100]}')
print()

print('=== i0 function definition ===')
for m in re.finditer(r'function i0\b|function\s+i0\s*\(', js):
    print(f'  pos={m.start()}: {js[m.start():m.start()+200]}')
print()

print('=== All rotation IIFEs: })(FUNC, NUMBER) ===')
for m in re.finditer(r'\}\)\(([a-zA-Z_$][a-zA-Z0-9_$]*),\s*(-?\d+)\)', js):
    func = m.group(1)
    num = m.group(2)
    print(f'  pos={m.start()}: func={func!r}, target={num}  ctx={js[m.start()-50:m.start()+80]}')
print()

# Also look for the window[] decrypt/encrypt assignments to understand which a0 they use
print('=== window decrypt assignment context ===')
for m in re.finditer(r'window\[', js):
    ctx = js[m.start():m.start()+100]
    if 'pt' in ctx:
        print(f'  pos={m.start()}: {ctx}')
