"""
1. Inspect metruyencv.com/api/chapters/21589884 response body (200 but non-JSON)
2. Check android.lonoapp.net/api/books/139039 full response
3. Look for key in web JS bundles from metruyencv.com
4. Try authenticated mobile API (if login endpoint exists)
"""
import sys, base64, hmac, hashlib, requests, json, re
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# ============================================================
# 1. Check web chapter API response body
# ============================================================
print('=== metruyencv.com chapter API ===')
try:
    r = requests.get('https://metruyencv.com/api/chapters/21589884', timeout=15,
                     headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                              'Accept': 'application/json, text/plain, */*',
                              'Referer': 'https://metruyencv.com/'})
    print(f'  Status: {r.status_code}')
    print(f'  Content-Type: {r.headers.get("Content-Type", "?")}')
    ct = r.text[:500]
    print(f'  Body (first 500 chars): {ct}')
except Exception as e:
    print(f'  ERROR: {e}')

print()

# Try with different headers / auth
print('=== metruyencv.com chapter with auth headers ===')
try:
    r2 = requests.get('https://metruyencv.com/api/chapters/21589884', timeout=15,
                      headers={'User-Agent': 'MeTruyenCV/1.0',
                               'Accept': 'application/json',
                               'X-Requested-With': 'XMLHttpRequest'})
    print(f'  Status: {r2.status_code}')
    print(f'  Content-Type: {r2.headers.get("Content-Type", "?")}')
    if r2.headers.get('Content-Type','').startswith('application/json'):
        d = r2.json()
        print(f'  Keys: {list(d.keys()) if isinstance(d,dict) else type(d)}')
    else:
        print(f'  Body: {r2.text[:200]}')
except Exception as e:
    print(f'  ERROR: {e}')

print()

# ============================================================
# 2. Check books/139039 full response
# ============================================================
print('=== android.lonoapp.net/api/books/139039 ===')
try:
    r3 = requests.get('https://android.lonoapp.net/api/books/139039', timeout=15)
    d3 = r3.json()
    print(json.dumps(d3, indent=2, ensure_ascii=False)[:2000])
except Exception as e:
    print(f'  ERROR: {e}')

print()

# ============================================================
# 3. Check metruyencv.com for JS bundle URLs
# ============================================================
print('=== Searching metruyencv.com JS for key ===')
try:
    r4 = requests.get('https://metruyencv.com/', timeout=15,
                      headers={'User-Agent': 'Mozilla/5.0'})
    html = r4.text
    # Find JS bundle URLs
    js_urls = re.findall(r'src="([^"]*\.js[^"]*)"', html)
    print(f'  Found {len(js_urls)} JS URLs on homepage')
    for u in js_urls[:10]:
        print(f'    {u}')
except Exception as e:
    print(f'  ERROR: {e}')

print()

# ============================================================
# 4. Check if there's a login endpoint
# ============================================================
print('=== android.lonoapp.net login/auth endpoints ===')
auth_endpoints = [
    '/api/auth/login',
    '/api/login',
    '/api/user/login',
    '/api/v1/auth/login',
]
for ep in auth_endpoints:
    try:
        url = f'https://android.lonoapp.net{ep}'
        # Just OPTIONS/HEAD to see if it exists
        r5 = requests.options(url, timeout=5)
        print(f'  OPTIONS {ep}: {r5.status_code}')
    except Exception as e:
        print(f'  OPTIONS {ep}: {e}')

print()

# ============================================================
# 5. List all returns from api/books - full dump
# ============================================================  
print('=== android.lonoapp.net/api/books full list ===')
try:
    r6 = requests.get('https://android.lonoapp.net/api/books', timeout=15)
    d6 = r6.json()
    if 'data' in d6:
        books = d6['data']
        if isinstance(books, list):
            print(f'  {len(books)} books:')
            for b in books:
                keys = list(b.keys())
                print(f'    id={b.get("id")} title={b.get("title","?")[:30]} keys={keys}')
        else:
            print(json.dumps(d6, indent=2, ensure_ascii=False)[:1000])
    else:
        print(json.dumps(d6, indent=2, ensure_ascii=False)[:1000])
except Exception as e:
    print(f'  ERROR: {e}')

print('\nDone.')
