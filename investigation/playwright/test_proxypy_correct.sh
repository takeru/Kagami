#!/bin/bash
# proxy.pyを正しい方法でJWT認証プロキシと連携させるテスト

echo "Starting proxy.py with ProxyPoolPlugin..."
echo "This is the CORRECT way to use proxy.py with upstream proxy!"
echo ""

# proxy.pyをProxyPoolPluginと共に起動
uv run proxy \
    --hostname 127.0.0.1 \
    --port 8891 \
    --plugins proxy.plugin.proxy_pool.ProxyPoolPlugin \
    --proxy-pool "$HTTPS_PROXY" \
    &

PROXY_PID=$!
echo "Proxy PID: $PROXY_PID"
echo ""

# Wait for proxy to start
sleep 5

# Test with curl
echo "Testing with curl..."
echo "curl -x http://127.0.0.1:8891 -k https://example.com -I"
echo ""

curl -x http://127.0.0.1:8891 -k https://example.com -I --connect-timeout 10 --max-time 15

# Cleanup
echo ""
echo "Stopping proxy..."
kill $PROXY_PID 2>/dev/null
wait $PROXY_PID 2>/dev/null
echo "Done!"
