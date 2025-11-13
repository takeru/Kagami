#!/usr/bin/env python3
"""
Playwright Route API for JWT Proxy Authentication
Route APIを使ってProxy-Authorizationヘッダーを注入
"""
from playwright.sync_api import sync_playwright, Route, Request
import os
from urllib.parse import urlparse
import base64

def parse_proxy_credentials():
    """環境変数からプロキシ認証情報を取得"""
    proxy_url = os.environ.get('HTTPS_PROXY') or os.environ.get('HTTP_PROXY')

    if not proxy_url:
        return None, None, None

    parsed = urlparse(proxy_url)

    # Basic認証形式の文字列を作成（username:passwordをBase64エンコード）
    if parsed.username and parsed.password:
        # JWT形式の場合は特殊処理
        # username:jwt_XXX の形式
        credentials = f"{parsed.username}:{parsed.password}"
        # Base64エンコード
        encoded = base64.b64encode(credentials.encode()).decode()

        return (
            f"{parsed.scheme}://{parsed.hostname}:{parsed.port}",
            credentials,
            encoded
        )

    return f"{parsed.scheme}://{parsed.hostname}:{parsed.port}", None, None


def test_route_api_basic():
    """Route APIを使った基本的なProxy-Authorization注入"""
    print("="*60)
    print("Playwright Route API - Basic Injection Test")
    print("="*60)

    proxy_server, credentials, encoded_creds = parse_proxy_credentials()

    if not proxy_server:
        print("❌ No proxy configuration found")
        return False

    print(f"\nProxy Server: {proxy_server}")
    print(f"Credentials: {credentials[:50]}..." if credentials else "No credentials")

    test_url = "https://example.com"

    try:
        with sync_playwright() as p:
            # プロキシなしでブラウザを起動（後でRoute APIで注入）
            browser = p.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                ]
            )

            context = browser.new_context()

            # Route APIでProxy-Authorizationヘッダーを注入
            request_count = 0

            def handle_route(route: Route, request: Request):
                nonlocal request_count
                request_count += 1

                print(f"\n[Request {request_count}] Intercepting: {request.url[:80]}")

                try:
                    # ヘッダーをコピー
                    headers = dict(request.headers)

                    # Proxy-Authorizationヘッダーを追加
                    if encoded_creds:
                        headers['Proxy-Authorization'] = f'Basic {encoded_creds}'
                        print(f"  → Added Proxy-Authorization header")

                    # context.request.fetch を使ってリクエストを実行
                    # これがプロキシを通るかどうかが鍵
                    response = context.request.fetch(
                        request.url,
                        method=request.method,
                        headers=headers,
                        data=request.post_data_buffer
                    )

                    print(f"  ✅ Fetch succeeded: {response.status}")

                    # レスポンスを返す
                    route.fulfill(
                        status=response.status,
                        headers=dict(response.headers),
                        body=response.body()
                    )

                except Exception as e:
                    error = str(e)[:150]
                    print(f"  ❌ Fetch failed: {error}")
                    route.abort()

            # 全リクエストをインターセプト
            context.route("**/*", handle_route)

            page = context.new_page()

            print(f"\n{'='*60}")
            print(f"Accessing: {test_url}")
            print(f"{'='*60}")

            page.goto(test_url, timeout=20000)

            title = page.title()
            final_url = page.url

            print(f"\n✅ SUCCESS!")
            print(f"   Title: {title}")
            print(f"   Final URL: {final_url}")
            print(f"   Total requests: {request_count}")

            browser.close()
            return True

    except Exception as e:
        print(f"\n❌ FAILED: {e}")
        return False


def test_route_api_without_fetch():
    """context.request.fetchを使わずにプロキシ設定を試す"""
    print("\n" + "="*60)
    print("Playwright Route API - Direct Proxy Test")
    print("="*60)

    proxy_server, credentials, encoded_creds = parse_proxy_credentials()

    if not proxy_server:
        print("❌ No proxy configuration found")
        return False

    print(f"\nProxy Server: {proxy_server}")

    parsed_proxy = urlparse(proxy_server)

    test_url = "https://example.com"

    try:
        with sync_playwright() as p:
            # プロキシサーバーを指定して起動
            # ただし、認証情報はRoute APIで注入
            browser = p.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                ],
                proxy={
                    "server": proxy_server
                }
            )

            context = browser.new_context()

            # Proxy-Authorizationを追加しようと試みる
            def handle_route(route: Route):
                headers = dict(route.request.headers)
                if encoded_creds:
                    headers['Proxy-Authorization'] = f'Basic {encoded_creds}'

                # 通常のcontinueで続行
                route.continue_(headers=headers)

            context.route("**/*", handle_route)

            page = context.new_page()

            print(f"\nAccessing: {test_url}")

            page.goto(test_url, timeout=20000)

            print(f"✅ SUCCESS: {page.title()}")

            browser.close()
            return True

    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False


def main():
    print("="*60)
    print("Playwright JWT Proxy Authentication via Route API")
    print("="*60)

    results = {}

    # Test 1: context.request.fetch を使う方法
    print("\n" + "="*60)
    print("TEST 1: Using context.request.fetch()")
    print("="*60)
    results['fetch'] = test_route_api_basic()

    # Test 2: プロキシ設定 + route.continue_()
    print("\n" + "="*60)
    print("TEST 2: Using proxy config + route.continue_()")
    print("="*60)
    results['continue'] = test_route_api_without_fetch()

    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)

    for test, success in results.items():
        status = "✅" if success else "❌"
        print(f"{status} {test}: {'Success' if success else 'Failed'}")

    # Conclusion
    print("\n" + "="*60)
    print("CONCLUSION")
    print("="*60)

    if any(results.values()):
        print("\n🎉 Route APIでHTTPSアクセスが可能になりました！")
        print("   JWT認証プロキシの回避策が有効です！")
    else:
        print("\n❌ Route APIでも失敗しました")
        print("   理由: HTTPSのCONNECTメソッドはRoute APIでインターセプトできない")
        print("   推奨: Python urllib + Playwrightのハイブリッドアプローチ")


if __name__ == "__main__":
    main()
