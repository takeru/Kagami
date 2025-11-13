#!/usr/bin/env python3
"""
proxy.pyの最もシンプルなテスト
"""
import subprocess
import time
import os
from playwright.sync_api import sync_playwright


# proxy.pyを起動
print("Starting proxy.py...")
proxy_process = subprocess.Popen(
    [
        'uv', 'run', 'proxy',
        '--hostname', '127.0.0.1',
        '--port', '8892',
        '--plugins', 'proxy.plugin.proxy_pool.ProxyPoolPlugin',
        '--proxy-pool', os.environ['HTTPS_PROXY'],
    ],
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL,
)

time.sleep(5)
print("Proxy started!\n")

# Playwrightテスト
try:
    print("Testing with Playwright...")
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=[
                '--no-sandbox',
                '--proxy-server=http://127.0.0.1:8892',
                '--ignore-certificate-errors',
            ],
        )

        page = browser.new_page(ignore_https_errors=True)

        print("Accessing https://example.com...")
        page.goto("https://example.com", timeout=20000, wait_until="domcontentloaded")

        print(f"✅ SUCCESS! Title: {page.title()}")

        browser.close()

except Exception as e:
    print(f"❌ FAILED: {e}")

finally:
    print("\nStopping proxy...")
    proxy_process.terminate()
    proxy_process.wait()
    print("Done!")
