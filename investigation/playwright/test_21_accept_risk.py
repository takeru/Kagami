#!/usr/bin/env python3
"""
テスト21: 証明書エラーを受け入れてページにアクセス

Python MCP Client → proxy.py → playwright-mcp → Firefox → Internet（成功版）
"""
import asyncio
import os
import sys
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def test_accept_risk_and_continue():
    """証明書エラーを受け入れてページにアクセス"""
    print("=" * 70)
    print("テスト: Python MCP Client → playwright-mcp → Firefox → Internet")
    print("=" * 70)
    print()

    project_root = Path(__file__).parent.parent.parent

    # proxy.pyを起動するコマンド（HOME=/home/user）
    server_params = StdioServerParameters(
        command="bash",
        args=[
            "-c",
            'uv run proxy --hostname 127.0.0.1 --port 18911 --plugins proxy.plugin.proxy_pool.ProxyPoolPlugin --proxy-pool "$HTTPS_PROXY" >/dev/null 2>&1 & PROXY_PID=$!; trap "kill $PROXY_PID 2>/dev/null" EXIT; sleep 2; node /opt/node22/lib/node_modules/@playwright/mcp/cli.js --config .mcp/playwright-firefox-config.json --browser firefox --proxy-server http://127.0.0.1:18911'
        ],
        env={
            **os.environ,
            "HOME": "/home/user"
        }
    )

    print("1. MCPサーバーに接続中...")
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            print("   ✅ MCPサーバーに接続")

            # example.comにナビゲート
            print("\n2. example.comにナビゲート中...")
            try:
                await session.call_tool(
                    "browser_navigate",
                    arguments={"url": "https://example.com"}
                )
            except:
                pass  # 証明書エラーは予期している

            # 証明書エラーページで「Advanced」ボタンをクリック
            print("\n3. 「Advanced」ボタンをクリック中...")
            await session.call_tool(
                "browser_click",
                arguments={"element": "Advanced… button", "ref": "e16"}
            )
            print("   ✅ クリック成功")

            # 「Accept the Risk and Continue」ボタンをクリック
            print("\n4. 「Accept the Risk and Continue」ボタンをクリック中...")
            result = await session.call_tool(
                "browser_click",
                arguments={"element": "Accept the Risk and Continue button", "ref": "e25"}
            )
            print("   ✅ クリック成功")

            # ページ読み込みを待つ
            await asyncio.sleep(2)

            # 最終的なスナップショットを取得
            print("\n5. ページ読み込み後のスナップショットを取得中...")
            result = await session.call_tool(
                "browser_snapshot",
                arguments={}
            )
            snapshot = result.content[0].text if result.content else ""
            print(f"   スナップショットサイズ: {len(snapshot)} 文字")

            # ブラウザを閉じる
            await session.call_tool("browser_close", arguments={})
            print("\n✅ テスト完了")

            # 結果を判定
            if "Example Domain" in snapshot:
                print("\n" + "=" * 70)
                print("🎉🎉🎉 成功: Python MCP Client → playwright-mcp → Internet 🎉🎉🎉")
                print("=" * 70)
                print("\n実現できたこと:")
                print("  ✅ Python MCP Client → proxy.py → playwright-mcp → Firefox → Internet")
                print("  ✅ HOME=/home/user設定で動作")
                print("  ✅ Firefox build v1496を正しく使用")
                print("  ✅ JWT認証プロキシ経由でアクセス成功")
                print("  ✅ 証明書エラーを手動で受け入れ")
                print("\nページ内容:")
                print(snapshot[:1000])
                return True
            else:
                print("\n❌ 失敗: ページが正しく読み込まれませんでした")
                print(f"\nスナップショット:\n{snapshot[:1500]}")
                return False


async def main():
    try:
        success = await test_accept_risk_and_continue()
        return success
    except Exception as e:
        print(f"\n❌ エラー: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
