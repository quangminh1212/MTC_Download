import zipfile, re

apk = 'base.apk'

# Scan raw bytes – URLs and API keywords in native libs
url_re = re.compile(rb'https?://[\x20-\x7e]{5,180}')
api_words = [b'api/v', b'/chapter', b'/novel', b'/book', b'/story', b'base_url', b'baseUrl', b'endpoint']

found_urls = set()
found_keywords = {}

with zipfile.ZipFile(apk) as z:
    names = z.namelist()
    print(f'Files in APK: {len(names)}')
    for name in names:
        try:
            data = z.read(name)
            for m in url_re.findall(data):
                url = m.decode('utf-8', errors='replace').rstrip('"\'  \x00\t\n\r')
                found_urls.add(url)
            for kw in api_words:
                idx = 0
                while True:
                    pos = data.find(kw, idx)
                    if pos < 0:
                        break
                    ctx = data[max(0,pos-40):pos+100]
                    ctx_str = ctx.decode('utf-8', errors='replace')
                    if sum(1 for c in ctx_str if c.isprintable()) > len(ctx_str)*0.7:
                        key = kw.decode()
                        found_keywords.setdefault(key, set()).add(f'[{name}] ' + repr(ctx_str))
                    idx = pos + 1
        except Exception:
            pass

print('\n=== URLs found ===')
for url in sorted(found_urls):
    print(url[:200])

print('\n=== API keyword contexts ===')
for kw, ctxs in sorted(found_keywords.items()):
    print(f'\n-- {kw} --')
    for c in list(ctxs)[:10]:
        print(c[:200])
