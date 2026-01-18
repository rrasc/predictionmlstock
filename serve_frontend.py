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

    # Start server
    with socketserver.TCPServer(("", PORT), MyHTTPRequestHandler) as httpd:
        print(f"\n{'='*60}")
        print(f"🚀 ML Trading System Frontend Server")
        print(f"{'='*60}")
        print(f"\n✅ Server running at: http://localhost:{PORT}")
        print(f"📁 Serving directory: {DIRECTORY}/")
        print(f"\n📊 Open in browser: http://localhost:{PORT}\n")
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
