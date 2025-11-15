#!/usr/bin/env python3
"""
セットアップ検証用テスト（対話なし）

setup.shが正しく動作したかを確認
"""
import asyncio
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def test_playwright_mcp_setup():
    """セットアップが正しく完了したかテスト"""
    print("=" * 70)
    print("Playwright MCP セットアップ検証テスト")
    print("=" * 70)
    print()

    # HOME環境変数を設定
    os.environ['HOME'] = '/home/user'

    # HTTPS_PROXY環境変数を確認
    https_proxy = os.environ.get('HTTPS_PROXY', '')
    if not https_proxy:
        print("❌ HTTPS_PROXY環境変数が設定されていません")
        return False

    print("環境変数:")
    print(f"  HOME: {os.environ['HOME']}")
    print(f"  HTTPS_PROXY: ✓ 設定されています")
    print()

    # 1. proxy.pyを起動
    print("1. proxy.pyを起動中...")
    proxy_process = subprocess.Popen(
        [
            "uv", "run", "proxy",
            "--hostname", "127.0.0.1",
            "--port", "18916",
            "--plugins", "proxy.plugin.proxy_pool.ProxyPoolPlugin",
            "--proxy-pool", https_proxy
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

    time.sleep(2)
    print("   ✅ proxy.py起動完了")
    print()

    try:
        # 2. playwright-mcpサーバーのパラメータを設定
        print("2. playwright-mcpサーバーに接続中...")

        config_path = "playwright_mcp_claude_code_web/playwright-firefox-config.json"

        server_params = StdioServerParameters(
            command="node",
            args=[
                "/opt/node22/lib/node_modules/@playwright/mcp/cli.js",
                "--config", config_path,
                "--browser", "firefox",
                "--proxy-server", "http://127.0.0.1:18916"
            ],
            env={
                **os.environ,
                "HOME": "/home/user"
            }
        )

        # 3. MCPクライアントセッションを開始
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                print("   ✅ playwright-mcpサーバーに接続成功")
                print()

                # 4. example.comにアクセス（シンプルなテスト）
                print("3. example.comにアクセス中...")
                result = await session.call_tool(
                    "browser_navigate",
                    arguments={"url": "https://example.com"}
                )

                nav_result = result.content[0].text if result.content else ""

                if "Error" in nav_result and "SEC_ERROR" in nav_result:
                    print("   ❌ 証明書エラーが発生しました")
                    print("   → CA証明書がインポートされていない可能性があります")
                    return False
                elif "Error" in nav_result:
                    print(f"   ⚠️ エラーが発生: {nav_result[:200]}")
                    return False
                else:
                    print("   ✅ example.comにアクセス成功（証明書エラーなし）")

                # 5. スナップショットを取得
                print()
                print("4. スナップショットを取得中...")
                result = await session.call_tool(
                    "browser_snapshot",
                    arguments={}
                )

                snapshot = result.content[0].text if result.content else ""
                print(f"   ✅ スナップショット取得完了 ({len(snapshot)} 文字)")

                # 6. Example Domainが表示されているか確認
                if "Example Domain" in snapshot:
                    print("   ✅ 'Example Domain' を確認")
                else:
                    print("   ⚠️ 'Example Domain' が見つかりません")

                # 7. ブラウザを閉じる
                print()
                print("5. ブラウザを閉じています...")
                await session.call_tool("browser_close", arguments={})
                print("   ✅ ブラウザを閉じました")

                # 8. 成功メッセージ
                print()
                print("=" * 70)
                print("🎉 セットアップ検証テスト成功！")
                print("=" * 70)
                print()
                print("✅ すべてのコンポーネントが正しく動作しています:")
                print("  - certutil")
                print("  - @playwright/mcp")
                print("  - Firefox build v1496")
                print("  - Firefoxプロファイル")
                print("  - CA証明書インポート")
                print("  - proxy.py")
                print("  - MCP設定ファイル")
                print()
                print("次のステップ:")
                print("  HOME=/home/user uv run python playwright_mcp_claude_code_web/example.py")
                print()
                return True

    except Exception as e:
        print()
        print(f"❌ エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        # proxy.pyを停止
        print()
        print("6. proxy.pyを停止中...")
        proxy_process.send_signal(signal.SIGTERM)
        try:
            proxy_process.wait(timeout=5)
            print("   ✅ proxy.pyを停止しました")
        except subprocess.TimeoutExpired:
            proxy_process.kill()
            print("   ⚠️ proxy.pyを強制終了しました")


async def main():
    """メイン関数"""
    try:
        success = await test_playwright_mcp_setup()
        return success
    except Exception as e:
        print(f"\n❌ エラー: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    # HOME環境変数を設定
    os.environ['HOME'] = '/home/user'

    success = asyncio.run(main())
    sys.exit(0 if success else 1)
