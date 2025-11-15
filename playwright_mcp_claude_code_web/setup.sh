#!/bin/bash
set -e

echo "======================================================================="
echo "Playwright MCP for Claude Code Web - セットアップスクリプト"
echo "======================================================================="
echo ""
echo "このスクリプトは以下をセットアップします:"
echo "  1. playwright-mcpのインストール"
echo "  2. Firefox build v1496のインストール"
echo "  3. Firefoxプロファイルの作成"
echo "  4. JWT認証プロキシCA証明書のインポート"
echo "  5. MCP設定ファイルの作成"
echo ""
echo "通信フロー:"
echo "  Python MCP Client → playwright-mcp (Firefox) → proxy.py → JWT認証Proxy → Internet"
echo ""

# HOME環境変数を設定
export HOME=/home/user
echo "環境変数: HOME=$HOME"
echo ""

# カラー定義
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# ステップ1: certutilのインストール確認
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "ステップ1: certutilのインストール確認"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if ! command -v certutil &> /dev/null; then
    echo -e "${YELLOW}certutilがインストールされていません。インストール中...${NC}"
    apt-get update -qq
    apt-get install -y libnss3-tools > /dev/null 2>&1
    echo -e "${GREEN}✓ certutilをインストールしました${NC}"
else
    echo -e "${GREEN}✓ certutilは既にインストールされています${NC}"
fi
echo ""

# ステップ2: playwright-mcpのグローバルインストール
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "ステップ2: playwright-mcpのグローバルインストール"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if npm list -g @playwright/mcp 2>&1 | grep -q @playwright/mcp; then
    echo -e "${GREEN}✓ @playwright/mcpは既にインストールされています${NC}"
    npm list -g @playwright/mcp | grep @playwright/mcp
else
    echo -e "${YELLOW}@playwright/mcpをインストール中...${NC}"
    npm install -g @playwright/mcp
    echo -e "${GREEN}✓ @playwright/mcpをインストールしました${NC}"
fi
echo ""

# ステップ3: Firefox build v1496のインストール
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "ステップ3: Firefox build v1496のインストール (HOME=/home/user)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
FIREFOX_BUILD="/home/user/.cache/ms-playwright/firefox-1496"

if [ -d "$FIREFOX_BUILD" ]; then
    echo -e "${GREEN}✓ Firefox build v1496がインストールされています: $FIREFOX_BUILD${NC}"
else
    echo -e "${YELLOW}Firefox build v1496をインストール中... (数分かかる場合があります)${NC}"
    HOME=/home/user node /opt/node22/lib/node_modules/@playwright/mcp/node_modules/playwright/cli.js install firefox
    echo -e "${GREEN}✓ Firefox build v1496をインストールしました${NC}"
fi
echo ""

# ステップ4: Firefoxプロファイルの作成
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "ステップ4: Firefoxプロファイルの作成"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
PROFILE_DIR="/home/user/firefox-profile"

if [ -d "$PROFILE_DIR" ] && [ -f "$PROFILE_DIR/cert9.db" ]; then
    echo -e "${GREEN}✓ Firefoxプロファイルは既に存在します: $PROFILE_DIR${NC}"
else
    echo -e "${YELLOW}Firefoxプロファイルを作成中...${NC}"
    mkdir -p "$PROFILE_DIR"
    certutil -N -d sql:"$PROFILE_DIR" --empty-password
    echo -e "${GREEN}✓ Firefoxプロファイルを作成しました: $PROFILE_DIR${NC}"
fi
echo ""

# ステップ5: JWT認証プロキシCA証明書のインポート
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "ステップ5: JWT認証プロキシCA証明書のインポート"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# staging CA証明書
STAGING_CERT="/usr/local/share/ca-certificates/swp-ca-staging.crt"
PRODUCTION_CERT="/usr/local/share/ca-certificates/swp-ca-production.crt"

if [ ! -f "$STAGING_CERT" ]; then
    echo -e "${RED}✗ staging CA証明書が見つかりません: $STAGING_CERT${NC}"
    exit 1
fi

