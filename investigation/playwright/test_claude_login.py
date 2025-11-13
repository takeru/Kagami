#!/usr/bin/env python3
"""
claude.ai/codeへのログインテスト
手動ログインのサポート（headless=False）とセッション保存
"""
import subprocess
import time
import os
import tempfile
from playwright.sync_api import sync_playwright


print("="*60)
print("Claude AI Login Test")
print("="*60)
print()

# proxy.pyを起動
print("Starting proxy.py...")
proxy_process = subprocess.Popen(
    [
        'uv', 'run', 'proxy',
        '--hostname', '127.0.0.1',
        '--port', '8902',
        '--plugins', 'proxy.plugin.proxy_pool.ProxyPoolPlugin',
        '--proxy-pool', os.environ['HTTPS_PROXY'],
    ],
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL,
)

time.sleep(5)
print("✅ Proxy started\n")

# セッション保存用ディレクトリ
session_dir = "/tmp/claude_ai_session"
cache_dir = "/tmp/claude_ai_cache"

# ディレクトリが存在しない場合は作成
os.makedirs(session_dir, exist_ok=True)
os.makedirs(cache_dir, exist_ok=True)

print(f"Session dir: {session_dir}")
print(f"Cache dir: {cache_dir}\n")

try:
    with sync_playwright() as p:
        print("Launching Chromium (headless=False for manual login)...")

        # headless=False にして手動ログインを可能にする
        browser = p.chromium.launch_persistent_context(
            user_data_dir=session_dir,
            headless=False,  # GUI表示
            args=[
                # 共有メモリ対策
                '--disable-dev-shm-usage',
                '--single-process',

                # サンドボックス無効化
                '--no-sandbox',
                '--disable-setuid-sandbox',

                # プロキシ設定
                '--proxy-server=http://127.0.0.1:8902',
                '--ignore-certificate-errors',

                # Bot検出回避
                '--disable-blink-features=AutomationControlled',
                '--disable-features=IsolateOrigins,site-per-process',
                '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',

                # その他
                '--disable-gpu',
                f'--disk-cache-dir={cache_dir}',

                # ウィンドウサイズ
                '--window-size=1920,1080',
            ]
        )

        print("✅ Browser launched\n")

        page = browser.pages[0]

        # Anti-detection JavaScript
        page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
            Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});
            window.chrome = { runtime: {} };
        """)

        # claude.ai/codeにアクセス
        print("Accessing https://claude.ai/code/ ...")
        response = page.goto("https://claude.ai/code/", timeout=60000)
        print(f"✅ Status: {response.status}")
        print(f"✅ URL: {response.url}")

        # 少し待ってからタイトル取得
        time.sleep(2)
        title = page.title()
        print(f"✅ Title: {title}\n")

        # スクリーンショット
        page.screenshot(path="claude_login_initial.png")
        print("✅ Initial screenshot saved\n")

        # ログイン状態を確認
        print("="*60)
        print("Login Status Check")
        print("="*60)

        # URLを確認（ログイン済みならリダイレクトされない）
        current_url = page.url
        print(f"Current URL: {current_url}")

        # ログインボタンの存在を確認
        try:
            # 複数のセレクタで試す
            login_selectors = [
                'button:has-text("Sign in")',
                'button:has-text("Log in")',
                'a:has-text("Sign in")',
                'a:has-text("Log in")',
                '[data-testid="login-button"]',
                '.login-button',
            ]

            login_button = None
            for selector in login_selectors:
                try:
                    login_button = page.wait_for_selector(selector, timeout=5000)
                    if login_button:
                        print(f"✅ Login button found: {selector}")
                        break
                except:
                    continue

            if login_button:
                print("\n⚠️  Not logged in. Please login manually.")
                print("\nInstructions:")
                print("  1. The browser window is now open")
                print("  2. Click the login button and complete authentication")
                print("  3. After successful login, press Enter in this terminal")
                print("\nWaiting for manual login...")

                input("\nPress Enter after you've logged in successfully...")

                # ログイン後のスクリーンショット
                page.screenshot(path="claude_login_after.png")
                print("\n✅ Post-login screenshot saved")

                # セッション情報を確認
                print("\n" + "="*60)
                print("Session Info")
                print("="*60)

                # Cookieを取得
                cookies = browser.cookies()
                print(f"✅ Cookies saved: {len(cookies)} cookies")

                # ローカルストレージを取得
                local_storage = page.evaluate("() => JSON.stringify(localStorage)")
                print(f"✅ LocalStorage data captured")

                # セッションストレージを取得
                session_storage = page.evaluate("() => JSON.stringify(sessionStorage)")
                print(f"✅ SessionStorage data captured")

                print(f"\n✅ Session data saved in: {session_dir}")
                print("   This session can be reused in future runs!")

            else:
                print("✅ Already logged in or login not required")

        except Exception as e:
            print(f"Note: Could not find login button: {e}")
            print("You may already be logged in.")

        # 最終スクリーンショット
        page.screenshot(path="claude_login_final.png", full_page=True)
        print("\n✅ Final screenshot saved")

        print("\n" + "="*60)
        print("✅ Login test completed!")
        print("="*60)
        print(f"\nSession directory: {session_dir}")
        print("To reuse this session, use the same user_data_dir in future runs.")

        print("\nKeeping browser open for 30 seconds...")
        print("You can interact with the page during this time.")
        time.sleep(30)

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
