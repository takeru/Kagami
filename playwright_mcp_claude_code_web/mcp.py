#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# ///
"""
Claude Code用 Playwright MCP サーバー起動スクリプト（遅延ツール登録対応）

このスクリプトは以下を実現します：
  1. 起動時に即座にMCPプロトコルサーバーとして応答（タイムアウト回避）
  2. バックグラウンドスレッドでセットアップを実行
  3. セットアップ完了後、playwright-mcpにリクエストをプロキシ
  4. セットアップ中は適切なレスポンスを返す

通信フロー:
  Claude Code → mcp.py (JSON-RPC wrapper) → playwright-mcp (Firefox) → proxy.py → Internet
"""
import os
import sys
import subprocess
import time
import json
import threading
import signal
import atexit
from pathlib import Path
from typing import Optional, Dict, Any
from io import TextIOWrapper

# グローバル変数
proxy_process = None
playwright_process = None
setup_completed = False
setup_error = None
setup_thread = None


def log(message: str, level: str = "INFO"):
    """ログ出力（stderrに出力）"""
    prefix = {
        "INFO": "✓",
        "WARN": "⚠️",
        "ERROR": "❌",
        "DEBUG": "🔍"
    }.get(level, "ℹ️")
    print(f"[MCP] {prefix} {message}", file=sys.stderr, flush=True)


def check_setup_completed() -> bool:
    """セットアップが完了しているかチェック"""
    script_dir = Path(__file__).parent

    checks = [
        Path("/home/user/.cache/ms-playwright/firefox-1496").exists(),
        Path("/home/user/firefox-profile/cert9.db").exists(),
        (script_dir / "playwright-firefox-config.json").exists(),
    ]

    return all(checks)


def send_tools_list_changed():
    """tools/list_changedイベントを送信"""
    try:
        notification = {
            "jsonrpc": "2.0",
            "method": "notifications/tools/list_changed"
        }
        write_jsonrpc_message(sys.stdout, notification)
        log("tools/list_changed通知を送信しました")
    except Exception as e:
        log(f"通知送信エラー: {e}", "ERROR")


def run_setup_script():
    """セットアップスクリプトを実行"""
    global setup_completed, setup_error

    try:
        log("バックグラウンドセットアップを開始します...")
        script_dir = Path(__file__).parent
        setup_script = script_dir / "setup_mcp.py"

        result = subprocess.run(
            ["python3", str(setup_script)],
            capture_output=True,
            text=True,
            check=True
        )

        log("セットアップが完了しました！")
        setup_completed = True

        # セットアップ完了を通知
        send_tools_list_changed()

    except subprocess.CalledProcessError as e:
        setup_error = f"セットアップエラー: {e.stderr}"
        log(setup_error, "ERROR")
    except Exception as e:
        setup_error = f"予期しないエラー: {str(e)}"
        log(setup_error, "ERROR")


def start_proxy():
    """proxy.pyを起動"""
    global proxy_process

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

        time.sleep(2)
        log("proxy.py起動完了 (localhost:18915)")
        return True

    except Exception as e:
        log(f"proxy.py起動エラー: {e}", "ERROR")
        return False


def stop_proxy():
    """proxy.pyを停止"""
    global proxy_process

    if proxy_process is None:
        return

    try:
        proxy_process.terminate()
        proxy_process.wait(timeout=5)
    except:
        try:
            proxy_process.kill()
        except:
            pass


def start_playwright_mcp():
    """playwright-mcpプロセスを起動"""
    global playwright_process

    script_dir = Path(__file__).parent
    config_path = str(script_dir / "playwright-firefox-config.json")

    if not os.path.exists(config_path):
        log(f"設定ファイルが見つかりません: {config_path}", "ERROR")
        return None

    log("playwright-mcpプロセスを起動中...")

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
        playwright_process = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            env=env,
            bufsize=0
        )

        log("playwright-mcpプロセス起動完了")
        return playwright_process

    except Exception as e:
        log(f"playwright-mcp起動エラー: {e}", "ERROR")
        return None


def stop_playwright():
    """playwright-mcpプロセスを停止"""
    global playwright_process

    if playwright_process is None:
        return

    try:
        playwright_process.terminate()
        playwright_process.wait(timeout=5)
    except:
        try:
            playwright_process.kill()
        except:
            pass


def cleanup():
    """クリーンアップ処理"""
    log("クリーンアップ中...")
    stop_playwright()
    stop_proxy()


def read_jsonrpc_message(stream) -> Optional[Dict[str, Any]]:
    """JSON-RPCメッセージを読み取る"""
    try:
        # Content-Lengthヘッダーを読み取る
        content_length = None
        while True:
            line = stream.readline()
            if not line:
                return None

            line = line.strip()
            if not line:
                break

            if line.lower().startswith("content-length:"):
                content_length = int(line.split(":")[1].strip())

        if content_length is None:
            return None

        # JSON本文を読み取る
        content = stream.read(content_length)
        if not content:
            return None

        return json.loads(content)

    except Exception as e:
        log(f"メッセージ読み取りエラー: {e}", "ERROR")
        return None


def write_jsonrpc_message(stream, message: Dict[str, Any]):
    """JSON-RPCメッセージを書き込む"""
    try:
        content = json.dumps(message)
        content_bytes = content.encode('utf-8')

        header = f"Content-Length: {len(content_bytes)}\r\n\r\n"
        stream.write(header)
        stream.write(content)
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


