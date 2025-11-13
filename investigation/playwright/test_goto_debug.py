#!/usr/bin/env python3
"""
Playwright goto()の詳細デバッグ
- proxy.py経由でclaude.ai/codeにアクセス
- 詳細なログを出力
"""
import subprocess
import time
import os
import sys
from playwright.sync_api import sync_playwright


print("="*60, flush=True)
print("Playwright goto() Debug Test", flush=True)
print("="*60, flush=True)
print(flush=True)

# proxy.pyを起動
print("Starting proxy.py with ProxyPoolPlugin...", flush=True)
proxy_process = subprocess.Popen(
    [
        'uv', 'run', 'proxy',
        '--hostname', '127.0.0.1',
        '--port', '8896',
        '--plugins', 'proxy.plugin.proxy_pool.ProxyPoolPlugin',
        '--proxy-pool', os.environ['HTTPS_PROXY'],
    ],
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL,
)

time.sleep(5)
print("✅ Proxy started on port 8896\n", flush=True)

try:
    # Playwrightのデバッグ環境変数を設定
    env = os.environ.copy()
    env['DEBUG'] = 'pw:api,pw:browser'  # Playwrightのデバッグログ

    print("="*60, flush=True)
    print("Test 1: goto() with proxy", flush=True)
    print("="*60, flush=True)
    print(flush=True)

    with sync_playwright() as p:
        print("Launching Chromium with proxy...", flush=True)
        sys.stdout.flush()

        browser = p.chromium.launch(
            headless=True,
            args=[
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--proxy-server=http://127.0.0.1:8896',
                '--ignore-certificate-errors',
                # 追加のデバッグフラグ
                '--enable-logging',
                '--v=1',
            ],
        )

        print("✅ Browser launched", flush=True)
        sys.stdout.flush()

        context = browser.new_context(
            ignore_https_errors=True,
        )

        print("✅ Context created", flush=True)
        sys.stdout.flush()

        page = context.new_page()

        print("✅ Page created", flush=True)
        sys.stdout.flush()

        # ページイベントのリスナーを追加
        page.on("console", lambda msg: print(f"  [Console] {msg.type}: {msg.text}", flush=True))
        page.on("pageerror", lambda err: print(f"  [PageError] {err}", flush=True))
        page.on("crash", lambda: print("  [Crash] Page crashed!", flush=True))
        page.on("close", lambda: print("  [Close] Page closed", flush=True))

        print("\nAttempting to navigate to https://example.com...", flush=True)
        sys.stdout.flush()

        try:
            # まずはsimpleなexample.comでテスト
            response = page.goto("https://example.com", timeout=30000, wait_until="domcontentloaded")

            print(f"✅ Navigation succeeded!", flush=True)
            print(f"   Status: {response.status}", flush=True)
            print(f"   URL: {response.url}", flush=True)

            # タイトルを取得してみる
            print("\nGetting page title...", flush=True)
            sys.stdout.flush()

            title = page.title()
            print(f"✅ Title: {title}", flush=True)

        except Exception as e:
            print(f"❌ Navigation failed: {e}", flush=True)
            import traceback
            traceback.print_exc()

        print("\nClosing browser...", flush=True)
        browser.close()
        print("✅ Browser closed", flush=True)

except Exception as e:
    print(f"\n❌ Test failed: {e}", flush=True)
    import traceback
    traceback.print_exc()

finally:
    print("\nStopping proxy...", flush=True)
    proxy_process.terminate()
    try:
        proxy_process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proxy_process.kill()
    print("✅ Proxy stopped", flush=True)

print("\n" + "="*60, flush=True)
print("Test completed", flush=True)
print("="*60, flush=True)
