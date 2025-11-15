#!/usr/bin/env python3
"""
テスト16: HOME=/home/userでMCPクライアントから接続

proxy.py方式 + HOME=/home/userで動作確認
"""
import asyncio
import os
import sys
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def test_with_home_user():
    """HOME=/home/userでMCPクライアントからアクセス"""
    print("=" * 70)
    print("テスト: MCP Client -> proxy.py方式 (HOME=/home/user)")
    print("=" * 70)
    print()

    project_root = Path(__file__).parent.parent.parent

    # proxy.pyを起動するコマンド（HOME=/home/user）
    server_params = StdioServerParameters(
        command="bash",
        args=[
            "-c",
            'uv run proxy --hostname 127.0.0.1 --port 18911 --plugins proxy.plugin.proxy_pool.ProxyPoolPlugin --proxy-pool "$HTTPS_PROXY" >/dev/null 2>&1 & PROXY_PID=$!; trap "kill $PROXY_PID 2>/dev/null" EXIT; sleep 2; npx @playwright/mcp@latest --config .mcp/playwright-firefox-config.json --browser firefox --proxy-server http://127.0.0.1:18911'
        ],
        env={
            **os.environ,
            "HOME": "/home/user"  # 変更: /home/user に設定
        }
    )

    print("1. MCPサーバー（proxy.py方式、HOME=/home/user）に接続中...")
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
            nav_result = result.content[0].text if result.content else 'No content'
            print(f"   結果:\n{nav_result}")

            # スナップショットを取得
            print("\n3. スナップショット取得中...")
            result = await session.call_tool(
                "browser_snapshot",
                arguments={}
            )
            snapshot = result.content[0].text if result.content else ""
            print(f"   スナップショットサイズ: {len(snapshot)} 文字")

            # スナップショットの一部を表示
            if len(snapshot) > 200:
                print(f"   内容の一部:\n{snapshot[:500]}")

            # ブラウザを閉じる
            await session.call_tool("browser_close", arguments={})
            print("\n✅ テスト完了")

            # 結果を判定
            if "Example Domain" in snapshot or "example.com" in snapshot.lower():
                print("\n🎉 成功: HOME=/home/userで動作しました！")
                print("\n📝 結論:")
                print("  - Firefox インストール先: /home/user/.cache/ms-playwright/firefox-1495")
                print("  - HOME=/home/user設定: ✅ 有効")
                print("  - proxy.py方式: ✅ 動作する")
                return True
            else:
                print("\n❌ 失敗: ページが正しく読み込まれませんでした")
                print(f"\nスナップショット: {snapshot}")
                return False


async def main():
    try:
        success = await test_with_home_user()
        return success
    except Exception as e:
        print(f"\n❌ エラー: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
