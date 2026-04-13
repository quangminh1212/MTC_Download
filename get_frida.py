"""Download frida-server for android-x86_64 matching our frida version."""
import sys, urllib.request, lzma, os
sys.stdout.reconfigure(encoding='utf-8')

import frida
version = frida.__version__
print(f'frida version: {version}')

url = f'https://github.com/frida/frida/releases/download/{version}/frida-server-{version}-android-x86_64.xz'
print(f'Downloading: {url}')

outfile = 'frida-server'
xzfile = 'frida-server.xz'

if os.path.exists(outfile):
    print(f'Already exists: {outfile} ({os.path.getsize(outfile)} bytes)')
else:
    print('Downloading...', flush=True)
    try:
        urllib.request.urlretrieve(url, xzfile, lambda n, bs, ts: print(f'  {n*bs/1024/1024:.1f}/{ts/1024/1024:.1f} MB', end='\r', flush=True) if ts>0 else None)
        print('\nDownload complete!')
        
        print('Extracting xz...')
        with lzma.open(xzfile, 'rb') as xz_f:
            data = xz_f.read()
        with open(outfile, 'wb') as f:
            f.write(data)
        os.remove(xzfile)
        print(f'Extracted: {outfile} ({os.path.getsize(outfile)} bytes)')
    except Exception as e:
        print(f'Error: {e}')
        print('Trying alternative URL format...')
        # Try without the architecture suffix variations
        alt_urls = [
            f'https://github.com/frida/frida/releases/download/{version}/frida-server-{version}-android-x86_64.xz',
        ]

print('Done.')
