#!/usr/bin/env python3
"""
Playwright MCP - Yahoo! JAPANニュースのトピック取得

Yahoo! JAPANのトップページから最新ニュースのトピックを取得します。
"""
import asyncio
import os
import re
import signal
import subprocess
import sys
import time
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def get_yahoo_news_via_mcp():
    """
    playwright-mcp経由でYahoo! JAPANのニューストピックを取得
    """
    print("=" * 70)
    print("Playwright MCP - Yahoo! JAPANニュース取得")
    print("=" * 70)
    print()

    # HOME環境変数を設定
    os.environ['HOME'] = '/home/user'

    # HTTPS_PROXY環境変数を確認
    https_proxy = os.environ.get('HTTPS_PROXY', '')
    if not https_proxy:
        print("❌ HTTPS_PROXY環境変数が設定されていません")
        return False

    print(f"環境変数:")
    print(f"  HOME: {os.environ['HOME']}")
    print(f"  HTTPS_PROXY: {https_proxy[:50]}...")
    print()

    # 1. proxy.pyを起動
    print("1. proxy.pyを起動中...")
    proxy_process = subprocess.Popen(
        [
            "uv", "run", "proxy",
            "--hostname", "127.0.0.1",
            "--port", "18915",
            "--plugins", "proxy.plugin.proxy_pool.ProxyPoolPlugin",
            "--proxy-pool", https_proxy
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

    # proxy.pyの起動を待つ
    time.sleep(2)
    print("   ✅ proxy.py起動完了 (localhost:18915)")
    print()

    try:
        # 2. playwright-mcpサーバーのパラメータを設定
        print("2. playwright-mcpサーバーに接続中...")

        config_path = str(Path(__file__).parent / "playwright-firefox-config.json")

        server_params = StdioServerParameters(
            command="node",
            args=[
                "/opt/node22/lib/node_modules/@playwright/mcp/cli.js",
                "--config", config_path,
                "--browser", "firefox",
                "--proxy-server", "http://127.0.0.1:18915"
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
                print("   ✅ playwright-mcpサーバーに接続しました")
                print()

                # 4. Yahoo! JAPANにナビゲート
                print("3. Yahoo! JAPANにアクセス中...")
                result = await session.call_tool(
                    "browser_navigate",
                    arguments={"url": "https://www.yahoo.co.jp/"}
                )

                nav_result = result.content[0].text if result.content else ""

                if "SEC_ERROR" in nav_result:
                    print("   ❌ 証明書エラーが発生しました")
                    print(f"   詳細: {nav_result[:200]}")
                    print()
                    print("💡 ヒント:")
                    print("   ./playwright_mcp_claude_code_web/setup.sh を実行して")
                    print("   CA証明書をインポートしてください")
                    return False
                else:
                    print("   ✅ Yahoo! JAPANにアクセス成功")

                # 5. スナップショットを取得
                print()
                print("4. ページスナップショットを取得中...")
                result = await session.call_tool(
                    "browser_snapshot",
                    arguments={}
                )

                snapshot = result.content[0].text if result.content else ""
                print(f"   ✅ スナップショット取得完了 ({len(snapshot)} 文字)")

                # 6. ニューストピックを抽出
                print()
                print("5. ニューストピックを抽出中...")

                # heading要素からニュース記事のみを抽出
                # Yahoo!ニュースのトピックは "heading "...""" パターンで表されている
                heading_pattern = r'heading "([^"]+)" \[level=1\]'
                headings = re.findall(heading_pattern, snapshot)

                # フィルタリング
                news_topics = []
                skip_patterns = [
                    'Yahoo',
                    'ニュース',
                    '主要',
                    '経済',
                    'エンタメ',
                    'スポーツ',
                    '国内',
                    '国際',
                    'IT',
                    '科学',
                    '地域',
                    'ビジネス',
                    '社会的な取り組み',
                    'LINE',
                    'おすすめ',
                    '検索',
                    'お知らせ',
                    '主なサービス',
                ]

                for text in headings:
                    # 長さチェック（ニュースのヘッドラインは通常10文字以上）
                    if len(text) >= 10:
                        # スキップパターンチェック
                        if not any(skip in text for skip in skip_patterns):
                            # 「へ遷移する」などのナビゲーション用テキストを除外
                            if 'へ遷移' not in text and 'で検索' not in text:
                                news_topics.append(text)

                # ユニークなトピックを抽出
                unique_news = list(dict.fromkeys(news_topics))[:20]

                # 7. 結果を表示
                print()
                print("=" * 70)
                print("📰 Yahoo! JAPANのニューストピック")
                print("=" * 70)

                if unique_news:
                    for idx, topic in enumerate(unique_news, 1):
                        print(f"{idx:2d}. {topic}")
                    print()
                    print(f"✅ {len(unique_news)} 件のニューストピックを取得しました")
                else:
                    print("⚠️ ニューストピックを抽出できませんでした")
                    print()
                    print("デバッグ情報:")
                    print(f"  取得したheading要素数: {len(headings)}")
                    if headings:
                        print("  最初の10件:")
                        for idx, h in enumerate(headings[:10], 1):
                            print(f"    {idx}. {h}")

                # 8. ブラウザを閉じる
                print()
                print("6. ブラウザを閉じています...")
                await session.call_tool("browser_close", arguments={})
                print("   ✅ ブラウザを閉じました")

                # 9. 成功メッセージ
                if unique_news:
                    print()
                    print("=" * 70)
                    print("🎉 成功！")
                    print("=" * 70)
                    print()
                    print("通信フロー:")
                    print("  ✅ Python MCP Client → playwright-mcp (Firefox)")
                    print("  ✅ Firefox (CA証明書インポート済み) → proxy.py")
                    print("  ✅ proxy.py (JWT認証処理) → JWT認証Proxy")
                    print("  ✅ JWT認証Proxy (TLS Inspection) → Yahoo! JAPAN")
                    print()
                    return True
                else:
                    return False

    except Exception as e:
        print()
        print(f"❌ エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        # proxy.pyを停止
        print()
        print("7. proxy.pyを停止中...")
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
        success = await get_yahoo_news_via_mcp()
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
