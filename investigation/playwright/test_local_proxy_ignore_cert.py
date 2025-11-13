#!/usr/bin/env python3
"""
Test Local Proxy with Certificate Validation Disabled
証明書検証を無効化してローカルプロキシをテスト
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
    print("Proxy server ready\n")


def test_with_ignore_certificate_errors():
    """証明書エラーを無視してテスト"""
    print("="*60)
    print("Testing with --ignore-certificate-errors")
    print("="*60)

    test_sites = [
        ("https://example.com", "Example.com"),
        ("https://api.github.com", "GitHub API"),
        ("https://claude.ai/code/", "Claude AI Code"),
    ]

    results = {}

    try:
        with sync_playwright() as p:
            print("\nLaunching Chromium...")
            print("  Proxy: http://127.0.0.1:8888")
            print("  Flags: --ignore-certificate-errors")
            print()

            browser = p.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--ignore-certificate-errors',
                    '--ignore-certificate-errors-spki-list',
                ],
                proxy={
                    "server": "http://127.0.0.1:8888"
                }
            )

            context = browser.new_context(
                ignore_https_errors=True
            )

            page = context.new_page()

            for url, name in test_sites:
                try:
                    print(f"Testing: {name}")
                    print(f"  URL: {url}")

                    page.goto(url, timeout=30000)

                    title = page.title()
                    final_url = page.url

                    print(f"  ✅ SUCCESS!")
                    print(f"     Title: {title[:80]}")
                    print(f"     Final URL: {final_url[:80]}")
                    print()

                    results[name] = True

                except Exception as e:
                    error_msg = str(e).split('\n')[0][:200]
                    print(f"  ❌ FAILED")
                    print(f"     Error: {error_msg}")
                    print()

                    results[name] = False

            browser.close()

    except Exception as e:
        print(f"\n❌ Browser launch failed: {e}")
        return {}

    return results


def test_claude_ai_with_screenshot():
    """Claude AIにアクセスしてスクリーンショットを保存"""
    print("="*60)
    print("Testing Claude AI Access with Screenshot")
    print("="*60)

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--ignore-certificate-errors',
                ],
                proxy={
                    "server": "http://127.0.0.1:8888"
                }
            )

            context = browser.new_context(
                ignore_https_errors=True
            )

            page = context.new_page()

            print("\nAccessing https://claude.ai/code/...")

            page.goto("https://claude.ai/code/", timeout=30000)
            page.wait_for_load_state("domcontentloaded", timeout=10000)

            title = page.title()
            url = page.url

            print(f"\n✅ SUCCESS!")
            print(f"   Title: {title}")
            print(f"   URL: {url}")

            # スクリーンショット保存
            screenshot_path = "/home/user/Kagami/investigation/playwright/claude_ai_access_success.png"
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
    print("Local Proxy + Playwright (Certificate Errors Ignored)")
    print("="*60)
    print()

    # 環境変数チェック
    upstream_proxy = os.environ.get('HTTPS_PROXY') or os.environ.get('HTTP_PROXY')
    if not upstream_proxy:
        print("❌ No upstream proxy configured")
        return

    print(f"Upstream proxy: {upstream_proxy[:80]}...")
    print()

    # ローカルプロキシサーバーを起動
    start_proxy_in_background(port=8888)

    # Test 1: 複数サイトへのアクセス
    print("\n" + "="*60)
    print("TEST 1: Multiple HTTPS Sites")
    print("="*60)
    results = test_with_ignore_certificate_errors()

    # Test 2: Claude AI
    print("\n" + "="*60)
    print("TEST 2: Claude AI Code Access")
    print("="*60)
    claude_result = test_claude_ai_with_screenshot()

    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)

    if results:
        success_count = sum(1 for v in results.values() if v)
        total_count = len(results)

        print(f"\nHTTPS Sites: {success_count}/{total_count} successful")
        for site, ok in results.items():
            status = "✅" if ok else "❌"
            print(f"  {status} {site}")

    print(f"\nClaude AI Code: {'✅ Success' if claude_result else '❌ Failed'}")

    # Conclusion
    print("\n" + "="*60)
    print("FINAL CONCLUSION")
    print("="*60)

    if claude_result:
        print("\n🎉🎉🎉 完全成功！🎉🎉🎉")
        print("\n✅ Playwrightからhttps://claude.ai/code/へのアクセスが可能になりました！")
        print("\n実装した解決策:")
        print("  1. Pythonでローカルプロキシサーバーを作成（標準ライブラリのみ）")
        print("     - src/local_proxy.py")
        print("  2. JWT認証を透過的に処理")
        print("  3. Chromiumは証明書エラーを無視する設定で起動")
        print("\nアーキテクチャ:")
        print("  Chromium (--ignore-certificate-errors)")
        print("      ↓")
        print("  localhost:8888 (Python local proxy)")
        print("      ↓ (JWT authentication)")
        print("  21.0.0.123:15004 (JWT proxy)")
        print("      ↓")
        print("  インターネット")
        print("\n次のステップ:")
        print("  ✓ ログイン操作の実装")
        print("  ✓ セッション永続化（storage_state API）")
        print("  ✓ Cookie管理")

    elif any(results.values()):
        print("\n🎉 部分的成功！")
        print("\n一部のHTTPSサイトにアクセスできましたが、Claude AIは失敗しました")

    else:
        print("\n❌ 証明書エラー無視でも失敗しました")
        print("   さらなるデバッグが必要です")


if __name__ == "__main__":
    main()
