"""Parse mitmdump binary capture and look for decrypted HTTPS content."""
import sys, os
sys.stdout.reconfigure(encoding='utf-8')

# Try to parse with mitmproxy API
try:
    from mitmproxy.io import FlowReader
    from mitmproxy.net.http import http1
    import io
    
    flows = []
    with open('mitm_capture.bin', 'rb') as f:
        reader = FlowReader(f)
        try:
            for flow in reader.stream():
                flows.append(flow)
        except Exception as e:
            print(f'Parse error after {len(flows)} flows: {e}')
    
    print(f'Total flows: {len(flows)}')
    for i, flow in enumerate(flows[:50]):
        if hasattr(flow, 'request'):
            req = flow.request
            resp = flow.response if hasattr(flow, 'response') and flow.response else None
            print(f'  [{i}] {req.method} {req.pretty_url}')
            if resp:
                ct = resp.headers.get('content-type', '')
                print(f'       -> {resp.status_code} {ct} ({len(resp.content)} bytes)')
                # If it's JSON, show it
                if 'json' in ct and len(resp.content) < 2000:
                    print(f'       JSON: {resp.text[:200]}')
            else:
                print(f'       -> (no response)')

except ImportError:
    print('mitmproxy not available as Python package, checking raw binary...')
    with open('mitm_capture.bin', 'rb') as f:
        data = f.read()
    print(f'File size: {len(data)} bytes')
    print(f'First 200 bytes hex: {data[:200].hex()}')
    print(f'First 200 bytes repr: {data[:200]!r}')

except Exception as e:
    print(f'Error: {type(e).__name__}: {e}')
    import traceback; traceback.print_exc()
