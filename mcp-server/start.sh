#!/bin/bash
# Start both the REST API (port 8001) and MCP SSE server (port 8002)
# in the same container. The REST API serves the backend and simple
# HTTP clients; the SSE server enables MCP protocol connections from
# Databricks AI agents and other MCP-compatible clients.

set -e

echo "Starting Cookidoo MCP Server (dual-mode)"
echo "  REST API:     http://0.0.0.0:8001"
echo "  MCP SSE:      http://0.0.0.0:${MCP_SSE_PORT:-8002}"

# Start MCP SSE server in background
python mcp_tools.py &
MCP_PID=$!

# Start REST API in foreground
uvicorn server:app --host 0.0.0.0 --port 8001 &
REST_PID=$!

# Wait for either process to exit
wait -n $MCP_PID $REST_PID

# If one exits, kill the other
kill $MCP_PID $REST_PID 2>/dev/null
exit 1
