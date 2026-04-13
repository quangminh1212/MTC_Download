"""Find and display the rotation function body next to x1."""
import sys, re
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

with open('app_bundle.js', 'r', encoding='utf-8') as f:
    js = f.read()

# x1 function is at pos=25875, length ~1416, so ends around pos 27332
# The rotation IIFE should be directly after x1 definition
# Search for the pattern near x1 end
x1_end_marker = '};return x1=function(){return x},x1()}'
pos = js.find(x1_end_marker)
print(f'x1 return pattern at pos: {pos}')
if pos == -1:
    # try alternate
    alt = 'return x1=function()'
    pos = js.find(alt)
    print(f'alt marker at pos: {pos}')
    
# Show what comes after x1 function (next 1000 chars)
if pos < 0:
    # look at area around pos 27291
    pos = 27000
print(f'\nContext after x1 function (pos {pos} to {pos+1500}):')
snippet = js[pos:pos+1500]
print(snippet)
