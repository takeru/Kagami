#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# ///
"""
Claude Code用 Playwright MCP サーバー起動スクリプト (タイムアウト対策版)

通信フロー:
  Claude Code → mcp.py (MCPラッパー) → playwright-mcp (Firefox) → proxy.py → JWT認証Proxy → Internet

このスクリプトは:
  1. 起動時に即座にMCPサーバーとして応答（タイムアウト回避）
  2. バックグラウンドスレッドでセットアップを実行
  3. セットアップ完了後、playwright-mcpにリクエストをプロキシ
  4. 終了時にproxy.pyとplaywright-mcpを停止

これにより、Claude Code Webの30秒タイムアウトを回避します。
"""
import os
import sys
import json
import subprocess
import threading
import time
import atexit
import signal
from pathlib import Path
from typing import Optional, Dict, Any

# グローバル変数
proxy_process = None
playwright_mcp_process = None
setup_completed = False
setup_error = None


def log(message: str, level: str = "INFO"):
    """ログ出力（stderrに出力）"""
    prefix = {
        "INFO": "✓",
        "WARN": "⚠️",
        "ERROR": "❌",
        "DEBUG": "🔍"
    }.get(level, "ℹ️")
    print(f"{prefix} [MCP Wrapper] {message}", file=sys.stderr, flush=True)


def run_setup_script():
    """セットアップスクリプトを実行（バックグラウンドスレッド）"""
    global setup_completed, setup_error

    try:
        log("バックグラウンドでセットアップを開始...")

        script_dir = Path(__file__).parent
        setup_script = script_dir / "setup_mcp.py"

        result = subprocess.run(
            ["uv", "run", "python", str(setup_script)],
            capture_output=True,
            text=True,
            env=os.environ.copy()
        )

        if result.returncode != 0:
            setup_error = f"セットアップ失敗: {result.stderr}"
            log(setup_error, "ERROR")
            return

        log("セットアップ完了")
        setup_completed = True

    except Exception as e:
        setup_error = f"セットアップ中にエラー: {e}"
        log(setup_error, "ERROR")


def start_proxy():
    """proxy.pyを起動"""
    global proxy_process

    # HTTPS_PROXY環境変数を確認
    https_proxy = os.environ.get('HTTPS_PROXY', '')
    if not https_proxy:
        log("HTTPS_PROXY環境変数が設定されていません", "ERROR")
        return False

    log(f"proxy.pyを起動中...")

    try:
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
        log("proxy.py起動完了 (localhost:18915)")
        return True

    except Exception as e:
        log(f"proxy.py起動エラー: {e}", "ERROR")
        return False


def start_playwright_mcp():
    """playwright-mcpを起動"""
    global playwright_mcp_process

    script_dir = Path(__file__).parent
    config_path = str(script_dir / "playwright-firefox-config.json")

    if not os.path.exists(config_path):
        log(f"設定ファイルが見つかりません: {config_path}", "ERROR")
        return False

    log(f"playwright-mcpを起動中...")

    cmd = [
        'node',
        '/opt/node22/lib/node_modules/@playwright/mcp/cli.js',
        '--config', config_path,
        '--browser', 'firefox',
        '--proxy-server', 'http://127.0.0.1:18915'
    ]

    env = os.environ.copy()
    env['HOME'] = '/home/user'

    try:
        playwright_mcp_process = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            env=env,
            bufsize=0
        )

        log("playwright-mcp起動完了")
        return True

    except Exception as e:
        log(f"playwright-mcp起動エラー: {e}", "ERROR")
        return False


def stop_processes():
    """proxy.pyとplaywright-mcpを停止"""
    global proxy_process, playwright_mcp_process

    if playwright_mcp_process:
        log("playwright-mcpを停止中...")
        try:
            playwright_mcp_process.terminate()
            playwright_mcp_process.wait(timeout=5)
        except:
            playwright_mcp_process.kill()

    if proxy_process:
        log("proxy.pyを停止中...")
        try:
            proxy_process.terminate()
            proxy_process.wait(timeout=5)
        except:
            proxy_process.kill()


def read_jsonrpc_message(stream) -> Optional[Dict[str, Any]]:
    """JSON-RPCメッセージを読み取る"""
    try:
        line = stream.readline()
        if not line:
            return None

        message = json.loads(line)
        return message
    except Exception as e:
        log(f"メッセージ読み取りエラー: {e}", "ERROR")
        return None


def write_jsonrpc_message(stream, message: Dict[str, Any]):
    """JSON-RPCメッセージを書き込む"""
    try:
        json_str = json.dumps(message) + "\n"
        stream.write(json_str)
        stream.flush()
    except Exception as e:
        log(f"メッセージ書き込みエラー: {e}", "ERROR")


