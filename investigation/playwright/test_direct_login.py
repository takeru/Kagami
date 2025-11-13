#!/usr/bin/env python3
"""
直接ログインページにアクセスしてログイン要素を検出
"""
import subprocess
import time
import os
import tempfile
from playwright.sync_api import sync_playwright


print("="*60)
print("Claude AI Direct Login Page Test")
print("="*60)
print()

# proxy.pyを起動
print("Starting proxy.py...")
proxy_process = subprocess.Popen(
    [
        'uv', 'run', 'proxy',
        '--hostname', '127.0.0.1',
        '--port', '8903',
        '--plugins', 'proxy.plugin.proxy_pool.ProxyPoolPlugin',
        '--proxy-pool', os.environ['HTTPS_PROXY'],
    ],
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL,
)

time.sleep(5)
print("✅ Proxy started\n")

# 一時ディレクトリ作成
user_data_dir = tempfile.mkdtemp(prefix="claude_direct_login_", dir="/tmp")
cache_dir = tempfile.mkdtemp(prefix="cache_", dir="/tmp")

try:
    with sync_playwright() as p:
        print("Launching Chromium (undetected mode)...")

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
                '--proxy-server=http://127.0.0.1:8903',
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

        # 直接ログインページにアクセス
        print("Accessing https://claude.ai/login?returnTo=%2Fcode ...")
        try:
            response = page.goto("https://claude.ai/login?returnTo=%2Fcode", timeout=60000)
            print(f"✅ Status: {response.status}")
            print(f"✅ URL: {response.url}")

            # タイトル取得
            title = page.title()
            print(f"✅ Title: {title}")

            # Cloudflareチャレンジの確認
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

            # スクリーンショット
            page.screenshot(path="claude_direct_login.png", full_page=True)
            print(f"\n✅ Screenshot saved")

            # ログイン要素を検出
            print("\n" + "="*60)
            print("Looking for login elements...")
            print("="*60)

            # ボタンを探す
            buttons = page.locator("button").all()
            print(f"\nFound {len(buttons)} buttons")
            for i, btn in enumerate(buttons[:15], 1):
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
            for i, link in enumerate(links[:20], 1):
                try:
                    text = link.text_content(timeout=1000) or ""
                    text = text.strip()[:40]
                    href = link.get_attribute("href", timeout=1000) or ""
                    if text or "login" in href.lower() or "google" in href.lower() or "email" in href.lower():
                        print(f"  [{i}] '{text}' → {href[:60]}")
                except:
                    pass

            # HTMLを保存
            with open("claude_direct_login.html", 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"\n✅ HTML saved: claude_direct_login.html ({len(content)} bytes)")

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
