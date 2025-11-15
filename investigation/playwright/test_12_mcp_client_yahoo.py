#!/usr/bin/env python3
"""
テスト12: PythonのMCPクライアントからplaywright-mcp-serverに接続してYahoo! Japanにアクセス

Python MCP Client -> playwright-mcp-server (Firefox) -> Internet
"""
import asyncio
import os
import sys
from pathlib import Path

# mcp をインストールする必要があるかチェック
try:
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
except ImportError:
    print("❌ mcpライブラリがインストールされていません")
    print("インストール: uv add mcp")
    sys.exit(1)


async def test_mcp_client_to_yahoo():
    """MCPクライアントからYahoo! Japanにアクセス"""
    print("=" * 70)
    print("テスト: Python MCP Client -> playwright-mcp-server -> Yahoo! Japan")
    print("=" * 70)
    print()

    # プロジェクトルート
    project_root = Path(__file__).parent.parent.parent

    # MCPサーバーの起動コマンド
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
            # サーバーを初期化
            await session.initialize()
            print("   ✅ MCPサーバーに接続しました")

            # 利用可能なツールを確認
            print("\n2. 利用可能なツールを確認中...")
            tools = await session.list_tools()
            print(f"   ✅ {len(tools.tools)} 個のツールが利用可能です")

            tool_names = [tool.name for tool in tools.tools]
            print(f"   主なツール: {', '.join(tool_names[:5])}...")

            # Yahoo! Japanにナビゲート
            print("\n3. Yahoo! Japanにナビゲート中...")
            try:
                result = await session.call_tool(
                    "browser_navigate",
                    arguments={"url": "https://www.yahoo.co.jp/"}
                )
                print("   ✅ Yahoo! Japanにアクセスしました")
                print(f"   結果: {result.content[0].text[:200] if result.content else 'No content'}...")
            except Exception as e:
                print(f"   ❌ ナビゲート失敗: {e}")
                return False

            # ページのスナップショットを取得
            print("\n4. ページのスナップショットを取得中...")
            try:
                result = await session.call_tool(
                    "browser_snapshot",
                    arguments={}
                )
                snapshot_text = result.content[0].text if result.content else ""
                print("   ✅ スナップショット取得成功")
                print(f"   スナップショットサイズ: {len(snapshot_text)} 文字")

                # トピックを抽出（簡易版）
                print("\n5. トピックを抽出中...")
                lines = snapshot_text.split('\n')
                topics = []
                for line in lines[:100]:  # 最初の100行から探す
                    if 'link' in line.lower() or 'heading' in line.lower():
                        # 行から意味のあるテキストを抽出
                        if len(line.strip()) > 10 and len(line.strip()) < 200:
                            topics.append(line.strip())

                if topics:
                    print(f"   ✅ {len(topics)} 個のトピック候補を発見")
                    print("\n   主なトピック:")
                    for i, topic in enumerate(topics[:10], 1):
                        print(f"   {i}. {topic[:100]}...")
                else:
                    print("   ⚠ トピックが見つかりませんでした")
                    print(f"\n   スナップショットの一部:\n{snapshot_text[:500]}...")

            except Exception as e:
                print(f"   ❌ スナップショット取得失敗: {e}")
                import traceback
                traceback.print_exc()
                return False

            # ブラウザを閉じる
            print("\n6. ブラウザを閉じています...")
            try:
                await session.call_tool("browser_close", arguments={})
                print("   ✅ ブラウザを閉じました")
            except Exception as e:
                print(f"   ⚠ ブラウザのクローズ: {e}")

            return True


async def main():
    """メイン処理"""
    print("Python MCP Client -> playwright-mcp-server (Firefox) -> Internet")
    print("Yahoo! Japan トピック取得テスト")
    print()

    try:
        success = await test_mcp_client_to_yahoo()

        print("\n\n")
        print("=" * 70)
        print("テスト結果")
        print("=" * 70)

        if success:
            print("\n🎉 成功: Python MCP Client経由でYahoo! Japanにアクセスできました！")
            print()
            print("確認できたこと:")
            print("  ✅ PythonのMCPクライアントからサーバーに接続")
            print("  ✅ playwright-mcp-server（Firefox）が起動")
            print("  ✅ proxy.pyなしで外部サイト（Yahoo! Japan）にアクセス")
            print("  ✅ ページのスナップショット取得")
        else:
            print("\n❌ 失敗: エラーが発生しました")

        return success

    except Exception as e:
        print(f"\n❌ エラー: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
