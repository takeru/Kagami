#!/usr/bin/env python3
"""
テスト5: Playwright route()でプロキシ認証ヘッダーを注入

page.route() を使ってCONNECTリクエストを傍受し、
Proxy-Authorizationヘッダーを追加することで
Preemptive Authenticationを実現できるか試します。

注意: page.route() はHTTPリクエストを傍受できますが、
HTTPS CONNECTリクエスト（プロキシトンネリング）には
適用できない可能性があります。
"""
import os
import sys
import tempfile
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


def test_route_header_injection():
    """
    page.route() でリクエストを傍受してヘッダーを追加
    """
    print("=" * 70)
    print("テスト5: Playwright route()でProxy-Authorizationヘッダー注入")
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
            temp_home = tempfile.mkdtemp(prefix="firefox_route_")

            print("1. Firefoxを起動...")
            browser = p.firefox.launch(
                headless=True,
                proxy={
                    "server": server,
                },
                firefox_user_prefs={
                    "privacy.trackingprotection.enabled": False,
                    "network.proxy.allow_hijacking_localhost": True,
                    "network.stricttransportsecurity.preloadlist": False,
                    "security.cert_pinning.enforcement_level": 0,
                    "security.enterprise_roots.enabled": True,
                    "security.ssl.errorReporting.enabled": False,
                    "browser.xul.error_pages.expert_bad_cert": True,
                    "media.navigator.streams.fake": True,
                },
                env={
                    **os.environ,
                    "HOME": temp_home,
                }
            )
            print("   ✅ Firefox起動完了")

            context = browser.new_context(ignore_https_errors=True)
            page = context.new_page()

            # リクエストを傍受してProxy-Authorizationヘッダーを追加
            print("\n2. リクエスト傍受ハンドラーを設定...")

            def handle_route(route, request):
                """すべてのリクエストにProxy-Authorizationヘッダーを追加"""
                headers = request.headers
                headers["Proxy-Authorization"] = f"Basic {auth_b64}"

                print(f"   傍受: {request.method} {request.url}")
                print(f"   ヘッダー追加: Proxy-Authorization: Basic {auth_b64[:20]}...")

                route.continue_(headers=headers)

            # すべてのリクエストを傍受
            page.route("**/*", handle_route)
            print("   ✅ リクエスト傍受設定完了")

            test_url = "https://example.com"
            print(f"\n3. {test_url} にアクセス...")

            response = page.goto(test_url, timeout=30000)

            print(f"   ✅ ステータス: {response.status}")
            print(f"   ✅ URL: {response.url}")
            print(f"   ✅ タイトル: {page.title()}")

            screenshot_path = "/home/user/Kagami/investigation/playwright/test_05_screenshot.png"
            page.screenshot(path=screenshot_path)
            print(f"   ✅ スクリーンショット: {screenshot_path}")

            browser.close()

            print("\n" + "=" * 70)
            print("✅ 成功：route()でヘッダー注入が機能しました！")
            print("=" * 70)
            print("\n結論: proxy.pyは不要です（route()で解決）")
            return True

    except Exception as e:
        print("\n" + "=" * 70)
        print("❌ 失敗")
        print("=" * 70)
        print(f"\nエラー: {e}")
        import traceback
        traceback.print_exc()
        print("\n結論: route()ではHTTPS CONNECTリクエストを傍受できません")
        print("\n理由:")
        print("  - page.route()はHTTPリクエストを傍受")
        print("  - プロキシへのCONNECTリクエストはブラウザが直接送信")
        print("  - Playwrightはこのレイヤーにアクセスできない")
        return False


def main():
    print("Playwright route()を使ったヘッダー注入テスト")
    print()

    result = test_route_header_injection()

    print("\n\n")
    print("=" * 70)
    print("最終結論")
    print("=" * 70)

    if result:
        print("\n✅ proxy.pyは不要です！")
        print("Playwrightのroute()機能で解決できます。")
    else:
        print("\n❌ proxy.pyは必要です。")
        print("\nすべてのブラウザレベルの方法を試しましたが：")
        print("  1. Playwright username/password設定 → 失敗")
        print("  2. Firefox network prefs → 失敗")
        print("  3. Chromium比較 → 失敗")
        print("  4. Playwright route() ヘッダー注入 → 失敗")
        print("\nHTTPS CONNECTトンネリングのレイヤーでは、")
        print("ブラウザがプロキシと直接通信するため、")
        print("Playwright/ブラウザ設定では介入できません。")
        print("\n中間プロキシ（proxy.py）が唯一の解決策です。")

    return result


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
