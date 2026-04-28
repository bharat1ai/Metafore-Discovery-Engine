#!/bin/bash
DIR="$( cd "$( dirname "$0" )" && pwd )"

clear
echo ""
echo "  ======================================================="
echo "    Metafore Works  |  Discovery Engine"
echo "    Starting up, please wait..."
echo "  ======================================================="
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "  [!] Python is not installed on this Mac."
    echo ""
    echo "      Please install Python first:"
    echo "      1. Go to  https://www.python.org/downloads/"
    echo "      2. Click the big Download button"
    echo "      3. Run the installer and follow the steps"
    echo "      4. Once done, double-click START.command again"
    echo ""
    open "https://www.python.org/downloads/"
    echo "  Press Enter to close this window..."
    read
    exit 1
fi
echo "  [OK] Python is installed."
echo ""

# Check .env
if [ ! -f "$DIR/discovery-engine/.env" ]; then
    echo "  [!] Missing configuration file."
    echo "      Contact the person who sent you this project."
    echo ""
    echo "  Press Enter to close this window..."
    read
    exit 1
fi
echo "  [OK] Configuration found."
echo ""

# Install packages
echo "  Installing required packages (1-2 min on first run, instant after that)..."
pip3 install -r "$DIR/discovery-engine/backend/requirements.txt" --quiet --disable-pip-version-check 2>/dev/null
if [ $? -ne 0 ]; then
    python3 -m pip install -r "$DIR/discovery-engine/backend/requirements.txt" --quiet --disable-pip-version-check
fi
echo "  [OK] All packages ready."
echo ""

# Stop any old instance
lsof -ti:8083 2>/dev/null | xargs kill -9 2>/dev/null
sleep 1

# Start server
echo "  Starting server..."
python3 -m uvicorn main:app --port 8083 --app-dir "$DIR/discovery-engine/backend" > /tmp/mw_de_server.log 2>&1 &
echo $! > /tmp/mw_de_server.pid

# Wait for server to be ready
echo "  Waiting for server to start..."
for i in {1..15}; do
    sleep 1
    if curl -s http://localhost:8083 > /dev/null 2>&1; then
        break
    fi
done

# Open browser
echo "  Opening browser..."
open "http://localhost:8083"

echo ""
echo "  ======================================================="
echo "    Discovery Engine is RUNNING"
echo ""
echo "    Your browser should have opened automatically."
echo "    If not, go to:  http://localhost:8083"
echo ""
echo "    To stop the app:  double-click STOP.command"
echo ""
echo "    You can close this window — the app keeps running."
echo "  ======================================================="
echo ""
