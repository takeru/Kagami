#!/usr/bin/env python3
"""
テスト1: playwright + firefox（proxy.pyなし）
Firefoxで直接上流プロキシに接続を試みる

このテストでは、proxy.pyを使わずに、Firefoxが直接JWT認証プロキシに接続できるか確認します。
"""
import os
import sys
from playwright.sync_api import sync_playwright


def test_firefox_direct_proxy():
    print("=" * 70)
    print("テスト1: Firefox + 直接プロキシ接続（proxy.pyなし）")
    print("=" * 70)
    print()

    # 環境変数チェック
    https_proxy = os.getenv("HTTPS_PROXY")
    if not https_proxy:
        print("❌ エラー: HTTPS_PROXY 環境変数が設定されていません")
        sys.exit(1)

    print(f"使用するプロキシ: {https_proxy}")
    print()

    try:
        with sync_playwright() as p:
            print("1. Firefoxを起動（直接プロキシ設定）...")

            # 一時的なHOMEディレクトリを作成
            import tempfile
            temp_home = tempfile.mkdtemp(prefix="firefox_direct_")
            print(f"   一時HOME: {temp_home}")

            # Firefoxを起動（上流プロキシを直接指定）
            browser = p.firefox.launch(
                headless=True,
                proxy={
                    "server": https_proxy,  # 直接上流プロキシに接続
                },
                firefox_user_prefs={
                    # プライバシー設定
                    "privacy.trackingprotection.enabled": False,
                    # プロキシ設定
                    "network.proxy.allow_hijacking_localhost": True,
                    # 証明書エラーを無視
                    "network.stricttransportsecurity.preloadlist": False,
                    "security.cert_pinning.enforcement_level": 0,
                    "security.enterprise_roots.enabled": True,
                    "security.ssl.errorReporting.enabled": False,
                    "browser.xul.error_pages.expert_bad_cert": True,
                    # メディアデバイス設定
                    "media.navigator.streams.fake": True,
                },
                env={
                    **os.environ,
                    "HOME": temp_home,
                }
            )
            print("   ✅ Firefox起動完了")

            # HTTPS証明書エラーを無視するコンテキストを作成
            print("\n2. ブラウザコンテキストを作成...")
            context = browser.new_context(ignore_https_errors=True)
            page = context.new_page()
            print("   ✅ コンテキスト作成完了")

            # テストURL
            test_url = "https://example.com"
            print(f"\n3. {test_url} にアクセス...")

            response = page.goto(test_url, timeout=30000)

            print(f"   ✅ ステータス: {response.status}")
            print(f"   ✅ URL: {response.url}")
            print(f"   ✅ タイトル: {page.title()}")

            # スクリーンショット
            screenshot_path = "/home/user/Kagami/investigation/playwright/test_01_screenshot.png"
            page.screenshot(path=screenshot_path)
            print(f"   ✅ スクリーンショット保存: {screenshot_path}")

            browser.close()

            print("\n" + "=" * 70)
            print("✅ テスト成功：proxy.pyなしでも動作しました！")
            print("=" * 70)
            print("\n結論: Firefoxは直接JWT認証プロキシに接続できます")
            return True

    except Exception as e:
        print("\n" + "=" * 70)
        print("❌ テスト失敗")
        print("=" * 70)
        print(f"\nエラー: {e}")
        print("\nスタックトレース:")
        import traceback
        traceback.print_exc()
        print("\n結論: Firefoxは直接JWT認証プロキシに接続できませんでした")
        print("考えられる理由:")
        print("  - Firefoxが407レスポンス後に認証ヘッダーを送る仕様")
        print("  - JWT認証プロキシが最初のリクエストから認証ヘッダーを要求")
        return False


if __name__ == "__main__":
    success = test_firefox_direct_proxy()
    sys.exit(0 if success else 1)
