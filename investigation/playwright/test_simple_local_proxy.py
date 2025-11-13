#!/usr/bin/env python3
"""
Simple Playwright Test with Local Proxy
最もシンプルなローカルプロキシテスト
"""
from playwright.sync_api import sync_playwright
import time

def test_simple():
    """シンプルなHTTPSテスト"""
    print("="*60)
    print("Simple Playwright + Local Proxy Test")
    print("="*60)
    print("\nローカルプロキシは別途起動済みであることを前提")
    print("ポート: 8888")
    print()

    # プロキシサーバーの起動を待つ
    print("Waiting 2 seconds for proxy...")
    time.sleep(2)

    try:
        with sync_playwright() as p:
            print("\nLaunching Chromium...")

            browser = p.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    # 証明書エラーを無視
                    '--ignore-certificate-errors',
                    # プロキシ設定
                    '--proxy-server=http://127.0.0.1:8888',
                ],
            )

            # コンテキストも証明書エラーを無視
            context = browser.new_context(
                ignore_https_errors=True
            )

            page = context.new_page()

            print("Accessing https://example.com...")

            # タイムアウトを60秒に延長
            page.goto("https://example.com", timeout=60000, wait_until="domcontentloaded")

            title = page.title()
            url = page.url

            print(f"\n✅ SUCCESS!")
            print(f"   Title: {title}")
            print(f"   URL: {url}")

            # HTMLの最初の200文字を表示
            content = page.content()
            print(f"   HTML preview: {content[:200]}...")

            browser.close()
            return True

    except Exception as e:
        print(f"\n❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    result = test_simple()

    print("\n" + "="*60)
    print("RESULT")
    print("="*60)

    if result:
        print("\n🎉 Playwright経由のHTTPSアクセスに成功しました！")
        print("\n解決策:")
        print("  1. Pythonでローカルプロキシサーバーを起動")
        print("     - src/local_proxy.py")
        print("  2. Chromiumの起動オプション:")
        print("     - --ignore-certificate-errors")
        print("     - --proxy-server=http://127.0.0.1:8888")
        print("  3. コンテキスト設定:")
        print("     - ignore_https_errors=True")
        print("\n次のステップ: https://claude.ai/code/ へのアクセステスト")
    else:
        print("\n❌ 失敗しました")


if __name__ == "__main__":
    main()
