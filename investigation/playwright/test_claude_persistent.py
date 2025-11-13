#!/usr/bin/env python3
"""
claude.aiアクセステスト - セッション永続化版
Cloudflareチャレンジを突破するための設定を追加
"""
import sys
import os
import threading
import time
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.local_proxy import run_proxy_server
from playwright.sync_api import sync_playwright

CA_SPKI_HASH = "L+/CZomxifpzjiAVG11S0bTbaTopj+c49s0rBjjSC6A="


def start_proxy():
    def run():
        run_proxy_server(port=8888)
    t = threading.Thread(target=run, daemon=True)
    t.start()
    time.sleep(2)


def test_claude_with_persistence():
    """セッション永続化を使用してclaude.aiにアクセス"""
    print("="*60)
    print("Claude AI with Persistent Session")
    print("="*60)

    # ユーザーデータディレクトリを/tmpに作成
    user_data_dir = tempfile.mkdtemp(prefix="playwright_claude_", dir="/tmp")
    print(f"\n📁 User data dir: {user_data_dir}")

    with sync_playwright() as p:
        print("\nLaunching Chromium with persistent context...")

        # より人間らしいブラウザ設定
        browser = p.chromium.launch_persistent_context(
            user_data_dir=user_data_dir,
            headless=True,  # headlessでもUser-Agentは設定可能
            args=[
                # 共有メモリ対策
                '--disable-dev-shm-usage',
                '--single-process',
                # サンドボックス無効化
                '--no-sandbox',
                '--disable-setuid-sandbox',
                # プロキシ設定
                '--proxy-server=http://127.0.0.1:8888',
                # CA証明書対策
                f'--ignore-certificate-errors-spki-list={CA_SPKI_HASH}',
                '--ignore-certificate-errors',
                # パフォーマンス
                '--disable-gpu',
                '--disable-accelerated-2d-canvas',
                # ボット検出回避
                '--disable-blink-features=AutomationControlled',
            ],
            viewport={'width': 1920, 'height': 1080},
            # より本物らしいUser-Agent
            user_agent='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            # HTTPS errors無視
            ignore_https_errors=True,
        )

        print("✅ Browser launched")

        page = browser.pages[0]

        # JavaScript でnavigator.webdriverを隠す
        page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """)

        # Test 1: シンプルなサイトで確認
        print("\n" + "="*60)
        print("Test 1: example.com (baseline)")
        print("="*60)
        try:
            page.goto("https://example.com", timeout=10000)
            print(f"✅ Title: {page.title()}")
        except Exception as e:
            print(f"❌ Failed: {e}")

        # Test 2: claude.ai
        print("\n" + "="*60)
        print("Test 2: claude.ai/")
        print("="*60)
        try:
            print("Navigating...")
            page.goto("https://claude.ai/", timeout=30000, wait_until="commit")

            print(f"✅ Navigation completed")
            print(f"URL: {page.url}")

            # 少し待つ（Cloudflareチャレンジの処理）
            print("Waiting for page to load...")
            time.sleep(5)

            # タイトルを確認
            try:
                title = page.title()
                print(f"Title: {title}")
            except:
                pass

            # スクリーンショット保存
            screenshot_path = "/home/user/Kagami/investigation/playwright/claude_persistent.png"
            page.screenshot(path=screenshot_path, full_page=True)
            print(f"✅ Screenshot: {screenshot_path}")

            # HTMLを保存
            html = page.content()
            html_path = "/home/user/Kagami/investigation/playwright/claude_persistent.html"
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(html)
            print(f"✅ HTML saved: {html_path}")
            print(f"HTML size: {len(html)} bytes")

            # Cloudflareチャレンジページかどうか確認
            if "Just a moment" in title or "Just a moment" in html:
                print("\n⚠️  Cloudflare Challenge detected")
                print("This is expected for bot protection")
            else:
                print("\n🎉 Successfully passed Cloudflare!")

        except Exception as e:
            print(f"❌ Failed: {e}")

            try:
                page.screenshot(path="/home/user/Kagami/investigation/playwright/claude_persistent_error.png")
            except:
                pass

        # Test 3: claude.ai/code
        print("\n" + "="*60)
        print("Test 3: claude.ai/code")
        print("="*60)
        try:
            print("Navigating...")
            page.goto("https://claude.ai/code", timeout=30000, wait_until="commit")

            print(f"✅ Navigation completed")
            print(f"URL: {page.url}")

            time.sleep(5)

            try:
                title = page.title()
                print(f"Title: {title}")
            except:
                pass

            screenshot_path = "/home/user/Kagami/investigation/playwright/claude_code_persistent.png"
            page.screenshot(path=screenshot_path, full_page=True)
            print(f"✅ Screenshot: {screenshot_path}")

        except Exception as e:
            print(f"❌ Failed: {e}")

        browser.close()

        print(f"\n📁 User data saved in: {user_data_dir}")
        print("   (Contains cookies and session data)")


if __name__ == "__main__":
    start_proxy()
    test_claude_with_persistence()

    print("\n" + "="*60)
    print("Done")
    print("="*60)
