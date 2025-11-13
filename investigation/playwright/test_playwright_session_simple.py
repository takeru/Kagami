#!/usr/bin/env python3
"""
Playwright セッション永続化テスト（シンプル版）
共有メモリ問題の対策付き - Cookieベース
"""

from playwright.sync_api import sync_playwright
import sys
import tempfile

def test_session_simple():
    """セッション永続化のテスト - Cookieベース"""
    try:
        print("=" * 60)
        print("Playwright セッション永続化テスト（シンプル版）")
        print("=" * 60)

        # ユーザーデータディレクトリを/tmpに作成（/dev/shmを避ける）
        user_data_dir = tempfile.mkdtemp(prefix="playwright_session_", dir="/tmp")
        print(f"\n📁 ユーザーデータディレクトリ: {user_data_dir}")

        # キャッシュディレクトリも明示的に指定
        cache_dir = tempfile.mkdtemp(prefix="playwright_cache_", dir="/tmp")
        print(f"📁 キャッシュディレクトリ: {cache_dir}")

        # 共有メモリ対策のための引数
        chromium_args = [
            # 共有メモリ対策（最重要）
            '--disable-dev-shm-usage',  # /dev/shmの代わりに/tmpを使用

            # サンドボックス無効化（コンテナ環境用）
            '--no-sandbox',
            '--disable-setuid-sandbox',

            # パフォーマンス最適化
            '--disable-gpu',
            '--disable-software-rasterizer',
            '--disable-accelerated-2d-canvas',

            # メモリ管理
            '--disable-background-timer-throttling',
            '--disable-backgrounding-occluded-windows',
            '--memory-pressure-off',

            # キャッシュディレクトリを明示的に指定
            f'--disk-cache-dir={cache_dir}',

            # 共有メモリ使用量削減
            '--disable-features=AudioServiceOutOfProcess',
            '--disable-features=IsolateOrigins',
            '--disable-features=site-per-process',
        ]

        # セッション1: データを保存
        print("\n" + "=" * 60)
        print("セッション1: データ保存")
        print("=" * 60)

        with sync_playwright() as p:
            print("\n[1] ブラウザ起動（永続化設定）...")
            browser = p.chromium.launch_persistent_context(
                user_data_dir=user_data_dir,
                headless=True,
                args=chromium_args
            )
            print("    ✓ 成功")

            page = browser.pages[0]

            print("\n[2] HTMLコンテンツを設定...")
            html_content = """
            <!DOCTYPE html>
            <html>
            <head><title>Session Test</title></head>
            <body>
                <h1>セッション永続化テスト</h1>
                <p id="session-id"></p>
                <script>
                    // セッションIDを表示
                    const sessionId = 'session_' + Date.now();
                    document.getElementById('session-id').textContent = 'Session ID: ' + sessionId;
                </script>
            </body>
            </html>
            """
            page.set_content(html_content)
            print("    ✓ HTMLコンテンツを設定しました")

            print("\n[3] Cookieを設定...")
            # ナビゲーション後にCookieを設定
            page.goto("https://example.com")
            page.context.add_cookies([{
                'name': 'session_id',
                'value': 'test_session_12345',
                'domain': 'example.com',
                'path': '/',
                'httpOnly': True,
                'secure': True,
                'sameSite': 'Lax'
            }])
            cookies = page.context.cookies()
            print(f"    ✓ Cookie設定成功: {len(cookies)}個のクッキー")
            for cookie in cookies:
                print(f"      - {cookie['name']}: {cookie['value']}")

            print("\n[4] スクリーンショット...")
            page.screenshot(path="/home/user/Kagami/playwright_session1.png")
            print("    ✓ スクリーンショット保存: /home/user/Kagami/playwright_session1.png")

            browser.close()
            print("\n    ✓ ブラウザを閉じました")

        # セッション2: データを読み込み
        print("\n" + "=" * 60)
        print("セッション2: データ読み込み")
        print("=" * 60)

        with sync_playwright() as p:
            print("\n[5] 同じユーザーデータディレクトリで再起動...")
            browser = p.chromium.launch_persistent_context(
                user_data_dir=user_data_dir,
                headless=True,
                args=chromium_args
            )
            print("    ✓ 成功")

            page = browser.pages[0]

            print("\n[6] Cookieを確認...")
            page.goto("https://example.com")
            cookies = page.context.cookies()
            print(f"    ✓ Cookie読み込み成功: {len(cookies)}個のクッキー")

            session_cookie = None
            for cookie in cookies:
                print(f"      - {cookie['name']}: {cookie['value']}")
                if cookie['name'] == 'session_id':
                    session_cookie = cookie

            if session_cookie and session_cookie['value'] == 'test_session_12345':
                print("\n    ✅ セッションが正しく復元されました！")
            else:
                raise Exception("セッションCookieが見つかりません")

            print("\n[7] スクリーンショット...")
            page.screenshot(path="/home/user/Kagami/playwright_session2.png")
            print("    ✓ スクリーンショット保存: /home/user/Kagami/playwright_session2.png")

            browser.close()
            print("\n    ✓ ブラウザを閉じました")

        print("\n" + "=" * 60)
        print("✅ セッション永続化テスト成功！")
        print("=" * 60)

        print("\n📋 確認できた機能:")
        print("  ✓ 共有メモリ問題の回避（--disable-dev-shm-usage）")
        print("  ✓ ユーザーデータディレクトリの永続化")
        print("  ✓ Cookieの保存と読み込み")
        print("  ✓ セッション間でのデータ保持")

        print("\n🔧 使用した主要な対策:")
        print("  • --disable-dev-shm-usage: /dev/shmの代わりに/tmpを使用")
        print("  • --disk-cache-dir: キャッシュディレクトリを明示的に指定")
        print("  • --disable-features: 不要な機能を無効化して共有メモリ使用量を削減")

        print(f"\n🗑️  一時ディレクトリ:")
        print(f"  - {user_data_dir}")
        print(f"  - {cache_dir}")
        print("  （不要になったら手動で削除してください）")

        return True

    except Exception as e:
        print(f"\n❌ エラー: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_session_simple()
    sys.exit(0 if success else 1)
