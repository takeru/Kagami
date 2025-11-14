#!/usr/bin/env python3
"""
テスト3: playwright-mcp + firefox + python mcp client
Python MCPクライアントでplaywright MCPサーバーをテスト

このテストでは：
1. proxy.pyなしでplaywright MCPサーバーを起動（Firefoxで直接プロキシ）
2. proxy.pyありでplaywright MCPサーバーを起動

両方をテストして、どちらが動作するか確認します。
"""
import os
import sys
import subprocess
import time
import json
import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def test_mcp_without_proxy_py():
    """proxy.pyなしでMCPサーバーをテスト"""
    print("=" * 70)
    print("テスト3-A: playwright-mcp + Firefox（proxy.pyなし）")
    print("=" * 70)
    print()

    https_proxy = os.getenv("HTTPS_PROXY")
    if not https_proxy:
        print("❌ HTTPS_PROXY環境変数が設定されていません")
        return False

    print(f"上流プロキシ: {https_proxy}")
    print()

    try:
        # MCPサーバーパラメータ（proxy.pyなし）
        print("1. playwright MCPサーバーを起動（proxy.pyなし）...")
        server_params = StdioServerParameters(
            command="npx",
            args=[
                "@playwright/mcp@latest",
                "--config", "/home/user/Kagami/.mcp/playwright-firefox-config.json",
                "--browser", "firefox",
                "--proxy-server", https_proxy,  # 直接上流プロキシを指定
            ],
            env={
                **os.environ,
                "HOME": "/home/user/Kagami/.mcp/firefox_home",
            }
        )

        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                # MCPサーバーを初期化
                await session.initialize()
                print("   ✅ MCPサーバー初期化完了")

                # 利用可能なツールを取得
                tools = await session.list_tools()
                print(f"   ✅ 利用可能なツール数: {len(tools.tools)}")
                print(f"   ツール: {[tool.name for tool in tools.tools[:5]]}")

                # browser_navigateツールでexample.comにアクセス
                print("\n2. example.comにアクセス...")
                result = await session.call_tool(
                    "browser_navigate",
                    arguments={"url": "https://example.com"}
                )
                print(f"   ✅ ナビゲーション成功")
                print(f"   結果: {result.content[:200] if result.content else 'No content'}")

                # スナップショットを取得
                print("\n3. ページスナップショットを取得...")
                snapshot = await session.call_tool("browser_snapshot", arguments={})
                print(f"   ✅ スナップショット取得成功")

                print("\n" + "=" * 70)
                print("✅ テスト成功：proxy.pyなしでも動作しました！")
                print("=" * 70)
                return True

    except Exception as e:
        print("\n" + "=" * 70)
        print("❌ テスト失敗")
        print("=" * 70)
        print(f"\nエラー: {e}")
        import traceback
        traceback.print_exc()
        print("\n結論: proxy.pyなしではMCPサーバーも動作しませんでした")
        return False


async def test_mcp_with_proxy_py():
    """proxy.pyありでMCPサーバーをテスト"""
    print("\n\n")
    print("=" * 70)
    print("テスト3-B: playwright-mcp + Firefox（proxy.pyあり）")
    print("=" * 70)
    print()

    https_proxy = os.getenv("HTTPS_PROXY")
    if not https_proxy:
        print("❌ HTTPS_PROXY環境変数が設定されていません")
        return False

    print(f"上流プロキシ: {https_proxy}")
    print()

    # proxy.pyを起動
    proxy_port = 18913
    print(f"1. proxy.pyを起動（ポート {proxy_port}）...")
    proxy_process = subprocess.Popen(
        [
            'uv', 'run', 'proxy',
            '--hostname', '127.0.0.1',
            '--port', str(proxy_port),
            '--plugins', 'proxy.plugin.proxy_pool.ProxyPoolPlugin',
            '--proxy-pool', https_proxy,
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    # プロキシの起動を待機
    time.sleep(3)
    print(f"   ✅ proxy.py起動完了: http://127.0.0.1:{proxy_port}")

    try:
        # MCPサーバーパラメータ（proxy.pyあり）
        print("\n2. playwright MCPサーバーを起動（proxy.py経由）...")
        server_params = StdioServerParameters(
            command="npx",
            args=[
                "@playwright/mcp@latest",
                "--config", "/home/user/Kagami/.mcp/playwright-firefox-config.json",
                "--browser", "firefox",
                "--proxy-server", f"http://127.0.0.1:{proxy_port}",  # proxy.pyを経由
            ],
            env={
                **os.environ,
                "HOME": "/home/user/Kagami/.mcp/firefox_home",
            }
        )

        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                # MCPサーバーを初期化
                await session.initialize()
                print("   ✅ MCPサーバー初期化完了")

                # 利用可能なツールを取得
                tools = await session.list_tools()
                print(f"   ✅ 利用可能なツール数: {len(tools.tools)}")
                print(f"   ツール: {[tool.name for tool in tools.tools[:5]]}")

                # browser_navigateツールでexample.comにアクセス
                print("\n3. example.comにアクセス...")
                result = await session.call_tool(
                    "browser_navigate",
                    arguments={"url": "https://example.com"}
                )
                print(f"   ✅ ナビゲーション成功")

                # スナップショットを取得
                print("\n4. ページスナップショットを取得...")
                snapshot = await session.call_tool("browser_snapshot", arguments={})
                print(f"   ✅ スナップショット取得成功")
                # スナップショットの内容を少し表示
                if snapshot.content:
                    content_str = str(snapshot.content)[:300]
                    print(f"   内容: {content_str}...")

                print("\n" + "=" * 70)
                print("✅ テスト成功：proxy.pyを使うことで動作しました！")
                print("=" * 70)
                print("\nアーキテクチャ:")
                print("  Python MCP Client")
                print("      ↓ (stdio)")
                print("  playwright MCP Server")
                print("      ↓")
                print("  Firefox")
                print("      ↓")
                print(f"  localhost:{proxy_port} (proxy.py)")
                print("      ↓")
                print("  upstream proxy (JWT認証)")
                print("      ↓")
                print("  Internet")
                return True

    except Exception as e:
        print("\n" + "=" * 70)
        print("❌ テスト失敗")
        print("=" * 70)
        print(f"\nエラー: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        # proxy.pyを停止
        print("\n5. proxy.pyを停止...")
        proxy_process.terminate()
        try:
            proxy_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proxy_process.kill()
        print("   ✅ 停止完了")


async def main():
    print("playwright-mcp + Python MCPクライアント テスト")
    print()

    # まず proxy.pyなしをテスト
    result_without_proxy = await test_mcp_without_proxy_py()

    # 次に proxy.pyありをテスト
    result_with_proxy = await test_mcp_with_proxy_py()

    print("\n\n")
    print("=" * 70)
    print("テスト3 まとめ")
    print("=" * 70)
    print(f"\nproxy.pyなし: {'✅ 成功' if result_without_proxy else '❌ 失敗'}")
    print(f"proxy.pyあり: {'✅ 成功' if result_with_proxy else '❌ 失敗'}")

    if result_with_proxy and not result_without_proxy:
        print("\n結論: playwright MCPサーバーでもproxy.pyが必要です")
    elif result_without_proxy:
        print("\n結論: playwright MCPサーバーはproxy.pyなしでも動作します")

    return result_with_proxy or result_without_proxy


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
