#!/bin/bash
clear
echo ""
echo "  Stopping the Discovery Engine server..."
echo ""

lsof -ti:8083 2>/dev/null | xargs kill -9 2>/dev/null

if [ -f /tmp/mw_de_server.pid ]; then
    kill -9 $(cat /tmp/mw_de_server.pid) 2>/dev/null
    rm /tmp/mw_de_server.pid
fi

echo "  [OK] Server stopped."
echo ""
sleep 2
