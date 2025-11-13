#!/usr/bin/env python3
"""
proxy.py + Firefox でのテスト
Firefoxならプロキシ認証が動作するはず！
"""
import subprocess
import time
import os
from playwright.sync_api import sync_playwright


print("="*60)
print("proxy.py + Firefox Test")
print("="*60)
print()

# proxy.pyを起動
print("Starting proxy.py with ProxyPoolPlugin...")
proxy_process = subprocess.Popen(
    [
        'uv', 'run', 'proxy',
        '--hostname', '127.0.0.1',
        '--port', '8893',
        '--plugins', 'proxy.plugin.proxy_pool.ProxyPoolPlugin',
        '--proxy-pool', os.environ['HTTPS_PROXY'],
    ],
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL,
)

time.sleep(5)
print("Proxy started on port 8893\n")

# Firefoxでテスト
try:
    print("Testing with Firefox (should work!)...")

    # Firefox用に環境変数を設定
    env = os.environ.copy()
    env['HOME'] = '/root'

    with sync_playwright() as p:
        print("Launching Firefox with HOME=/root...")
        browser = p.firefox.launch(
            headless=True,
            proxy={
                "server": "http://127.0.0.1:8893"
            },
            env=env
        )

        context = browser.new_context()
        page = context.new_page()

        print("Accessing https://example.com...")
        page.goto("https://example.com", timeout=30000, wait_until="domcontentloaded")

        title = page.title()
        url = page.url
        content_preview = page.content()[:200]

        print(f"\n🎉 SUCCESS!")
        print(f"   Title: {title}")
        print(f"   URL: {url}")
        print(f"   Content: {content_preview}...")
        print()

        # Claude AIもテスト
        print("Testing https://claude.ai/code/...")
        page.goto("https://claude.ai/code/", timeout=30000, wait_until="domcontentloaded")

        claude_title = page.title()
        claude_url = page.url

        print(f"\n🎉🎉🎉 CLAUDE AI SUCCESS!")
        print(f"   Title: {claude_title}")
        print(f"   URL: {claude_url}")

        # スクリーンショット
        screenshot_path = "/home/user/Kagami/investigation/playwright/claude_ai_firefox_success.png"
        page.screenshot(path=screenshot_path, full_page=True)
        print(f"   Screenshot: {screenshot_path}")

        browser.close()

        print("\n" + "="*60)
        print("CONCLUSION")
        print("="*60)
        print("\n🎉🎉🎉 完全成功！！！")
        print("\nFirefoxを使うことでPlaywrightからHTTPSアクセスが可能になりました！")
        print("\n実装した解決策:")
        print("  1. proxy.py + ProxyPoolPlugin")
        print("  2. Firefox browser (Chromiumの代わり)")
        print("  3. JWT認証は自動処理")
        print("\nアーキテクチャ:")
        print("  Firefox")
        print("      ↓")
        print("  localhost:8893 (proxy.py)")
        print("      ↓ (JWT auth)")
        print("  upstream proxy")
        print("      ↓")
        print("  Internet")
        print("\n次のステップ:")
        print("  ✓ ログイン操作の実装")
        print("  ✓ セッション永続化")

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
