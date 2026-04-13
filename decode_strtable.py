"""Find x1 string array by looking for '];return x1=' pattern."""
import requests, re, base64, sys
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

with open('app_bundle.js', 'r', encoding='utf-8') as f:
    js = f.read()

# The array ends with: ];return x1=function(){return x},x1()}
# Let's find that exact marker
end_marker = '];return x1=function'
pos = js.find(end_marker)
print(f'End marker at pos: {pos}')

if pos > 0:
    # Search backwards for the start of the array - look for opening [
    chunk = js[max(0, pos-50000):pos+50]
    # Find the last [ that could be array start
    start_bracket = chunk.rfind('[')
    print(f'Array start at offset: {start_bracket}')
    arr_text = chunk[start_bracket:]
    print(f'Array length: {len(arr_text)}')
    
    # Extract all quoted strings
    entries = re.findall(r'"([^"]*)"', arr_text)
    print(f'Total entries: {len(entries)}')
    
    # Find ch7CR
    idx = None
    for i, e in enumerate(entries):
        if e == 'ch7CR':
            idx = i
            break
    print(f'ch7CR at index: {idx}')
    if idx is not None:
        print(f'Entries around it: {entries[max(0,idx-5):idx+6]}')
    
    print(f'\nTotal entries: {len(entries)}')
    print(f'First 30: {entries[:30]}')
    print(f'Entries 100-120: {entries[100:120] if len(entries)>100 else "too short"}')
    
    if idx is None:
        # Maybe ch7CR isn't extracted cleanly - look for it differently  
        print('Searching raw...')
        pos2 = arr_text.find('ch7CR')
        if pos2 >= 0:
            print(f'  Found at raw pos {pos2}: {arr_text[max(0,pos2-20):pos2+30]}')
        import sys; sys.exit(1)
    
    # Now simulate rotation
    # a0(n) = x1()[n-130], with base 130
    # e(149) = x1()[19], e(169) = x1()[39] = "ch7CR", e(224) = x1()[94]
    # rotation: shuffled[i] = original[(i+k)%n]
    n = len(entries)
    k = (idx - 39) % n
    print(f'\nArray length: {n}, ch7CR orig pos: {idx}, needed rotation: k={k}')
    
    # Build shuffled array
    shuffled = [(i + k) % n for i in range(n)]
    # shuffled[i] = entries[(i + k) % n]... wait
    # "shift" means elements move left, so after shift k, element at position 0 was at position k
    # shuffled[i] = original_entries[(i + k) % n]
    
    def shuffled_get(i):
        return entries[(i + k) % n]
    
    # Verify e(169) = x1()[39] = "ch7CR"
    e169 = shuffled_get(39)
    print(f'e(169) = x1()[39] = {e169!r} (should be "ch7CR")')
    
    # Get e(149) = x1()[19] and e(224) = x1()[94]
    e149 = shuffled_get(19)
    e224 = shuffled_get(94)
    print(f'e(149) = x1()[19] = {e149!r}')
    print(f'e(224) = x1()[94] = {e224!r}')
    
    key_str = e149 + "ch7CR" + e224 + "Q"
    print(f'\nKey string: {key_str!r}')
    print(f'Key length: {len(key_str)}, bytes: {key_str.encode().hex()}')

    # Get chapter CT
    r0 = requests.get('https://android.lonoapp.net/api/chapters/21589884', timeout=15)
    d = r0.json()
    content = d['data']['content']
    outer = base64.b64decode(content + '==')
    sep = b'","value":"'
    p2 = outer.find(sep); vs = p2 + len(sep)
    ct_end = outer.find(b'"', vs)
    iv16 = outer[7:23]
    ct_ = base64.b64decode(outer[vs:ct_end] + b'==')
    print(f'CT: {len(ct_)}B, IV: {iv16.hex()}')

    def check(key_b, label='', test_ct=None, test_iv=None):
        tc = test_ct if test_ct is not None else ct_
        tiv = test_iv if test_iv is not None else iv16
        try:
            if len(key_b) not in (16,24,32): 
                # CryptoJS pads short keys with zero or truncates to valid lengths
                # Try all valid sizes by padding/truncating
                results = []
                for sz in (16,24,32):
                    kb = (key_b * ((sz//len(key_b))+1))[:sz]
                    results.append((kb, sz))
            else:
                results = [(key_b, len(key_b))]
            
            for kb, sz in results:
                try:
                    ecb = AES.new(kb, AES.MODE_ECB)
                    lp = bytes(a^b for a,b in zip(ecb.decrypt(tc[-16:]), tc[-32:-16]))
                    pv = lp[-1]
                    if not (1<=pv<=16) or any(lp[-i]!=pv for i in range(1,pv+1)): continue
                    pt = unpad(AES.new(kb, AES.MODE_CBC, tiv).decrypt(tc), 16)
                    t_ = pt.decode('utf-8')
                    viet = ['chuong','khong','nguoi','trong','duoc','la ']
                    score = sum(t_.lower().encode('ascii','ignore').decode().count(w) for w in viet)
                    print(f'  DECRYPTED! ({label}, {sz}B) score={score}: {repr(t_[:100])}')
                    if score >= 3: return kb
                except: pass
        except Exception as e:
            print(f'  Error: {e}')
        return None

    # Test key_str directly
    print('\n--- Testing key_str ---')
    k8 = key_str.encode('utf-8')
    result = check(k8, f'key_str_utf8')
    if result:
        print(f'*** KEY FOUND: {result.hex()} ***')
    else:
        # Also try key as IV with chapter IV approach
        # But first: test with iv = Utf8.parse(key) approach (web style)
        key_as_iv = k8[:16] if len(k8) >= 16 else (k8 * 2)[:16]
        print(f'\n--- Testing with IV = UTF8 key bytes ---')
        result2 = check(k8, 'key_with_own_iv', test_iv=key_as_iv)
        if result2:
            print(f'*** KEY FOUND (web style): {result2.hex()} ***')
    
    # Also try all rotations +/-5 in case my rotation math is off
    print('\n--- Testing nearby rotations ---')
    for dk in range(-5, 6):
        kk = (k + dk) % n
        e149t = entries[(19 + kk) % n]
        e224t = entries[(94 + kk) % n]
        key_try = e149t + "ch7CR" + e224t + "Q"
        if key_try != key_str:  # don't retest same
            kb = key_try.encode('utf-8')
            r = check(kb, f'rot+{dk}:{key_try!r}')
            if r: print(f'*** KEY FOUND at rot+{dk}: {r.hex()} ***')