if [ ! -f "$PRODUCTION_CERT" ]; then
    echo -e "${RED}✗ production CA証明書が見つかりません: $PRODUCTION_CERT${NC}"
    exit 1
fi

# staging CA証明書のインポート
if certutil -L -d sql:"$PROFILE_DIR" -n "Anthropic TLS Inspection CA" &> /dev/null; then
    echo -e "${GREEN}✓ staging CA証明書は既にインポートされています${NC}"
else
    certutil -A -n "Anthropic TLS Inspection CA" -t "C,," -i "$STAGING_CERT" -d sql:"$PROFILE_DIR"
    echo -e "${GREEN}✓ staging CA証明書をインポートしました${NC}"
fi

# production CA証明書のインポート
if certutil -L -d sql:"$PROFILE_DIR" -n "Anthropic TLS Inspection CA Production" &> /dev/null; then
    echo -e "${GREEN}✓ production CA証明書は既にインポートされています${NC}"
else
    certutil -A -n "Anthropic TLS Inspection CA Production" -t "C,," -i "$PRODUCTION_CERT" -d sql:"$PROFILE_DIR"
    echo -e "${GREEN}✓ production CA証明書をインポートしました${NC}"
fi

echo ""
echo "インポートされた証明書:"
echo "----------------------------------------"
certutil -L -d sql:"$PROFILE_DIR" | grep -i anthropic || echo "証明書が見つかりません"
echo "----------------------------------------"
echo ""

# ステップ6: MCP設定ファイルの作成
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "ステップ6: MCP設定ファイルの作成"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

CONFIG_DIR="playwright_mcp_claude_code_web"
CONFIG_FILE="$CONFIG_DIR/playwright-firefox-config.json"

mkdir -p "$CONFIG_DIR"

cat > "$CONFIG_FILE" << 'EOF'
{
  "browser": {
    "browserName": "firefox",
    "userDataDir": "/home/user/firefox-profile",
    "launchOptions": {
      "headless": true,
      "firefoxUserPrefs": {
        "privacy.trackingprotection.enabled": false,
        "network.proxy.allow_hijacking_localhost": true,
        "network.stricttransportsecurity.preloadlist": false,
        "security.cert_pinning.enforcement_level": 0,
        "security.enterprise_roots.enabled": false,
        "security.ssl.errorReporting.enabled": false,
        "browser.xul.error_pages.expert_bad_cert": true,
        "media.navigator.streams.fake": true,
        "security.insecure_connection_text.enabled": false,
        "security.insecure_connection_text.pbmode.enabled": false,
        "security.mixed_content.block_active_content": false,
        "security.mixed_content.block_display_content": false,
        "security.OCSP.enabled": 0
      },
      "acceptDownloads": false
    },
    "contextOptions": {
      "ignoreHTTPSErrors": true,
      "bypassCSP": true
    }
  }
}
EOF

echo -e "${GREEN}✓ MCP設定ファイルを作成しました: $CONFIG_FILE${NC}"
echo ""

# ステップ7: start_playwright_mcp.pyの作成
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "ステップ7: start_playwright_mcp.py の作成"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

STARTER_SCRIPT="$CONFIG_DIR/start_playwright_mcp.py"

cat > "$STARTER_SCRIPT" << 'EOF'
#!/usr/bin/env python3
"""
Playwright MCP Server Starter with proxy.py

通信フロー:
  Python MCP Client → playwright-mcp (Firefox) → proxy.py → JWT認証Proxy → Internet
"""
import os
import signal
import subprocess
import sys
import time