def handle_tools_list(request: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    tools/listリクエストを処理

    セットアップ完了後はNoneを返し、呼び出し元でプロキシモードに移行する
    """
    global setup_completed, setup_error

    if setup_error:
        # セットアップエラー時
        return {
            "jsonrpc": "2.0",
            "id": request.get("id"),
            "result": {
                "tools": [
                    {
                        "name": "mcp_setup_status",
                        "description": f"セットアップエラー: {setup_error}",
                        "inputSchema": {
                            "type": "object",
                            "properties": {}
                        }
                    }
                ]
            }
        }

    if not setup_completed:
        # セットアップ中
        return {
            "jsonrpc": "2.0",
            "id": request.get("id"),
            "result": {
                "tools": [
                    {
                        "name": "mcp_setup_status",
                        "description": "Playwright MCPのセットアップ中です。数分お待ちください...",
                        "inputSchema": {
                            "type": "object",
                            "properties": {}
                        }
                    }
                ]
            }
        }

    # セットアップ完了：Noneを返してプロキシモードへ移行を指示
    return None


def proxy_mode():
    """プロキシモード: playwright-mcpとの間でメッセージを中継"""
    global playwright_process

    if playwright_process is None:
        log("playwright-mcpプロセスが起動していません", "ERROR")
        return

    log("プロキシモードに移行します")

    # stdoutからplaywright-mcpの出力を読み取り、sys.stdoutに書き込む
    def forward_output():
        try:
            while True:
                msg = read_jsonrpc_message(playwright_process.stdout)
                if msg is None:
                    break
                write_jsonrpc_message(sys.stdout, msg)
        except Exception as e:
            log(f"出力転送エラー: {e}", "ERROR")

    # バックグラウンドスレッドで出力転送
    output_thread = threading.Thread(target=forward_output, daemon=True)
    output_thread.start()

    # stdinから読み取り、playwright-mcpに書き込む
    try:
        while True:
            msg = read_jsonrpc_message(sys.stdin)
            if msg is None:
                break

            content = json.dumps(msg)
            content_bytes = content.encode('utf-8')
            header = f"Content-Length: {len(content_bytes)}\r\n\r\n"

            playwright_process.stdin.write(header.encode('utf-8'))
            playwright_process.stdin.write(content_bytes)
            playwright_process.stdin.flush()

    except Exception as e:
        log(f"入力転送エラー: {e}", "ERROR")


def wrapper_mode():
    """ラッパーモード: セットアップ完了までリクエストを処理"""
    global setup_completed

    log("ラッパーモードで起動しました")

    # initializeを待つ
    initialized = False

    try:
        while True:
            msg = read_jsonrpc_message(sys.stdin)
            if msg is None:
                break

            method = msg.get("method")

            if method == "initialize":
                response = handle_initialize(msg)
                write_jsonrpc_message(sys.stdout, response)
                initialized = True

            elif method == "initialized":
                # initialized通知には応答しない
                pass

            elif method == "tools/list":
                response = handle_tools_list(msg)

                # セットアップ完了後、プロキシモードに移行
                if response is None:
                    log("セットアップ完了。プロキシモードに移行します...")
                    if start_proxy() and start_playwright_mcp():
                        # このtools/listリクエストをplaywright-mcpに転送
                        content = json.dumps(msg)
                        content_bytes = content.encode('utf-8')
                        header = f"Content-Length: {len(content_bytes)}\r\n\r\n"

                        playwright_process.stdin.write(header.encode('utf-8'))
                        playwright_process.stdin.write(content_bytes)
                        playwright_process.stdin.flush()

                        # playwright-mcpからの応答を読み取って返す
                        playwright_response = read_jsonrpc_message(playwright_process.stdout)
                        if playwright_response:
                            write_jsonrpc_message(sys.stdout, playwright_response)

                        # プロキシモードへ移行
                        proxy_mode()
                        return
                    else:
                        # プロキシ起動失敗
                        error_response = {
                            "jsonrpc": "2.0",
                            "id": msg.get("id"),
                            "error": {
                                "code": -32603,
                                "message": "Failed to start playwright-mcp"
                            }
                        }
                        write_jsonrpc_message(sys.stdout, error_response)
                else:
                    write_jsonrpc_message(sys.stdout, response)

            else:
                # その他のメソッドはエラーを返す
                response = {
                    "jsonrpc": "2.0",
                    "id": msg.get("id"),
                    "error": {
                        "code": -32601,
                        "message": "Method not found"
                    }
                }
                write_jsonrpc_message(sys.stdout, response)

    except Exception as e:
        log(f"ラッパーモードエラー: {e}", "ERROR")
        import traceback
        traceback.print_exc(file=sys.stderr)


def main():
    """メイン処理"""
    global setup_completed, setup_thread

    # HOME環境変数を設定
    os.environ['HOME'] = '/home/user'

    # クリーンアップ処理を登録
    atexit.register(cleanup)

    # セットアップ状態をチェック
    if check_setup_completed():
        log("セットアップ済みを確認しました")
        setup_completed = True
    else:
        log("セットアップが必要です。バックグラウンドで開始します...")
        setup_thread = threading.Thread(target=run_setup_script, daemon=True)
        setup_thread.start()

    # ラッパーモードで起動
    try:
        wrapper_mode()
    except KeyboardInterrupt:
        log("中断されました")
    except Exception as e:
        log(f"エラー: {e}", "ERROR")
        import traceback
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
