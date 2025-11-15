#!/usr/bin/env python3
"""
Yahoo! JAPANにアクセスしてトピックを取得

Python MCP Client → playwright-mcp-server(firefox) → proxy.py → JWT認証Proxy → internet
"""
import asyncio
import os
import sys
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def test_yahoo_topics():
    """Yahoo! JAPANにアクセスしてトピックを取得"""
    print("=" * 70)
    print("Yahoo! JAPAN トピック取得テスト")
    print("=" * 70)
    print()

    project_root = Path(__file__).parent.parent.parent

    # cli.jsを直接実行（HOME=/home/user）
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

            # yahoo.co.jpにナビゲート
            print("\n2. yahoo.co.jpにナビゲート中...")
            result = await session.call_tool(
                "browser_navigate",
                arguments={"url": "https://www.yahoo.co.jp"}
            )
            nav_result = result.content[0].text if result.content else 'No content'
            print(f"   結果:\n{nav_result[:500]}")

            # スナップショットを取得
            print("\n3. スナップショット取得中...")
            result = await session.call_tool(
                "browser_snapshot",
                arguments={}
            )
            snapshot = result.content[0].text if result.content else ""
            print(f"   スナップショットサイズ: {len(snapshot)} 文字")

            # トピックを抽出
            print("\n4. トピックを抽出中...")
            topics = []

            # スナップショットからトピックを抽出
            lines = snapshot.split('\n')
            for i, line in enumerate(lines):
                # リンクやheadingを探す
                if 'link' in line.lower() or 'heading' in line.lower():
                    # 次の行にテキストがあるかチェック
                    if i + 1 < len(lines):
                        text = lines[i + 1].strip()
                        if text and len(text) > 5 and len(text) < 100:
                            # 明らかにUIテキストでないものを抽出
                            if not any(skip in text.lower() for skip in ['button', 'menu', 'search', 'login', 'yahoo']):
                                topics.append(text)

            # ユニークなトピックを表示
            unique_topics = list(dict.fromkeys(topics))[:20]  # 上位20件

            if unique_topics:
                print("\n📰 Yahoo! JAPANトピック:")
                for idx, topic in enumerate(unique_topics, 1):
                    print(f"   {idx}. {topic}")
            else:
                print("   ⚠️ トピックを抽出できませんでした")

            # スナップショットの一部を表示（デバッグ用）
            print("\n5. スナップショット詳細（最初の2000文字）:")
            print(snapshot[:2000])

            # ブラウザを閉じる
            await session.call_tool("browser_close", arguments={})
            print("\n✅ テスト完了")

            # 結果を判定
            if "yahoo" in snapshot.lower():
                print("\n" + "=" * 70)
                print("🎉 成功: Yahoo! JAPANにアクセスできました")
                print("=" * 70)
                return True
            else:
                print("\n❌ 失敗: Yahoo! JAPANにアクセスできませんでした")
                return False


async def main():
    try:
        success = await test_yahoo_topics()
        return success
    except Exception as e:
        print(f"\n❌ エラー: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
