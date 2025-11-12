#!/usr/bin/env python3
"""
Playwright テスト - サンドボックス無効化
"""

from playwright.sync_api import sync_playwright
import sys

def test_no_sandbox():
    """サンドボックスを無効にしてテスト"""
    try:
        print("=" * 60)
        print("Playwright テスト (サンドボックス無効)")
        print("=" * 60)

        with sync_playwright() as p:
            print("\n[1] ブラウザ起動 (サンドボックス無効)...")
            # サンドボックスを無効化
            browser = p.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-accelerated-2d-canvas',
                    '--disable-gpu',
                    '--single-process'
                ]
            )
            print("    ✓ 成功")

            print("\n[2] ページ作成...")
            page = browser.new_page()
            print("    ✓ 成功")

            print("\n[3] 空のページにナビゲート...")
            page.goto("about:blank")
            print("    ✓ 成功")

            print("\n[4] JavaScript実行テスト...")
            result = page.evaluate("2 * 3")
            print(f"    ✓ 成功: 2 * 3 = {result}")

            print("\n[5] HTMLコンテンツ設定...")
            page.set_content("<html><body><h1>Hello</h1></body></html>")
            print("    ✓ 成功")

            print("\n[6] スクリーンショット...")
            page.screenshot(path="/home/user/Kagami/playwright_nosandbox.png")
            print("    ✓ 成功")

            browser.close()

            print("\n" + "=" * 60)
            print("✅ サンドボックス無効化で動作しました！")
            print("=" * 60)

            return True

    except Exception as e:
        print(f"\n❌ エラー: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_no_sandbox()
    sys.exit(0 if success else 1)
