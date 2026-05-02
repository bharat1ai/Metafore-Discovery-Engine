#!/bin/bash
DIR="$( cd "$( dirname "$0" )" && pwd )"

# Best-effort: strip macOS "downloaded from internet" quarantine flag from
# the launchers + .env so repeat launches don't re-prompt Gatekeeper.
# First launch still needs right-click → Open if the zip was emailed/shared.
xattr -d com.apple.quarantine "$DIR/START.command" "$DIR/STOP.command" "$DIR/discovery-engine/.env" 2>/dev/null || true

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

# Set up an isolated virtual environment so `pip install` works on
# Python builds that enforce PEP 668 (python.org 3.12+, Homebrew, etc.).
VENV="$DIR/discovery-engine/.venv"
if [ ! -d "$VENV" ]; then
    echo "  Creating Python environment (one-time setup, ~10 sec)..."
    python3 -m venv "$VENV" 2>/dev/null
    if [ ! -d "$VENV" ]; then
        echo "  [!] Could not create the Python environment."
        echo "      This usually means the python3 install is incomplete."
        echo "      Reinstall Python from https://www.python.org/downloads/ and try again."
        echo ""
        echo "  Press Enter to close this window..."
        read
        exit 1
    fi
fi

VENV_PY="$VENV/bin/python"

# Install packages inside the venv via `python -m pip` (avoids shebang-line
# problems when the install path contains spaces). No PEP 668 issues, no sudo.
echo "  Installing required packages (1-2 min on first run, instant after that)..."
"$VENV_PY" -m pip install --upgrade pip --quiet --disable-pip-version-check 2>/dev/null
"$VENV_PY" -m pip install -r "$DIR/discovery-engine/backend/requirements.txt" --quiet --disable-pip-version-check
if [ $? -ne 0 ]; then
    echo "  [!] Package installation failed."
    echo "      Check your internet connection and try again."
    echo "      Detailed log: /tmp/mw_de_server.log"
    echo ""
    echo "  Press Enter to close this window..."
    read
    exit 1
fi
echo "  [OK] All packages ready."
echo ""

# Stop any old instance
lsof -ti:8083 2>/dev/null | xargs kill -9 2>/dev/null
sleep 1

# Start server using the venv's python so dependencies resolve correctly.
echo "  Starting server..."
"$VENV_PY" -m uvicorn main:app --port 8083 --app-dir "$DIR/discovery-engine/backend" > /tmp/mw_de_server.log 2>&1 &
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
