#!/usr/bin/env python3
"""
ハイブリッドアプローチ：httpx + Playwright
- httpx（proxy.py経由）でHTTPSアクセス
- PlaywrightでDOM操作・JavaScript実行
"""
import subprocess
import time
import os
import httpx
from playwright.sync_api import sync_playwright


print("="*60)
print("Hybrid Approach: httpx + Playwright")
print("="*60)
print()

# proxy.pyを起動
print("Starting proxy.py with ProxyPoolPlugin...")
proxy_process = subprocess.Popen(
    [
        'uv', 'run', 'proxy',
        '--hostname', '127.0.0.1',
        '--port', '8894',
        '--plugins', 'proxy.plugin.proxy_pool.ProxyPoolPlugin',
        '--proxy-pool', os.environ['HTTPS_PROXY'],
    ],
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL,
)

time.sleep(5)
print("Proxy started on port 8894\n")

try:
    # Step 1: httpxでHTMLを取得（proxy.py経由）
    print("="*60)
    print("STEP 1: Fetch HTML with httpx (via proxy.py)")
    print("="*60)

    client = httpx.Client(
        proxy="http://127.0.0.1:8894",
        timeout=30.0,
        verify=False,  # 証明書検証を無効化
    )

    print("\nFetching https://example.com...")
    response = client.get("https://example.com")

    print(f"✅ Status: {response.status_code}")
    print(f"   Content-Type: {response.headers.get('content-type')}")
    print(f"   Content length: {len(response.text)} bytes")
    print(f"   HTML preview: {response.text[:150]}...")

    html = response.text

    # Step 2: PlaywrightでHTMLを読み込んで操作
    print("\n" + "="*60)
    print("STEP 2: Load HTML in Playwright and interact")
    print("="*60)

    with sync_playwright() as p:
        print("\nLaunching Chromium...")
        browser = p.chromium.launch(
            headless=True,
            args=['--no-sandbox', '--disable-setuid-sandbox']
        )

        page = browser.new_page()

        print("Loading HTML content...")
        page.set_content(html, timeout=5000)

        # ページ情報を取得
        title = page.title()
        h1_text = page.locator("h1").first.text_content() if page.locator("h1").count() > 0 else "N/A"

        print(f"✅ Page loaded successfully")
        print(f"   Title: {title}")
        print(f"   H1 text: {h1_text}")

        # JavaScriptが実行可能か確認
        js_result = page.evaluate("() => { return 'JavaScript works!'; }")
        print(f"   JavaScript: {js_result}")

        browser.close()

    # Step 3: Claude AIでテスト
    print("\n" + "="*60)
    print("STEP 3: Test with Claude AI")
    print("="*60)

    print("\nFetching https://claude.ai/code/...")
    claude_response = client.get("https://claude.ai/code/", follow_redirects=True)

    print(f"✅ Status: {claude_response.status_code}")
    print(f"   Final URL: {claude_response.url}")
    print(f"   Content length: {len(claude_response.text)} bytes")

    claude_html = claude_response.text

    # Playwrightで読み込み
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=['--no-sandbox', '--disable-setuid-sandbox']
        )

        page = browser.new_page()

        print("\nLoading Claude AI HTML...")
        page.set_content(claude_html, timeout=5000)

        title = page.title()
        print(f"✅ Claude AI loaded")
        print(f"   Title: {title}")

        # スクリーンショット
        screenshot_path = "/home/user/Kagami/investigation/playwright/claude_ai_hybrid.png"
        page.screenshot(path=screenshot_path, full_page=True)
        print(f"   Screenshot: {screenshot_path}")

        # DOM要素の確認
        body_text = page.locator("body").text_content()
        print(f"   Body text length: {len(body_text) if body_text else 0} chars")

        browser.close()

    client.close()

    # Summary
    print("\n" + "="*60)
    print("CONCLUSION")
    print("="*60)
    print("\n🎉🎉🎉 ハイブリッドアプローチ成功！🎉🎉🎉")
    print("\n✅ httpx経由でHTTPSアクセス完全動作")
    print("✅ PlaywrightでDOM操作・JavaScript実行可能")
    print("✅ Chromiumのプロキシ認証バグを完全回避")
    print("\n実装した解決策:")
    print("  1. httpx（proxy.py経由）でHTMLを取得")
    print("  2. Playwrightでset_content()を使用")
    print("  3. DOM操作・JavaScript実行はPlaywrightで可能")
    print("\nアーキテクチャ:")
    print("  httpx")
    print("      ↓")
    print("  localhost:8894 (proxy.py)")
    print("      ↓ (JWT auth)")
    print("  upstream proxy")
    print("      ↓")
    print("  Internet")
    print("      ↓")
    print("  HTML → Playwright (Chromium)")
    print("      ↓")
    print("  DOM操作・JavaScript実行")
    print("\n次のステップ:")
    print("  ✓ ログイン操作の実装")
    print("  ✓ セッション永続化（Cookieの保存・復元）")
    print("  ✓ 動的なページ遷移の処理")

except Exception as e:
    print(f"\n❌ FAILED: {e}")
    import traceback
    traceback.print_exc()

finally:
    print("\n\nStopping proxy...")
    proxy_process.terminate()
    try:
        proxy_process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proxy_process.kill()
    print("Proxy stopped.")
