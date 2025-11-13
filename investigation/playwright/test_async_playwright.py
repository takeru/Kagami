#!/usr/bin/env python3
"""
async Playwright APIでテスト
- sync APIの代わりにasync APIを使用
- プロキシ経由でアクセス
"""
import asyncio
import subprocess
import time
import os
import sys


async def main():
    print("="*60, flush=True)
    print("Async Playwright Test", flush=True)
    print("="*60, flush=True)
    print(flush=True)

    # proxy.pyを起動
    print("Starting proxy.py with ProxyPoolPlugin...", flush=True)
    proxy_process = subprocess.Popen(
        [
            'uv', 'run', 'proxy',
            '--hostname', '127.0.0.1',
            '--port', '8897',
            '--plugins', 'proxy.plugin.proxy_pool.ProxyPoolPlugin',
            '--proxy-pool', os.environ['HTTPS_PROXY'],
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    time.sleep(5)
    print("✅ Proxy started on port 8897\n", flush=True)

    try:
        from playwright.async_api import async_playwright

        print("="*60, flush=True)
        print("Test 1: async goto() with proxy", flush=True)
        print("="*60, flush=True)
        print(flush=True)

        async with async_playwright() as p:
            print("Launching Chromium with proxy...", flush=True)
            sys.stdout.flush()

            browser = await p.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--proxy-server=http://127.0.0.1:8897',
                    '--ignore-certificate-errors',
                ],
            )

            print("✅ Browser launched", flush=True)
            sys.stdout.flush()

            context = await browser.new_context(
                ignore_https_errors=True,
            )

            print("✅ Context created", flush=True)
            sys.stdout.flush()

            page = await context.new_page()

            print("✅ Page created", flush=True)
            sys.stdout.flush()

            # イベントリスナー
            page.on("crash", lambda: print("  [Crash] Page crashed!", flush=True))

            print("\nAttempting to navigate to https://example.com...", flush=True)
            sys.stdout.flush()

            try:
                response = await page.goto(
                    "https://example.com",
                    timeout=30000,
                    wait_until="domcontentloaded"
                )

                print(f"✅ Navigation succeeded!", flush=True)
                print(f"   Status: {response.status}", flush=True)
                print(f"   URL: {response.url}", flush=True)

                # タイトルを取得
                print("\nGetting page title...", flush=True)
                sys.stdout.flush()

                title = await page.title()
                print(f"✅ Title: {title}", flush=True)

                # コンテンツを取得
                print("\nGetting page content...", flush=True)
                content = await page.content()
                print(f"✅ Content length: {len(content)} bytes", flush=True)

            except Exception as e:
                print(f"❌ Navigation failed: {e}", flush=True)
                import traceback
                traceback.print_exc()

            print("\nClosing browser...", flush=True)
            await browser.close()
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


if __name__ == "__main__":
    asyncio.run(main())
