#!/usr/bin/env python3
"""
Playwright MCP サンプルコード - Yahoo! JAPANトピック取得

通信フロー:
  Python MCP Client → playwright-mcp (Firefox) → proxy.py → JWT認証Proxy → Yahoo! JAPAN

このサンプルは、CA証明書をインポートしたFirefoxプロファイルを使用して、
証明書エラーなしでYahoo! JAPANにアクセスし、トピックを取得します。
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


async def get_yahoo_topics_via_mcp():
    """
    playwright-mcp経由でYahoo! JAPANのトピックを取得

    セットアップ:
        ./playwright_mcp_claude_code_web/setup.sh を事前に実行してください
    """
    print("=" * 70)
    print("Playwright MCP サンプル - Yahoo! JAPANトピック取得")
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

                if "Error" in nav_result and "SEC_ERROR" in nav_result:
                    print("   ❌ 証明書エラーが発生しました")
                    print(f"   詳細: {nav_result[:200]}")
                    print()
                    print("💡 ヒント:")
                    print("   ./playwright_mcp_claude_code_web/setup.sh を実行して")
                    print("   CA証明書をインポートしてください")
                    return False
                elif "Error" in nav_result:
                    print(f"   ⚠️ エラーが発生: {nav_result[:200]}")
                    return False
                else:
                    print("   ✅ Yahoo! JAPANにアクセス成功（証明書エラーなし）")

                # 5. スナップショットを取得
                print()
                print("4. ページスナップショットを取得中...")
                result = await session.call_tool(
                    "browser_snapshot",
                    arguments={}
                )

                snapshot = result.content[0].text if result.content else ""
                print(f"   ✅ スナップショット取得完了 ({len(snapshot)} 文字)")

                # 6. トピックを抽出
                print()
                print("5. トピックを抽出中...")

                # リンクとヘッダーを抽出
                link_pattern = r'link "([^"]+)"'
                heading_pattern = r'heading "([^"]+)"'

                links = re.findall(link_pattern, snapshot)
                headings = re.findall(heading_pattern, snapshot)

                # フィルタリング
                topics = []
                skip_words = [
                    'ログイン', 'プライバシー', 'ヘルプ', '利用規約',
                    'cookie', 'yahoo', 'japan', 'メニュー', 'search',
                    'すべて', 'もっと見る'
                ]

                for text in links + headings:
                    # 長さチェック
                    if 5 < len(text) < 100:
                        # スキップワードチェック
                        if not any(skip.lower() in text.lower() for skip in skip_words):
                            topics.append(text)

                # ユニークなトピックを抽出
                unique_topics = list(dict.fromkeys(topics))[:30]

                # 7. 結果を表示
                print()
                print("=" * 70)
                print("📰 Yahoo! JAPANのトピック")
                print("=" * 70)

                if unique_topics:
                    for idx, topic in enumerate(unique_topics, 1):
                        print(f"{idx:2d}. {topic}")
                    print()
                    print(f"✅ {len(unique_topics)} 件のトピックを取得しました")
                else:
                    print("⚠️ トピックを抽出できませんでした")
                    print()
                    print("デバッグ情報（スナップショットの一部）:")
                    print("-" * 70)
                    print(snapshot[:1000])
                    print("-" * 70)

                # 8. ブラウザを閉じる
                print()
                print("6. ブラウザを閉じています...")
                await session.call_tool("browser_close", arguments={})
                print("   ✅ ブラウザを閉じました")

                # 9. 成功メッセージ
                if unique_topics:
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
    print()
    print("=" * 70)
    print("Playwright MCP サンプルコード")
    print("=" * 70)
    print()
    print("このサンプルでは、以下を実行します:")
    print("  1. proxy.pyを起動（JWT認証処理）")
    print("  2. playwright-mcpサーバーに接続")
    print("  3. CA証明書インポート済みFirefoxでYahoo! JAPANにアクセス")
    print("  4. トピックを抽出して表示")
    print()
    print("前提条件:")
    print("  - ./playwright_mcp_claude_code_web/setup.sh を実行済み")
    print("  - CA証明書がFirefoxプロファイルにインポート済み")
    print()
    input("Enterキーを押して続行...")
    print()

    try:
        success = await get_yahoo_topics_via_mcp()
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
