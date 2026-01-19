#!/usr/bin/env python3
"""
Instant Mobile Link - No Installation Required!
Uses Python-only solution with pyngrok for easy mobile access
"""

import http.server
import socketserver
import threading
import time
import sys
import subprocess
from pathlib import Path

PORT = 8000
FRONTEND_DIR = "frontend"

class ColoredOutput:
    """Colored terminal output"""
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    END = '\033[0m'

    @staticmethod
    def success(text):
        print(f"{ColoredOutput.GREEN}✅ {text}{ColoredOutput.END}")

    @staticmethod
    def info(text):
        print(f"{ColoredOutput.CYAN}ℹ️  {text}{ColoredOutput.END}")

    @staticmethod
    def warning(text):
        print(f"{ColoredOutput.YELLOW}⚠️  {text}{ColoredOutput.END}")

    @staticmethod
    def error(text):
        print(f"{ColoredOutput.RED}❌ {text}{ColoredOutput.END}")

    @staticmethod
    def header(text):
        print(f"\n{ColoredOutput.BOLD}{ColoredOutput.CYAN}{'='*60}{ColoredOutput.END}")
        print(f"{ColoredOutput.BOLD}{ColoredOutput.CYAN}{text}{ColoredOutput.END}")
        print(f"{ColoredOutput.BOLD}{ColoredOutput.CYAN}{'='*60}{ColoredOutput.END}\n")

class FrontendServer:
    """Simple frontend HTTP server"""

    def __init__(self, port=8000, directory="frontend"):
        self.port = port
        self.directory = directory
        self.server_thread = None

    def start(self):
        """Start the server in a background thread"""

        class Handler(http.server.SimpleHTTPRequestHandler):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, directory=FRONTEND_DIR, **kwargs)

            def end_headers(self):
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate')
                super().end_headers()

            def log_message(self, format, *args):
                pass  # Suppress logging

        def run_server():
            with socketserver.TCPServer(("", self.port), Handler) as httpd:
                httpd.serve_forever()

        self.server_thread = threading.Thread(target=run_server, daemon=True)
        self.server_thread.start()
        time.sleep(1)

def try_install_pyngrok():
    """Try to install pyngrok"""
    ColoredOutput.info("Installing pyngrok for instant public URL...")
    try:
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "pyngrok", "-q"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        return True
    except:
        return False

def create_public_url_with_pyngrok():
    """Create public URL using pyngrok"""
    try:
        from pyngrok import ngrok, conf

        # Set up ngrok
        ColoredOutput.info("Setting up ngrok tunnel...")

        # Create tunnel
        public_url = ngrok.connect(PORT, bind_tls=True)

        return str(public_url)
    except ImportError:
        ColoredOutput.warning("pyngrok not installed")
        if input("Install pyngrok for instant public URL? (y/n): ").lower() == 'y':
            if try_install_pyngrok():
                return create_public_url_with_pyngrok()
        return None
    except Exception as e:
        ColoredOutput.error(f"Failed to create tunnel: {e}")
        ColoredOutput.info("You may need to sign up at: https://dashboard.ngrok.com/signup")
        return None

def show_github_pages_instructions():
    """Show GitHub Pages setup instructions"""
    ColoredOutput.header("📄 GitHub Pages Deployment")

    print("Your repository: rrasc/predictionmlstock\n")
    print(f"{ColoredOutput.BOLD}Quick Setup (2 minutes):{ColoredOutput.END}\n")
    print("1. Visit: https://github.com/rrasc/predictionmlstock/settings/pages")
    print("2. Under 'Build and deployment':")
    print("   - Source: Select 'Deploy from a branch'")
    print("   - Branch: Select 'claude/ml-trading-system-ls0cM'")
    print("   - Folder: Select '/frontend'")
    print("   - Click 'Save'")
    print("3. Wait 2-3 minutes for deployment")
    print(f"4. Visit: {ColoredOutput.CYAN}https://rrasc.github.io/predictionmlstock/{ColoredOutput.END}")
    print("\n" + "="*60 + "\n")

def main():
    """Main function"""

    # Check frontend directory
    if not Path(FRONTEND_DIR).exists():
        ColoredOutput.error(f"{FRONTEND_DIR} directory not found!")
        sys.exit(1)

    ColoredOutput.header("📱 Instant Mobile Link Generator")

    print("Choose deployment option:\n")
    print(f"{ColoredOutput.BOLD}1. Quick Tunnel (Instant){ColoredOutput.END}")
    print("   Creates public URL using pyngrok")
    print("   ✅ Works immediately")
    print("   ⏱️  Free tier: 2-hour sessions\n")

    print(f"{ColoredOutput.BOLD}2. GitHub Pages (Permanent){ColoredOutput.END}")
    print("   Show setup instructions")
    print("   ✅ Free forever")
    print("   ✅ Custom domain support\n")

    print(f"{ColoredOutput.BOLD}3. Both{ColoredOutput.END}")
    print("   Show instructions for both\n")

    choice = input(f"{ColoredOutput.CYAN}Enter choice (1-3) or press Enter for option 1: {ColoredOutput.END}").strip() or "1"

    if choice in ["1", "3"]:
        # Start local server
        ColoredOutput.info(f"Starting frontend server on port {PORT}...")
        server = FrontendServer(PORT, FRONTEND_DIR)
        server.start()
        ColoredOutput.success("Server started")

        # Create public tunnel
        public_url = create_public_url_with_pyngrok()

        if public_url:
            ColoredOutput.header("✅ PUBLIC URL READY!")
            print(f"{ColoredOutput.BOLD}📱 Access from your iPhone:{ColoredOutput.END}\n")
            print(f"   {ColoredOutput.BOLD}{ColoredOutput.CYAN}{public_url}{ColoredOutput.END}\n")
            print("="*60)
            print(f"\n{ColoredOutput.GREEN}✨ Open this URL on ANY device - iPhone, Android, computer!{ColoredOutput.END}")
            print("🌍 Works from anywhere in the world")
            print("⏱️  Session lasts 2 hours on free tier")
            print("\nPress Ctrl+C to stop the tunnel")
            print("="*60 + "\n")

            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                ColoredOutput.info("\nStopping tunnel...")
                from pyngrok import ngrok
                ngrok.kill()
                ColoredOutput.success("Stopped")
        else:
            ColoredOutput.warning("Could not create public tunnel")
            ColoredOutput.info("\nAlternative: Use GitHub Pages (see option 2)")

    if choice in ["2", "3"]:
        if choice == "3":
            print("\n")
        show_github_pages_instructions()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n🛑 Cancelled")
        sys.exit(0)
    except Exception as e:
        ColoredOutput.error(f"Unexpected error: {e}")
        ColoredOutput.info("\nTry manual deployment:")
        ColoredOutput.info("1. Visit: https://app.netlify.com/drop")
        ColoredOutput.info("2. Drag 'frontend' folder")
        ColoredOutput.info("3. Get instant public URL")
        sys.exit(1)
