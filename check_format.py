import base64, requests

r = requests.get('https://android.lonoapp.net/api/chapters/21589884', timeout=15)
d = r.json()
content = d['data']['content']
print('content[:100]:', content[:100])
outer = base64.b64decode(content + '==')
print('outer len:', len(outer))
print('outer[:80] hex:', outer[:80].hex())
print('outer[:80] repr:', repr(outer[:80]))
print()
print('outer[0:7]   =', outer[0:7])

sep = b'","value":"'
pos = outer.find(sep)
print('separator "\\",\\"value\\":\\"" pos:', pos)
if pos >= 0:
    print('=> iv field outer[7:%d] = %d bytes' % (pos, pos-7))
    iv_field = outer[7:pos]
    print('   iv_field hex:', iv_field.hex())
    print('   iv_field repr:', repr(iv_field))
    vs = pos + len(sep)
    # Find the closing " of the value field (base64 chars don't include ")
    ct_end = outer.find(b'"', vs)
    print('value_start:', vs, '  ct_end:', ct_end)
    print('outer[ct_end:ct_end+20]:', repr(outer[ct_end:ct_end+20]))
    print('outer[-20:]:', repr(outer[-20:]))
    ct_b64_correct = outer[vs:ct_end]
    ct_b64_old = outer[vs:-2]
    print('ct_b64 (correct) len:', len(ct_b64_correct))
    print('ct_b64 (old -2) len:', len(ct_b64_old))
    ct = base64.b64decode(ct_b64_correct + b'==')
    print('ct len (correct):', len(ct))
    print('ct % 16 =', len(ct) % 16)
    # also try substrings to find proper IV interpretation
    print()
    print('=== IV analysis ===')
    print('iv_field len:', len(iv_field))
    # try: iv_field is a base64 string with some raw bytes - count valid b64 chars
    valid_b64 = b'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/='
    valid_count = sum(1 for b in iv_field if b in valid_b64)
    print('valid base64 chars in iv_field:', valid_count, 'out of', len(iv_field))
    print('iv_field last 4 bytes:', iv_field[-4:].hex(), repr(iv_field[-4:]))
