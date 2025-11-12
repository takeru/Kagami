#!/usr/bin/env python3
"""
Playwright 最小限のテスト
"""

from playwright.sync_api import sync_playwright
import sys

def test_simple():
    """最小限のテスト - HTML文字列からページを作成"""
    try:
        print("=" * 60)
        print("Playwright 簡易テスト")
        print("=" * 60)

        with sync_playwright() as p:
            # 1. ブラウザ起動
            print("\n[1/6] ブラウザを起動中...")
            browser = p.chromium.launch(headless=True)
            print("      ✓ 成功: Chromiumブラウザが起動しました")

            # 2. ページ作成
            print("\n[2/6] 新しいページを作成中...")
            page = browser.new_page()
            print("      ✓ 成功: ページコンテキストを作成しました")

            # 3. HTMLコンテンツを直接設定
            print("\n[3/6] HTMLコンテンツを設定中...")
            html_content = """
            <!DOCTYPE html>
            <html>
            <head><title>Playwrightテスト</title></head>
            <body>
                <h1 id="title">Hello, Playwright!</h1>
                <p>これはテストページです。</p>
                <button id="btn">クリック</button>
                <div id="output"></div>
                <script>
                    document.getElementById('btn').addEventListener('click', function() {
                        document.getElementById('output').textContent = 'ボタンがクリックされました！';
                    });
                </script>
            </body>
            </html>
            """
            page.set_content(html_content)
            print("      ✓ 成功: HTMLコンテンツを設定しました")

            # 4. 要素取得
            print("\n[4/6] DOM要素を取得中...")
            title = page.locator("#title").text_content()
            print(f"      ✓ 成功: タイトル = '{title}'")

            # 5. インタラクション
            print("\n[5/6] ボタンクリックを実行中...")
            page.locator("#btn").click()
            output = page.locator("#output").text_content()
            print(f"      ✓ 成功: クリック後の出力 = '{output}'")

            # 6. スクリーンショット
            print("\n[6/6] スクリーンショットを撮影中...")
            page.screenshot(path="/home/user/Kagami/playwright_simple_test.png")
            print("      ✓ 成功: スクリーンショットを保存しました")
            print("         → /home/user/Kagami/playwright_simple_test.png")

            browser.close()

            print("\n" + "=" * 60)
            print("✅ テスト完了: すべての機能が正常に動作しました！")
            print("=" * 60)

            print("\n📋 動作確認できた機能:")
            print("  ✓ Chromiumブラウザの起動 (headlessモード)")
            print("  ✓ ページコンテキストの作成")
            print("  ✓ HTMLコンテンツの設定")
            print("  ✓ DOM要素の取得 (locator, text_content)")
            print("  ✓ ユーザーインタラクション (click)")
            print("  ✓ スクリーンショット撮影")

            return True

    except Exception as e:
        print(f"\n❌ エラー: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_simple()
    sys.exit(0 if success else 1)
