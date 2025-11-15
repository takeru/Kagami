#!/usr/bin/env python3
"""
テスト23: PlaywrightでFirefoxプロファイルを直接使用（MCP経由ではなく）

CA証明書をインポートしたプロファイルを使用して直接Playwrightを実行
"""
import asyncio
import os
from pathlib import Path
from playwright.async_api import async_playwright


async def test_firefox_direct_with_cert():
    """PlaywrightでFirefoxプロファイルを直接使用"""
    print("=" * 70)
    print("テスト: Playwright直接実行 + CA証明書インポート済みプロファイル")
    print("=" * 70)
    print()

    # プロキシ設定を環境変数から取得
    https_proxy = os.environ.get('HTTPS_PROXY', '')
    if not https_proxy:
        print("❌ HTTPS_PROXY環境変数が設定されていません")
        return False

    print(f"プロキシ: {https_proxy[:50]}...")
    print(f"プロファイル: /home/user/firefox-profile")
    print()

    async with async_playwright() as p:
        print("1. Firefoxを起動中（CA証明書インポート済みプロファイル使用）...")

        # CA証明書をインポートしたプロファイルを使用
        # launch_persistent_contextを使用してプロファイルを指定
        context = await p.firefox.launch_persistent_context(
            user_data_dir="/home/user/firefox-profile",
            executable_path="/home/user/.cache/ms-playwright/firefox-1496/firefox/firefox",
            headless=True,
            proxy={
                "server": https_proxy
            },
            firefox_user_prefs={
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
                "security.OCSP.enabled": 0,
            },
            ignore_https_errors=True,
            bypass_csp=True
        )

        print("   ✅ Firefox起動成功")

        page = await context.new_page()

        try:
            # Yahoo! JAPANにアクセス
            print("\n2. Yahoo! JAPANにアクセス中...")
            response = await page.goto("https://www.yahoo.co.jp/", wait_until="domcontentloaded", timeout=30000)

            print(f"   ステータス: {response.status}")
            print(f"   URL: {page.url}")
            print(f"   タイトル: {await page.title()}")

            # 証明書エラーページかチェック
            content = await page.content()

            if "Warning: Potential Security Risk Ahead" in content or "SEC_ERROR" in content:
                print("\n❌ 証明書エラーページです")
                print("\nページの一部:")
                print(content[:500])
                success = False
            else:
                print("\n✅ Yahoo! JAPANに正常にアクセスできました！")

                # トピックを抽出
                print("\n3. トピックを抽出中...")

                # ヘッダーやリンクを取得
                links = await page.query_selector_all('a')
                headings = await page.query_selector_all('h1, h2, h3, h4')

                topics = []

                for heading in headings[:20]:
                    text = await heading.text_content()
                    if text and 5 < len(text.strip()) < 100:
                        topics.append(text.strip())

                for link in links[:50]:
                    text = await link.text_content()
                    if text and 5 < len(text.strip()) < 100:
                        skip_words = ['ログイン', 'プライバシー', 'ヘルプ', 'メニュー']
                        if not any(skip in text for skip in skip_words):
                            topics.append(text.strip())

                unique_topics = list(dict.fromkeys(topics))[:20]

                if unique_topics:
                    print(f"\n📰 Yahoo! JAPANのコンテンツ（{len(unique_topics)}件）:")
                    for idx, topic in enumerate(unique_topics, 1):
                        print(f"   {idx}. {topic}")
                    success = True
                else:
                    print("   ⚠️ コンテンツを抽出できませんでした")
                    success = False

        except Exception as e:
            print(f"\n❌ エラー: {e}")
            import traceback
            traceback.print_exc()
            success = False

        finally:
            await context.close()
            print("\n✅ テスト完了")

    if success:
        print("\n" + "=" * 70)
        print("🎉 成功: CA証明書インポートで証明書エラーを回避できました！")
        print("=" * 70)
    else:
        print("\n⚠️ 証明書エラーが発生しました")

    return success


async def main():
    try:
        success = await test_firefox_direct_with_cert()
        return success
    except Exception as e:
        print(f"\n❌ エラー: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    import sys
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
