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
