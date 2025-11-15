#!/usr/bin/env python3
"""
テスト7: extraHTTPHeadersでProxy-Authorizationを設定

context.new_page()やpage.set_extra_http_headers()を使って
Proxy-Authorizationヘッダーを設定できるか試します。
"""
import os
import sys
import base64
import tempfile
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


def test_firefox_extra_headers():
    """Firefox: extraHTTPHeadersでProxy-Authorizationを設定"""
    print("=" * 70)
    print("テスト7-A: Firefox + extraHTTPHeaders")
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
    print()

    try:
        with sync_playwright() as p:
            temp_home = tempfile.mkdtemp(prefix="firefox_extra_")

            print("1. Firefoxを起動...")
            browser = p.firefox.launch(
                headless=True,
                proxy={"server": server},
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
                env={**os.environ, "HOME": temp_home}
            )
            print("   ✅ Firefox起動完了")

            # extraHTTPHeadersを設定してコンテキストを作成
            print("\n2. extraHTTPHeadersを設定...")
            context = browser.new_context(
                ignore_https_errors=True,
                extra_http_headers={
                    "Proxy-Authorization": f"Basic {auth_b64}"
                }
            )
            print("   ✅ コンテキスト作成完了")

            page = context.new_page()

            test_url = "https://example.com"
            print(f"\n3. {test_url} にアクセス...")

            response = page.goto(test_url, timeout=30000)

            print(f"   ✅ ステータス: {response.status}")
            print(f"   ✅ URL: {response.url}")
            print(f"   ✅ タイトル: {page.title()}")

            browser.close()

            print("\n" + "=" * 70)
            print("✅ 成功：extraHTTPHeadersが機能しました！")
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


def test_chromium_extra_headers():
    """Chromium: extraHTTPHeadersでProxy-Authorizationを設定"""
    print("\n\n")
    print("=" * 70)
    print("テスト7-B: Chromium + extraHTTPHeaders")
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
    print()

    try:
        with sync_playwright() as p:
            print("1. Chromiumを起動...")
            browser = p.chromium.launch(
                headless=True,
                proxy={"server": server},
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-gpu',
                    '--ignore-certificate-errors',
                ]
            )
            print("   ✅ Chromium起動完了")

            # extraHTTPHeadersを設定してコンテキストを作成
            print("\n2. extraHTTPHeadersを設定...")
            context = browser.new_context(
                ignore_https_errors=True,
                extra_http_headers={
                    "Proxy-Authorization": f"Basic {auth_b64}"
                }
            )
            print("   ✅ コンテキスト作成完了")

            page = context.new_page()

            test_url = "https://example.com"
            print(f"\n3. {test_url} にアクセス...")

            response = page.goto(test_url, timeout=30000)

            print(f"   ✅ ステータス: {response.status}")
            print(f"   ✅ URL: {response.url}")
            print(f"   ✅ タイトル: {page.title()}")

            browser.close()

            print("\n" + "=" * 70)
            print("✅ 成功：Chromiumでも機能しました！")
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
    print("extraHTTPHeadersテスト")
    print()

    result_firefox = test_firefox_extra_headers()
    result_chromium = test_chromium_extra_headers()

    print("\n\n")
    print("=" * 70)
    print("最終結論")
    print("=" * 70)
    print(f"\nFirefox + extraHTTPHeaders: {'✅ 成功' if result_firefox else '❌ 失敗'}")
    print(f"Chromium + extraHTTPHeaders: {'✅ 成功' if result_chromium else '❌ 失敗'}")

    if result_firefox or result_chromium:
        print("\n🎉 proxy.pyは不要です！")
        print("\nextraHTTPHeadersでProxy-Authorizationを設定することで")
        print("Preemptive Authenticationが実現できます。")
    else:
        print("\nextraHTTPHeadersではProxy-Authorizationを設定できませんでした。")

    return result_firefox or result_chromium


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
