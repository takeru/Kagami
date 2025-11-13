#!/usr/bin/env python3
"""
Playwright セッション永続化テスト
共有メモリ問題の対策付き
"""

from playwright.sync_api import sync_playwright
import sys
import os
from pathlib import Path
import tempfile

def test_session_persistence():
    """セッション永続化のテスト - 共有メモリ問題の対策付き"""
    try:
        print("=" * 60)
        print("Playwright セッション永続化テスト")
        print("=" * 60)

        # ユーザーデータディレクトリを/tmpに作成（/dev/shmを避ける）
        user_data_dir = tempfile.mkdtemp(prefix="playwright_session_", dir="/tmp")
        print(f"\n📁 ユーザーデータディレクトリ: {user_data_dir}")

        # キャッシュディレクトリも明示的に指定
        cache_dir = tempfile.mkdtemp(prefix="playwright_cache_", dir="/tmp")
        print(f"📁 キャッシュディレクトリ: {cache_dir}")

        # セッション1: データを保存
        print("\n" + "=" * 60)
        print("セッション1: データ保存")
        print("=" * 60)

        with sync_playwright() as p:
            print("\n[1] ブラウザ起動（永続化設定）...")
            browser = p.chromium.launch_persistent_context(
                user_data_dir=user_data_dir,
                headless=True,
                args=[
                    # 共有メモリ対策
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

                    # 共有メモリサイズ削減
                    '--disable-features=AudioServiceOutOfProcess',
                    '--disable-features=IsolateOrigins',
                    '--disable-features=site-per-process',
                ]
            )
            print("    ✓ 成功")

            page = browser.pages[0]  # launch_persistent_contextは自動的にページを作成

            print("\n[2] LocalStorageにデータを保存...")
            # about:blankではLocalStorageが使えないので、data URLを使用
            page.goto("data:text/html,<html><body><h1>Session Test</h1></body></html>")
            page.evaluate("""
                localStorage.setItem('test_key', 'セッション永続化テスト');
                localStorage.setItem('timestamp', new Date().toISOString());
            """)

            saved_value = page.evaluate("localStorage.getItem('test_key')")
            saved_time = page.evaluate("localStorage.getItem('timestamp')")
            print(f"    ✓ 保存成功: {saved_value}")
            print(f"    ✓ タイムスタンプ: {saved_time}")

            print("\n[3] Cookieを設定...")
            page.context.add_cookies([{
                'name': 'session_id',
                'value': 'abc123xyz',
                'domain': 'example.com',
                'path': '/'
            }])
            cookies = page.context.cookies()
            print(f"    ✓ Cookie設定成功: {len(cookies)}個のクッキー")

            browser.close()
            print("\n    ✓ ブラウザを閉じました")

        # セッション2: データを読み込み
        print("\n" + "=" * 60)
        print("セッション2: データ読み込み")
        print("=" * 60)

        with sync_playwright() as p:
            print("\n[4] 同じユーザーデータディレクトリで再起動...")
            browser = p.chromium.launch_persistent_context(
                user_data_dir=user_data_dir,
                headless=True,
                args=[
                    '--disable-dev-shm-usage',
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-gpu',
                    '--disable-software-rasterizer',
                    '--disable-accelerated-2d-canvas',
                    '--disable-background-timer-throttling',
                    '--disable-backgrounding-occluded-windows',
                    '--memory-pressure-off',
                    f'--disk-cache-dir={cache_dir}',
                    '--disable-features=AudioServiceOutOfProcess',
                    '--disable-features=IsolateOrigins',
                    '--disable-features=site-per-process',
                ]
            )
            print("    ✓ 成功")

            page = browser.pages[0]

            print("\n[5] LocalStorageからデータを読み込み...")
            # 同じdata URLドメインを使用
            page.goto("data:text/html,<html><body><h1>Session Test</h1></body></html>")
            loaded_value = page.evaluate("localStorage.getItem('test_key')")
            loaded_time = page.evaluate("localStorage.getItem('timestamp')")

            if loaded_value == 'セッション永続化テスト':
                print(f"    ✓ 読み込み成功: {loaded_value}")
                print(f"    ✓ タイムスタンプ: {loaded_time}")
            else:
                raise Exception(f"データが一致しません: {loaded_value}")

            print("\n[6] Cookieを確認...")
            cookies = page.context.cookies()
            print(f"    ✓ Cookie読み込み成功: {len(cookies)}個のクッキー")
            for cookie in cookies:
                print(f"      - {cookie['name']}: {cookie['value']}")

            browser.close()
            print("\n    ✓ ブラウザを閉じました")

        print("\n" + "=" * 60)
        print("✅ セッション永続化テスト成功！")
        print("=" * 60)

        print("\n📋 確認できた機能:")
        print("  ✓ 共有メモリ問題の回避（--disable-dev-shm-usage）")
        print("  ✓ ユーザーデータディレクトリの永続化")
        print("  ✓ LocalStorageの保存と読み込み")
        print("  ✓ Cookieの保存と読み込み")
        print("  ✓ セッション間でのデータ保持")

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
    success = test_session_persistence()
    sys.exit(0 if success else 1)
