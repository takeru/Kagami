#!/usr/bin/env python3
"""
Cloudflare回避を試みる - より高度な設定
"""
import subprocess
import time
import os
import tempfile
from playwright.sync_api import sync_playwright


print("="*60)
print("Claude AI Access Test (Undetected Mode)")
print("="*60)
print()

# proxy.pyを起動
print("Starting proxy.py...")
proxy_process = subprocess.Popen(
    [
        'uv', 'run', 'proxy',
        '--hostname', '127.0.0.1',
        '--port', '8901',
        '--plugins', 'proxy.plugin.proxy_pool.ProxyPoolPlugin',
        '--proxy-pool', os.environ['HTTPS_PROXY'],
    ],
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL,
)

time.sleep(5)
print("✅ Proxy started\n")

# 一時ディレクトリ作成
user_data_dir = tempfile.mkdtemp(prefix="claude_undetected_", dir="/tmp")
cache_dir = tempfile.mkdtemp(prefix="cache_", dir="/tmp")

try:
    with sync_playwright() as p:
        print("Launching Chromium (undetected mode)...")

        browser = p.chromium.launch_persistent_context(
            user_data_dir=user_data_dir,
            headless=True,  # Note: headless検出を回避する追加フラグ
            args=[
                # 共有メモリ対策
                '--disable-dev-shm-usage',
                '--single-process',

                # サンドボックス無効化
                '--no-sandbox',
                '--disable-setuid-sandbox',

                # プロキシ設定
                '--proxy-server=http://127.0.0.1:8901',
                '--ignore-certificate-errors',

                # Bot検出回避
                '--disable-blink-features=AutomationControlled',
                '--disable-features=IsolateOrigins,site-per-process',

                # Headless検出回避
                '--window-size=1920,1080',
                '--start-maximized',

                # その他
                '--disable-gpu',
                '--disable-accelerated-2d-canvas',
                f'--disk-cache-dir={cache_dir}',

                # User agent
                '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            ]
        )

        print("✅ Browser launched\n")

        page = browser.pages[0]

        # JavaScript injection to hide automation
        await_js = """
        Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
        Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
        Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});
        window.chrome = { runtime: {} };
        """

        page.add_init_script(await_js)
        print("✅ Anti-detection scripts injected\n")

        # Test: claude.ai/codeにアクセス
        print("Accessing https://claude.ai/code/ ...")
        try:
            response = page.goto("https://claude.ai/code/", timeout=60000)
            print(f"✅ Status: {response.status}")
            print(f"✅ URL: {response.url}")

            # タイトル取得
            title = page.title()
            print(f"✅ Title: {title}")

            # CloudflareチャレンジかCheck
            content = page.content()

            if "Just a moment" in content or "Cloudflare" in content:
                print("\n⚠️  Cloudflare challenge page detected")
                print("   Waiting for JavaScript challenge to complete...")

                # より長い待機 + ポーリング
                for i in range(10):
                    time.sleep(3)
                    new_title = page.title()
                    print(f"   [{i+1}/10] Title: {new_title}")

                    if new_title != "Just a moment...":
                        print(f"   ✅ Challenge passed!")
                        break
                else:
                    print(f"   ⚠️ Challenge not completed after 30s")

                # 最終状態を確認
                content = page.content()
                title = page.title()
                print(f"\n   Final title: {title}")
                print(f"   Final content length: {len(content)} bytes")

            # チャレンジ完了後のコンテンツを再取得
            print("\n" + "="*60)
            print("Page loaded successfully")
            print("="*60)
            final_title = page.title()
            final_url = page.url
            print(f"Final Title: {final_title}")
            print(f"Final URL: {final_url}")

            # スクリーンショット
            page.screenshot(path="claude_login_page.png", full_page=True)
            print(f"\n✅ Screenshot saved")

            # ログインボタンを探す
            print("\n" + "="*60)
            print("Looking for login elements...")
            print("="*60)

            # ボタンを探す
            buttons = page.locator("button").all()
            print(f"\nFound {len(buttons)} buttons")
            for i, btn in enumerate(buttons[:10], 1):
                try:
                    text = btn.text_content(timeout=1000) or ""
                    text = text.strip()[:50]
                    visible = btn.is_visible()
                    if visible and text:
                        print(f"  [{i}] '{text}' (visible)")
                except:
                    pass

            # リンクを探す
            links = page.locator("a").all()
            print(f"\nFound {len(links)} links")
            for i, link in enumerate(links[:10], 1):
                try:
                    text = link.text_content(timeout=1000) or ""
                    text = text.strip()[:30]
                    href = link.get_attribute("href", timeout=1000) or ""
                    if text:
                        print(f"  [{i}] '{text}' → {href[:40]}")
                except:
                    pass

            # HTMLを保存
            final_content = page.content()
            with open("claude_login_page.html", 'w', encoding='utf-8') as f:
                f.write(final_content)
            print(f"\n✅ HTML saved: claude_login_page.html ({len(final_content)} bytes)")

            print("\n" + "="*60)
            print("✅ Page successfully loaded and ready for login!")
            print("="*60)
            print("\nNext steps:")
            print("  1. Review the screenshot and HTML file")
            print("  2. Identify the login button selector")
            print("  3. Implement automated login")

        except Exception as e:
            print(f"❌ Failed: {e}")
            import traceback
            traceback.print_exc()

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
    print("✅ Done")
