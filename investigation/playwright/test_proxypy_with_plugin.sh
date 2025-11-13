#!/bin/bash

echo "Starting proxy.py with JWT plugin..."

# Start proxy.py in background
uv run proxy \
    --hostname 127.0.0.1 \
    --port 8890 \
    --plugins src.jwt_proxy_plugin.JWTProxyPlugin \
    --proxy-pool "$HTTPS_PROXY" \
    &

PROXY_PID=$!
echo "Proxy PID: $PROXY_PID"

# Wait for proxy to start
sleep 5

# Test with curl
echo ""
echo "Testing with curl..."
curl -x http://127.0.0.1:8890 -k https://example.com -I --connect-timeout 10 --max-time 15

# Cleanup
echo ""
echo "Stopping proxy..."
kill $PROXY_PID 2>/dev/null
wait $PROXY_PID 2>/dev/null
echo "Done"
