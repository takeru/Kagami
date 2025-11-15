#!/usr/bin/env python3
"""
テスト6: route()方式をChromiumでも確認

Firefoxで成功したroute()によるヘッダー注入が
Chromiumでも動作するか確認します。
"""
import os
import sys
import base64
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright


def extract_proxy_credentials(proxy_url):
    """プロキシURLから認証情報を抽出"""
    parsed = urlparse(proxy_url)
    username = parsed.username or ""
    password = parsed.password or ""

    if parsed.port:
        server = f"{parsed.scheme}://{parsed.hostname}:{parsed.port}"
    else:
        server = f"{parsed.scheme}://{parsed.hostname}"

    return server, username, password


def test_chromium_route():
    """Chromiumでroute()によるヘッダー注入をテスト"""
    print("=" * 70)
    print("テスト6: Chromium + route()でProxy-Authorizationヘッダー注入")
    print("=" * 70)
    print()

    https_proxy = os.getenv("HTTPS_PROXY")
    if not https_proxy:
        print("❌ HTTPS_PROXY環境変数が設定されていません")
        return False

    server, username, password = extract_proxy_credentials(https_proxy)

    # Basic認証ヘッダーの値を作成
    auth_string = f"{username}:{password}"
    auth_bytes = auth_string.encode('utf-8')
    auth_b64 = base64.b64encode(auth_bytes).decode('utf-8')

    print(f"プロキシサーバー: {server}")
    print(f"認証ヘッダー（Base64）: {auth_b64[:40]}...")
    print()

    try:
        with sync_playwright() as p:
            print("1. Chromiumを起動...")
            browser = p.chromium.launch(
                headless=True,
                proxy={
                    "server": server,
                },
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-gpu',
                    '--ignore-certificate-errors',
                ]
            )
            print("   ✅ Chromium起動完了")

            context = browser.new_context(ignore_https_errors=True)
            page = context.new_page()

            # リクエストを傍受してProxy-Authorizationヘッダーを追加
            print("\n2. リクエスト傍受ハンドラーを設定...")

            def handle_route(route, request):
                """すべてのリクエストにProxy-Authorizationヘッダーを追加"""
                headers = request.headers
                headers["Proxy-Authorization"] = f"Basic {auth_b64}"

                print(f"   傍受: {request.method} {request.url}")
                route.continue_(headers=headers)

            page.route("**/*", handle_route)
            print("   ✅ リクエスト傍受設定完了")

            test_url = "https://example.com"
            print(f"\n3. {test_url} にアクセス...")

            response = page.goto(test_url, timeout=30000)

            print(f"   ✅ ステータス: {response.status}")
            print(f"   ✅ URL: {response.url}")
            print(f"   ✅ タイトル: {page.title()}")

            screenshot_path = "/home/user/Kagami/investigation/playwright/test_06_screenshot.png"
            page.screenshot(path=screenshot_path)
            print(f"   ✅ スクリーンショット: {screenshot_path}")

            browser.close()

            print("\n" + "=" * 70)
            print("✅ 成功：Chromiumでもroute()が機能しました！")
            print("=" * 70)
            return True

    except Exception as e:
        print("\n" + "=" * 70)
        print("❌ 失敗")
        print("=" * 70)
        print(f"\nエラー: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    print("Chromiumでのroute()テスト")
    print()

    result = test_chromium_route()

    print("\n\n")
    print("=" * 70)
    print("結論")
    print("=" * 70)

    if result:
        print("\n✅ Chromiumでも成功しました！")
        print("\nroute()によるヘッダー注入は、")
        print("Firefox/Chromium両方で動作します。")
        print("\n🎉 proxy.pyは不要です！")
    else:
        print("\n❌ Chromiumでは失敗しました")
        print("Firefoxのみで動作する可能性があります")

    return result


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
