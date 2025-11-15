#!/bin/bash
set -e

echo "=== Firefox インストール検証 ==="

# 1. HOMEを確認
echo "Current HOME: $HOME"

# 2. @playwright/mcpのインストール確認
echo -e "\n@playwright/mcp version:"
npm list -g @playwright/mcp | grep @playwright/mcp || echo "Not installed, installing..."
if ! npm list -g @playwright/mcp | grep -q @playwright/mcp; then
    echo "Installing @playwright/mcp..."
    npm install -g @playwright/mcp
fi

# 3. Firefox build v1496のインストール
echo -e "\nInstalling Firefox build v1496..."
HOME=/home/user node /opt/node22/lib/node_modules/@playwright/mcp/node_modules/playwright/cli.js install firefox

# 4. インストール確認
echo -e "\nInstalled Firefox browsers:"
ls -la /home/user/.cache/ms-playwright/ 2>/dev/null || echo "No browsers installed yet"

# 5. cli.jsの存在確認
echo -e "\ncli.js location:"
ls -la /opt/node22/lib/node_modules/@playwright/mcp/cli.js

# 6. プロキシCA証明書の確認
echo -e "\nProxy CA certificate:"
if [ -f /usr/local/share/ca-certificates/swp-ca-staging.crt ]; then
    echo "✅ Found: /usr/local/share/ca-certificates/swp-ca-staging.crt"
    openssl x509 -in /usr/local/share/ca-certificates/swp-ca-staging.crt -noout -subject -issuer
else
    echo "❌ Not found: /usr/local/share/ca-certificates/swp-ca-staging.crt"
fi

echo -e "\n✅ Setup complete!"
echo -e "\nNext steps:"
echo "  1. Run test: uv run python investigation/playwright/test_17_mcp_with_cli_direct.py"
echo "  2. Expected: Firefox starts, certificate error page appears"
echo "  3. See HOME_USER_FIREFOX_SETUP.md for details"
