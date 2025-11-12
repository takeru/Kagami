#!/usr/bin/env python3
"""
Playwright動作テストスクリプト
"""

from playwright.sync_api import sync_playwright
import sys

def test_basic_navigation():
    """基本的なページナビゲーションとコンテンツ取得のテスト"""
    try:
        with sync_playwright() as p:
            print("Playwrightを起動中...")
            # Chromiumをheadlessモードで起動
            browser = p.chromium.launch(headless=True)
            print("✓ ブラウザの起動に成功")

            # 新しいページを開く
            page = browser.new_page()
            print("✓ 新しいページを作成")

            # Example.comにアクセス
            print("\nExample.comにアクセス中...")
            page.goto("https://example.com", wait_until="networkidle")
            print(f"✓ ページタイトル: {page.title()}")

            # ページコンテンツを取得
            content = page.content()
            print(f"✓ HTMLコンテンツ取得成功 (長さ: {len(content)}文字)")

            # スクリーンショットを撮影
            page.screenshot(path="/home/user/Kagami/test_screenshot.png")
            print("✓ スクリーンショット保存成功: test_screenshot.png")

            # h1要素のテキストを取得
            h1_text = page.locator("h1").text_content()
            print(f"✓ H1テキスト: {h1_text}")

            browser.close()
            print("\n✅ すべてのテストが成功しました！")
            return True

    except Exception as e:
        print(f"\n❌ エラーが発生しました: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return False

def test_github_navigation():
    """GitHubへのアクセステスト"""
    try:
        with sync_playwright() as p:
            print("\n--- GitHub アクセステスト ---")
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            print("GitHubにアクセス中...")
            page.goto("https://github.com", timeout=30000)
            print(f"✓ ページタイトル: {page.title()}")

            # メタ情報を取得
            description = page.locator('meta[name="description"]').get_attribute("content")
            print(f"✓ ページ説明: {description[:100]}...")

            browser.close()
            print("✅ GitHubアクセステスト成功")
            return True

    except Exception as e:
        print(f"❌ GitHubアクセステストでエラー: {e}", file=sys.stderr)
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("Playwright 動作テスト")
    print("=" * 60)

    # 基本的なテスト
    test1_result = test_basic_navigation()

    # GitHubアクセステスト
    test2_result = test_github_navigation()

    print("\n" + "=" * 60)
    if test1_result and test2_result:
        print("結果: ✅ すべてのテストが成功しました")
        print("Playwrightはこの環境で正常に動作します！")
        sys.exit(0)
    else:
        print("結果: ❌ 一部のテストが失敗しました")
        sys.exit(1)
