#!/usr/bin/env python3
"""
Playwright ローカルファイル動作テスト
"""

from playwright.sync_api import sync_playwright
import sys
import os

def test_local_file():
    """ローカルHTMLファイルを使ったテスト"""
    try:
        with sync_playwright() as p:
            print("=" * 60)
            print("Playwright ローカルファイルテスト")
            print("=" * 60)

            print("\n1. ブラウザを起動中...")
            browser = p.chromium.launch(headless=True)
            print("   ✓ Chromiumブラウザの起動成功")

            context = browser.new_context()
            page = context.new_page()
            print("   ✓ 新しいページコンテキストを作成")

            # ローカルHTMLファイルを開く
            html_path = "file://" + os.path.abspath("/home/user/Kagami/test_page.html")
            print(f"\n2. ローカルファイルを開く: {html_path}")
            page.goto(html_path)
            print(f"   ✓ ページタイトル: {page.title()}")

            # 要素の取得テスト
            print("\n3. DOM要素の取得テスト...")
            h1_text = page.locator("h1").text_content()
            print(f"   ✓ H1テキスト: {h1_text}")

            # ボタンの存在確認
            button_count = page.locator("button.button").count()
            print(f"   ✓ ボタン要素の数: {button_count}")

            # ボタンをクリックしてインタラクション
            print("\n4. インタラクションテスト...")
            page.locator("#test-button").click()
            print("   ✓ ボタンクリック成功")

            # ボタンのテキストが変わったことを確認
            new_button_text = page.locator("#test-button").text_content()
            print(f"   ✓ クリック後のボタンテキスト: {new_button_text}")

            # スクリーンショット撮影
            print("\n5. スクリーンショット撮影...")
            screenshot_path = "/home/user/Kagami/playwright_test_local.png"
            page.screenshot(path=screenshot_path)
            print(f"   ✓ スクリーンショット保存: {screenshot_path}")

            # JavaScriptの実行テスト
            print("\n6. JavaScript実行テスト...")
            result = page.evaluate("() => { return 2 + 3; }")
            print(f"   ✓ JavaScript実行結果 (2 + 3): {result}")

            # ページ情報の取得
            print("\n7. ページ情報の取得...")
            url = page.url
            print(f"   ✓ 現在のURL: {url}")

            browser.close()

            print("\n" + "=" * 60)
            print("✅ すべてのテストが成功しました！")
            print("=" * 60)
            print("\n結論:")
            print("✓ Playwrightは正常にインストールされています")
            print("✓ Chromiumブラウザがheadlessモードで動作します")
            print("✓ ページ操作、要素の取得、クリックなどが可能です")
            print("✓ スクリーンショット撮影が可能です")
            print("✓ JavaScript実行が可能です")
            print("\n⚠ 制限事項:")
            print("  - 外部ネットワークへのアクセスは制限されています")
            print("  - ローカルファイルやローカルサーバーを使用する必要があります")

            return True

    except Exception as e:
        print(f"\n❌ エラーが発生しました: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_local_file()
    sys.exit(0 if success else 1)
