#!/usr/bin/env python3
"""
Test Local Proxy with Chromium SSL Flags
Chromiumの証明書関連フラグをテスト
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

    print("Waiting for proxy server to start...")
    time.sleep(2)
    print("Proxy server ready\n")


def test_with_ignore_all_cert_errors():
    """すべての証明書エラーを無視"""
    print("="*60)
    print("Test: Ignore ALL Certificate Errors")
    print("="*60)

    try:
        with sync_playwright() as p:
            print("\nLaunching Chromium with aggressive cert bypass...")

            browser = p.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--proxy-server=http://127.0.0.1:8888',
                    # 証明書エラーを完全に無視
                    '--ignore-certificate-errors',
                    '--ignore-certificate-errors-spki-list',
                    '--allow-insecure-localhost',
                    '--disable-web-security',
                    '--reduce-security-for-testing',
                    # SSL関連のフラグ
                    '--disable-features=CertificateTransparencyEnforcement',
                ],
            )

            # コンテキストでも証明書エラーを無視
            context = browser.new_context(
                ignore_https_errors=True
            )

            page = context.new_page()

            print("Testing: https://example.com")
            page.goto("https://example.com", timeout=30000, wait_until="domcontentloaded")

            title = page.title()
            url = page.url

            print(f"\n✅ SUCCESS!")
            print(f"   Title: {title}")
            print(f"   URL: {url}")

            browser.close()
            return True

    except Exception as e:
        print(f"\n❌ FAILED: {e}")
        return False


def test_claude_ai_aggressive():
    """Claude AIに最も積極的な設定でアクセス"""
    print("="*60)
    print("Test: Claude AI with Aggressive Settings")
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
                    '--ignore-certificate-errors-spki-list',
                    '--allow-insecure-localhost',
                    '--disable-web-security',
                    '--reduce-security-for-testing',
                    '--disable-features=CertificateTransparencyEnforcement',
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
            screenshot_path = "/home/user/Kagami/investigation/playwright/claude_ai_aggressive.png"
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
    print("Local Proxy + Aggressive Certificate Bypass")
    print("="*60)
    print()

    # ローカルプロキシサーバーを起動
    start_proxy_in_background(port=8888)

    # Test 1: example.com
    print("\n" + "="*60)
    print("TEST 1: Example.com")
    print("="*60)
    result1 = test_with_ignore_all_cert_errors()

    # 少し待つ
    time.sleep(2)

    # Test 2: Claude AI
    print("\n" + "="*60)
    print("TEST 2: Claude AI Code")
    print("="*60)
    result2 = test_claude_ai_aggressive()

    # Summary
    print("\n" + "="*60)
    print("FINAL RESULT")
    print("="*60)

    print(f"\nExample.com: {'✅ Success' if result1 else '❌ Failed'}")
    print(f"Claude AI: {'✅ Success' if result2 else '❌ Failed'}")

    if result1 and result2:
        print("\n🎉🎉🎉 完全成功！🎉🎉🎉")
        print("\n解決策:")
        print("  1. ローカルプロキシサーバー (src/local_proxy.py)")
        print("  2. Chromiumフラグ:")
        print("     --ignore-certificate-errors")
        print("     --ignore-certificate-errors-spki-list")
        print("     --disable-web-security")
        print("     --reduce-security-for-testing")
        print("  3. Playwright Context:")
        print("     ignore_https_errors=True")
        print("\n次のステップ: ログイン・セッション永続化の実装")
    elif result1:
        print("\n部分的成功: example.comはアクセスできました")
    else:
        print("\n完全失敗: さらなる調査が必要です")


if __name__ == "__main__":
    main()
