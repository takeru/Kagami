#!/usr/bin/env python3
"""
claude.ai/codeへの自動ログイン
メールアドレスでのログインフローを実装
"""
import subprocess
import time
import os
import tempfile
from playwright.sync_api import sync_playwright


print("="*60)
print("Claude AI Automated Login")
print("="*60)
print()

# proxy.pyを起動
print("Starting proxy.py...")
proxy_process = subprocess.Popen(
    [
        'uv', 'run', 'proxy',
        '--hostname', '127.0.0.1',
        '--port', '8904',
        '--plugins', 'proxy.plugin.proxy_pool.ProxyPoolPlugin',
        '--proxy-pool', os.environ['HTTPS_PROXY'],
    ],
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL,
)

time.sleep(5)
print("✅ Proxy started\n")

# 一時ディレクトリ作成（セッション永続化用）
user_data_dir = tempfile.mkdtemp(prefix="claude_session_", dir="/tmp")
cache_dir = tempfile.mkdtemp(prefix="cache_", dir="/tmp")

print(f"Session data dir: {user_data_dir}")
print(f"Cache dir: {cache_dir}\n")

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
                '--proxy-server=http://127.0.0.1:8904',
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

        # Step 1: ログインページにアクセス
        print("="*60)
        print("Step 1: Accessing login page")
        print("="*60)
        response = page.goto("https://claude.ai/login?returnTo=%2Fcode", timeout=60000)
        print(f"✅ Status: {response.status}")
        print(f"✅ URL: {response.url}")
        print(f"✅ Title: {page.title()}\n")

        # Step 2: "Continue with email" ボタンをクリック
        print("="*60)
        print("Step 2: Click 'Continue with email' button")
        print("="*60)

        try:
            # ボタンを探してクリック
            email_button = page.locator("button:has-text('Continue with email')").first
            email_button.wait_for(state="visible", timeout=10000)
            print("✅ Found 'Continue with email' button")

            email_button.click()
            print("✅ Clicked 'Continue with email' button\n")

            # ページ遷移を待機
            time.sleep(2)

            # Step 3: メール入力フォームを確認
            print("="*60)
            print("Step 3: Email input form")
            print("="*60)
            print(f"Current URL: {page.url}")
            print(f"Current Title: {page.title()}")

            # スクリーンショット
            page.screenshot(path="claude_login_email_form.png", full_page=True)
            print(f"✅ Screenshot saved: claude_login_email_form.png\n")

            # メール入力フィールドを探す
            email_inputs = page.locator("input[type='email'], input[name='email'], input[placeholder*='email' i]").all()
            print(f"Found {len(email_inputs)} email input fields")

            for i, inp in enumerate(email_inputs, 1):
                try:
                    visible = inp.is_visible()
                    placeholder = inp.get_attribute("placeholder") or ""
                    name = inp.get_attribute("name") or ""
                    if visible:
                        print(f"  [{i}] name='{name}', placeholder='{placeholder}' (visible)")
                except:
                    pass

            # テキスト入力フィールド（type="email"以外も含む）
            text_inputs = page.locator("input[type='text']").all()
            print(f"\nFound {len(text_inputs)} text input fields")
            for i, inp in enumerate(text_inputs[:5], 1):
                try:
                    visible = inp.is_visible()
                    placeholder = inp.get_attribute("placeholder") or ""
                    name = inp.get_attribute("name") or ""
                    if visible:
                        print(f"  [{i}] name='{name}', placeholder='{placeholder}' (visible)")
                except:
                    pass

            # HTMLを保存
            content = page.content()
            with open("claude_login_email_form.html", 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"\n✅ HTML saved: claude_login_email_form.html ({len(content)} bytes)\n")

            print("="*60)
            print("Next steps:")
            print("="*60)
            print("1. Review the screenshot and HTML to identify the email input field")
            print("2. Enter email address and submit")
            print("3. Handle verification code (if required)")
            print("4. Complete login and save session")
            print(f"\nSession will be saved in: {user_data_dir}")

        except Exception as e:
            print(f"❌ Failed to click button: {e}")
            page.screenshot(path="claude_login_error.png", full_page=True)
            print("Screenshot saved: claude_login_error.png")

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
