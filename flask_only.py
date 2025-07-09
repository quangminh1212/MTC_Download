# -*- coding: utf-8 -*-
"""
Flask only test
"""

import socket
from flask import Flask

def find_free_port(start_port=5000, max_port=5100):
    """Tìm port khả dụng"""
    for port in range(start_port, max_port):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('localhost', port))
                return port
        except OSError:
            continue
    return None

# Initialize Flask app
app = Flask(__name__)

@app.route('/')
def index():
    return "Hello World!"

if __name__ == '__main__':
    print("Starting Flask only app...", flush=True)
    
    port = find_free_port()
    if port is None:
        print("No free port found", flush=True)
        exit(1)
    
    print(f"Starting on port {port}...", flush=True)
    
    try:
        app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)
    except Exception as e:
        print(f"Error: {e}", flush=True)
        import traceback
        traceback.print_exc()
