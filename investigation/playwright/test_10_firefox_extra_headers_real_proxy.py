#!/usr/bin/env python3
"""
テスト10: Firefox + extraHTTPHeaders + 実際のプロキシで動作確認

実際のHTTPS_PROXY環境変数を使って、Firefoxでproxy.pyなしで
外部サイトにアクセスできるか確認します。
"""
import os
import sys
import base64
import tempfile
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright


def extract_proxy_credentials(proxy_url):
    """プロキシURLから認証情報を抽出"""
    if not proxy_url:
        return None, None, None

    parsed = urlparse(proxy_url)
    username = parsed.username or ""
    password = parsed.password or ""

    if parsed.port:
        server = f"{parsed.scheme}://{parsed.hostname}:{parsed.port}"
    else:
        server = f"{parsed.scheme}://{parsed.hostname}"

    return server, username, password


def test_firefox_with_extra_headers():
    """Firefox + extraHTTPHeaders方式でアクセステスト"""
    print("=" * 70)
    print("テスト: Firefox + extraHTTPHeaders + 実際のプロキシ")
    print("=" * 70)
    print()

    https_proxy = os.getenv("HTTPS_PROXY")
    if not https_proxy:
        print("❌ HTTPS_PROXY環境変数が設定されていません")
        return False

    # URLの構造を表示（認証情報はマスク）
    import re
    masked_url = re.sub(r'(://[^:]+:)[^@]+(@)', r'\1***\2', https_proxy)
    print(f"プロキシ: {masked_url}")
    print()

    server, username, password = extract_proxy_credentials(https_proxy)

    # Basic認証ヘッダーの値を作成
    auth_string = f"{username}:{password}"
    auth_bytes = auth_string.encode('utf-8')
    auth_b64 = base64.b64encode(auth_bytes).decode('utf-8')

    print(f"プロキシサーバー: {server}")
    print(f"認証ヘッダー: Basic {auth_b64[:30]}...")
    print()

    try:
        with sync_playwright() as p:
            temp_home = tempfile.mkdtemp(prefix="firefox_extra_headers_")

            print("1. Firefoxを起動中...")
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
            print("\n2. extraHTTPHeadersでProxy-Authorizationを設定中...")
            context = browser.new_context(
                ignore_https_errors=True,
                extra_http_headers={
                    "Proxy-Authorization": f"Basic {auth_b64}"
                }
            )
            print("   ✅ コンテキスト作成完了")

            page = context.new_page()

            # テスト: example.comにアクセス
            test_url = "https://example.com"
            print(f"\n3. {test_url} にアクセス中...")

            try:
                response = page.goto(test_url, timeout=30000)

                print(f"   ✅ ステータス: {response.status}")
                print(f"   ✅ URL: {response.url}")

                title = page.title()
                print(f"   ✅ タイトル: {title}")

                # ページの一部を取得して確認
                body_text = page.locator("body").text_content()
                if body_text:
                    preview = body_text[:100].replace('\n', ' ')
                    print(f"   ✅ コンテンツ: {preview}...")

                browser.close()

                print("\n" + "=" * 70)
                print("🎉 成功: proxy.pyなしでFirefoxから外部サイトにアクセスできました！")
                print("=" * 70)
                print()
                print("✅ extraHTTPHeaders方式が正しく動作しています")
                print("✅ プロキシ認証が成功しました")
                print("✅ proxy.pyは不要です！")
                return True

            except Exception as e:
                print(f"\n   ❌ アクセス失敗: {e}")
                browser.close()
                return False

    except Exception as e:
        print("\n" + "=" * 70)
        print("❌ 失敗")
        print("=" * 70)
        print(f"\nエラー: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    print("Firefox + extraHTTPHeaders方式の実際のプロキシでの動作確認")
    print()

    success = test_firefox_with_extra_headers()

    print()
    if success:
        print("=" * 70)
        print("最終結論")
        print("=" * 70)
        print()
        print("🎉 Firefox + extraHTTPHeaders方式が実際の環境で動作しました！")
        print()
        print("確認できたこと:")
        print("  ✅ 実際のHTTPS_PROXY環境変数から認証情報を抽出")
        print("  ✅ extraHTTPHeadersでProxy-Authorizationヘッダーを設定")
        print("  ✅ proxy.pyなしで外部サイトにアクセス成功")
        print()
        print("これで以下が実現できました:")
        print("  • proxy.py不要")
        print("  • シンプルな構成")
        print("  • プロセス数の削減")
        print("  • レイテンシの改善")

    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
