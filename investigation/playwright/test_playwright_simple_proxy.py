#!/usr/bin/env python3
"""
Playwright with Simple Proxy Configuration
シンプルなプロキシアドレスでテスト
"""
from playwright.sync_api import sync_playwright

def test_with_simple_proxy(proxy_server):
    """シンプルなプロキシ設定でテスト"""
    print(f"\n{'='*60}")
    print(f"Testing with proxy: {proxy_server}")
    print(f"{'='*60}")

    test_sites = [
        ("https://example.com", "Example.com"),
        ("https://api.github.com", "GitHub API"),
        ("https://claude.ai", "Claude.ai"),
    ]

    results = {}

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    f'--proxy-server={proxy_server}',
                ]
            )

            page = browser.new_page()

            for url, name in test_sites:
                try:
                    print(f"\n  Testing: {name}")
                    page.goto(url, timeout=15000)
                    print(f"    ✅ SUCCESS - {page.title()[:50]}")
                    results[name] = True
                except Exception as e:
                    error = str(e).split('\n')[0][:100]
                    print(f"    ❌ FAILED - {error}")
                    results[name] = False

            browser.close()

    except Exception as e:
        print(f"  ❌ Browser launch failed: {e}")
        return {}

    return results


def main():
    print("="*60)
    print("Playwright Simple Proxy Test")
    print("="*60)

    # テストする各種プロキシ設定
    proxy_configs = [
        "http://21.0.0.123:15004",
        "21.0.0.123:15004",
        "http://127.0.0.1:15004",  # ローカルホストの場合
    ]

    all_results = {}

    for proxy in proxy_configs:
        results = test_with_simple_proxy(proxy)
        if results:
            all_results[proxy] = results

    # サマリー
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)

    best_proxy = None
    best_score = 0

    for proxy, results in all_results.items():
        success = sum(1 for v in results.values() if v)
        total = len(results)
        print(f"\n{proxy}: {success}/{total}")
        for site, ok in results.items():
            status = "✅" if ok else "❌"
            print(f"  {status} {site}")

        if success > best_score:
            best_score = success
            best_proxy = proxy

    if best_proxy and best_score > 0:
        print(f"\n✅ Best proxy: {best_proxy} ({best_score} sites)")
    else:
        print(f"\n❌ No working proxy configuration found")
        print("\nPossible reasons:")
        print("  1. Chromium doesn't support the authentication format")
        print("  2. Proxy requires special headers or credentials")
        print("  3. Browser subprocess cannot inherit proxy environment")


if __name__ == "__main__":
    main()
