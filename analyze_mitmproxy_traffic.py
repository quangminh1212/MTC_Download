#!/usr/bin/env python3
"""Phân tích mitmproxy flow file để tìm APP_KEY."""
import sys
import json
from pathlib import Path

def analyze_flow_file(flow_file):
    """Phân tích mitmproxy flow file (format: JSON lines)."""
    print(f"Analyzing: {flow_file}")
    print("=" * 60)
    
    if not Path(flow_file).exists():
        print(f"❌ File not found: {flow_file}")
        return
    
    # Try to read as JSON lines
    try:
        with open(flow_file, 'r', encoding='utf-8') as f:
            flows = [json.loads(line) for line in f if line.strip()]
    except:
        print("⚠️  Not a JSON file. Trying binary format...")
        print("\nTo export mitmproxy flows to JSON:")
        print("  mitmdump -r traffic.flow -w traffic.json")
        return
    
    print(f"Found {len(flows)} flows")
    
    # Analyze each flow
    api_requests = []
    potential_keys = []
    decrypted_content = []
    
    for flow in flows:
        if 'request' not in flow:
            continue
        
        req = flow['request']
        resp = flow.get('response', {})
        
        # Check if it's API request
        if 'api.lonoapp.net' in req.get('host', ''):
            api_requests.append(flow)
            
            # Check headers for keys
            for header, value in req.get('headers', {}).items():
                if 'key' in header.lower() or 'auth' in header.lower():
                    potential_keys.append({
                        'source': 'request_header',
                        'header': header,
                        'value': value
                    })
            
            # Check response headers
            for header, value in resp.get('headers', {}).items():
                if 'key' in header.lower() or 'encrypt' in header.lower():
                    potential_keys.append({
                        'source': 'response_header',
                        'header': header,
                        'value': value
                    })
            
            # Check response content
            content = resp.get('content', '')
            if content and not content.startswith('eyJ'):
                # Not encrypted!
                decrypted_content.append({
                    'url': req.get('url', ''),
                    'content': content[:200]
                })
    
    # Display results
    print("\n" + "=" * 60)
    print("RESULTS")
    print("=" * 60)
    
    print(f"\n📊 API Requests: {len(api_requests)}")
    
    if potential_keys:
        print(f"\n✅ Found {len(potential_keys)} potential keys:")
        print("-" * 60)
        for key in potential_keys:
            print(f"\nSource: {key['source']}")
            print(f"Header: {key['header']}")
            print(f"Value: {key['value']}")
    else:
        print("\n❌ No encryption keys found in headers")
    
    if decrypted_content:
        print(f"\n✅ Found {len(decrypted_content)} decrypted responses:")
        print("-" * 60)
        for item in decrypted_content:
            print(f"\nURL: {item['url']}")
            print(f"Content: {item['content']}...")
    else:
        print("\n⚠️  All responses are encrypted")
    
    # Save detailed report
    report_file = Path("mitmproxy_analysis_report.json")
    report = {
        'total_flows': len(flows),
        'api_requests': len(api_requests),
        'potential_keys': potential_keys,
        'decrypted_content': decrypted_content
    }
    
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Detailed report saved to: {report_file}")

def main():
    if len(sys.argv) < 2:
        print("Usage: python analyze_mitmproxy_traffic.py <flow_file>")
        print("\nExamples:")
        print("  python analyze_mitmproxy_traffic.py traffic.json")
        print("  python analyze_mitmproxy_traffic.py traffic.flow")
        print("\nTo capture traffic with mitmproxy:")
        print("  mitmdump -w traffic.flow")
        print("\nTo convert flow to JSON:")
        print("  mitmdump -r traffic.flow -w traffic.json")
        return
    
    flow_file = sys.argv[1]
    analyze_flow_file(flow_file)

if __name__ == "__main__":
    main()
