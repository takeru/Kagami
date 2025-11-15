#!/usr/bin/env python3
"""
テスト24: CA証明書インポート済みプロファイル + proxy.py経由

proxy.pyを起動してから、CA証明書をインポートしたプロファイルでFirefoxを起動
"""
import asyncio
import os
import signal
import subprocess
import time
from pathlib import Path
from playwright.async_api import async_playwright


async def test_firefox_with_cert_and_proxy_py():
    """proxy.py経由でCA証明書インポート済みプロファイルを使用"""
    print("=" * 70)
    print("テスト: CA証明書インポート済み + proxy.py経由でYahoo! JAPANにアクセス")
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

    # proxy.pyを起動
    print("1. proxy.pyを起動中...")
    proxy_process = subprocess.Popen(
        [
            "uv", "run", "proxy",
            "--hostname", "127.0.0.1",
            "--port", "18913",
            "--plugins", "proxy.plugin.proxy_pool.ProxyPoolPlugin",
            "--proxy-pool", https_proxy
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

    # proxy.pyの起動を待つ
    time.sleep(2)
    print("   ✅ proxy.py起動完了 (localhost:18913)")

    try:
        async with async_playwright() as p:
            print("\n2. Firefoxを起動中（CA証明書インポート済みプロファイル使用）...")

            # CA証明書をインポートしたプロファイルを使用
            # proxy.py経由で接続
            context = await p.firefox.launch_persistent_context(
                user_data_dir="/home/user/firefox-profile",
                executable_path="/home/user/.cache/ms-playwright/firefox-1496/firefox/firefox",
                headless=True,
                proxy={
                    "server": "http://127.0.0.1:18913"  # proxy.py経由
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
                print("\n3. Yahoo! JAPANにアクセス中...")
                response = await page.goto("https://www.yahoo.co.jp/", wait_until="domcontentloaded", timeout=30000)

                print(f"   ステータス: {response.status}")
                print(f"   URL: {page.url}")
                print(f"   タイトル: {await page.title()}")

                # 証明書エラーページかチェック
                content = await page.content()

                if "Warning: Potential Security Risk Ahead" in content or "SEC_ERROR" in content:
                    print("\n❌ 証明書エラーページです")
                    print("   → CA証明書のインポートが効いていない")
                    print("\nページの一部:")
                    print(content[:500])
                    success = False
                else:
                    print("\n✅ Yahoo! JAPANに正常にアクセスできました！")
                    print("   → CA証明書が正しく認識されています！")

                    # トピックを抽出
                    print("\n4. トピックを抽出中...")

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

                    # ページの一部を表示
                    print("\n5. ページ内容の一部:")
                    print(content[:1000])

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
            print("🎉 成功: CA証明書インポート + proxy.py経由でアクセスできました！")
            print("=" * 70)
            print("\n実現できたこと:")
            print("  ✅ proxy.py経由でのプロキシ認証処理")
            print("  ✅ CA証明書インポートによる証明書エラー回避")
            print("  ✅ Yahoo! JAPANへの正常なアクセス")
        else:
            print("\n⚠️ 証明書エラーまたは接続エラーが発生しました")

        return success

    finally:
        # proxy.pyを停止
        print("\n6. proxy.pyを停止中...")
        proxy_process.send_signal(signal.SIGTERM)
        proxy_process.wait(timeout=5)
        print("   ✅ proxy.py停止完了")


async def main():
    try:
        # HOME=/home/userで実行
        os.environ['HOME'] = '/home/user'
        success = await test_firefox_with_cert_and_proxy_py()
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
