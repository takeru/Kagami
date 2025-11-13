#!/usr/bin/env python3
"""
共有メモリ問題を解決した状態でプロキシ経由アクセスをテスト
"""
import subprocess
import time
import os
import tempfile
from playwright.sync_api import sync_playwright


print("="*60)
print("Playwright + proxy.py Test (Fixed)")
print("="*60)
print()

# proxy.pyを起動
print("Starting proxy.py...")
proxy_process = subprocess.Popen(
    [
        'uv', 'run', 'proxy',
        '--hostname', '127.0.0.1',
        '--port', '8899',
        '--plugins', 'proxy.plugin.proxy_pool.ProxyPoolPlugin',
        '--proxy-pool', os.environ['HTTPS_PROXY'],
    ],
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL,
)

time.sleep(5)
print("✅ Proxy started on port 8899\n")

# 一時ディレクトリ作成
user_data_dir = tempfile.mkdtemp(prefix="chrome_", dir="/tmp")
cache_dir = tempfile.mkdtemp(prefix="cache_", dir="/tmp")

print(f"User data dir: {user_data_dir}")
print(f"Cache dir: {cache_dir}\n")

try:
    with sync_playwright() as p:
        print("Launching Chromium with proxy...")

        browser = p.chromium.launch_persistent_context(
            user_data_dir=user_data_dir,
            headless=True,
            args=[
                # 共有メモリ対策（最重要）
                '--disable-dev-shm-usage',
                '--single-process',

                # サンドボックス無効化
                '--no-sandbox',
                '--disable-setuid-sandbox',

                # プロキシ設定
                '--proxy-server=http://127.0.0.1:8899',
                '--ignore-certificate-errors',

                # その他
                '--disable-gpu',
                '--disable-accelerated-2d-canvas',
                f'--disk-cache-dir={cache_dir}',
            ]
        )

        print("✅ Browser launched\n")

        page = browser.pages[0]

        # Test 1: example.comにアクセス
        print("Test 1: Accessing example.com...")
        try:
            response = page.goto("https://example.com", timeout=30000)
            print(f"✅ Status: {response.status}")
            print(f"✅ URL: {response.url}")

            # タイトル取得
            title = page.title()
            print(f"✅ Title: {title}")

            # スクリーンショット
            page.screenshot(path="test_proxy_fixed.png")
            print(f"✅ Screenshot saved\n")

        except Exception as e:
            print(f"❌ Failed: {e}\n")

        browser.close()

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

finally:
    print("\nStopping proxy...")
    proxy_process.terminate()
    try:
        proxy_process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proxy_process.kill()
    print("✅ Proxy stopped")

    # クリーンアップ
    import shutil
    shutil.rmtree(user_data_dir, ignore_errors=True)
    shutil.rmtree(cache_dir, ignore_errors=True)
