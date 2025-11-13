#!/usr/bin/env python3
"""
Test Local Proxy Server with Playwright
ローカルプロキシサーバー経由でPlaywrightのHTTPSアクセスをテスト
"""
import sys
import os
import threading
import time

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.local_proxy import run_proxy_server
from playwright.sync_api import sync_playwright


def start_proxy_in_background(port=8888):
    """プロキシサーバーをバックグラウンドで起動"""
    def run_proxy():
        run_proxy_server(port=port)

    proxy_thread = threading.Thread(target=run_proxy, daemon=True)
    proxy_thread.start()

    # プロキシサーバーの起動を待つ
    print("Waiting for proxy server to start...")
    time.sleep(2)
    print("Proxy server should be running now\n")


def test_playwright_with_local_proxy():
    """ローカルプロキシ経由でPlaywrightをテスト"""
    print("="*60)
    print("Testing Playwright with Local Proxy")
    print("="*60)

    test_sites = [
        ("https://example.com", "Example.com"),
        ("https://api.github.com", "GitHub API"),
        ("https://claude.ai", "Claude.ai"),
        ("http://example.com", "Example.com (HTTP)"),
    ]

    results = {}

    try:
        with sync_playwright() as p:
            print("\nLaunching Chromium with local proxy...")
            browser = p.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                ],
                proxy={
                    "server": "http://127.0.0.1:8888"
                }
            )

            print("✅ Browser launched successfully\n")

            page = browser.new_page()

            for url, name in test_sites:
                try:
                    print(f"Testing: {name}")
                    print(f"  URL: {url}")

                    page.goto(url, timeout=30000)

                    title = page.title()
                    final_url = page.url

                    print(f"  ✅ SUCCESS!")
                    print(f"     Title: {title[:60]}")
                    print(f"     Final URL: {final_url[:80]}")
                    print()

                    results[name] = True

                except Exception as e:
                    error_msg = str(e).split('\n')[0][:150]
                    print(f"  ❌ FAILED")
                    print(f"     Error: {error_msg}")
                    print()

                    results[name] = False

            browser.close()

    except Exception as e:
        print(f"\n❌ Browser launch or test failed: {e}")
        return {}

    return results


def test_claude_ai_access():
    """Claude AIへのアクセスをテスト"""
    print("="*60)
    print("Testing Claude AI Access")
    print("="*60)

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                ],
                proxy={
                    "server": "http://127.0.0.1:8888"
                }
            )

            page = browser.new_page()

            print("\nAccessing https://claude.ai/code/...")

            page.goto("https://claude.ai/code/", timeout=30000)

            # ページが読み込まれるまで待つ
            page.wait_for_load_state("domcontentloaded")

            title = page.title()
            url = page.url

            print(f"\n✅ SUCCESS!")
            print(f"   Title: {title}")
            print(f"   URL: {url}")

            # ページのスクリーンショットを保存
            screenshot_path = "/home/user/Kagami/investigation/playwright/claude_ai_screenshot.png"
            page.screenshot(path=screenshot_path)
            print(f"   Screenshot saved to: {screenshot_path}")

            browser.close()
            return True

    except Exception as e:
        print(f"\n❌ FAILED: {e}")
        return False


def main():
    print("="*60)
    print("Local Proxy + Playwright Integration Test")
    print("="*60)
    print()

    # 環境変数チェック
    upstream_proxy = os.environ.get('HTTPS_PROXY') or os.environ.get('HTTP_PROXY')
    if not upstream_proxy:
        print("❌ No upstream proxy configured")
        print("   HTTPS_PROXY or HTTP_PROXY environment variable not set")
        return

    print(f"Upstream proxy: {upstream_proxy[:80]}...")
    print()

    # ローカルプロキシサーバーを起動
    start_proxy_in_background(port=8888)

    # Test 1: 複数サイトへのアクセステスト
    print("\n" + "="*60)
    print("TEST 1: Multiple Sites Access")
    print("="*60)
    results = test_playwright_with_local_proxy()

    # Test 2: Claude AIへのアクセステスト
    print("\n" + "="*60)
    print("TEST 2: Claude AI Access")
    print("="*60)
    claude_result = test_claude_ai_access()

    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)

    if results:
        success_count = sum(1 for v in results.values() if v)
        total_count = len(results)

        print(f"\nMultiple Sites Test: {success_count}/{total_count} successful")
        for site, ok in results.items():
            status = "✅" if ok else "❌"
            print(f"  {status} {site}")

    print(f"\nClaude AI Access: {'✅ Success' if claude_result else '❌ Failed'}")

    # Conclusion
    print("\n" + "="*60)
    print("CONCLUSION")
    print("="*60)

    https_success = results.get("Example.com", False) or results.get("GitHub API", False) or results.get("Claude.ai", False)

    if https_success or claude_result:
        print("\n🎉 SUCCESS! ローカルプロキシ経由でHTTPSアクセスが可能になりました！")
        print("\n解決策:")
        print("  1. Pythonでローカルプロキシサーバーを起動（標準ライブラリのみ）")
        print("  2. PlaywrightからlocalhoSt:8888に接続")
        print("  3. ローカルプロキシがJWT認証を処理")
        print("  4. ChromiumはJWT認証を意識せずにHTTPSアクセス可能")
        print("\nアーキテクチャ:")
        print("  Chromium → localhost:8888 (local proxy) → JWT proxy → Internet")

        if claude_result:
            print("\n✅ https://claude.ai/code/ へのアクセスも成功しました！")
            print("   次のステップ: セッション永続化の実装")
    else:
        print("\n❌ ローカルプロキシでも失敗しました")
        print("   デバッグが必要です")


if __name__ == "__main__":
    main()
