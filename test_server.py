# -*- coding: utf-8 -*-
"""
Test server startup
"""

import sys
import socket

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

if __name__ == '__main__':
    print("Testing port finding...", flush=True)
    port = find_free_port()
    print(f"Found port: {port}", flush=True)
    
    if port is None:
        print("No free port found", flush=True)
        sys.exit(1)
    
    print("Starting Flask app...", flush=True)
    
    try:
        from flask import Flask
        from flask_socketio import SocketIO
        
        app = Flask(__name__)
        app.config['SECRET_KEY'] = 'test_key'
        socketio = SocketIO(app, cors_allowed_origins="*", async_mode='gevent', logger=False, engineio_logger=False)
        
        @app.route('/')
        def index():
            return "Hello World!"
        
        print(f"Starting server on port {port}...", flush=True)
        socketio.run(app, host='0.0.0.0', port=port, debug=False)
        
    except Exception as e:
        print(f"Error: {e}", flush=True)
        import traceback
        traceback.print_exc()
        sys.exit(1)
