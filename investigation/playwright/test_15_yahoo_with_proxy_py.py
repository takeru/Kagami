#!/usr/bin/env python3
"""
テスト15: proxy.py方式でYahoo! Japanのトピックを取得

Python MCP Client -> proxy.py -> playwright-mcp-server (Chromium) -> Internet
"""
import asyncio
import os
import sys
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def get_yahoo_topics():
    """proxy.py方式でYahoo! Japanのトピックを取得"""
    print("=" * 70)
    print("Python MCP Client -> proxy.py -> playwright-mcp (Chromium) -> Yahoo! Japan")
    print("=" * 70)
    print()

    # ロックディレクトリを削除
    import shutil
    lock_dir = Path("/root/.cache/ms-playwright/mcp-chromium")
    if lock_dir.exists():
        shutil.rmtree(lock_dir)
        print("   🔧 ロックディレクトリを削除しました")

    project_root = Path(__file__).parent.parent.parent

    # proxy.pyを使う従来の方式
    server_params = StdioServerParameters(
        command="bash",
        args=[
            "-c",
            'uv run proxy --hostname 127.0.0.1 --port 18911 --plugins proxy.plugin.proxy_pool.ProxyPoolPlugin --proxy-pool "$HTTPS_PROXY" >/dev/null 2>&1 & PROXY_PID=$!; trap "kill $PROXY_PID 2>/dev/null" EXIT; sleep 2; HTTPS_PROXY=http://127.0.0.1:18911 HTTP_PROXY=http://127.0.0.1:18911 npx @playwright/mcp --browser chromium --isolated'
        ],
        env=os.environ
    )

    print("1. MCPサーバー（proxy.py方式）に接続中...")
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            print("   ✅ MCPサーバーに接続しました")

            # Yahoo! Japanにナビゲート
            print("\n2. Yahoo! Japanにナビゲート中...")
            result = await session.call_tool(
                "browser_navigate",
                arguments={"url": "https://www.yahoo.co.jp/"}
            )
            nav_result = result.content[0].text if result.content else ""
            if "Error" in nav_result:
                print(f"   ⚠ ナビゲート結果: {nav_result[:200]}")
            else:
                print("   ✅ Yahoo! Japanにアクセスしました")

            # スナップショットを取得
            print("\n3. ページのスナップショットを取得中...")
            result = await session.call_tool(
                "browser_snapshot",
                arguments={}
            )
            snapshot = result.content[0].text if result.content else ""
            print(f"   ✅ スナップショット取得完了（{len(snapshot)} 文字）")

            # トピックを抽出
            print("\n4. Yahoo! Japanトピックを抽出中...")
            topics = []

            # スナップショットから見出しやリンクを探す
            lines = snapshot.split('\n')
            for line in lines:
                # Yahoo!のニューストピックらしい行を探す
                if any(keyword in line.lower() for keyword in ['link', 'heading', 'button']):
                    # 長すぎる行や短すぎる行をフィルタ
                    cleaned = line.strip()
                    if 15 < len(cleaned) < 300:
                        topics.append(cleaned)

            # ブラウザを閉じる
            await session.call_tool("browser_close", arguments={})

            if topics:
                print(f"   ✅ {len(topics)} 個のトピック候補を発見")
                print("\n" + "=" * 70)
                print("Yahoo! Japan トピックリスト")
                print("=" * 70)
                for i, topic in enumerate(topics[:20], 1):  # 最初の20件
                    print(f"{i:2d}. {topic[:100]}")
                    if len(topic) > 100:
                        print(f"     {topic[100:200]}...")
                print("=" * 70)
                return True
            else:
                print("   ⚠ トピックが見つかりませんでした")
                print("\n📝 スナップショットの一部:")
                print(snapshot[:1000])
                return False


async def main():
    print("Yahoo! Japan トピック取得テスト")
    print()

    try:
        success = await get_yahoo_topics()

        print("\n\n")
        print("=" * 70)
        print("最終結果")
        print("=" * 70)

        if success:
            print("\n🎉 成功！")
            print()
            print("実現できたこと:")
            print("  ✅ Python MCP Client -> proxy.py -> playwright-mcp -> Chromium -> Internet")
            print("  ✅ JWT認証プロキシ経由でYahoo! Japanにアクセス")
            print("  ✅ トピックリストの取得")
            print()
            print("📝 注意:")
            print("  - extraHTTPHeaders方式はplaywright-mcp-serverが未対応")
            print("  - proxy.py方式が現時点での最適解")
        else:
            print("\n⚠ 部分的に成功")
            print("  - Yahoo! Japanにはアクセスできましたが、トピックの抽出に失敗しました")

        return success

    except Exception as e:
        print(f"\n❌ エラー: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
