#!/usr/bin/env python3
"""
async Playwright + goto()でプロキシ経由のテスト
以前の調査では:
- goto() は成功 (Status: 200)
- その後のpage.title()でクラッシュ

しかし、もう一度試してみる価値がある
"""
import asyncio
import subprocess
import time
import os
import sys


async def main():
    print("="*60, flush=True)
    print("Async Playwright + proxy.py Test (Retry)", flush=True)
    print("="*60, flush=True)
    print(flush=True)

    # proxy.pyを起動
    print("Starting proxy.py with ProxyPoolPlugin...", flush=True)
    proxy_process = subprocess.Popen(
        [
            'uv', 'run', 'proxy',
            '--hostname', '127.0.0.1',
            '--port', '8898',
            '--plugins', 'proxy.plugin.proxy_pool.ProxyPoolPlugin',
            '--proxy-pool', os.environ['HTTPS_PROXY'],
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    time.sleep(5)
    print("✅ Proxy started on port 8898\n", flush=True)

    try:
        from playwright.async_api import async_playwright

        async with async_playwright() as p:
            print("Launching Chromium with proxy...", flush=True)
            sys.stdout.flush()

            browser = await p.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--proxy-server=http://127.0.0.1:8898',
                    '--ignore-certificate-errors',
                ],
            )

            print("✅ Browser launched", flush=True)
            sys.stdout.flush()

            context = await browser.new_context(
                ignore_https_errors=True,
            )

            page = await context.new_page()
            print("✅ Page created", flush=True)
            sys.stdout.flush()

            # Test 1: example.comにアクセス
            print("\n" + "="*60, flush=True)
            print("Test 1: Navigate to example.com", flush=True)
            print("="*60, flush=True)

            try:
                response = await page.goto(
                    "https://example.com",
                    timeout=30000,
                    wait_until="domcontentloaded"  # DOMが読み込まれるまで待つ
                )

                print(f"✅ Navigation succeeded!", flush=True)
                print(f"   Status: {response.status}", flush=True)
                print(f"   URL: {response.url}", flush=True)

                # Test 2: コンテンツ取得（title()をスキップ）
                print("\nTest 2: Getting page content directly...", flush=True)
                sys.stdout.flush()

                content = await page.content()
                print(f"✅ Content length: {len(content)} bytes", flush=True)

                # Test 3: タイトルをJavaScriptで取得
                print("\nTest 3: Getting title via evaluate()...", flush=True)
                title = await page.evaluate("() => document.title")
                print(f"✅ Title via JS: {title}", flush=True)

                # Test 4: 要素を探す
                print("\nFinding h1 element...", flush=True)
                h1 = await page.query_selector("h1")
                if h1:
                    h1_text = await h1.text_content()
                    print(f"✅ H1 text: {h1_text}", flush=True)

                print("\n" + "="*60, flush=True)
                print("ALL TESTS PASSED!", flush=True)
                print("="*60, flush=True)

            except Exception as e:
                print(f"❌ Test failed: {e}", flush=True)
                import traceback
                traceback.print_exc()

            await browser.close()

    except Exception as e:
        print(f"\n❌ Setup failed: {e}", flush=True)
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


if __name__ == "__main__":
    asyncio.run(main())
