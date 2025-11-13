#!/usr/bin/env python3
"""
Playwright with Proxy Settings Test
プロキシ設定を追加してHTTPSアクセスをテスト
"""
from playwright.sync_api import sync_playwright
import os

# 環境変数からプロキシを確認
print("Environment Variables:")
print(f"HTTP_PROXY: {os.environ.get('HTTP_PROXY', 'Not set')}")
print(f"HTTPS_PROXY: {os.environ.get('HTTPS_PROXY', 'Not set')}")
print(f"http_proxy: {os.environ.get('http_proxy', 'Not set')}")
print(f"https_proxy: {os.environ.get('https_proxy', 'Not set')}")
print()

def test_with_proxy(proxy_url, test_name):
    """プロキシ設定でテスト"""
    print(f"\n{'='*60}")
    print(f"Test: {test_name}")
    print(f"Proxy: {proxy_url}")
    print(f"{'='*60}")

    test_sites = [
        ("https://example.com", "Example.com"),
        ("https://api.github.com", "GitHub API"),
        ("https://claude.ai", "Claude.ai"),
        ("https://claude.ai/code/", "Claude Code"),
    ]

    results = {}

    try:
        with sync_playwright() as p:
            # プロキシ設定を追加
            browser = p.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-accelerated-2d-canvas',
                    '--disable-gpu'
                ],
                proxy={
                    "server": proxy_url
                } if proxy_url else None
            )

            page = browser.new_page()

            for url, name in test_sites:
                try:
                    print(f"\nTesting: {name} ({url})")
                    page.goto(url, timeout=15000)
                    print(f"  ✅ SUCCESS")
                    print(f"     Final URL: {page.url}")
                    print(f"     Title: {page.title()}")
                    results[name] = True
                except Exception as e:
                    print(f"  ❌ FAILED: {str(e)[:150]}")
                    results[name] = False

            browser.close()

    except Exception as e:
        print(f"❌ Browser launch failed: {e}")
        return {}

    return results


def main():
    print("="*60)
    print("Playwright Proxy Configuration Test")
    print("="*60)

    all_results = {}

    # Test 1: プロキシなし（ベースライン）
    print("\n" + "="*60)
    print("TEST 1: No Proxy (Baseline)")
    print("="*60)
    results_no_proxy = test_with_proxy(None, "No Proxy")
    all_results["No Proxy"] = results_no_proxy

    # Test 2: 検出されたプロキシ（HTTP）
    print("\n" + "="*60)
    print("TEST 2: Detected Proxy (HTTP)")
    print("="*60)
    results_http_proxy = test_with_proxy("http://21.0.0.123:15004", "HTTP Proxy")
    all_results["HTTP Proxy"] = results_http_proxy

    # Test 3: 検出されたプロキシ（HTTPS）
    print("\n" + "="*60)
    print("TEST 3: Detected Proxy (HTTPS)")
    print("="*60)
    results_https_proxy = test_with_proxy("https://21.0.0.123:15004", "HTTPS Proxy")
    all_results["HTTPS Proxy"] = results_https_proxy

    # Test 4: 環境変数のプロキシ
    http_proxy = os.environ.get('HTTP_PROXY') or os.environ.get('http_proxy')
    if http_proxy:
        print("\n" + "="*60)
        print("TEST 4: Environment Variable Proxy")
        print("="*60)
        results_env_proxy = test_with_proxy(http_proxy, "Environment Proxy")
        all_results["Env Proxy"] = results_env_proxy

    # サマリー
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)

    for test_name, results in all_results.items():
        if results:
            success_count = sum(1 for v in results.values() if v)
            total_count = len(results)
            print(f"\n{test_name}: {success_count}/{total_count} successful")
            for site, success in results.items():
                status = "✅" if success else "❌"
                print(f"  {status} {site}")
        else:
            print(f"\n{test_name}: Failed to initialize")

    # 結論
    print("\n" + "="*60)
    print("CONCLUSION")
    print("="*60)

    best_config = None
    best_score = 0

    for test_name, results in all_results.items():
        if results:
            score = sum(1 for v in results.values() if v)
            if score > best_score:
                best_score = score
                best_config = test_name

    if best_config and best_score > 0:
        print(f"✅ Best configuration: {best_config} ({best_score} sites accessible)")
    else:
        print("❌ No proxy configuration worked for HTTPS sites")


if __name__ == "__main__":
    main()
