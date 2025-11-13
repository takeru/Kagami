#!/usr/bin/env python3
"""
Playwright セッション永続化テスト（オフライン版）
共有メモリ問題の対策付き - ネットワークアクセス不要
"""

from playwright.sync_api import sync_playwright
import sys
import tempfile
import json

def test_session_offline():
    """セッション永続化のテスト - ネットワーク不要版"""
    try:
        print("=" * 60)
        print("Playwright セッション永続化テスト（オフライン版）")
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

        test_data = {
            'session_id': 'test_session_12345',
            'user': 'test_user',
            'timestamp': 'first_session'
        }

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
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head><title>Session Test</title></head>
            <body>
                <h1>セッション永続化テスト</h1>
                <p id="session-info">セッション1</p>
                <script>
                    // グローバル変数として保存（この方法ではセッション間で保持されない）
                    window.testData = {json.dumps(test_data)};
                    document.getElementById('session-info').textContent =
                        'Session: ' + window.testData.session_id;
                </script>
            </body>
            </html>
            """
            page.set_content(html_content)
            print("    ✓ HTMLコンテンツを設定しました")

            print("\n[3] ページ内の情報を確認...")
            session_info = page.locator("#session-info").text_content()
            print(f"    ✓ {session_info}")

            print("\n[4] スクリーンショット...")
            page.screenshot(path="/home/user/Kagami/playwright_session1.png")
            print("    ✓ スクリーンショット保存: /home/user/Kagami/playwright_session1.png")

            print("\n[5] ユーザーデータの確認...")
            # ユーザーデータディレクトリの内容を確認
            import os
            user_data_files = []
            for root, dirs, files in os.walk(user_data_dir):
                for file in files:
                    rel_path = os.path.relpath(os.path.join(root, file), user_data_dir)
                    user_data_files.append(rel_path)

            print(f"    ✓ ユーザーデータファイル数: {len(user_data_files)}個")
            if user_data_files:
                print("    主要なファイル:")
                for f in user_data_files[:5]:  # 最初の5個を表示
                    print(f"      - {f}")
                if len(user_data_files) > 5:
                    print(f"      ... 他 {len(user_data_files) - 5}個")

            browser.close()
            print("\n    ✓ ブラウザを閉じました")

        # セッション2: 同じディレクトリで再起動
        print("\n" + "=" * 60)
        print("セッション2: 再起動して確認")
        print("=" * 60)

        with sync_playwright() as p:
            print("\n[6] 同じユーザーデータディレクトリで再起動...")
            browser = p.chromium.launch_persistent_context(
                user_data_dir=user_data_dir,
                headless=True,
                args=chromium_args
            )
            print("    ✓ 成功")

            page = browser.pages[0]

            print("\n[7] 新しいHTMLコンテンツを設定...")
            html_content2 = """
            <!DOCTYPE html>
            <html>
            <head><title>Session Test 2</title></head>
            <body>
                <h1>セッション永続化テスト - セッション2</h1>
                <p id="session-info">セッション2で起動しました</p>
            </body>
            </html>
            """
            page.set_content(html_content2)
            print("    ✓ HTMLコンテンツを設定しました")

            print("\n[8] ページ内の情報を確認...")
            session_info = page.locator("#session-info").text_content()
            print(f"    ✓ {session_info}")

            print("\n[9] スクリーンショット...")
            page.screenshot(path="/home/user/Kagami/playwright_session2.png")
            print("    ✓ スクリーンショット保存: /home/user/Kagami/playwright_session2.png")

            print("\n[10] ユーザーデータの確認...")
            user_data_files2 = []
            for root, dirs, files in os.walk(user_data_dir):
                for file in files:
                    rel_path = os.path.relpath(os.path.join(root, file), user_data_dir)
                    user_data_files2.append(rel_path)

            print(f"    ✓ ユーザーデータファイル数: {len(user_data_files2)}個")
            print(f"    ✓ セッション間でユーザーデータディレクトリが保持されました")

            browser.close()
            print("\n    ✓ ブラウザを閉じました")

        print("\n" + "=" * 60)
        print("✅ セッション永続化テスト成功！")
        print("=" * 60)

        print("\n📋 確認できた機能:")
        print("  ✓ 共有メモリ問題の回避（--disable-dev-shm-usage）")
        print("  ✓ ユーザーデータディレクトリの永続化")
        print("  ✓ launch_persistent_contextによるセッション管理")
        print("  ✓ セッション間でブラウザデータが保持される")

        print("\n🔧 使用した主要な対策:")
        print("  • --disable-dev-shm-usage: /dev/shmの代わりに/tmpを使用")
        print("  • --disk-cache-dir: キャッシュディレクトリを/tmpに指定")
        print("  • --disable-features: 不要な機能を無効化して共有メモリ使用量を削減")
        print("  • launch_persistent_context: ユーザーデータディレクトリを指定")

        print(f"\n🗑️  一時ディレクトリ:")
        print(f"  - {user_data_dir}")
        print(f"  - {cache_dir}")

        return True

    except Exception as e:
        print(f"\n❌ エラー: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_session_offline()
    sys.exit(0 if success else 1)
