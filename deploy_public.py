#!/usr/bin/env python3
"""
Quick Public Deployment Script
Deploy ML Trading System frontend to free hosting services
"""

import os
import sys
import subprocess
import json
import http.server
import socketserver
import threading
import time
from pathlib import Path

class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_header(text):
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*60}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.CYAN}{text}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*60}{Colors.ENDC}\n")

def print_success(text):
    print(f"{Colors.GREEN}✅ {text}{Colors.ENDC}")

def print_error(text):
    print(f"{Colors.FAIL}❌ {text}{Colors.ENDC}")

def print_info(text):
    print(f"{Colors.BLUE}ℹ️  {text}{Colors.ENDC}")

def print_warning(text):
    print(f"{Colors.WARNING}⚠️  {text}{Colors.ENDC}")

def run_command(cmd, shell=True):
    """Run shell command and return output"""
    try:
        result = subprocess.run(
            cmd,
            shell=shell,
            capture_output=True,
            text=True,
            timeout=30
        )
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)

def check_ngrok():
    """Check if ngrok is installed"""
    success, _, _ = run_command("which ngrok")
    return success

def install_ngrok():
    """Try to install ngrok"""
    print_info("Attempting to install ngrok...")

    # Check OS
    if sys.platform == "darwin":
        # macOS
        if run_command("which brew")[0]:
            return run_command("brew install ngrok/ngrok/ngrok")[0]
    elif sys.platform.startswith("linux"):
        # Linux
        commands = [
            "curl -s https://ngrok-agent.s3.amazonaws.com/ngrok.asc | sudo tee /etc/apt/trusted.gpg.d/ngrok.asc >/dev/null",
            "echo 'deb https://ngrok-agent.s3.amazonaws.com buster main' | sudo tee /etc/apt/sources.list.d/ngrok.list",
            "sudo apt update",
            "sudo apt install -y ngrok"
        ]
        for cmd in commands:
            if not run_command(cmd)[0]:
                return False
        return True

    return False

def start_ngrok_tunnel(port=8000):
    """Start ngrok tunnel"""
    print_info(f"Starting ngrok tunnel on port {port}...")

    # Kill existing ngrok
    run_command("pkill ngrok")
    time.sleep(1)

    # Start ngrok in background
    subprocess.Popen(
        f"ngrok http {port}",
        shell=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

    # Wait for ngrok to start
    time.sleep(3)

    # Get public URL
    try:
        import urllib.request
        response = urllib.request.urlopen("http://localhost:4040/api/tunnels")
        data = json.loads(response.read())
        public_url = data['tunnels'][0]['public_url']
        return True, public_url
    except:
        return False, None

def deploy_github_pages():
    """Deploy to GitHub Pages"""
    print_header("📄 Deploying to GitHub Pages")

    print_info("Checking git repository...")

    # Check if in git repo
    if not run_command("git rev-parse --git-dir")[0]:
        print_error("Not in a git repository")
        return False

    print_info("Checking GitHub remote...")
    success, stdout, _ = run_command("git remote get-url origin")
    if not success:
        print_error("No git remote 'origin' found")
        print_info("Please push your code to GitHub first")
        return False

    remote_url = stdout.strip()
    print_success(f"Repository: {remote_url}")

    # Extract username and repo name
    if "github.com" in remote_url:
        # Parse GitHub URL
        parts = remote_url.replace(".git", "").split("/")
        username = parts[-2].split(":")[-1]
        repo = parts[-1]

        pages_url = f"https://{username}.github.io/{repo}/"

        print("\n" + "="*60)
        print(f"{Colors.BOLD}{Colors.GREEN}✅ GitHub Repository Found!{Colors.ENDC}")
        print("="*60)
        print(f"\nRepository: {username}/{repo}")
        print(f"GitHub Pages URL: {Colors.CYAN}{pages_url}{Colors.ENDC}")
        print("\n" + "="*60)
        print(f"\n{Colors.BOLD}📋 Setup Instructions:{Colors.ENDC}\n")
        print("1. Go to: https://github.com/{}/{}/settings/pages".format(username, repo))
        print("2. Under 'Source', select:")
        print("   - Source: 'Deploy from a branch'")
        print("   - Branch: 'claude/ml-trading-system-ls0cM'")
        print("   - Folder: '/frontend'")
        print("3. Click 'Save'")
        print("4. Wait 2-3 minutes for deployment")
        print(f"5. Visit: {Colors.CYAN}{pages_url}{Colors.ENDC}")
        print("\n" + "="*60)

        return True, pages_url

    return False, None

def start_local_server(port=8000):
    """Start local server"""
    class MyHandler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory="frontend", **kwargs)

        def end_headers(self):
            self.send_header('Access-Control-Allow-Origin', '*')
            super().end_headers()

        def log_message(self, format, *args):
            pass  # Suppress logs

    def run_server():
        with socketserver.TCPServer(("", port), MyHandler) as httpd:
            httpd.serve_forever()

    thread = threading.Thread(target=run_server, daemon=True)
    thread.start()
    time.sleep(1)
    return thread

