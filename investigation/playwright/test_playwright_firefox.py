#!/usr/bin/env python3
"""
Playwright Firefox & WebKit Proxy Test
Chromium以外のブラウザエンジンでJWT認証プロキシをテスト
"""
from playwright.sync_api import sync_playwright
import os

def test_browser_with_proxy(browser_type_name, playwright_instance):
    """指定されたブラウザでプロキシアクセスをテスト"""
    print(f"\n{'='*60}")
    print(f"Testing: {browser_type_name.upper()}")
    print(f"{'='*60}")

    # 環境変数からプロキシを取得
    proxy_url = os.environ.get('HTTPS_PROXY') or os.environ.get('HTTP_PROXY')

    if not proxy_url:
        print("❌ No proxy found in environment variables")
        return {}

    print(f"Proxy: {proxy_url[:80]}...")

    test_sites = [
        ("https://example.com", "Example.com"),
        ("https://api.github.com", "GitHub API"),
        ("https://claude.ai", "Claude.ai"),
        ("http://example.com", "Example.com (HTTP)"),
    ]

    results = {}

    try:
        # ブラウザタイプを取得
        if browser_type_name == 'chromium':
            browser_type = playwright_instance.chromium
        elif browser_type_name == 'firefox':
            browser_type = playwright_instance.firefox
        elif browser_type_name == 'webkit':
            browser_type = playwright_instance.webkit
        else:
            print(f"❌ Unknown browser type: {browser_type_name}")
            return {}

        # 環境変数のプロキシをそのまま使用
        from urllib.parse import urlparse
        parsed = urlparse(proxy_url)

        # プロキシ設定を構築
        proxy_config = {
            "server": f"{parsed.scheme}://{parsed.hostname}:{parsed.port}",
        }

        # 認証情報がある場合は追加
        if parsed.username and parsed.password:
            proxy_config["username"] = parsed.username
            proxy_config["password"] = parsed.password

        print(f"\nProxy config:")
        print(f"  Server: {proxy_config['server']}")
        if 'username' in proxy_config:
            print(f"  Username: {proxy_config['username'][:50]}...")
            print(f"  Password: {proxy_config['password'][:50]}...")

        # ブラウザを起動
        browser = browser_type.launch(
            headless=True,
            proxy=proxy_config
        )

        page = browser.new_page()

        for url, name in test_sites:
            try:
                print(f"\n  Testing: {name}")
                print(f"    URL: {url}")
                page.goto(url, timeout=20000)
                title = page.title()
                print(f"    ✅ SUCCESS")
                print(f"       Title: {title[:60]}")
                results[name] = True
            except Exception as e:
                error = str(e).split('\n')[0][:150]
                print(f"    ❌ FAILED")
                print(f"       Error: {error}")
                results[name] = False

        browser.close()

    except Exception as e:
        print(f"\n❌ Browser launch failed: {e}")
        return {}

    return results


def main():
    print("="*60)
    print("Playwright Multi-Browser Proxy Test")
    print("="*60)
    print("\nTesting different browser engines with JWT proxy:")
    print("- Chromium: Blink engine (Google)")
    print("- Firefox: Gecko engine (Mozilla)")
    print("- WebKit: WebKit engine (Apple)")

    all_results = {}

    with sync_playwright() as p:
        # Test 1: Chromium (baseline)
        print("\n" + "="*60)
        print("TEST 1: CHROMIUM (Baseline)")
        print("="*60)
        all_results['Chromium'] = test_browser_with_proxy('chromium', p)

        # Test 2: Firefox
        print("\n" + "="*60)
        print("TEST 2: FIREFOX")
        print("="*60)
        all_results['Firefox'] = test_browser_with_proxy('firefox', p)

        # Test 3: WebKit
        print("\n" + "="*60)
        print("TEST 3: WEBKIT")
        print("="*60)
        all_results['WebKit'] = test_browser_with_proxy('webkit', p)

    # サマリー
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)

    for browser, results in all_results.items():
        if results:
            success = sum(1 for v in results.values() if v)
            total = len(results)
            print(f"\n{browser}: {success}/{total} successful")
            for site, ok in results.items():
                status = "✅" if ok else "❌"
                print(f"  {status} {site}")
        else:
            print(f"\n{browser}: Failed to initialize")

    # 結論
    print("\n" + "="*60)
    print("CONCLUSION")
    print("="*60)

    best_browser = None
    best_score = 0

    for browser, results in all_results.items():
        if results:
            # HTTPSサイトのみカウント（HTTPは除外）
            https_results = {k: v for k, v in results.items() if 'HTTP)' not in k}
            score = sum(1 for v in https_results.values() if v)
            if score > best_score:
                best_score = score
                best_browser = browser

    if best_browser and best_score > 0:
        print(f"\n🎉 SUCCESS! {best_browser} can access HTTPS sites!")
        print(f"   HTTPS success rate: {best_score} sites")
        print(f"\n   → {best_browser}はJWT認証プロキシに対応しています！")
    else:
        print(f"\n❌ すべてのブラウザでHTTPSアクセスに失敗しました")
        print(f"   すべてのブラウザエンジンがJWT認証プロキシに未対応です")


if __name__ == "__main__":
    main()
