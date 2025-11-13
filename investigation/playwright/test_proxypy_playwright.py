#!/usr/bin/env python3
"""
proxy.pyを使ったPlaywrightテスト
ProxyPoolPluginで上流JWT認証プロキシに転送
"""
import subprocess
import time
import os
from playwright.sync_api import sync_playwright


def start_proxypy_server(port=8891):
    """proxy.pyサーバーをバックグラウンドで起動"""
    upstream_proxy = os.environ.get('HTTPS_PROXY') or os.environ.get('HTTP_PROXY')
    if not upstream_proxy:
        raise ValueError("HTTPS_PROXY environment variable not set")

    print("="*60)
    print("Starting proxy.py with ProxyPoolPlugin")
    print("="*60)
    print(f"Upstream proxy: {upstream_proxy[:80]}...")
    print(f"Local proxy: 127.0.0.1:{port}")
    print()

    cmd = [
        'uv', 'run', 'proxy',
        '--hostname', '127.0.0.1',
        '--port', str(port),
        '--plugins', 'proxy.plugin.proxy_pool.ProxyPoolPlugin',
        '--proxy-pool', upstream_proxy,
    ]

    # プロキシをバックグラウンドで起動
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    # 起動を待つ
    print("Waiting for proxy server to start...")
    time.sleep(5)
    print("Proxy server ready!\n")

    return process


def test_example_com():
    """example.comへのアクセステスト"""
    print("="*60)
    print("TEST 1: Example.com")
    print("="*60)

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--proxy-server=http://127.0.0.1:8891',
                    '--ignore-certificate-errors',
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
            content = page.content()[:200]

            print(f"\n✅ SUCCESS!")
            print(f"   Title: {title}")
            print(f"   URL: {url}")
            print(f"   Content preview: {content}...")
            print()

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
    print("TEST 2: Multiple HTTPS Sites")
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
                    '--proxy-server=http://127.0.0.1:8891',
                    '--ignore-certificate-errors',
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

                    print(f"  ✅ SUCCESS!")
                    print(f"     Title: {title[:60]}")

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
    print("TEST 3: Claude AI Code")
    print("="*60)

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--proxy-server=http://127.0.0.1:8891',
                    '--ignore-certificate-errors',
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
            screenshot_path = "/home/user/Kagami/investigation/playwright/claude_ai_proxypy_success.png"
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
    print("proxy.py + Playwright Integration Test")
    print("="*60)
    print()

    # proxy.pyサーバーを起動
    proxy_process = None
    try:
        proxy_process = start_proxypy_server(port=8891)

        # Test 1: example.com
        result1 = test_example_com()
        time.sleep(2)

        # Test 2: 複数サイト
        result2 = test_multiple_sites()
        time.sleep(2)

        # Test 3: Claude AI
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
        print("FINAL CONCLUSION")
        print("="*60)

        if result1 and result3:
            print("\n🎉🎉🎉 完全成功！！！🎉🎉🎉")
            print("\n✅ proxy.pyを使ってPlaywrightからHTTPSアクセスが可能になりました！")
            print("\n実装した解決策:")
            print("  1. proxy.pyライブラリ（HTTP/2ネイティブサポート）")
            print("  2. ProxyPoolPluginで上流JWT認証プロキシに転送")
            print("  3. JWT認証情報はURLに含める")
            print("  4. Chromiumフラグ: --ignore-certificate-errors")
            print("\nアーキテクチャ:")
            print("  Chromium")
            print("      ↓")
            print("  localhost:8891 (proxy.py + ProxyPoolPlugin)")
            print("      ↓ (JWT authentication)")
            print("  upstream JWT proxy")
            print("      ↓")
            print("  インターネット")
            print("\n次のステップ:")
            print("  ✓ claude.ai/codeへのログイン実装")
            print("  ✓ セッション永続化（storage_state API）")

        elif result1:
            print("\n🎉 部分的成功！")
            print("\nexample.comへのアクセスは成功しました")

        else:
            print("\n❌ 失敗しました")

    finally:
        # プロキシプロセスを終了
        if proxy_process:
            print("\n\nStopping proxy server...")
            proxy_process.terminate()
            try:
                proxy_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proxy_process.kill()
            print("Proxy server stopped.")


if __name__ == "__main__":
    main()
