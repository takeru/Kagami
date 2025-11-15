#!/usr/bin/env python3
"""
テスト14: proxy.py方式でMCPクライアントから接続

従来のproxy.py方式で動作するか確認
"""
import asyncio
import os
import sys
import time
import subprocess
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def test_with_proxy_py():
    """proxy.py方式でMCPクライアントからアクセス"""
    print("=" * 70)
    print("テスト: MCP Client -> proxy.py方式")
    print("=" * 70)
    print()

    project_root = Path(__file__).parent.parent.parent

    # proxy.pyを起動するコマンド
    server_params = StdioServerParameters(
        command="bash",
        args=[
            "-c",
            'uv run proxy --hostname 127.0.0.1 --port 18911 --plugins proxy.plugin.proxy_pool.ProxyPoolPlugin --proxy-pool "$HTTPS_PROXY" >/dev/null 2>&1 & PROXY_PID=$!; trap "kill $PROXY_PID 2>/dev/null" EXIT; sleep 2; npx @playwright/mcp@latest --config .mcp/playwright-firefox-config.json --browser firefox --proxy-server http://127.0.0.1:18911'
        ],
        env={
            **os.environ,
            "HOME": str(project_root / ".mcp" / "firefox_home")
        }
    )

    print("1. MCPサーバー（proxy.py方式）に接続中...")
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

            # ブラウザを閉じる
            await session.call_tool("browser_close", arguments={})
            print("\n✅ テスト完了")

            # 結果を判定
            if "Example Domain" in snapshot or "example.com" in snapshot.lower():
                print("\n🎉 成功: proxy.py方式では動作しました！")
                print("\n📝 結論:")
                print("  - proxy.py方式: ✅ 動作する")
                print("  - extraHTTPHeaders方式: ❌ playwright-mcp-serverが対応していない可能性")
                return True
            else:
                print("\n❌ 失敗: proxy.py方式でも失敗しました")
                return False


async def main():
    try:
        success = await test_with_proxy_py()
        return success
    except Exception as e:
        print(f"\n❌ エラー: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
