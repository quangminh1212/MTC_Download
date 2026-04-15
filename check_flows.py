import requests
import json
import base64

def check_flows():
    try:
        resp = requests.get("http://127.0.0.1:8081/flows", timeout=5)
        flows = resp.json()
        print(f"Captured {len(flows)} flows")
        
        found = False
        for flow in flows:
            req = flow.get('request', {})
            host = req.get('host', '')
            
            if 'lonoapp.net' not in host and 'api' not in host.lower():
                continue
                
            headers = req.get('headers', [])
            for header_pair in headers:
                if isinstance(header_pair, list) and len(header_pair) >= 2:
                    header = header_pair[0].lower()
                    value = header_pair[1]
                    if 'key' in header or 'auth' in header or 'token' in header:
                        print(f"Request Header [{header}]: {value}")
                        
            resp_data = flow.get('response', {})
            resp_headers = resp_data.get('headers', [])
            for header_pair in resp_headers:
                if isinstance(header_pair, list) and len(header_pair) >= 2:
                    header = header_pair[0].lower()
                    value = header_pair[1]
                    if 'key' in header or 'secret' in header:
                        print(f"Response Header [{header}]: {value}")
                        
            content = resp_data.get('content')
            if content and isinstance(content, str):
                pass # it's base64 encoded by mitmproxy API usually or utf-8 strings
                
    except Exception as e:
        print("Error checking flows:", e)

if __name__ == '__main__':
    check_flows()
