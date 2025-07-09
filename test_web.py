# -*- coding: utf-8 -*-
"""
Test web interface
"""

import requests
import time
import json

def test_web_interface():
    """Test web interface endpoints"""
    base_url = "http://localhost:5000"
    
    print("Testing web interface...", flush=True)
    
    try:
        # Test main page
        print("Testing main page...", flush=True)
        response = requests.get(f"{base_url}/")
        if response.status_code == 200:
            print("✅ Main page OK", flush=True)
        else:
            print(f"❌ Main page failed: {response.status_code}", flush=True)
            return False
        
        # Test config page
        print("Testing config page...", flush=True)
        response = requests.get(f"{base_url}/config")
        if response.status_code == 200:
            print("✅ Config page OK", flush=True)
        else:
            print(f"❌ Config page failed: {response.status_code}", flush=True)
            return False
        
        # Test download page
        print("Testing download page...", flush=True)
        response = requests.get(f"{base_url}/download")
        if response.status_code == 200:
            print("✅ Download page OK", flush=True)
        else:
            print(f"❌ Download page failed: {response.status_code}", flush=True)
            return False
        
        # Test API endpoints
        print("Testing API endpoints...", flush=True)
        
        # Test status API
        response = requests.get(f"{base_url}/api/status")
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print("✅ Status API OK", flush=True)
            else:
                print(f"❌ Status API failed: {data}", flush=True)
                return False
        else:
            print(f"❌ Status API failed: {response.status_code}", flush=True)
            return False
        
        # Test config API
        response = requests.get(f"{base_url}/api/config")
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print("✅ Config API OK", flush=True)
            else:
                print(f"❌ Config API failed: {data}", flush=True)
                return False
        else:
            print(f"❌ Config API failed: {response.status_code}", flush=True)
            return False
        
        print("🎉 All tests passed!", flush=True)
        return True
        
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server. Make sure it's running on port 5000", flush=True)
        return False
    except Exception as e:
        print(f"❌ Test failed: {e}", flush=True)
        return False

if __name__ == '__main__':
    success = test_web_interface()
    if success:
        print("\n✅ Web interface is working correctly!", flush=True)
    else:
        print("\n❌ Web interface has issues!", flush=True)
    
    input("Press Enter to exit...")
