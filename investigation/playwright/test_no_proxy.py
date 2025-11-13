#!/usr/bin/env python3
"""
プロキシなしでPlaywrightをテスト
- プロキシを使わずにローカルHTMLファイルをロード
- DOM操作が正常に動作するか確認
"""
import sys
from playwright.sync_api import sync_playwright


print("="*60, flush=True)
print("Playwright WITHOUT Proxy Test", flush=True)
print("="*60, flush=True)
print(flush=True)

html_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Test Page</title>
</head>
<body>
    <h1>Hello World</h1>
    <button id="btn">Click me</button>
    <div id="output"></div>
    <script>
        document.getElementById('btn').addEventListener('click', function() {
            document.getElementById('output').textContent = 'Button clicked!';
        });
    </script>
</body>
</html>"""

try:
    with sync_playwright() as p:
        print("Launching Chromium (NO PROXY)...", flush=True)
        sys.stdout.flush()

        browser = p.chromium.launch(
            headless=True,
            args=[
                '--no-sandbox',
                '--disable-setuid-sandbox',
                # プロキシ設定なし
            ],
        )

        print("✅ Browser launched", flush=True)
        sys.stdout.flush()

        page = browser.new_page()
        print("✅ Page created", flush=True)
        sys.stdout.flush()

        # イベントリスナー
        page.on("crash", lambda: print("  [Crash] Page crashed!", flush=True))

        # Test 1: set_content()
        print("\nTest 1: set_content() + DOM operations", flush=True)
        print("Setting HTML content...", flush=True)
        sys.stdout.flush()

        page.set_content(html_content)
        print("✅ set_content() succeeded", flush=True)
        sys.stdout.flush()

        # Test 2: page.title()
        print("\nTest 2: page.title()", flush=True)
        sys.stdout.flush()

        title = page.title()
        print(f"✅ Title: {title}", flush=True)

        # Test 3: locator + text_content()
        print("\nTest 3: locator + text_content()", flush=True)
        h1_text = page.locator("h1").text_content()
        print(f"✅ H1 text: {h1_text}", flush=True)

        # Test 4: JavaScript execution
        print("\nTest 4: evaluate JavaScript", flush=True)
        result = page.evaluate("() => document.title")
        print(f"✅ JS result: {result}", flush=True)

        # Test 5: Click button
        print("\nTest 5: Click button", flush=True)
        page.click("#btn")
        output_text = page.locator("#output").text_content()
        print(f"✅ Output after click: {output_text}", flush=True)

        print("\n" + "="*60, flush=True)
        print("ALL TESTS PASSED!", flush=True)
        print("="*60, flush=True)

        browser.close()

except Exception as e:
    print(f"\n❌ Test failed: {e}", flush=True)
    import traceback
    traceback.print_exc()
