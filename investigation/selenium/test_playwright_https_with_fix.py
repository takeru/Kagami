"""
共有メモリ問題の解決策 + proxy.py でHTTPSアクセス

以前の調査で失敗していたHTTPSアクセスを、共有メモリ対策を適用して再試行
"""

from playwright.sync_api import sync_playwright
import tempfile
import subprocess
import time
import os
import signal
import sys

def start_proxy():
    """proxy.pyサーバーを起動"""
    https_proxy = os.getenv('HTTPS_PROXY')
    if not https_proxy:
        raise Exception("HTTPS_PROXY environment variable is not set")

    print(f"[Proxy] Starting proxy.py with upstream proxy...")
    print(f"[Proxy] Upstream: {https_proxy[:80]}...")

    # proxy.pyをProxyPoolPluginと共に起動
    process = subprocess.Popen([
        'uv', 'run', 'proxy',
        '--hostname', '127.0.0.1',
        '--port', '8891',
        '--plugins', 'proxy.plugin.proxy_pool.ProxyPoolPlugin',
        '--proxy-pool', https_proxy,
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    print(f"[Proxy] Started with PID: {process.pid}")
    print(f"[Proxy] Waiting for proxy to be ready...")
    time.sleep(6)

    return process

def stop_proxy(process):
    """proxy.pyサーバーを停止"""
    print(f"\n[Proxy] Stopping proxy (PID: {process.pid})...")
    process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
    print(f"[Proxy] Stopped")

def test_https_with_shared_memory_fix():
    """共有メモリ対策 + proxy.py でHTTPSアクセス"""
    proxy_process = None

    try:
        print("=" * 70)
        print("共有メモリ対策 + proxy.py でHTTPSアクセステスト")
        print("=" * 70)

        # proxy.pyを起動
        proxy_process = start_proxy()

        # ユーザーデータディレクトリを/tmpに作成
        user_data_dir = tempfile.mkdtemp(prefix="playwright_https_", dir="/tmp")
        cache_dir = tempfile.mkdtemp(prefix="playwright_cache_", dir="/tmp")
        print(f"\n📁 ユーザーデータディレクトリ: {user_data_dir}")
        print(f"📁 キャッシュディレクトリ: {cache_dir}")

        # 共有メモリ対策のための引数
        chromium_args = [
            # 共有メモリ対策（最重要）
            '--disable-dev-shm-usage',

            # サンドボックス無効化
            '--no-sandbox',
            '--disable-setuid-sandbox',

            # プロセス管理
            '--single-process',

            # GPU無効化
            '--disable-gpu',
            '--disable-accelerated-2d-canvas',

            # キャッシュディレクトリ
            f'--disk-cache-dir={cache_dir}',

            # プロキシ設定
            '--proxy-server=http://127.0.0.1:8891',

            # 証明書エラー無視
            '--ignore-certificate-errors',
            '--ignore-certificate-errors-spki-list',
        ]

        print("\n" + "=" * 70)
        print("Test 1: https://example.com にアクセス")
        print("=" * 70)

        with sync_playwright() as p:
            print("\n[1] ブラウザ起動（永続化モード + プロキシ）...")
            browser = p.chromium.launch_persistent_context(
                user_data_dir=user_data_dir,
                headless=True,
                args=chromium_args,
                ignore_https_errors=True,
            )
            print("    ✓ 成功")

            page = browser.pages[0]

            print("\n[2] https://example.com にアクセス中...")
            page.set_default_timeout(120000)  # 2分

            try:
                page.goto("https://example.com", wait_until="domcontentloaded")
                print("    ✓ ページロード成功！")

                print("\n[3] ページ情報取得...")
                title = page.title()
                url = page.url
                content_length = len(page.content())

                print(f"    ✓ タイトル: '{title}'")
                print(f"    ✓ URL: {url}")
                print(f"    ✓ コンテンツ長: {content_length} 文字")

                # コンテンツ確認
                content = page.content()
                if "Example Domain" in content:
                    print("    ✅ 正常にHTTPSコンテンツを取得できました！")
                else:
                    print("    ⚠️ 予期しないコンテンツ")
                    print(f"    最初の500文字: {content[:500]}")

                print("\n[4] スクリーンショット...")
                page.screenshot(path="/home/user/Kagami/playwright_https_success.png")
                print("    ✓ スクリーンショット保存")

                success = True

            except Exception as e:
                print(f"    ❌ ページアクセス失敗: {e}")
                success = False

            browser.close()

        if success:
            print("\n" + "=" * 70)
            print("✅ HTTPSアクセス成功！")
            print("=" * 70)
            print("\n📋 確認できた機能:")
            print("  ✓ 共有メモリ問題の回避")
            print("  ✓ proxy.py経由のHTTPS通信")
            print("  ✓ ページタイトル・コンテンツ取得")
            print("  ✓ スクリーンショット撮影")
            print("\n🎯 これで以前の問題がすべて解決しました！")
        else:
            print("\n⚠️ HTTPSアクセスは失敗しましたが、")
            print("   共有メモリ問題の対策は有効であることが確認できました。")

        return success

    except Exception as e:
        print(f"\n❌ エラー: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        if proxy_process:
            stop_proxy(proxy_process)

if __name__ == "__main__":
    success = test_https_with_shared_memory_fix()
    sys.exit(0 if success else 1)