def handle_initialize(request: Dict[str, Any]) -> Dict[str, Any]:
    """initializeリクエストを処理"""
    return {
        "jsonrpc": "2.0",
        "id": request.get("id"),
        "result": {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {}
            },
            "serverInfo": {
                "name": "playwright-mcp-wrapper",
                "version": "1.0.0"
            }
        }
    }


def handle_tools_list(request: Dict[str, Any]) -> Dict[str, Any]:
    """tools/listリクエストを処理"""
    if setup_error:
        # セットアップエラー時
        return {
            "jsonrpc": "2.0",
            "id": request.get("id"),
            "error": {
                "code": -32603,
                "message": f"セットアップエラー: {setup_error}"
            }
        }
    elif not setup_completed:
        # セットアップ中
        return {
            "jsonrpc": "2.0",
            "id": request.get("id"),
            "result": {
                "tools": [{
                    "name": "playwright_setup_in_progress",
                    "description": "Playwright MCPサーバーのセットアップ中です。しばらくお待ちください...",
                    "inputSchema": {
                        "type": "object",
                        "properties": {}
                    }
                }]
            }
        }
    else:
        # セットアップ完了 - playwright-mcpにプロキシ
        return None  # プロキシが必要


def proxy_to_playwright_mcp(request: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """リクエストをplaywright-mcpにプロキシ"""
    global playwright_mcp_process

    if not playwright_mcp_process:
        return {
            "jsonrpc": "2.0",
            "id": request.get("id"),
            "error": {
                "code": -32603,
                "message": "playwright-mcpが起動していません"
            }
        }

    try:
        # リクエストを送信
        write_jsonrpc_message(playwright_mcp_process.stdin, request)

        # レスポンスを受信
        response = read_jsonrpc_message(playwright_mcp_process.stdout)
        return response

    except Exception as e:
        log(f"プロキシエラー: {e}", "ERROR")
        return {
            "jsonrpc": "2.0",
            "id": request.get("id"),
            "error": {
                "code": -32603,
                "message": f"プロキシエラー: {e}"
            }
        }


def main():
    """メイン処理"""
    global setup_completed

    # HOME環境変数を設定
    os.environ['HOME'] = '/home/user'

    # 終了時のクリーンアップを登録
    atexit.register(stop_processes)

    log("=" * 70)
    log("Playwright MCP Wrapper 起動")
    log("=" * 70)

    # セットアップをバックグラウンドで開始
    setup_thread = threading.Thread(target=run_setup_script, daemon=True)
    setup_thread.start()

    log("MCPサーバーとして応答を開始します")

    # メインループ: JSON-RPCメッセージを処理
    try:
        while True:
            # リクエストを読み取る
            request = read_jsonrpc_message(sys.stdin)
            if not request:
                break

            method = request.get("method")
            log(f"リクエスト受信: {method}", "DEBUG")

            # メソッドに応じて処理
            response = None

            if method == "initialize":
                response = handle_initialize(request)

            elif method == "tools/list":
                response = handle_tools_list(request)
                if response is None:
                    # セットアップ完了後、playwright-mcpを起動してプロキシ
                    if not playwright_mcp_process:
                        if not start_proxy():
                            response = {
                                "jsonrpc": "2.0",
                                "id": request.get("id"),
                                "error": {
                                    "code": -32603,
                                    "message": "proxy.pyの起動に失敗しました"
                                }
                            }
                        elif not start_playwright_mcp():
                            response = {
                                "jsonrpc": "2.0",
                                "id": request.get("id"),
                                "error": {
                                    "code": -32603,
                                    "message": "playwright-mcpの起動に失敗しました"
                                }
                            }

                    if response is None:
                        response = proxy_to_playwright_mcp(request)

            else:
                # その他のメソッドはplaywright-mcpにプロキシ
                if setup_completed and playwright_mcp_process:
                    response = proxy_to_playwright_mcp(request)
                else:
                    response = {
                        "jsonrpc": "2.0",
                        "id": request.get("id"),
                        "error": {
                            "code": -32603,
                            "message": "セットアップ中です。しばらくお待ちください..."
                        }
                    }

            # レスポンスを送信
            if response:
                write_jsonrpc_message(sys.stdout, response)

    except KeyboardInterrupt:
        log("中断されました")
    except Exception as e:
        log(f"エラー: {e}", "ERROR")
        import traceback
        traceback.print_exc(file=sys.stderr)


if __name__ == '__main__':
    main()
