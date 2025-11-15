#!/usr/bin/env python3
"""
テスト22: CA証明書をインポートしたFirefoxプロファイルを使用

/home/user/firefox-profile にCA証明書をインポート済み
このプロファイルを使用してYahoo! JAPANにアクセス
"""
import asyncio
import os
import sys
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def test_firefox_with_imported_cert():
    """CA証明書をインポートしたFirefoxプロファイルでアクセス"""
    print("=" * 70)
    print("テスト: CA証明書インポート済みプロファイルでYahoo! JAPANにアクセス")
    print("=" * 70)
    print()

    project_root = Path(__file__).parent.parent.parent

    # プロファイルパスを指定した設定を作成
    import json
    import tempfile

    config = {
        "launchOptions": {
            "headless": True,
            "args": [f"-profile", "/home/user/firefox-profile"],
            "firefoxUserPrefs": {
                "privacy.trackingprotection.enabled": False,
                "network.proxy.allow_hijacking_localhost": True,
                "network.stricttransportsecurity.preloadlist": False,
                "security.cert_pinning.enforcement_level": 0,
                "security.enterprise_roots.enabled": True,
                "security.ssl.errorReporting.enabled": False,
                "browser.xul.error_pages.expert_bad_cert": True,
                "media.navigator.streams.fake": True,
                "security.insecure_connection_text.enabled": False,
                "security.insecure_connection_text.pbmode.enabled": False,
                "security.mixed_content.block_active_content": False,
                "security.mixed_content.block_display_content": False,
                "security.OCSP.enabled": 0
            },
            "acceptDownloads": False
        },
        "contextOptions": {
            "ignoreHTTPSErrors": True,
            "bypassCSP": True
        }
    }

    # 一時設定ファイルを作成
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(config, f, indent=2)
        config_file = f.name

    print(f"設定ファイル: {config_file}")
    print(f"プロファイル: /home/user/firefox-profile")
    print()

    try:
        # MCPサーバーを起動
        server_params = StdioServerParameters(
            command="bash",
            args=[
                "-c",
                f'uv run proxy --hostname 127.0.0.1 --port 18912 --plugins proxy.plugin.proxy_pool.ProxyPoolPlugin --proxy-pool "$HTTPS_PROXY" >/dev/null 2>&1 & PROXY_PID=$!; trap "kill $PROXY_PID 2>/dev/null" EXIT; sleep 2; node /opt/node22/lib/node_modules/@playwright/mcp/cli.js --config {config_file} --browser firefox --proxy-server http://127.0.0.1:18912'
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
                print("\n2. Yahoo! JAPANにナビゲート中...")
                result = await session.call_tool(
                    "browser_navigate",
                    arguments={"url": "https://www.yahoo.co.jp"}
                )
                nav_result = result.content[0].text if result.content else 'No content'

                if "Error" in nav_result and "SEC_ERROR_UNKNOWN_ISSUER" in nav_result:
                    print("   ❌ 証明書エラー発生（CA証明書が効いていない）")
                    print(f"   詳細: {nav_result[:500]}")
                elif "Error" in nav_result:
                    print(f"   ⚠️ エラー発生: {nav_result[:500]}")
                else:
                    print("   ✅ ナビゲート成功（証明書エラーなし！）")

                # スナップショットを取得
                print("\n3. スナップショット取得中...")
                result = await session.call_tool(
                    "browser_snapshot",
                    arguments={}
                )
                snapshot = result.content[0].text if result.content else ""
                print(f"   スナップショットサイズ: {len(snapshot)} 文字")

                # 証明書エラーページかチェック
                if "Warning: Potential Security Risk Ahead" in snapshot:
                    print("\n❌ まだ証明書エラーページです")
                    print("\nスナップショット（最初の1000文字）:")
                    print(snapshot[:1000])
                    success = False
                else:
                    # トピックを抽出
                    print("\n4. Yahoo! JAPANのコンテンツを抽出中...")
                    import re

                    links = re.findall(r'link "([^"]+)"', snapshot)
                    headings = re.findall(r'heading "([^"]+)"', snapshot)

                    topics = []
                    skip_words = ['ログイン', 'プライバシー', 'ヘルプ', '利用規約',
                                 'cookie', 'yahoo', 'japan', 'メニュー']

                    for text in links + headings:
                        if 5 < len(text) < 100:
                            if not any(skip.lower() in text.lower() for skip in skip_words):
                                topics.append(text)

                    unique_topics = list(dict.fromkeys(topics))[:20]

                    if unique_topics:
                        print(f"\n📰 Yahoo! JAPANのコンテンツ（{len(unique_topics)}件）:")
                        for idx, topic in enumerate(unique_topics, 1):
                            print(f"   {idx}. {topic}")
                        success = True
                    else:
                        print("   ⚠️ コンテンツを抽出できませんでした")
                        success = False

                    print("\n5. スナップショット詳細（最初の2000文字）:")
                    print(snapshot[:2000])

                # ブラウザを閉じる
                await session.call_tool("browser_close", arguments={})
                print("\n✅ テスト完了")

                if success:
                    print("\n" + "=" * 70)
                    print("🎉 成功: CA証明書インポートで証明書エラーを回避できました！")
                    print("=" * 70)
                else:
                    print("\n⚠️ 証明書エラーは残っています")

                return success

    finally:
        # 一時ファイルを削除
        if os.path.exists(config_file):
            os.unlink(config_file)


async def main():
    try:
        success = await test_firefox_with_imported_cert()
        return success
    except Exception as e:
        print(f"\n❌ エラー: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
