#!/usr/bin/env python3
"""
プロキシ経由でのHTTPSアクセステスト（シンプル版）
"""
import sys
import os
import threading
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.local_proxy import run_proxy_server
from playwright.sync_api import sync_playwright

CA_SPKI_HASH = "L+/CZomxifpzjiAVG11S0bTbaTopj+c49s0rBjjSC6A="


def start_proxy():
    """プロキシサーバーをバックグラウンドで起動"""
    def run():
        run_proxy_server(port=8888)

    t = threading.Thread(target=run, daemon=True)
    t.start()
    print("Proxy starting...")
    time.sleep(2)
    print("Proxy ready\n")


def test_https_sites():
    """シンプルなHTTPSサイトへのアクセステスト"""
    print("="*60)
    print("HTTPS Access Test via Proxy")
    print("="*60)

    sites = [
        "https://example.com",
        "https://example.org",
        "https://httpbin.org/get",
    ]

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=[
                '--disable-dev-shm-usage',
                '--single-process',
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--proxy-server=http://127.0.0.1:8888',
                f'--ignore-certificate-errors-spki-list={CA_SPKI_HASH}',
                '--ignore-certificate-errors',
                '--disable-gpu',
                '--disable-accelerated-2d-canvas',
            ]
        )

        context = browser.new_context(ignore_https_errors=True)
        page = context.new_page()

        for url in sites:
            try:
                print(f"\n🔗 {url}")
                page.goto(url, timeout=15000, wait_until="domcontentloaded")

                title = page.title()
                final_url = page.url

                print(f"   ✅ SUCCESS")
                print(f"   Title: {title[:60]}")
                print(f"   URL: {final_url[:60]}")

                # HTMLの一部を取得
                body = page.inner_text("body")
                print(f"   Content length: {len(body)} chars")

            except Exception as e:
                print(f"   ❌ FAILED: {str(e).split(':')[0]}")

        browser.close()


if __name__ == "__main__":
    start_proxy()
    test_https_sites()
    print("\n" + "="*60)
    print("テスト完了")
    print("="*60)
