#!/usr/bin/env python3
"""
Claude Code用 Playwright MCP サーバー起動スクリプト

通信フロー:
  Claude Code → mcp.py → playwright-mcp (Firefox) → proxy.py → JWT認証Proxy → Internet

このスクリプトは:
  1. proxy.pyをバックグラウンドで起動
  2. playwright-mcpをstdioモードで起動
  3. 終了時にproxy.pyを停止
"""
import os
import sys
import subprocess
import time
import atexit
import signal
from pathlib import Path

# グローバル変数でproxy.pyのプロセスを保持
proxy_process = None


def start_proxy():
    """proxy.pyを起動"""
    global proxy_process

    # HTTPS_PROXY環境変数を確認
    https_proxy = os.environ.get('HTTPS_PROXY', '')
    if not https_proxy:
        print("❌ HTTPS_PROXY環境変数が設定されていません", file=sys.stderr)
        sys.exit(1)

    print(f"✓ proxy.pyを起動中... (プロキシ: {https_proxy[:50]}...)", file=sys.stderr)

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
    print("✓ proxy.py起動完了 (localhost:18915)", file=sys.stderr)


def stop_proxy():
    """proxy.pyを停止"""
    global proxy_process

    if proxy_process is None:
        return

    print("✓ proxy.pyを停止中...", file=sys.stderr)

    try:
        proxy_process.send_signal(signal.SIGTERM)
        proxy_process.wait(timeout=5)
        print("✓ proxy.pyを停止しました", file=sys.stderr)
    except subprocess.TimeoutExpired:
        proxy_process.kill()
        print("⚠️ proxy.pyを強制終了しました", file=sys.stderr)
    except Exception as e:
        print(f"⚠️ proxy.py停止時にエラー: {e}", file=sys.stderr)


def main():
    """メイン処理"""
    # HOME環境変数を設定
    os.environ['HOME'] = '/home/user'

    # 終了時にproxy.pyを停止するよう登録
    atexit.register(stop_proxy)

    # proxy.pyを起動
    start_proxy()

    # playwright-mcpの設定ファイルパス
    script_dir = Path(__file__).parent
    config_path = str(script_dir / "playwright-firefox-config.json")

    if not os.path.exists(config_path):
        print(f"❌ 設定ファイルが見つかりません: {config_path}", file=sys.stderr)
        sys.exit(1)

    print(f"✓ 設定ファイル: {config_path}", file=sys.stderr)
    print("✓ playwright-mcpを起動します...", file=sys.stderr)

    # playwright-mcpを起動（stdioモード）
    cmd = [
        'node',
        '/opt/node22/lib/node_modules/@playwright/mcp/cli.js',
        '--config', config_path,
        '--browser', 'firefox',
        '--proxy-server', 'http://127.0.0.1:18915'
    ]

    # 環境変数を準備
    env = os.environ.copy()
    env['HOME'] = '/home/user'

    # playwright-mcpを実行（stdioモード）
    # Claude CodeがstdinからMCPプロトコルのリクエストを送り、
    # stdoutでレスポンスを受け取る
    try:
        subprocess.run(cmd, env=env)
    except KeyboardInterrupt:
        print("\n✓ 中断されました", file=sys.stderr)
    except Exception as e:
        print(f"\n❌ エラー: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
