#!/usr/bin/env python3
"""
Playwright テスト - ロード待機付き
"""

from playwright.sync_api import sync_playwright
import sys
import time

def test_with_wait():
    """ページロード待機を含めたテスト"""
    try:
        print("=" * 60)
        print("Playwright 詳細テスト (待機処理あり)")
        print("=" * 60)

        with sync_playwright() as p:
            # ブラウザ起動
            print("\n[1] ブラウザ起動...")
            browser = p.chromium.launch(headless=True)
            print("    ✓ 成功")

            # ページ作成
            print("\n[2] ページ作成...")
            page = browser.new_page()
            print("    ✓ 成功")

            # シンプルなHTMLを設定
            print("\n[3] HTMLコンテンツ設定...")
            simple_html = "<html><body><h1>Test</h1></body></html>"
            page.set_content(simple_html, wait_until="load")
            print("    ✓ 成功")

            # 少し待機
            print("\n[4] ページ安定化待機...")
            time.sleep(1)
            page.wait_for_load_state("domcontentloaded")
            print("    ✓ 成功")

            # HTML取得
            print("\n[5] HTMLコンテンツ取得...")
            content = page.content()
            print(f"    ✓ 成功 (長さ: {len(content)}文字)")
            print(f"    コンテンツ: {content[:100]}...")

            # タイトル取得
            print("\n[6] ページタイトル取得...")
            title = page.title()
            print(f"    ✓ 成功: '{title}'")

            # スクリーンショット
            print("\n[7] スクリーンショット...")
            page.screenshot(path="/home/user/Kagami/playwright_wait_test.png")
            print("    ✓ 成功")

            # JavaScript評価
            print("\n[8] JavaScript実行...")
            result = page.evaluate("1 + 1")
            print(f"    ✓ 成功: 1 + 1 = {result}")

            browser.close()

            print("\n" + "=" * 60)
            print("✅ 基本機能は動作しています")
            print("=" * 60)

            return True

    except Exception as e:
        print(f"\n❌ エラー: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_with_wait()
    sys.exit(0 if success else 1)
