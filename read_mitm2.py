"""Parse mitmdump capture - show all flows."""
import sys
sys.stdout.reconfigure(encoding='utf-8')

from mitmproxy.io import FlowReader

flows = []
with open('mitm_capture.bin', 'rb') as f:
    reader = FlowReader(f)
    try:
        for flow in reader.stream():
            flows.append(flow)
    except Exception as e:
        print(f'Parse stopped at {len(flows)}: {e}')

print(f'Total flows: {len(flows)}')
print()

# Show all flows not related to books listing (to find app traffic)
for i, flow in enumerate(flows):
    if not hasattr(flow, 'request'):
        continue
    req = flow.request
    url = req.pretty_url
    resp = flow.response if hasattr(flow, 'response') and flow.response else None
    
    # Show all auth headers 
    auth = req.headers.get('authorization', req.headers.get('Authorization', ''))
    
    if 'chapters' in url or auth or ('books' not in url and 'books/search' not in url):
        print(f'[{i}] {req.method} {url}')
        for k, v in req.headers.items():
            if k.lower() in ('authorization', 'x-api-key', 'x-auth-token', 'cookie', 'token'):
                print(f'     Header {k}: {v!r}')
        if resp:
            ct = resp.headers.get('content-type', '')
            print(f'     -> {resp.status_code} ({len(resp.content)} bytes)')
            if 'json' in ct and len(resp.content) < 3000:
                text = resp.text
                # Look for chapter content
                if 'content' in text or 'chapters' in text:
                    print(f'     JSON: {text[:500]}')
