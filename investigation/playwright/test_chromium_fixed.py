#!/usr/bin/env python3
"""
Chromium単体の動作確認テスト（共有メモリ対策版）
--single-processフラグを使用
"""
from playwright.sync_api import sync_playwright
import sys


def test_basic_chromium_single_process():
    """基本的なChromium起動テスト（単一プロセスモード）"""
    print("="*60)
    print("Test: Basic Chromium with --single-process")
    print("="*60)

    try:
        with sync_playwright() as p:
            print("\nLaunching Chromium (single-process mode)...")

            browser = p.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',  # 最重要
                    '--single-process',          # 単一プロセスモード
                    '--disable-gpu',
                    '--disable-accelerated-2d-canvas',
                ]
            )

            print("✅ Browser launched successfully")

            context = browser.new_context()
            page = context.new_page()

            print("✅ Page created successfully")

            # data:URLでテスト
            print("\nNavigating to data: URL...")
            page.goto("data:text/html,<html><head><title>Test Page</title></head><body><h1>Hello World</h1></body></html>")
            print("✅ Navigation successful")

            print("Getting page title...")
            sys.stdout.flush()
            title = page.title()
            print(f"✅ Title: {title}")

            print("Getting page content...")
            content = page.content()
            print(f"✅ Content length: {len(content)} bytes")

            if "Hello World" in content:
                print("✅ Content verification successful")

            # JavaScript実行
            print("\nExecuting JavaScript...")
            result = page.evaluate("() => 1 + 1")
            print(f"✅ JavaScript result: 1 + 1 = {result}")

            browser.close()
            print("\n🎉 すべての操作が成功しました！")
            return True

    except Exception as e:
        print(f"❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_set_content_single_process():
    """set_content()のテスト（単一プロセスモード）"""
    print("\n" + "="*60)
    print("Test: set_content() with --single-process")
    print("="*60)

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--single-process',
                    '--disable-gpu',
                    '--disable-accelerated-2d-canvas',
                ]
            )

            context = browser.new_context()
            page = context.new_page()

            html = """
            <!DOCTYPE html>
            <html>
            <head>
                <title>Set Content Test</title>
            </head>
            <body>
                <h1 id="heading">Test Heading</h1>
                <p id="para">Test paragraph</p>
                <button id="btn">Click Me</button>
                <div id="output"></div>
                <script>
                    document.getElementById('btn').addEventListener('click', function() {
                        document.getElementById('output').textContent = 'Button clicked!';
                    });
                </script>
            </body>
            </html>
            """

            print("\nSetting page content...")
            page.set_content(html)
            print("✅ set_content() successful")

            print("Getting page title...")
            sys.stdout.flush()
            title = page.title()
            print(f"✅ Title: {title}")

            print("Querying element...")
            heading = page.query_selector("#heading")
            if heading:
                text = heading.inner_text()
                print(f"✅ Heading text: {text}")

            print("Clicking button...")
            page.click("#btn")
            print("✅ Button clicked")

            print("Checking output...")
            output = page.query_selector("#output")
            if output:
                output_text = output.inner_text()
                print(f"✅ Output text: {output_text}")

            browser.close()
            print("\n🎉 set_content()とDOM操作が成功しました！")
            return True

    except Exception as e:
        print(f"❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    print("="*60)
    print("Chromium Tests with Shared Memory Fix")
    print("="*60)
    print()

    results = {}

    # Test 1
    results['basic_single_process'] = test_basic_chromium_single_process()

    # Test 2
    results['set_content_single_process'] = test_set_content_single_process()

    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)

    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")

    success_count = sum(1 for r in results.values() if r)
    total_count = len(results)

    print(f"\nTotal: {success_count}/{total_count} tests passed")

    if success_count == total_count:
        print("\n🎉🎉🎉 すべてのテストが成功しました！")
        print("→ --single-processフラグで共有メモリ問題を解決しました")
        print("→ 次はプロキシ経由でのアクセスをテストできます")
    else:
        print("\n❌ 一部のテストが失敗しました")


if __name__ == "__main__":
    main()
