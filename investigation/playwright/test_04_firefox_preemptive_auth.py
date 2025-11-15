#!/usr/bin/env python3
"""
テスト4: Firefoxでのpreemptive authentication設定を試す

proxy.pyを使わずに、PlaywrightやFirefoxの設定で
Preemptive Authenticationを実現できないか検証します。

試す方法：
1. Playwrightのproxy設定でusername/passwordを指定
2. プロキシURLに認証情報を埋め込む（http://user:pass@proxy:port）
3. Firefoxのネットワーク設定でpreemptive authを有効化
"""
import os
import sys
import tempfile
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright


def extract_proxy_credentials(proxy_url):
    """プロキシURLから認証情報を抽出"""
    parsed = urlparse(proxy_url)

    # ユーザー名とパスワードを抽出
    # 形式: http://username:password@host:port
    username = parsed.username or ""
    password = parsed.password or ""

    # ホスト部分（認証情報なし）
    if parsed.port:
        server = f"{parsed.scheme}://{parsed.hostname}:{parsed.port}"
    else:
        server = f"{parsed.scheme}://{parsed.hostname}"

    return server, username, password


def test_method_1_playwright_username_password():
    """
    方法1: Playwrightのproxy設定でusername/passwordを指定

    Playwrightは proxy.username と proxy.password をサポートしています。
    これらを指定すると、ブラウザにPreemptive Authenticationを
    させようとするかもしれません。
    """
    print("=" * 70)
    print("テスト4-A: Playwright proxy設定でusername/password指定")
    print("=" * 70)
    print()

    https_proxy = os.getenv("HTTPS_PROXY")
    if not https_proxy:
        print("❌ HTTPS_PROXY環境変数が設定されていません")
        return False

    server, username, password = extract_proxy_credentials(https_proxy)

    print(f"プロキシサーバー: {server}")
    print(f"ユーザー名: {username[:20]}..." if len(username) > 20 else f"ユーザー名: {username}")
    print(f"パスワード: {password[:20]}..." if len(password) > 20 else f"パスワード: {password}")
    print()

    try:
        with sync_playwright() as p:
            temp_home = tempfile.mkdtemp(prefix="firefox_method1_")

            print("1. Firefoxを起動（username/password指定）...")
            browser = p.firefox.launch(
                headless=True,
                proxy={
                    "server": server,
                    "username": username,  # 認証情報を明示的に指定
                    "password": password,
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

            test_url = "https://example.com"
            print(f"\n2. {test_url} にアクセス...")

            response = page.goto(test_url, timeout=30000)

            print(f"   ✅ ステータス: {response.status}")
            print(f"   ✅ URL: {response.url}")
            print(f"   ✅ タイトル: {page.title()}")

            screenshot_path = "/home/user/Kagami/investigation/playwright/test_04a_screenshot.png"
            page.screenshot(path=screenshot_path)
            print(f"   ✅ スクリーンショット: {screenshot_path}")

            browser.close()

            print("\n" + "=" * 70)
            print("✅ 成功：username/password指定でPreemptive Authが機能しました！")
            print("=" * 70)
            print("\n結論: proxy.pyは不要です（この方法で解決）")
            return True

    except Exception as e:
        print("\n" + "=" * 70)
        print("❌ 失敗")
        print("=" * 70)
        print(f"\nエラー: {e}")
        print("\n結論: username/password指定だけでは不十分")
        return False


def test_method_2_firefox_network_prefs():
    """
    方法2: Firefoxのネットワーク設定でpreemptive authを強制

    Firefoxには network.auth.force-generic-ntlm などの設定があります。
    これらの設定でpreemptive authenticationを有効化できるかもしれません。
    """
    print("\n\n")
    print("=" * 70)
    print("テスト4-B: Firefoxネットワーク設定でpreemptive auth有効化")
    print("=" * 70)
    print()

    https_proxy = os.getenv("HTTPS_PROXY")
    if not https_proxy:
        print("❌ HTTPS_PROXY環境変数が設定されていません")
        return False

    server, username, password = extract_proxy_credentials(https_proxy)

    print(f"プロキシサーバー: {server}")
    print()

    try:
        with sync_playwright() as p:
            temp_home = tempfile.mkdtemp(prefix="firefox_method2_")

            print("1. Firefoxを起動（preemptive auth設定追加）...")
            browser = p.firefox.launch(
                headless=True,
                proxy={
                    "server": server,
                    "username": username,
                    "password": password,
                },
                firefox_user_prefs={
                    # 既存の設定
                    "privacy.trackingprotection.enabled": False,
                    "network.proxy.allow_hijacking_localhost": True,
                    "network.stricttransportsecurity.preloadlist": False,
                    "security.cert_pinning.enforcement_level": 0,
                    "security.enterprise_roots.enabled": True,
                    "security.ssl.errorReporting.enabled": False,
                    "browser.xul.error_pages.expert_bad_cert": True,
                    "media.navigator.streams.fake": True,

                    # Preemptive authentication関連の設定を試す
                    "network.auth.force-generic-ntlm": True,
                    "network.automatic-ntlm-auth.allow-proxies": True,
                    "network.automatic-ntlm-auth.trusted-uris": ".anthropic.com,.example.com",
                    "network.negotiate-auth.allow-proxies": True,
                    "signon.autologin.proxy": True,
                },
                env={
                    **os.environ,
                    "HOME": temp_home,
                }
            )
            print("   ✅ Firefox起動完了")

            context = browser.new_context(ignore_https_errors=True)
            page = context.new_page()

            test_url = "https://example.com"
            print(f"\n2. {test_url} にアクセス...")

            response = page.goto(test_url, timeout=30000)

            print(f"   ✅ ステータス: {response.status}")
            print(f"   ✅ URL: {response.url}")
            print(f"   ✅ タイトル: {page.title()}")

            screenshot_path = "/home/user/Kagami/investigation/playwright/test_04b_screenshot.png"
            page.screenshot(path=screenshot_path)
            print(f"   ✅ スクリーンショット: {screenshot_path}")

            browser.close()

            print("\n" + "=" * 70)
            print("✅ 成功：Firefox設定でPreemptive Authが機能しました！")
            print("=" * 70)
            print("\n結論: proxy.pyは不要です（Firefox設定で解決）")
            return True

    except Exception as e:
        print("\n" + "=" * 70)
        print("❌ 失敗")
        print("=" * 70)
        print(f"\nエラー: {e}")
        print("\n結論: Firefox設定だけでは不十分")
        return False


def test_method_3_chromium_comparison():
    """
    方法3: Chromiumで同じ設定を試す（比較用）

    Chromiumでも同じ設定を試して、ブラウザによる違いを確認します。
    """
    print("\n\n")
    print("=" * 70)
    print("テスト4-C: Chromiumでusername/password指定（比較用）")
    print("=" * 70)
    print()

    https_proxy = os.getenv("HTTPS_PROXY")
    if not https_proxy:
        print("❌ HTTPS_PROXY環境変数が設定されていません")
        return False

    server, username, password = extract_proxy_credentials(https_proxy)

    print(f"プロキシサーバー: {server}")
    print()

    try:
        with sync_playwright() as p:
            print("1. Chromiumを起動（username/password指定）...")
            browser = p.chromium.launch(
                headless=True,
                proxy={
                    "server": server,
                    "username": username,
                    "password": password,
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

            test_url = "https://example.com"
            print(f"\n2. {test_url} にアクセス...")

            response = page.goto(test_url, timeout=30000)

            print(f"   ✅ ステータス: {response.status}")
            print(f"   ✅ URL: {response.url}")
            print(f"   ✅ タイトル: {page.title()}")

            screenshot_path = "/home/user/Kagami/investigation/playwright/test_04c_screenshot.png"
            page.screenshot(path=screenshot_path)
            print(f"   ✅ スクリーンショット: {screenshot_path}")

            browser.close()

            print("\n" + "=" * 70)
            print("✅ 成功：Chromiumでも動作しました！")
            print("=" * 70)
            return True

    except Exception as e:
        print("\n" + "=" * 70)
        print("❌ 失敗")
        print("=" * 70)
        print(f"\nエラー: {e}")
        return False


def main():
    print("Firefoxでのpreemptive authentication設定テスト")
    print()

    # 方法1: Playwrightのusername/password設定
    result1 = test_method_1_playwright_username_password()

    # 方法2: Firefoxのネットワーク設定
    result2 = test_method_2_firefox_network_prefs()

    # 方法3: Chromiumとの比較
    result3 = test_method_3_chromium_comparison()

    print("\n\n")
    print("=" * 70)
    print("テスト4 総合結果")
    print("=" * 70)
    print(f"\n方法1（Playwright username/password）: {'✅ 成功' if result1 else '❌ 失敗'}")
    print(f"方法2（Firefox network prefs）: {'✅ 成功' if result2 else '❌ 失敗'}")
    print(f"方法3（Chromium比較）: {'✅ 成功' if result3 else '❌ 失敗'}")

    if result1 or result2 or result3:
        print("\n🎉 重要な発見！")
        print("proxy.pyなしでもPreemptive Authenticationが実現できました！")
        if result1:
            print("\n推奨される方法: Playwrightのusername/password設定を使用")
        if result2:
            print("\n代替方法: Firefoxのnetwork prefsを調整")
    else:
        print("\n残念ながら、どの方法でもproxy.pyなしでは動作しませんでした。")
        print("proxy.pyが必要です。")

    return result1 or result2 or result3


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
