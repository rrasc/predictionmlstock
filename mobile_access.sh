#!/bin/bash

# Quick Mobile Access Script
# Creates a public ngrok tunnel for instant mobile access

echo "╔════════════════════════════════════════════════════════════╗"
echo "║  📱 Quick Mobile Access - Public URL Generator            ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Check if ngrok is installed
if ! command -v ngrok &> /dev/null; then
    echo "⚠️  ngrok is not installed."
    echo ""
    echo "Installing ngrok..."
    echo ""

    # Detect OS
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        if command -v brew &> /dev/null; then
            brew install ngrok/ngrok/ngrok
        else
            echo "❌ Homebrew not found. Please install from: https://ngrok.com/download"
            exit 1
        fi
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux
        curl -s https://ngrok-agent.s3.amazonaws.com/ngrok.asc | \
            sudo tee /etc/apt/trusted.gpg.d/ngrok.asc >/dev/null && \
            echo "deb https://ngrok-agent.s3.amazonaws.com buster main" | \
            sudo tee /etc/apt/sources.list.d/ngrok.list && \
            sudo apt update && sudo apt install ngrok
    else
        echo "❌ Please install ngrok manually from: https://ngrok.com/download"
        exit 1
    fi
fi

# Start frontend server in background
echo "🚀 Starting frontend server..."
python3 serve_frontend.py > /tmp/frontend_server.log 2>&1 &
SERVER_PID=$!
sleep 2

# Check if server started
if ! ps -p $SERVER_PID > /dev/null; then
    echo "❌ Failed to start server"
    exit 1
fi

echo "✅ Frontend server running (PID: $SERVER_PID)"
echo ""

# Start ngrok tunnel
echo "🌐 Creating public tunnel with ngrok..."
echo ""

# Kill any existing ngrok processes
pkill ngrok 2>/dev/null

# Start ngrok
ngrok http 8000 > /dev/null &
NGROK_PID=$!

# Wait for ngrok to start
sleep 3

# Get the public URL
PUBLIC_URL=$(curl -s http://localhost:4040/api/tunnels | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(data['tunnels'][0]['public_url'])
except:
    print('')
")

if [ -z "$PUBLIC_URL" ]; then
    echo "❌ Failed to get ngrok URL"
    echo ""
    echo "Try manually:"
    echo "1. Visit https://dashboard.ngrok.com/get-started/setup"
    echo "2. Sign up for free account"
    echo "3. Run: ngrok config add-authtoken YOUR_TOKEN"
    echo "4. Run: ngrok http 8000"
    kill $SERVER_PID
    exit 1
fi

# Display the public URL
echo "╔════════════════════════════════════════════════════════════╗"
echo "║  ✅ PUBLIC URL READY - Access from ANY device!            ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo "📱 Mobile URL (iOS, Android, any device):"
echo ""
echo "   $PUBLIC_URL"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "✨ Open this URL on your iPhone/iPad/any device"
echo "🌍 Works from anywhere - not just local WiFi!"
echo "⏱️  Tunnel is active (free tier: 2 hours, then reconnect)"
echo ""
echo "Press Ctrl+C to stop the tunnel and server"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Generate QR code if qrencode is available
if command -v qrencode &> /dev/null; then
    echo ""
    echo "📷 Scan QR code with your phone:"
    echo ""
    qrencode -t ANSIUTF8 "$PUBLIC_URL"
fi

# Keep script running
trap "echo ''; echo '🛑 Stopping server and tunnel...'; kill $SERVER_PID $NGROK_PID 2>/dev/null; echo '✅ Stopped'; exit 0" INT

# Wait
while true; do
    sleep 1
    # Check if processes are still running
    if ! ps -p $SERVER_PID > /dev/null || ! ps -p $NGROK_PID > /dev/null; then
        echo "⚠️  Server or tunnel stopped unexpectedly"
        kill $SERVER_PID $NGROK_PID 2>/dev/null
        exit 1
    fi
done
