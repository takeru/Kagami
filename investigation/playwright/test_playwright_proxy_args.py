#!/usr/bin/env python3
"""
Playwright with Proxy via Command Line Args
Chromiumの起動引数で直接プロキシを指定
"""
from playwright.sync_api import sync_playwright
import os

def test_with_proxy_args():
    """Chromiumの起動引数でプロキシを指定"""
    print("="*60)
    print("Playwright with Proxy Command Line Arguments")
    print("="*60)

    # 環境変数からプロキシを取得
    proxy_url = os.environ.get('HTTPS_PROXY') or os.environ.get('HTTP_PROXY')
    print(f"\nProxy from environment: {proxy_url}")

    if not proxy_url:
        print("❌ No proxy found in environment variables")
        return

    test_sites = [
        ("https://example.com", "Example.com"),
        ("https://api.github.com", "GitHub API"),
        ("https://httpbin.org/get", "HTTPBin"),
        ("https://claude.ai", "Claude.ai"),
        ("https://claude.ai/code/", "Claude Code"),
    ]

    results = {}

    print("\n" + "="*60)
    print("TEST: Proxy via --proxy-server argument")
    print("="*60)

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-accelerated-2d-canvas',
                    '--disable-gpu',
                    f'--proxy-server={proxy_url}',  # プロキシを引数で指定
                ]
            )

            page = browser.new_page()

            for url, name in test_sites:
                try:
                    print(f"\nTesting: {name}")
                    print(f"  URL: {url}")
                    page.goto(url, timeout=20000)
                    print(f"  ✅ SUCCESS")
                    print(f"     Final URL: {page.url}")
                    print(f"     Title: {page.title()[:80]}")
                    results[name] = True
                except Exception as e:
                    error_msg = str(e)
                    print(f"  ❌ FAILED")
                    print(f"     Error: {error_msg[:200]}")
                    results[name] = False

            browser.close()

    except Exception as e:
        print(f"\n❌ Browser launch failed: {e}")
        return {}

    # サマリー
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)

    success_count = sum(1 for v in results.values() if v)
    total_count = len(results)

    print(f"\nSuccess rate: {success_count}/{total_count}")
    for name, success in results.items():
        status = "✅" if success else "❌"
        print(f"  {status} {name}")

    if success_count > 0:
        print(f"\n✅ SUCCESS! Playwright can access external HTTPS sites with proxy!")
        print(f"   Working proxy: {proxy_url}")
    else:
        print(f"\n❌ Failed to access HTTPS sites even with proxy arguments")

    return results


if __name__ == "__main__":
    test_with_proxy_args()
