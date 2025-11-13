#!/usr/bin/env python3
"""
claude.ai/codeにアクセスしてログイン要素を検出（改良版）
Cloudflareチャレンジを確実に通過するまで待機
"""
import subprocess
import time
import os
import tempfile
from playwright.sync_api import sync_playwright


print("="*60)
print("Claude AI Login Detection (v2)")
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

# 一時ディレクトリ作成
user_data_dir = tempfile.mkdtemp(prefix="claude_login_v2_", dir="/tmp")
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
                '--proxy-server=http://127.0.0.1:8902',
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

        # claude.ai/codeにアクセス
        print("Accessing https://claude.ai/code/ ...")
        response = page.goto("https://claude.ai/code/", timeout=60000)
        print(f"✅ Initial Status: {response.status}")
        print(f"✅ Initial URL: {response.url}")

        # Cloudflareチャレンジを確実に通過するまで待機
        print("\nWaiting for Cloudflare challenge to complete...")
        max_attempts = 20
        for i in range(max_attempts):
            time.sleep(2)

            title = page.title()
            url = page.url

            # タイトルとコンテンツをチェック
            content_sample = page.content()[:500]  # 最初の500文字だけ取得

            print(f"  [{i+1}/{max_attempts}] Title: {title}")

            # Cloudflareチャレンジのチェック
            is_challenge = (
                "Just a moment" in title or
                "Verifying you are human" in content_sample or
                "challenge" in content_sample.lower()
            )

            if not is_challenge and title == "Claude Code | Claude":
                print(f"  ✅ Challenge passed! Title is correct.")
                break

            if i == max_attempts - 1:
                print(f"  ⚠️ Challenge not completed after {max_attempts * 2}s")
        else:
            # タイムアウトしても続行
            pass

        # 最終確認
        print("\n" + "="*60)
        print("Page Status")
        print("="*60)
        final_title = page.title()
        final_url = page.url
        print(f"Title: {final_title}")
        print(f"URL: {final_url}")

        # ネットワークがアイドル状態になるまで待機
        print("\nWaiting for network idle...")
        try:
            page.wait_for_load_state("networkidle", timeout=30000)
            print("✅ Network idle")
        except Exception as e:
            print(f"⚠️ Network idle timeout: {e}")

        # スクリーンショット
        page.screenshot(path="claude_login_v2.png", full_page=True)
        print(f"\n✅ Screenshot saved: claude_login_v2.png")

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
        for i, link in enumerate(links[:15], 1):
            try:
                text = link.text_content(timeout=1000) or ""
                text = text.strip()[:40]
                href = link.get_attribute("href", timeout=1000) or ""
                if text or "login" in href.lower():
                    print(f"  [{i}] '{text}' → {href[:50]}")
            except:
                pass

        # HTMLを保存
        final_content = page.content()
        with open("claude_login_v2.html", 'w', encoding='utf-8') as f:
            f.write(final_content)
        print(f"\n✅ HTML saved: claude_login_v2.html ({len(final_content)} bytes)")

        # 特定の要素を探す
        print("\n" + "="*60)
        print("Looking for specific elements...")
        print("="*60)

        # ログイン関連の要素
        selectors = [
            'button:has-text("Log in")',
            'button:has-text("Login")',
            'button:has-text("Sign in")',
            'a:has-text("Log in")',
            'a:has-text("Login")',
            'a[href*="login"]',
            '[data-testid*="login"]',
        ]

        for selector in selectors:
            try:
                element = page.locator(selector).first
                if element.is_visible(timeout=1000):
                    text = element.text_content() or ""
                    print(f"  ✅ Found: {selector} → '{text.strip()}'")
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
    print("✅ Done")