def start_playwright_mcp_with_proxy():
    """proxy.pyとplaywright-mcpを起動"""

    # HTTPS_PROXY環境変数を確認
    https_proxy = os.environ.get('HTTPS_PROXY', '')
    if not https_proxy:
        print("❌ HTTPS_PROXY環境変数が設定されていません")
        sys.exit(1)

    # HOME環境変数を設定
    os.environ['HOME'] = '/home/user'

    print("=" * 70)
    print("Playwright MCP Server with proxy.py")
    print("=" * 70)
    print(f"HOME: {os.environ['HOME']}")
    print(f"HTTPS_PROXY: {https_proxy[:50]}...")
    print()

    # 1. proxy.pyを起動
    print("1. proxy.pyを起動中...")
    proxy_process = subprocess.Popen(
        [
            "uv", "run", "proxy",
            "--hostname", "127.0.0.1",
            "--port", "18915",
            "--plugins", "proxy.plugin.proxy_pool.ProxyPoolPlugin",
            "--proxy-pool", https_proxy
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

    # proxy.pyの起動を待つ
    time.sleep(2)
    print("   ✅ proxy.py起動完了 (localhost:18915)")
    print()

    # 2. playwright-mcpを起動
    print("2. playwright-mcpを起動中...")
    print("   Firefox: /home/user/.cache/ms-playwright/firefox-1496")
    print("   プロファイル: /home/user/firefox-profile (CA証明書インポート済み)")
    print("   設定: playwright_mcp_claude_code_web/playwright-firefox-config.json")
    print()

    playwright_process = subprocess.Popen(
        [
            "node",
            "/opt/node22/lib/node_modules/@playwright/mcp/cli.js",
            "--config", "playwright_mcp_claude_code_web/playwright-firefox-config.json",
            "--browser", "firefox",
            "--proxy-server", "http://127.0.0.1:18915"
        ],
        env={**os.environ, "HOME": "/home/user"}
    )

    print("   ✅ playwright-mcp起動完了")
    print()
    print("=" * 70)
    print("🎉 セットアップ完了")
    print("=" * 70)
    print()
    print("通信フロー:")
    print("  Python MCP Client")
    print("    ↓")
    print("  playwright-mcp (Firefox with CA証明書)")
    print("    ↓")
    print("  proxy.py (localhost:18915) ← JWT認証処理")
    print("    ↓")
    print("  JWT認証Proxy ← TLS Inspection")
    print("    ↓")
    print("  Internet ✅")
    print()
    print("Ctrl+C で終了")
    print()

    def signal_handler(sig, frame):
        print("\n終了中...")
        playwright_process.terminate()
        proxy_process.terminate()
        playwright_process.wait()
        proxy_process.wait()
        print("✅ 終了しました")
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)

    # プロセスを監視
    try:
        playwright_process.wait()
    except KeyboardInterrupt:
        signal_handler(None, None)


if __name__ == "__main__":
    start_playwright_mcp_with_proxy()
EOF

chmod +x "$STARTER_SCRIPT"
echo -e "${GREEN}✓ start_playwright_mcp.py を作成しました${NC}"
echo ""

# 完了
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${GREEN}セットアップが完了しました！${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "✅ インストール済みコンポーネント:"
echo "  - certutil (libnss3-tools)"
echo "  - @playwright/mcp (npm global)"
echo "  - Firefox build v1496 ($FIREFOX_BUILD)"
echo "  - Firefoxプロファイル ($PROFILE_DIR)"
echo "  - CA証明書 (Anthropic TLS Inspection CA × 2)"
echo "  - MCP設定ファイル ($CONFIG_FILE)"
echo "  - MCPサーバー起動スクリプト ($STARTER_SCRIPT)"
echo ""
echo "📝 次のステップ:"
echo ""
echo "1. サンプルコードを実行:"
echo "   HOME=/home/user uv run python playwright_mcp_claude_code_web/example.py"
echo ""
echo "2. MCPサーバーを単独で起動:"
echo "   HOME=/home/user python playwright_mcp_claude_code_web/start_playwright_mcp.py"
echo ""
echo "3. 詳細なドキュメント:"
echo "   cat investigation/playwright/CA_CERTIFICATE_IMPORT_GUIDE.md"
echo ""
echo "🎯 通信フロー:"
echo "  Python MCP Client → playwright-mcp (Firefox) → proxy.py → JWT認証Proxy → Internet"
echo ""
echo "💡 ヒント:"
echo "  - proxy.pyはJWT認証を処理するために必須です"
echo "  - CA証明書はTLS Inspectionの証明書エラーを回避します"
echo "  - 両方が揃って初めて正常にアクセスできます"
echo ""
