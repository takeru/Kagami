#!/usr/bin/env python3
"""
Playwright with Proxy Authentication
プロキシ認証情報を明示的に設定
"""
from playwright.sync_api import sync_playwright
import os
from urllib.parse import urlparse

def parse_proxy_url(proxy_url):
    """プロキシURLをパースして認証情報を抽出"""
    parsed = urlparse(proxy_url)

    # http://username:password@host:port の形式
    return {
        'server': f"{parsed.scheme}://{parsed.hostname}:{parsed.port}",
        'username': parsed.username,
        'password': parsed.password,
        'hostname': parsed.hostname,
        'port': parsed.port,
    }


def test_with_proxy_auth():
    """プロキシ認証を明示的に設定してテスト"""
    print("="*60)
    print("Playwright with Proxy Authentication")
    print("="*60)

    # 環境変数からプロキシを取得
    proxy_url = os.environ.get('HTTPS_PROXY') or os.environ.get('HTTP_PROXY')

    if not proxy_url:
        print("❌ No proxy found in environment variables")
        return

    print(f"\nOriginal proxy URL: {proxy_url[:100]}...")

    # プロキシURLをパース
    proxy_info = parse_proxy_url(proxy_url)
    print(f"\nParsed proxy info:")
    print(f"  Server: {proxy_info['server']}")
    print(f"  Username: {proxy_info['username'][:50]}...")
    print(f"  Password: {proxy_info['password'][:50] if proxy_info['password'] else 'None'}...")
    print(f"  Hostname: {proxy_info['hostname']}")
    print(f"  Port: {proxy_info['port']}")

    test_sites = [
        ("https://example.com", "Example.com"),
        ("https://api.github.com", "GitHub API"),
        ("https://httpbin.org/get", "HTTPBin"),
        ("https://claude.ai", "Claude.ai"),
    ]

    results = {}

    print("\n" + "="*60)
    print("TEST: Proxy with explicit authentication")
    print("="*60)

    try:
        with sync_playwright() as p:
            # Playwright の proxy パラメータで認証情報を設定
            browser = p.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                ],
                proxy={
                    "server": proxy_info['server'],
                    "username": proxy_info['username'],
                    "password": proxy_info['password'],
                }
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
                    print(f"       Final URL: {page.url}")
                    results[name] = True
                except Exception as e:
                    error = str(e).split('\n')[0]
                    print(f"    ❌ FAILED")
                    print(f"       Error: {error[:150]}")
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
        print(f"\n🎉 SUCCESS! Playwright can access HTTPS sites with authenticated proxy!")
        print(f"\nWorking configuration:")
        print(f"  Server: {proxy_info['server']}")
        print(f"  Authentication: Yes (JWT-based)")
    else:
        print(f"\n❌ Failed with authenticated proxy")
        print(f"\nPossible issues:")
        print(f"  1. JWT authentication might not be compatible with Chromium")
        print(f"  2. Proxy might require additional headers")
        print(f"  3. Certificate validation issues")

    return results


if __name__ == "__main__":
    test_with_proxy_auth()
