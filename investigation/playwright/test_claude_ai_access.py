#!/usr/bin/env python3
"""
claude.ai/codeへのアクセステスト
共有メモリ問題解決 + プロキシ経由
"""
import subprocess
import time
import os
import tempfile
from playwright.sync_api import sync_playwright


print("="*60)
print("Claude AI Access Test")
print("="*60)
print()

# proxy.pyを起動
print("Starting proxy.py...")
proxy_process = subprocess.Popen(
    [
        'uv', 'run', 'proxy',
        '--hostname', '127.0.0.1',
        '--port', '8900',
        '--plugins', 'proxy.plugin.proxy_pool.ProxyPoolPlugin',
        '--proxy-pool', os.environ['HTTPS_PROXY'],
    ],
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL,
)

time.sleep(5)
print("✅ Proxy started on port 8900\n")

# 一時ディレクトリ作成
user_data_dir = tempfile.mkdtemp(prefix="claude_session_", dir="/tmp")
cache_dir = tempfile.mkdtemp(prefix="claude_cache_", dir="/tmp")

print(f"User data dir: {user_data_dir}")
print(f"Cache dir: {cache_dir}\n")

try:
    with sync_playwright() as p:
        print("Launching Chromium...")

        browser = p.chromium.launch_persistent_context(
            user_data_dir=user_data_dir,
            headless=True,
            args=[
                # 共有メモリ対策
                '--disable-dev-shm-usage',
                '--single-process',

                # サンドボックス無効化
                '--no-sandbox',
                '--disable-setuid-sandbox',

                # プロキシ設定
                '--proxy-server=http://127.0.0.1:8900',
                '--ignore-certificate-errors',

                # その他
                '--disable-gpu',
                '--disable-accelerated-2d-canvas',
                f'--disk-cache-dir={cache_dir}',
            ]
        )

        print("✅ Browser launched\n")

        page = browser.pages[0]

        # Test: claude.ai/codeにアクセス
        print("Accessing https://claude.ai/code/ ...")
        try:
            response = page.goto("https://claude.ai/code/", timeout=60000)
            print(f"✅ Status: {response.status}")
            print(f"✅ URL: {response.url}")

            # 少し待ってからタイトル取得
            time.sleep(2)
            title = page.title()
            print(f"✅ Title: {title}")

            # HTMLコンテンツの一部を取得
            content = page.content()
            print(f"✅ Content length: {len(content)} bytes")

            # スクリーンショット
            page.screenshot(path="claude_ai_code.png")
            print(f"✅ Screenshot saved to claude_ai_code.png")

            # Cloudflare challenge確認
            if "Just a moment" in content or "challenge" in content.lower():
                print("\n⚠️  Cloudflare challenge detected")
                print("   JavaScript実行を待機中...")
                page.wait_for_load_state("networkidle", timeout=30000)

                # 再度確認
                content = page.content()
                title = page.title()
                print(f"   Title after wait: {title}")
                page.screenshot(path="claude_ai_code_after_wait.png")

            print(f"\n✅ Claude AI access successful!")

        except Exception as e:
            print(f"❌ Failed: {e}")
            import traceback
            traceback.print_exc()

            # エラー時もスクリーンショット取得
            try:
                page.screenshot(path="claude_ai_code_error.png")
                print("Screenshot saved (error state)")
            except:
                pass

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

    print(f"\n📁 Session data saved in: {user_data_dir}")
    print(f"   (Can be reused for session persistence)")
