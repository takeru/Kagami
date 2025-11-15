#!/usr/bin/env python3
"""
Playwright MCP Server Wrapper for Claude Code Web

このスクリプトはMCPサーバーとして動作し、
proxy.pyをバックグラウンドで起動してから
playwright-mcpの標準入出力を親プロセスに接続します。
"""
import os
import subprocess
import sys
import time
import atexit

def main():
    # HTTPS_PROXY環境変数を確認
    https_proxy = os.environ.get('HTTPS_PROXY', '')
    if not https_proxy:
        print("❌ HTTPS_PROXY環境変数が設定されていません", file=sys.stderr)
        sys.exit(1)

    # HOME環境変数を設定
    os.environ['HOME'] = '/home/user'

    # proxy.pyを起動（バックグラウンド）
    proxy_process = subprocess.Popen(
        [
            "uv", "run", "proxy",
            "--hostname", "127.0.0.1",
            "--port", "18915",
            "--plugins", "proxy.plugin.proxy_pool.ProxyPoolPlugin",
            "--proxy-pool", https_proxy
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        cwd="/home/user/Kagami"
    )

    # proxy.pyの起動を待つ
    time.sleep(2)

    # 終了時にproxy.pyを停止
    def cleanup():
        proxy_process.terminate()
        try:
            proxy_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proxy_process.kill()

    atexit.register(cleanup)

    # playwright-mcpを起動（標準入出力は親プロセスに接続）
    playwright_process = subprocess.Popen(
        [
            "node",
            "/opt/node22/lib/node_modules/@playwright/mcp/cli.js",
            "--config", "playwright_mcp_claude_code_web/playwright-firefox-config.json",
            "--browser", "firefox",
            "--proxy-server", "http://127.0.0.1:18915"
        ],
        env={**os.environ, "HOME": "/home/user"},
        cwd="/home/user/Kagami"
    )

    # playwright-mcpの終了を待つ
    playwright_process.wait()
    sys.exit(playwright_process.returncode)

if __name__ == "__main__":
    main()
