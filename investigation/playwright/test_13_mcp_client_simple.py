#!/usr/bin/env python3
"""
テスト13: MCPクライアントから単純なページ（example.com）にアクセス

デバッグ目的でシンプルなページでテスト
"""
import asyncio
import os
import sys
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def test_simple_page():
    """MCPクライアントからexample.comにアクセス"""
    print("=" * 70)
    print("テスト: MCP Client -> example.com")
    print("=" * 70)
    print()

    project_root = Path(__file__).parent.parent.parent

    server_params = StdioServerParameters(
        command="uv",
        args=["run", "python", ".mcp/start_playwright_mcp_firefox.py"],
        env={
            **os.environ,
            "HOME": str(project_root / ".mcp" / "firefox_home")
        }
    )

    print("1. MCPサーバーに接続中...")
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            print("   ✅ MCPサーバーに接続")

            # example.comにナビゲート
            print("\n2. example.comにナビゲート中...")
            result = await session.call_tool(
                "browser_navigate",
                arguments={"url": "https://example.com"}
            )
            print(f"   結果:\n{result.content[0].text if result.content else 'No content'}")

            # スナップショットを取得
            print("\n3. スナップショット取得中...")
            result = await session.call_tool(
                "browser_snapshot",
                arguments={}
            )
            snapshot = result.content[0].text if result.content else ""
            print(f"   スナップショットサイズ: {len(snapshot)} 文字")
            print(f"   内容:\n{snapshot}")

            # ブラウザを閉じる
            await session.call_tool("browser_close", arguments={})
            print("\n✅ テスト完了")

            # 結果を判定
            if "Example Domain" in snapshot or "example.com" in snapshot.lower():
                print("\n🎉 成功: ページにアクセスできました！")
                return True
            else:
                print("\n❌ 失敗: ページが正しく読み込まれませんでした")
                return False


async def main():
    try:
        success = await test_simple_page()
        return success
    except Exception as e:
        print(f"\n❌ エラー: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
