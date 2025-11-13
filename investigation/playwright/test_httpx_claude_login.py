#!/usr/bin/env python3
"""
httpxでclaude.ai/codeのログインフローを調査
PlaywrightなしでセッションCookieを取得できるか確認
"""
import subprocess
import time
import os
import httpx


print("="*60)
print("Claude AI Login Flow Investigation (httpx only)")
print("="*60)
print()

# proxy.pyを起動
print("Starting proxy.py with ProxyPoolPlugin...")
proxy_process = subprocess.Popen(
    [
        'uv', 'run', 'proxy',
        '--hostname', '127.0.0.1',
        '--port', '8895',
        '--plugins', 'proxy.plugin.proxy_pool.ProxyPoolPlugin',
        '--proxy-pool', os.environ['HTTPS_PROXY'],
    ],
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL,
)

time.sleep(5)
print("Proxy started on port 8895\n")

try:
    # httpxクライアントを作成（Cookieを自動管理）
    client = httpx.Client(
        proxy="http://127.0.0.1:8895",
        timeout=30.0,
        verify=False,
        follow_redirects=True,  # リダイレクトを自動追跡
    )

    # Step 1: claude.ai/code/ にアクセス
    print("="*60)
    print("STEP 1: Access claude.ai/code/")
    print("="*60)
    print("\nGET https://claude.ai/code/")

    response = client.get("https://claude.ai/code/")

    print(f"✅ Status: {response.status_code}")
    print(f"   Final URL: {response.url}")
    print(f"   Cookies received: {len(response.cookies)} cookies")

    for cookie in response.cookies.jar:
        print(f"     - {cookie.name}: {cookie.value[:30]}...")

    print(f"   Content length: {len(response.text)} bytes")

    # HTML内のフォームやAPIエンドポイントを探す
    html = response.text.lower()

    if "login" in html:
        print("   'login' found in HTML")
    if "signin" in html:
        print("   'signin' found in HTML")
    if "api" in html:
        print("   'api' found in HTML")
    if "auth" in html:
        print("   'auth' found in HTML")

    # Step 2: レスポンスヘッダーを確認
    print("\n" + "="*60)
    print("STEP 2: Response Headers")
    print("="*60)

    important_headers = [
        'set-cookie',
        'location',
        'www-authenticate',
        'x-amzn-requestid',
        'content-type',
    ]

    for header in important_headers:
        if header in response.headers:
            value = response.headers[header]
            print(f"   {header}: {value[:100]}")

    # Step 3: JavaScriptバンドルの確認
    print("\n" + "="*60)
    print("STEP 3: JavaScript Analysis")
    print("="*60)

    # <script> タグを探す
    import re
    script_tags = re.findall(r'<script[^>]*src=["\']([^"\']+)["\']', response.text, re.IGNORECASE)

    print(f"\n   Found {len(script_tags)} script tags")
    for i, src in enumerate(script_tags[:5], 1):
        print(f"     {i}. {src}")

    if len(script_tags) > 5:
        print(f"     ... and {len(script_tags - 5)} more")

    # Step 4: メタタグの確認
    print("\n" + "="*60)
    print("STEP 4: Meta Tags")
    print("="*60)

    meta_tags = re.findall(r'<meta[^>]+>', response.text, re.IGNORECASE)
    print(f"\n   Found {len(meta_tags)} meta tags")

    # CSRFトークンやnonce を探す
    csrf_pattern = re.findall(r'csrf[_-]?token["\']?\s*[:=]\s*["\']([^"\']+)', html, re.IGNORECASE)
    if csrf_pattern:
        print(f"   CSRF token found: {csrf_pattern[0][:50]}...")

    # Step 5: APIエンドポイントの推測
    print("\n" + "="*60)
    print("STEP 5: Potential API Endpoints")
    print("="*60)

    api_patterns = re.findall(r'["\']/(api|auth|login|signin)/[^"\']+["\']', html)
    if api_patterns:
        print(f"\n   Found {len(api_patterns)} potential API endpoints:")
        for endpoint in set(api_patterns[:10]):
            print(f"     - {endpoint}")
    else:
        print("   No obvious API endpoints found in HTML")

    # Step 6: HTMLファイルを保存（後で詳細調査用）
    html_file = "/home/user/Kagami/investigation/playwright/claude_ai_initial.html"
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(response.text)

    print(f"\n   HTML saved to: {html_file}")
    print(f"   Size: {len(response.text)} bytes")

    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)

    print("\n✅ Successfully accessed claude.ai/code/")
    print(f"✅ Received {len(response.cookies)} cookies")
    print(f"✅ HTML content: {len(response.text)} bytes")

    print("\n次のステップ:")
    print("  1. HTMLファイルを調査してログインフローを特定")
    print("  2. APIエンドポイントを見つける")
    print("  3. 必要に応じてJavaScriptバンドルを解析")
    print("  4. httpxでログインAPIを叩いてセッションCookie取得を試す")

    client.close()

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
