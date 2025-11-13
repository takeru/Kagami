#!/usr/bin/env python3
"""
最小限のset_content()テスト
"""
import sys
from playwright.sync_api import sync_playwright


print("Starting minimal set_content() test...", flush=True)

html = """<!DOCTYPE html>
<html>
<head><title>Test</title></head>
<body><h1>Hello World</h1></body>
</html>"""

print(f"HTML to set: {len(html)} bytes", flush=True)

try:
    with sync_playwright() as p:
        print("Launching Chromium...", flush=True)
        sys.stdout.flush()

        browser = p.chromium.launch(
            headless=True,
            args=['--no-sandbox', '--disable-setuid-sandbox']
        )

        print("Creating new page...", flush=True)
        sys.stdout.flush()

        page = browser.new_page()

        print("Calling set_content()...", flush=True)
        sys.stdout.flush()

        # テスト1: タイムアウトなし、wait_untilなし
        try:
            page.set_content(html)
            print("✅ set_content() succeeded (no params)", flush=True)
        except Exception as e:
            print(f"❌ set_content() failed: {e}", flush=True)

        # ページ情報を取得
        title = page.title()
        print(f"Page title: {title}", flush=True)

        browser.close()
        print("✅ Test completed successfully!", flush=True)

except Exception as e:
    print(f"❌ Test failed: {e}", flush=True)
    import traceback
    traceback.print_exc()
