#!/usr/bin/env python3
"""
証明書エラーをバイパスしてYahoo! JAPANにアクセス

Python MCP Client → playwright-mcp-server(firefox) → proxy.py → JWT認証Proxy → internet
"""
import asyncio
import os
import sys
import re
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def test_yahoo_with_cert_bypass():
    """証明書エラーをバイパスしてYahoo! JAPANにアクセス"""
    print("=" * 70)
    print("Yahoo! JAPAN アクセステスト（証明書エラーバイパス）")
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

            # スナップショットを取得して証明書エラーページかチェック
            print("\n3. ページ状態を確認中...")
            result = await session.call_tool(
                "browser_snapshot",
                arguments={}
            )
            snapshot = result.content[0].text if result.content else ""

            if "Warning: Potential Security Risk Ahead" in snapshot:
                print("   ⚠️ 証明書エラーページを検出")

                # 「Advanced」ボタンをクリック
                print("\n4. 「Advanced」ボタンをクリック中...")
                try:
                    result = await session.call_tool(
                        "browser_action",
                        arguments={
                            "action": "await page.getByRole('button', { name: 'Advanced…' }).click();"
                        }
                    )
                    print("   ✅ 「Advanced」ボタンをクリック成功")

                    # 少し待機
                    await asyncio.sleep(1)

                    # 「Accept the Risk and Continue」ボタンをクリック
                    print("\n5. 「Accept the Risk and Continue」ボタンをクリック中...")
                    result = await session.call_tool(
                        "browser_action",
                        arguments={
                            "action": "await page.getByRole('button', { name: 'Accept the Risk and Continue' }).click();"
                        }
                    )
                    print("   ✅ 「Accept the Risk and Continue」ボタンをクリック成功")

                    # ページ読み込みを待つ
                    await asyncio.sleep(3)

                except Exception as e:
                    print(f"   ⚠️ ボタンクリック失敗: {e}")

            # 最終的なスナップショットを取得
            print("\n6. 最終スナップショット取得中...")
            result = await session.call_tool(
                "browser_snapshot",
                arguments={}
            )
            snapshot = result.content[0].text if result.content else ""
            print(f"   スナップショットサイズ: {len(snapshot)} 文字")

            # トピックを抽出
            print("\n7. トピックを抽出中...")

            # リンクテキストを抽出
            link_pattern = r'link "([^"]+)"'
            heading_pattern = r'heading "([^"]+)"'

            links = re.findall(link_pattern, snapshot)
            headings = re.findall(heading_pattern, snapshot)

            # フィルタリング
            topics = []
            skip_words = ['もっと見る', 'ログイン', 'プライバシー', 'ヘルプ', '利用規約',
                         'cookie', 'yahoo', 'japan', 'メニュー', 'search', 'すべて']

            for text in links + headings:
                if len(text) > 5 and len(text) < 100:
                    if not any(skip.lower() in text.lower() for skip in skip_words):
                        topics.append(text)

            # ユニークなトピックを表示
            unique_topics = list(dict.fromkeys(topics))[:30]

            if unique_topics:
                print("\n📰 Yahoo! JAPANのコンテンツ:")
                for idx, topic in enumerate(unique_topics, 1):
                    print(f"   {idx}. {topic}")
            else:
                print("   ⚠️ コンテンツを抽出できませんでした")

            # スナップショットの一部を表示（デバッグ用）
            print("\n8. スナップショット詳細（最初の3000文字）:")
            print(snapshot[:3000])

            # ブラウザを閉じる
            await session.call_tool("browser_close", arguments={})
            print("\n✅ テスト完了")

            # 結果を判定
            if "Warning: Potential Security Risk Ahead" in snapshot:
                print("\n⚠️ まだ証明書エラーページです")
                return False
            elif len(unique_topics) > 5:
                print("\n" + "=" * 70)
                print("🎉 成功: Yahoo! JAPANのコンテンツを取得できました")
                print("=" * 70)
                return True
            else:
                print("\n❌ コンテンツが少なすぎます")
                return False


async def main():
    try:
        success = await test_yahoo_with_cert_bypass()
        return success
    except Exception as e:
        print(f"\n❌ エラー: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
