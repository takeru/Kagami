#!/usr/bin/env python3
"""
ローカルプロキシなしでJWT認証プロキシに直接接続するテスト
"""
import os
from playwright.sync_api import sync_playwright

CA_SPKI_HASH = "L+/CZomxifpzjiAVG11S0bTbaTopj+c49s0rBjjSC6A="


def test_direct_proxy():
    """JWT認証プロキシに直接接続"""
    print("="*60)
    print("Direct JWT Proxy Connection Test")
    print("="*60)

    # 環境変数からプロキシURLを取得
    https_proxy = os.environ.get('HTTPS_PROXY')
    if not https_proxy:
        print("❌ HTTPS_PROXY not set")
        return

    print(f"\nProxy URL: {https_proxy[:80]}...")

    # プロキシURLを解析
    # http://username:password@host:port 形式
    import urllib.parse
    parsed = urllib.parse.urlparse(https_proxy)

    print(f"Proxy host: {parsed.hostname}")
    print(f"Proxy port: {parsed.port}")
    print(f"Username: {parsed.username[:30]}...")
    print(f"Password (JWT): jwt_{parsed.password[4:50] if parsed.password.startswith('jwt_') else ''}...")

    test_sites = [
        "https://example.com",
        "https://example.org",
    ]

    try:
        with sync_playwright() as p:
            print("\n" + "="*60)
            print("Launching Chromium with direct proxy...")
            print("="*60)

            # プロキシURLをそのまま使用
            browser = p.chromium.launch(
                headless=True,
                args=[
                    # 共有メモリ対策
                    '--disable-dev-shm-usage',
                    '--single-process',
                    # サンドボックス無効化
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    # 直接プロキシを指定（JWT認証情報を含む）
                    f'--proxy-server={https_proxy}',
                    # CA証明書対策
                    f'--ignore-certificate-errors-spki-list={CA_SPKI_HASH}',
                    '--ignore-certificate-errors',
                    '--disable-gpu',
                    '--disable-accelerated-2d-canvas',
                ]
            )

            print("✅ Browser launched")

            context = browser.new_context(ignore_https_errors=True)
            page = context.new_page()

            print("✅ Page created\n")

            for url in test_sites:
                try:
                    print(f"🔗 {url}")
                    page.goto(url, timeout=15000, wait_until="domcontentloaded")

                    title = page.title()
                    final_url = page.url

                    print(f"   ✅ SUCCESS")
                    print(f"   Title: {title[:60]}")
                    print(f"   URL: {final_url}")

                    # コンテンツ長を確認
                    body = page.inner_text("body")
                    print(f"   Content: {len(body)} chars\n")

                except Exception as e:
                    error_msg = str(e).split('\n')[0][:100]
                    print(f"   ❌ FAILED: {error_msg}\n")

            browser.close()

    except Exception as e:
        print(f"\n❌ Browser launch failed: {e}")
        import traceback
        traceback.print_exc()


def test_with_proxy_param():
    """proxyパラメータを使用してテスト"""
    print("\n" + "="*60)
    print("Test with proxy parameter")
    print("="*60)

    https_proxy = os.environ.get('HTTPS_PROXY')
    if not https_proxy:
        print("❌ HTTPS_PROXY not set")
        return

    print(f"\nProxy URL: {https_proxy[:80]}...")

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=[
                    '--disable-dev-shm-usage',
                    '--single-process',
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    f'--ignore-certificate-errors-spki-list={CA_SPKI_HASH}',
                    '--ignore-certificate-errors',
                    '--disable-gpu',
                    '--disable-accelerated-2d-canvas',
                ],
                proxy={
                    "server": https_proxy
                }
            )

            print("✅ Browser launched with proxy parameter")

            context = browser.new_context(ignore_https_errors=True)
            page = context.new_page()

            print("✅ Page created\n")

            url = "https://example.com"
            print(f"🔗 {url}")

            page.goto(url, timeout=15000, wait_until="domcontentloaded")
            title = page.title()

            print(f"   ✅ SUCCESS")
            print(f"   Title: {title}")

            browser.close()

    except Exception as e:
        print(f"   ❌ FAILED: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # Test 1: --proxy-server引数で直接指定
    test_direct_proxy()

    # Test 2: proxyパラメータを使用
    test_with_proxy_param()

    print("\n" + "="*60)
    print("テスト完了")
    print("="*60)
