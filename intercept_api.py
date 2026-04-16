#!/usr/bin/env python3
"""Intercept API calls to find encryption key in headers or responses."""
import requests
from pathlib import Path
import json

def test_api_endpoints():
    """Test API endpoints to see response format."""
    session = requests.Session()
    session.headers.update({
        "User-Agent": "MTC/1.0",
        "Accept": "application/json",
    })

    # Load token if exists
    token_file = Path('data/token.txt')
    if token_file.exists():
        token = token_file.read_text().strip()
        session.headers["Authorization"] = f"Bearer {token}"
        print(f"Using token: {token[:20]}...")
    else:
        print("No token found, trying without auth...")

    base_url = "https://api.mtruyen.com/api/v1"

    # Test endpoints
    endpoints = [
        "/books/1",  # Get book info
        "/chapters/1",  # Get chapter
        "/config",  # App config
        "/settings",  # Settings
    ]

    print("\nTesting API endpoints...")
    print("=" * 60)

    for endpoint in endpoints:
        try:
            url = base_url + endpoint
            print(f"\nGET {url}")
            resp = session.get(url, timeout=10)

            print(f"Status: {resp.status_code}")
            print(f"Headers: {dict(resp.headers)}")

            if resp.status_code == 200:
                data = resp.json()
                print(f"Response keys: {list(data.keys())}")

                # Look for encryption key in response
                response_str = json.dumps(data)
                if 'key' in response_str.lower() or 'secret' in response_str.lower():
                    print(f"*** Found key/secret in response! ***")
                    print(json.dumps(data, indent=2)[:500])

                # Save response
                output = Path(f'api_response_{endpoint.replace("/", "_")}.json')
                output.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding='utf-8')
                print(f"Saved to {output}")

        except Exception as e:
            print(f"Error: {e}")

    print("\n" + "=" * 60)
    print("Check api_response_*.json files for encryption keys")

if __name__ == "__main__":
    test_api_endpoints()
