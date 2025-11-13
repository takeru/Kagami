#!/usr/bin/env python3
"""
claude.ai/codeへのアクセステスト
ローカルプロキシ + CA SPKI Hash を使用
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
    """プロキシサーバーをバックグラウンドで起動"""
    def run():
        run_proxy_server(port=8888)

    t = threading.Thread(target=run, daemon=True)
    t.start()
    print("Starting local proxy...")
    time.sleep(2)
    print("Proxy ready\n")


def test_claude_ai():
    """claude.ai/codeへアクセス"""
    print("="*60)
    print("Claude AI Code Access Test")
    print("="*60)

    screenshot_dir = "/home/user/Kagami/investigation/playwright"

    with sync_playwright() as p:
        print("\nLaunching Chromium...")
        browser = p.chromium.launch(
            headless=True,
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
                '--allow-insecure-localhost',
                '--disable-web-security',
                # パフォーマンス最適化
                '--disable-gpu',
                '--disable-accelerated-2d-canvas',
            ]
        )
        print("✅ Browser launched")

        context = browser.new_context(
            ignore_https_errors=True,
            viewport={'width': 1280, 'height': 720}
        )
        page = context.new_page()
        print("✅ Page created")

        # まず簡単なサイトでテスト
        print("\n" + "="*60)
        print("Test 1: example.com (baseline)")
        print("="*60)
        try:
            page.goto("https://example.com", timeout=10000)
            print(f"✅ Title: {page.title()}")
            page.screenshot(path=f"{screenshot_dir}/test_example.png")
            print(f"✅ Screenshot saved: test_example.png\n")
        except Exception as e:
            print(f"❌ Failed: {e}\n")

        # Claude AIにアクセス
        print("="*60)
        print("Test 2: claude.ai/code")
        print("="*60)
        try:
            print("Navigating to https://claude.ai/code...")

            # wait_until="networkidle" を使わずに、より柔軟に
            page.goto("https://claude.ai/code", timeout=30000, wait_until="commit")

            print("✅ Navigation started")

            # 少し待つ
            time.sleep(3)

            # 現在のURLとタイトルを取得
            url = page.url
            print(f"Current URL: {url}")

            try:
                title = page.title()
                print(f"Title: {title}")
            except:
                print("Could not get title")

            # スクリーンショットを保存
            screenshot_path = f"{screenshot_dir}/claude_ai_code.png"
            page.screenshot(path=screenshot_path, full_page=True)
            print(f"✅ Screenshot saved: {screenshot_path}")

            # HTMLを少し取得
            try:
                html = page.content()
                print(f"HTML length: {len(html)} bytes")

                # HTMLの一部を保存
                html_path = f"{screenshot_dir}/claude_ai_code.html"
                with open(html_path, 'w', encoding='utf-8') as f:
                    f.write(html)
                print(f"✅ HTML saved: {html_path}")
            except Exception as e:
                print(f"Could not get HTML: {e}")

            print("\n🎉 Test completed!")

        except Exception as e:
            print(f"❌ Failed: {e}")

            # エラー時もスクリーンショット保存を試みる
            try:
                page.screenshot(path=f"{screenshot_dir}/claude_ai_code_error.png")
                print(f"Error screenshot saved")
            except:
                pass

        browser.close()


if __name__ == "__main__":
    start_proxy()
    test_claude_ai()

    print("\n" + "="*60)
    print("スクリーンショットを確認してください:")
    print("  investigation/playwright/test_example.png")
    print("  investigation/playwright/claude_ai_code.png")
    print("="*60)
