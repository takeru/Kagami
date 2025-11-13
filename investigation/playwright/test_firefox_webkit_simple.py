#!/usr/bin/env python3
"""
Simple Firefox & WebKit HTTPS Test
FirefoxとWebKitでHTTPSアクセスをテスト（シンプル版）
"""
from playwright.sync_api import sync_playwright
import os
from urllib.parse import urlparse

def test_browser_simple(browser_name):
    """指定されたブラウザで単一のHTTPSサイトをテスト"""
    print(f"\n{'='*60}")
    print(f"Testing: {browser_name.upper()}")
    print(f"{'='*60}")

    proxy_url = os.environ.get('HTTPS_PROXY') or os.environ.get('HTTP_PROXY')
    if not proxy_url:
        print("❌ No proxy found")
        return None

    # プロキシURLをパース
    parsed = urlparse(proxy_url)
    proxy_config = {
        "server": f"{parsed.scheme}://{parsed.hostname}:{parsed.port}",
    }
    if parsed.username and parsed.password:
        proxy_config["username"] = parsed.username
        proxy_config["password"] = parsed.password

    print(f"Proxy: {proxy_config['server']}")

    try:
        with sync_playwright() as p:
            # ブラウザタイプを選択
            if browser_name == 'firefox':
                browser_type = p.firefox
            elif browser_name == 'webkit':
                browser_type = p.webkit
            else:
                print(f"❌ Unknown browser: {browser_name}")
                return None

            print(f"Launching {browser_name}...")
            browser = browser_type.launch(
                headless=True,
                proxy=proxy_config
            )

            page = browser.new_page()

            # 単一のHTTPSサイトをテスト
            test_url = "https://example.com"
            print(f"\nAccessing: {test_url}")

            try:
                page.goto(test_url, timeout=15000)
                title = page.title()
                print(f"✅ SUCCESS!")
                print(f"   Title: {title}")
                print(f"   URL: {page.url}")
                browser.close()
                return True
            except Exception as e:
                error = str(e).split('\n')[0][:200]
                print(f"❌ FAILED")
                print(f"   Error: {error}")
                browser.close()
                return False

    except Exception as e:
        print(f"❌ Browser launch failed: {e}")
        return None


def main():
    print("="*60)
    print("Firefox & WebKit Simple HTTPS Test")
    print("="*60)

    results = {}

    # Test Firefox
    print("\n" + "="*60)
    print("TEST 1: FIREFOX")
    print("="*60)
    results['Firefox'] = test_browser_simple('firefox')

    # Test WebKit
    print("\n" + "="*60)
    print("TEST 2: WEBKIT")
    print("="*60)
    results['WebKit'] = test_browser_simple('webkit')

    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)

    for browser, success in results.items():
        if success is True:
            print(f"✅ {browser}: HTTPS access successful!")
        elif success is False:
            print(f"❌ {browser}: HTTPS access failed")
        else:
            print(f"⚠️  {browser}: Failed to launch")

    # Conclusion
    print("\n" + "="*60)
    print("CONCLUSION")
    print("="*60)

    success_count = sum(1 for v in results.values() if v is True)

    if success_count > 0:
        successful_browsers = [k for k, v in results.items() if v is True]
        print(f"\n🎉 SUCCESS! The following browsers can access HTTPS:")
        for browser in successful_browsers:
            print(f"   - {browser}")
        print(f"\n   → これらのブラウザはJWT認証プロキシに対応しています！")
    else:
        print(f"\n❌ すべてのブラウザでHTTPSアクセスに失敗しました")
        print(f"   Firefox, WebKit もJWT認証プロキシに未対応です")
        print(f"   Chromiumと同じ制限があります")


if __name__ == "__main__":
    main()
