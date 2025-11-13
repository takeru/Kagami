#!/usr/bin/env python3
"""
claude.aiアクセスの詳細デバッグ
"""
import sys
import os
import threading
import time

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


def test_claude_ai_root():
    """claude.aiのルート（/codeではなく）にアクセス"""
    print("="*60)
    print("Accessing https://claude.ai/ (root)")
    print("="*60)

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=[
                '--disable-dev-shm-usage',
                '--single-process',
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--proxy-server=http://127.0.0.1:8888',
                f'--ignore-certificate-errors-spki-list={CA_SPKI_HASH}',
                '--ignore-certificate-errors',
                '--disable-gpu',
            ]
        )

        context = browser.new_context(ignore_https_errors=True)
        page = context.new_page()

        # イベントリスナーを追加
        page.on("console", lambda msg: print(f"  [Console] {msg.text}"))
        page.on("pageerror", lambda err: print(f"  [Error] {err}"))
        page.on("requestfailed", lambda req: print(f"  [Failed] {req.url} - {req.failure}"))

        urls_to_test = [
            "https://claude.ai/",
            "https://www.anthropic.com/",
        ]

        for url in urls_to_test:
            print(f"\n{'='*60}")
            print(f"Testing: {url}")
            print('='*60)

            try:
                # より短いタイムアウトで試す
                response = page.goto(url, timeout=20000, wait_until="commit")

                print(f"Response status: {response.status if response else 'None'}")
                print(f"Current URL: {page.url}")

                # 少し待つ
                time.sleep(2)

                # 情報を取得
                try:
                    title = page.title()
                    print(f"Title: {title}")
                except:
                    print("Could not get title")

                # スクリーンショット
                screenshot_name = url.replace('https://', '').replace('/', '_').replace('.', '_')
                page.screenshot(path=f"/home/user/Kagami/investigation/playwright/{screenshot_name}.png")
                print(f"✅ Screenshot saved: {screenshot_name}.png")

            except Exception as e:
                print(f"❌ Error: {e}")

                # エラー時もスクリーンショット
                try:
                    screenshot_name = url.replace('https://', '').replace('/', '_').replace('.', '_') + '_error'
                    page.screenshot(path=f"/home/user/Kagami/investigation/playwright/{screenshot_name}.png")
                    print(f"Error screenshot: {screenshot_name}.png")
                except:
                    pass

        browser.close()


def test_with_longer_timeout():
    """より長いタイムアウトでテスト"""
    print("\n" + "="*60)
    print("Test with longer timeout (60s)")
    print("="*60)

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=[
                '--disable-dev-shm-usage',
                '--single-process',
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--proxy-server=http://127.0.0.1:8888',
                f'--ignore-certificate-errors-spki-list={CA_SPKI_HASH}',
                '--ignore-certificate-errors',
                '--disable-gpu',
            ]
        )

        context = browser.new_context(ignore_https_errors=True)
        page = context.new_page()

        url = "https://claude.ai/"
        print(f"\nTrying {url} with 60s timeout...")

        try:
            page.goto(url, timeout=60000, wait_until="commit")
            print("✅ Navigation completed")

            time.sleep(3)
            print(f"URL: {page.url}")

            try:
                title = page.title()
                print(f"Title: {title}")
            except:
                print("Could not get title")

            page.screenshot(path="/home/user/Kagami/investigation/playwright/claude_60s.png")
            print("✅ Screenshot saved")

        except Exception as e:
            print(f"❌ Still failed: {e}")

        browser.close()


if __name__ == "__main__":
    start_proxy()

    # Test 1: ルートとanthropicサイト
    test_claude_ai_root()

    # Test 2: 長いタイムアウト
    test_with_longer_timeout()

    print("\n" + "="*60)
    print("Done")
    print("="*60)
