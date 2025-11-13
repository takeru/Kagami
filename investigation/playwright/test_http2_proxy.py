#!/usr/bin/env python3
"""
Test HTTP/2 Compatible Local Proxy
HTTP/2対応ローカルプロキシのテスト
"""
import sys
import os
import threading
import time

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.local_proxy_http2 import run_proxy_server
from playwright.sync_api import sync_playwright


def start_proxy_in_background(port=8888):
    """プロキシサーバーをバックグラウンドで起動"""
    def run_proxy():
        run_proxy_server(port=port)

    proxy_thread = threading.Thread(target=run_proxy, daemon=True)
    proxy_thread.start()

    print("Waiting for HTTP/2 proxy server to start...")
    time.sleep(3)
    print("Proxy server ready\n")


def test_example_com():
    """example.comへのアクセステスト"""
    print("="*60)
    print("Test: Example.com with HTTP/2 Proxy")
    print("="*60)

    try:
        with sync_playwright() as p:
            print("\nLaunching Chromium...")

            browser = p.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--proxy-server=http://127.0.0.1:8888',
                    # 証明書エラーを無視
                    '--ignore-certificate-errors',
                    '--ignore-certificate-errors-spki-list',
                    '--disable-web-security',
                ],
            )

            context = browser.new_context(
                ignore_https_errors=True
            )

            page = context.new_page()

            print("Accessing https://example.com...")
            page.goto("https://example.com", timeout=30000, wait_until="domcontentloaded")

            title = page.title()
            url = page.url
            content_preview = page.content()[:200]

            print(f"\n✅ SUCCESS!")
            print(f"   Title: {title}")
            print(f"   URL: {url}")
            print(f"   Content preview: {content_preview}...")

            browser.close()
            return True

    except Exception as e:
        print(f"\n❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_multiple_sites():
    """複数サイトへのアクセステスト"""
    print("="*60)
    print("Test: Multiple Sites with HTTP/2 Proxy")
    print("="*60)

    test_sites = [
        ("https://example.com", "Example.com"),
        ("https://www.google.com", "Google"),
        ("https://api.github.com", "GitHub API"),
    ]

    results = {}

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--proxy-server=http://127.0.0.1:8888',
                    '--ignore-certificate-errors',
                    '--disable-web-security',
                ],
            )

            context = browser.new_context(
                ignore_https_errors=True
            )

            page = context.new_page()

            for url, name in test_sites:
                try:
                    print(f"\nTesting: {name}")
                    print(f"  URL: {url}")

                    page.goto(url, timeout=30000, wait_until="domcontentloaded")

                    title = page.title()
                    final_url = page.url

                    print(f"  ✅ SUCCESS!")
                    print(f"     Title: {title[:60]}")
                    print(f"     Final URL: {final_url[:80]}")

                    results[name] = True

                except Exception as e:
                    error_msg = str(e).split('\n')[0][:150]
                    print(f"  ❌ FAILED")
                    print(f"     Error: {error_msg}")

                    results[name] = False

            browser.close()

    except Exception as e:
        print(f"\n❌ Browser launch failed: {e}")
        return {}

    return results


def test_claude_ai():
    """Claude AIへのアクセステスト"""
    print("="*60)
    print("Test: Claude AI with HTTP/2 Proxy")
    print("="*60)

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--proxy-server=http://127.0.0.1:8888',
                    '--ignore-certificate-errors',
                    '--disable-web-security',
                ],
            )

            context = browser.new_context(
                ignore_https_errors=True
            )

            page = context.new_page()

            print("\nAccessing https://claude.ai/code/...")

            page.goto("https://claude.ai/code/", timeout=30000, wait_until="domcontentloaded")

            title = page.title()
            url = page.url

            print(f"\n✅ SUCCESS!")
            print(f"   Title: {title}")
            print(f"   URL: {url}")

            # スクリーンショット保存
            screenshot_path = "/home/user/Kagami/investigation/playwright/claude_ai_http2.png"
            page.screenshot(path=screenshot_path, full_page=True)
            print(f"   Screenshot: {screenshot_path}")

            browser.close()
            return True

    except Exception as e:
        print(f"\n❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    print("="*60)
    print("HTTP/2 Local Proxy + Playwright Test")
    print("="*60)
    print()

    # ローカルプロキシサーバーを起動
    start_proxy_in_background(port=8888)

    # Test 1: example.com
    print("\n" + "="*60)
    print("TEST 1: Example.com")
    print("="*60)
    result1 = test_example_com()

    time.sleep(2)

    # Test 2: 複数サイト
    print("\n" + "="*60)
    print("TEST 2: Multiple Sites")
    print("="*60)
    result2 = test_multiple_sites()

    time.sleep(2)

    # Test 3: Claude AI
    print("\n" + "="*60)
    print("TEST 3: Claude AI Code")
    print("="*60)
    result3 = test_claude_ai()

    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)

    print(f"\nExample.com: {'✅ Success' if result1 else '❌ Failed'}")

    if result2:
        success_count = sum(1 for v in result2.values() if v)
        total_count = len(result2)
        print(f"\nMultiple Sites: {success_count}/{total_count} successful")
        for site, ok in result2.items():
            status = "✅" if ok else "❌"
            print(f"  {status} {site}")

    print(f"\nClaude AI: {'✅ Success' if result3 else '❌ Failed'}")

    # Final conclusion
    print("\n" + "="*60)
    print("CONCLUSION")
    print("="*60)

    if result1 and result3:
        print("\n🎉🎉🎉 完全成功！🎉🎉🎉")
        print("\n✅ HTTP/2対応プロキシでPlaywrightからHTTPSアクセスが可能になりました！")
        print("\n実装した解決策:")
        print("  1. httpxライブラリを使用（HTTP/2ネイティブサポート）")
        print("  2. src/local_proxy_http2.py")
        print("  3. HTTPリクエスト: httpxが自動処理")
        print("  4. CONNECTトンネル: socketレベルのトンネリング")
        print("\nアーキテクチャ:")
        print("  Chromium")
        print("      ↓")
        print("  localhost:8888 (HTTP/2 proxy with httpx)")
        print("      ↓ (JWT authentication)")
        print("  upstream JWT proxy")
        print("      ↓")
        print("  インターネット")
        print("\n次のステップ:")
        print("  ✓ claude.ai/codeへのログイン実装")
        print("  ✓ セッション永続化（storage_state API）")
        print("  ✓ Cookie管理")

    elif result1:
        print("\n🎉 部分的成功！")
        print("\nexample.comへのアクセスは成功しました")
        print("Claude AIへのアクセスは要調査")

    else:
        print("\n❌ HTTP/2プロキシでも失敗しました")
        print("   さらなるデバッグが必要です")


if __name__ == "__main__":
    main()
