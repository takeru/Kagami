#!/usr/bin/env python3
"""
Chromium単体の動作確認テスト
プロキシなしでChromiumが正常に動作するかを確認
"""
from playwright.sync_api import sync_playwright
import sys


def test_basic_chromium():
    """基本的なChromium起動テスト"""
    print("="*60)
    print("Test 1: Basic Chromium Launch")
    print("="*60)

    try:
        with sync_playwright() as p:
            print("\nLaunching Chromium (no proxy)...")

            browser = p.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-gpu',
                ]
            )

            print("✅ Browser launched successfully")

            context = browser.new_context()
            page = context.new_page()

            print("✅ Page created successfully")

            browser.close()
            print("✅ Browser closed successfully\n")
            return True

    except Exception as e:
        print(f"❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_data_url():
    """data:URLでのテスト"""
    print("="*60)
    print("Test 2: Data URL Navigation")
    print("="*60)

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-gpu',
                ]
            )

            context = browser.new_context()
            page = context.new_page()

            print("\nNavigating to data: URL...")
            page.goto("data:text/html,<html><head><title>Test Page</title></head><body><h1>Hello World</h1></body></html>")

            print("✅ Navigation successful")

            print("Getting page title...")
            title = page.title()
            print(f"✅ Title: {title}")

            print("Getting page content...")
            content = page.content()
            print(f"✅ Content length: {len(content)} bytes")

            if "Hello World" in content:
                print("✅ Content verification successful")

            browser.close()
            return True

    except Exception as e:
        print(f"❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_set_content():
    """set_content()のテスト"""
    print("="*60)
    print("Test 3: set_content() Method")
    print("="*60)

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-gpu',
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

            browser.close()
            return True

    except Exception as e:
        print(f"❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_about_blank():
    """about:blankページのテスト"""
    print("="*60)
    print("Test 4: about:blank Navigation")
    print("="*60)

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-gpu',
                ]
            )

            context = browser.new_context()
            page = context.new_page()

            print("\nNavigating to about:blank...")
            page.goto("about:blank")
            print("✅ Navigation successful")

            print("Getting page URL...")
            url = page.url
            print(f"✅ URL: {url}")

            print("Evaluating JavaScript...")
            result = page.evaluate("() => 1 + 1")
            print(f"✅ JavaScript evaluation: 1 + 1 = {result}")

            browser.close()
            return True

    except Exception as e:
        print(f"❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_with_events():
    """イベントリスナーを付けたテスト"""
    print("="*60)
    print("Test 5: Browser Events Monitoring")
    print("="*60)

    events = []

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-gpu',
                ]
            )

            context = browser.new_context()
            page = context.new_page()

            # イベントリスナーを設定
            page.on("console", lambda msg: events.append(f"console: {msg.text}"))
            page.on("pageerror", lambda err: events.append(f"pageerror: {err}"))
            page.on("crash", lambda: events.append("crash"))
            page.on("close", lambda: events.append("close"))

            print("\nSetting content with JavaScript console.log...")
            html = """
            <!DOCTYPE html>
            <html>
            <head><title>Event Test</title></head>
            <body>
                <script>
                    console.log("Hello from JavaScript!");
                    console.log("Page loaded successfully");
                </script>
            </body>
            </html>
            """

            page.set_content(html)
            print("✅ Content set")

            # 少し待つ
            page.wait_for_timeout(1000)

            title = page.title()
            print(f"✅ Title: {title}")

            print(f"\nCaptured events: {len(events)}")
            for event in events:
                print(f"  - {event}")

            browser.close()

            if "crash" in str(events):
                print("❌ Page crash detected!")
                return False

            return True

    except Exception as e:
        print(f"❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    print("="*60)
    print("Chromium Standalone Tests")
    print("="*60)
    print()

    results = {}

    # Test 1
    results['basic_launch'] = test_basic_chromium()
    print()

    # Test 2
    results['data_url'] = test_data_url()
    print()

    # Test 3
    results['set_content'] = test_set_content()
    print()

    # Test 4
    results['about_blank'] = test_about_blank()
    print()

    # Test 5
    results['events'] = test_with_events()
    print()

    # Summary
    print("="*60)
    print("SUMMARY")
    print("="*60)

    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")

    success_count = sum(1 for r in results.values() if r)
    total_count = len(results)

    print(f"\nTotal: {success_count}/{total_count} tests passed")

    if success_count == total_count:
        print("\n🎉 すべてのテストが成功しました！")
        print("→ Chromium単体は正常に動作しています")
        print("→ 問題はプロキシ連携にあると考えられます")
    elif success_count > 0:
        print("\n⚠️ 一部のテストが失敗しました")
        print("→ Chromiumに部分的な問題がある可能性があります")
    else:
        print("\n❌ すべてのテストが失敗しました")
        print("→ Chromium自体に問題がある可能性があります")


if __name__ == "__main__":
    main()