def get_network_ip():
    """Get local network IP"""
    import socket
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

def main():
    print_header("🚀 ML Trading System - Quick Public Deployment")

    # Check frontend directory
    if not Path("frontend").exists():
        print_error("frontend directory not found!")
        print_info("Please run this script from the project root directory")
        sys.exit(1)

    print("Choose deployment method:\n")
    print(f"{Colors.BOLD}1. Quick Tunnel (ngrok){Colors.ENDC} - Instant public URL")
    print(f"{Colors.BOLD}2. GitHub Pages{Colors.ENDC} - Permanent hosting")
    print(f"{Colors.BOLD}3. Local Network{Colors.ENDC} - Same WiFi access")
    print(f"{Colors.BOLD}4. All Options{Colors.ENDC} - Show all URLs\n")

    choice = input(f"{Colors.CYAN}Enter choice (1-4): {Colors.ENDC}").strip()

    if choice == "1":
        # ngrok option
        print_header("🌐 Setting up ngrok tunnel")

        if not check_ngrok():
            print_warning("ngrok not found")
            if input("Install ngrok? (y/n): ").lower() == 'y':
                if not install_ngrok():
                    print_error("Failed to install ngrok")
                    print_info("Please install manually: https://ngrok.com/download")
                    sys.exit(1)
            else:
                print_info("Install ngrok from: https://ngrok.com/download")
                sys.exit(1)

        # Start local server
        print_info("Starting local server...")
        start_local_server()
        print_success("Local server started on port 8000")

        # Start ngrok
        success, public_url = start_ngrok_tunnel()

        if success:
            print("\n" + "="*60)
            print(f"{Colors.BOLD}{Colors.GREEN}✅ PUBLIC URL READY!{Colors.ENDC}")
            print("="*60)
            print(f"\n📱 Access from ANY device:\n")
            print(f"   {Colors.BOLD}{Colors.CYAN}{public_url}{Colors.ENDC}\n")
            print("="*60)
            print(f"\n{Colors.GREEN}✨ Open this URL on your iPhone/iPad!{Colors.ENDC}")
            print("🌍 Works from anywhere - not just local WiFi")
            print("⏱️  Free tier: 2 hours session\n")
            print("Press Ctrl+C to stop")
            print("="*60 + "\n")

            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\n\n🛑 Stopping tunnel...")
                run_command("pkill ngrok")
                print_success("Stopped")
        else:
            print_error("Failed to start ngrok tunnel")
            print_info("You may need to sign up at: https://dashboard.ngrok.com/get-started/setup")
            print_info("Then run: ngrok config add-authtoken YOUR_TOKEN")

    elif choice == "2":
        # GitHub Pages
        deploy_github_pages()

    elif choice == "3":
        # Local network
        print_header("📱 Local Network Access")

        local_ip = get_network_ip()
        port = 8000

        print_info("Starting local server...")
        start_local_server(port)
        print_success("Server started")

        print("\n" + "="*60)
        print(f"{Colors.BOLD}📱 Local Network URLs{Colors.ENDC}")
        print("="*60)
        print(f"\n🖥️  Desktop: http://localhost:{port}")
        print(f"📱 Mobile:  http://{local_ip}:{port}\n")
        print("="*60)
        print(f"\n{Colors.WARNING}⚠️  Both devices must be on SAME WiFi!{Colors.ENDC}\n")
        print("Press Ctrl+C to stop")
        print("="*60 + "\n")

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n\n🛑 Stopping server...")
            print_success("Stopped")

    else:
        # Show all options
        print_header("📋 All Access Options")

        local_ip = get_network_ip()

        print(f"{Colors.BOLD}1. Local Network (Same WiFi):{Colors.ENDC}")
        print(f"   http://{local_ip}:8000")
        print(f"   {Colors.WARNING}⚠️  Requires same WiFi network{Colors.ENDC}\n")

        print(f"{Colors.BOLD}2. ngrok Tunnel (Public):{Colors.ENDC}")
        print(f"   Run: bash mobile_access.sh")
        print(f"   {Colors.GREEN}✅ Works from anywhere{Colors.ENDC}\n")

        print(f"{Colors.BOLD}3. GitHub Pages (Permanent):{Colors.ENDC}")
        success, url = deploy_github_pages()
        print()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n🛑 Cancelled")
        sys.exit(0)
