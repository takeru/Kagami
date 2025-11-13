#!/usr/bin/env python3
"""
サンプル7: Firefoxでの基本的なアクセス

Firefoxブラウザを使った基本的な動作確認サンプルです。

実行方法:
    uv run python playwright_setup/samples/07_firefox_basic.py
"""
from playwright.sync_api import sync_playwright
import tempfile
import os


def main():
    print("="*60)
    print("Firefox 基本サンプル")
    print("="*60)

    with sync_playwright() as p:
        # Step 1: Firefoxを起動
        print("\n1. Firefoxを起動...")

        # 一時的なHOMEディレクトリを作成
        temp_home = tempfile.mkdtemp(prefix="firefox_home_")

        browser = p.firefox.launch(
            headless=True,
            firefox_user_prefs={
                # プライバシー設定
                "privacy.trackingprotection.enabled": False,
                # メディアデバイス設定（headlessで必要）
                "media.navigator.streams.fake": True,
            },
            env={
                **os.environ,
                "HOME": temp_home,
            }
        )
        print("   ✅ Firefox起動完了")

        # Step 2: ページにアクセス（プロキシなし）
        print("\n2. example.com にアクセス（プロキシなし）...")
        page = browser.new_page()

        try:
            response = page.goto("https://example.com", timeout=30000)
            print(f"   ✅ ステータス: {response.status}")
            print(f"   ✅ URL: {response.url}")
            print(f"   ✅ タイトル: {page.title()}")

            # スクリーンショット
            print("\n3. スクリーンショットを保存...")
            page.screenshot(path="example_firefox.png")
            print("   ✅ 保存完了: example_firefox.png")

        except Exception as e:
            print(f"   ❌ エラー: {e}")
            print("   ℹ️  プロキシなしでは外部アクセスできない可能性があります")
            print("   ℹ️  プロキシ付きサンプルをお試しください:")
            print("      uv run python playwright_setup/samples/08_firefox_with_proxy.py")

        browser.close()

    print("\n✅ 完了！")


if __name__ == "__main__":
    main()
