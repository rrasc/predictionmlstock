"""
Simple HTTP server to serve the frontend dashboard
Run: python serve_frontend.py
Access: http://localhost:8000
"""

import http.server
import socketserver
import os
from pathlib import Path

# Configuration
PORT = 8000
DIRECTORY = "frontend"

class MyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def end_headers(self):
        # Add CORS headers
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        super().end_headers()

def main():
    # Check if frontend directory exists
    if not Path(DIRECTORY).exists():
        print(f"Error: {DIRECTORY} directory not found!")
        print("Please make sure the frontend directory exists.")
        return

    # Get local network IP address
    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # Connect to a remote server to get local IP
        s.connect(('8.8.8.8', 80))
        local_ip = s.getsockname()[0]
    except:
        local_ip = '127.0.0.1'
    finally:
        s.close()

    # Start server
    with socketserver.TCPServer(("", PORT), MyHTTPRequestHandler) as httpd:
        print(f"\n{'='*60}")
        print(f"🚀 ML Trading System Frontend Server")
        print(f"{'='*60}")
        print(f"\n✅ Server running successfully!")
        print(f"📁 Serving directory: {DIRECTORY}/")
        print(f"\n🖥️  Desktop: http://localhost:{PORT}")
        print(f"📱 Mobile:  http://{local_ip}:{PORT}")
        print(f"\n💡 Make sure your mobile is on the same WiFi network!")
        print(f"{'='*60}")
        print(f"Press Ctrl+C to stop the server\n")

        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print(f"\n\n{'='*60}")
            print("🛑 Server stopped")
            print(f"{'='*60}\n")

if __name__ == "__main__":
    main()
