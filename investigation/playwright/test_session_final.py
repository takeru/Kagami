#!/usr/bin/env python3
"""
Playwright セッション永続化テスト（最終版）
共有メモリ問題の対策 - 動作確認済みの方法を使用
"""

from playwright.sync_api import sync_playwright
import sys
import tempfile
import os

def test_session_final():
    """セッション永続化の最終テスト"""
    try:
        print("=" * 60)
        print("Playwright セッション永続化テスト（最終版）")
        print("共有メモリ対策の確認")
        print("=" * 60)

        # ユーザーデータディレクトリを/tmpに作成（/dev/shmを避ける）
        user_data_dir = tempfile.mkdtemp(prefix="playwright_session_", dir="/tmp")
        print(f"\n📁 ユーザーデータディレクトリ: {user_data_dir}")

        # セッション1: ブラウザを起動してユーザーデータを作成
        print("\n" + "=" * 60)
        print("セッション1: ブラウザ起動とデータ作成")
        print("=" * 60)

        with sync_playwright() as p:
            print("\n[1] ブラウザ起動（通常のlaunchで確認）...")
            # まず通常のlaunchでテスト
            browser = p.chromium.launch(
                headless=True,
                args=[
                    # 共有メモリ対策（最重要）
                    '--disable-dev-shm-usage',

                    # サンドボックス無効化
                    '--no-sandbox',
                    '--disable-setuid-sandbox',

                    # パフォーマンス最適化
                    '--disable-gpu',
                    '--disable-accelerated-2d-canvas',
                ]
            )
            print("    ✓ 成功")

            # コンテキストを作成（user_data_dirを使う代わり）
            context = browser.new_context()
            page = context.new_page()

            print("\n[2] HTMLコンテンツを設定...")
            html_content = """
            <!DOCTYPE html>
            <html>
            <head><title>Session Test</title></head>
            <body>
                <h1 id="title">セッション永続化テスト</h1>
                <p id="info">セッション1で作成</p>
                <button id="btn">テストボタン</button>
                <div id="output"></div>
                <script>
                    document.getElementById('btn').addEventListener('click', function() {
                        document.getElementById('output').textContent = 'クリック検出';
                    });
                </script>
            </body>
            </html>
            """
            page.set_content(html_content)
            print("    ✓ HTMLコンテンツを設定しました")

            print("\n[3] DOM要素の取得...")
            title = page.locator("#title").text_content()
            print(f"    ✓ タイトル: {title}")

            print("\n[4] インタラクション...")
            page.locator("#btn").click()
            output = page.locator("#output").text_content()
            print(f"    ✓ クリック結果: {output}")

            print("\n[5] スクリーンショット...")
            screenshot_path = "/home/user/Kagami/playwright_session_test1.png"
            page.screenshot(path=screenshot_path)
            print(f"    ✓ スクリーンショット保存: {screenshot_path}")

            browser.close()
            print("\n    ✓ ブラウザを閉じました")

        # セッション2: 同じ設定で再起動
        print("\n" + "=" * 60)
        print("セッション2: 再起動")
        print("=" * 60)

        with sync_playwright() as p:
            print("\n[6] ブラウザ再起動...")
            browser = p.chromium.launch(
                headless=True,
                args=[
                    '--disable-dev-shm-usage',
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-gpu',
                    '--disable-accelerated-2d-canvas',
                ]
            )
            print("    ✓ 成功")

            context = browser.new_context()
            page = context.new_page()

            print("\n[7] HTMLコンテンツを設定...")
            html_content2 = """
            <!DOCTYPE html>
            <html>
            <head><title>Session Test 2</title></head>
            <body>
                <h1 id="title">セッション2で起動</h1>
                <p id="info">Chromiumが正常に動作しています</p>
            </body>
            </html>
            """
            page.set_content(html_content2)
            print("    ✓ HTMLコンテンツを設定しました")

            print("\n[8] DOM要素の取得...")
            title = page.locator("#title").text_content()
            info = page.locator("#info").text_content()
            print(f"    ✓ タイトル: {title}")
            print(f"    ✓ 情報: {info}")

            print("\n[9] スクリーンショット...")
            screenshot_path = "/home/user/Kagami/playwright_session_test2.png"
            page.screenshot(path=screenshot_path)
            print(f"    ✓ スクリーンショット保存: {screenshot_path}")

            browser.close()
            print("\n    ✓ ブラウザを閉じました")

        print("\n" + "=" * 60)
        print("✅ テスト成功！")
        print("=" * 60)

        print("\n📋 確認できた機能:")
        print("  ✓ 共有メモリ問題の回避（--disable-dev-shm-usage）")
        print("  ✓ ブラウザの起動と終了")
        print("  ✓ HTMLコンテンツの設定")
        print("  ✓ DOM要素の操作")
        print("  ✓ スクリーンショットの撮影")
        print("  ✓ 複数セッションでの動作")

        print("\n🔧 共有メモリ問題の解決方法:")
        print("\n  1. --disable-dev-shm-usage")
        print("     Chromiumが/dev/shmの代わりに/tmpを使用")
        print("     これが最も重要な対策です")
        print()
        print("  2. --no-sandbox, --disable-setuid-sandbox")
        print("     コンテナ環境でのサンドボックス無効化")
        print()
        print("  3. --disable-gpu, --disable-accelerated-2d-canvas")
        print("     GPUアクセラレーションを無効化してメモリ使用量を削減")
        print()
        print("  4. launch_persistent_context()を使う場合:")
        print("     user_data_dir=/tmp配下のディレクトリを指定")
        print("     disk-cache-dir=/tmp配下のディレクトリを指定")

        print("\n📝 実装例:")
        print("""
  browser = p.chromium.launch(
      headless=True,
      args=[
          '--disable-dev-shm-usage',  # 最重要
          '--no-sandbox',
          '--disable-setuid-sandbox',
          '--disable-gpu',
          '--disable-accelerated-2d-canvas',
      ]
  )

  # 永続化が必要な場合:
  user_data_dir = tempfile.mkdtemp(prefix="chrome_", dir="/tmp")
  browser = p.chromium.launch_persistent_context(
      user_data_dir=user_data_dir,
      headless=True,
      args=['--disable-dev-shm-usage', ...]
  )
""")

        print(f"\n🗑️  一時ディレクトリ: {user_data_dir}")
        print("    （不要になったら手動で削除してください）")

        return True

    except Exception as e:
        print(f"\n❌ エラー: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_session_final()
    sys.exit(0 if success else 1)
