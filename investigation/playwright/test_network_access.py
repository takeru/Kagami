#!/usr/bin/env python3
"""
ネットワークアクセステスト - Playwright編
"""
from playwright.sync_api import sync_playwright
import time

def test_site(page, url, name):
    """指定されたURLへのアクセスをテスト"""
    print(f"\n{'='*60}")
    print(f"Testing: {name}")
    print(f"URL: {url}")
    print(f"{'='*60}")

    try:
        page.goto(url, timeout=15000)
        print(f"✅ SUCCESS")
        print(f"   Final URL: {page.url}")
        print(f"   Title: {page.title()}")
        return True
    except Exception as e:
        print(f"❌ FAILED")
        print(f"   Error: {str(e)[:200]}")
        return False

def main():
    # テストするサイトのリスト
    test_sites = [
        ("https://example.com", "Example.com"),
        ("https://www.google.com", "Google"),
        ("https://github.com", "GitHub"),
        ("https://api.github.com", "GitHub API"),
        ("https://httpbin.org/get", "HTTPBin"),
        ("https://www.anthropic.com", "Anthropic"),
        ("https://claude.ai", "Claude.ai"),
        ("https://claude.ai/code/", "Claude Code"),
        ("http://example.com", "Example.com (HTTP)"),
    ]

    results = {}

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=[
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-accelerated-2d-canvas',
                '--disable-gpu'
            ]
        )

        page = browser.new_page()

        for url, name in test_sites:
            results[name] = test_site(page, url, name)
            time.sleep(1)

        browser.close()

    # サマリー
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")

    success_count = sum(1 for v in results.values() if v)
    total_count = len(results)

    for name, success in results.items():
        status = "✅" if success else "❌"
        print(f"{status} {name}")

    print(f"\nTotal: {success_count}/{total_count} successful")

if __name__ == "__main__":
    main()
