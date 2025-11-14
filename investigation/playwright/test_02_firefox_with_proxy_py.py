#!/usr/bin/env python3
"""
テスト2: playwright + firefox（proxy.pyあり）
proxy.pyを経由して上流プロキシに接続

このテストでは、proxy.pyを中間プロキシとして使い、
Firefoxが外部サイトにアクセスできるか確認します。
"""
import os
import sys
import subprocess
import time
import tempfile
from playwright.sync_api import sync_playwright


def test_firefox_with_proxy_py():
    print("=" * 70)
    print("テスト2: Firefox + proxy.py経由の接続")
    print("=" * 70)
    print()

    # 環境変数チェック
    https_proxy = os.getenv("HTTPS_PROXY")
    if not https_proxy:
        print("❌ エラー: HTTPS_PROXY 環境変数が設定されていません")
        sys.exit(1)

    print(f"上流プロキシ: {https_proxy}")
    print()

    # proxy.pyを起動
    proxy_port = 18912
    print(f"1. proxy.pyを起動（ポート {proxy_port}）...")
    proxy_process = subprocess.Popen(
        [
            'uv', 'run', 'proxy',
            '--hostname', '127.0.0.1',
            '--port', str(proxy_port),
            '--plugins', 'proxy.plugin.proxy_pool.ProxyPoolPlugin',
            '--proxy-pool', https_proxy,
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    # プロキシの起動を待機
    time.sleep(3)
    print(f"   ✅ proxy.py起動完了: http://127.0.0.1:{proxy_port}")

    try:
        with sync_playwright() as p:
            print("\n2. Firefoxを起動（proxy.py経由）...")

            # 一時的なHOMEディレクトリを作成
            temp_home = tempfile.mkdtemp(prefix="firefox_proxy_")
            print(f"   一時HOME: {temp_home}")

            browser = p.firefox.launch(
                headless=True,
                proxy={
                    "server": f"http://127.0.0.1:{proxy_port}",  # proxy.pyを経由
                },
                firefox_user_prefs={
                    # プライバシー設定
                    "privacy.trackingprotection.enabled": False,
                    # プロキシ設定
                    "network.proxy.allow_hijacking_localhost": True,
                    # 証明書エラーを無視
                    "network.stricttransportsecurity.preloadlist": False,
                    "security.cert_pinning.enforcement_level": 0,
                    "security.enterprise_roots.enabled": True,
                    "security.ssl.errorReporting.enabled": False,
                    "browser.xul.error_pages.expert_bad_cert": True,
                    # メディアデバイス設定
                    "media.navigator.streams.fake": True,
                },
                env={
                    **os.environ,
                    "HOME": temp_home,
                }
            )
            print("   ✅ Firefox起動完了")

            # HTTPS証明書エラーを無視するコンテキストを作成
            print("\n3. ブラウザコンテキストを作成...")
            context = browser.new_context(ignore_https_errors=True)
            page = context.new_page()
            print("   ✅ コンテキスト作成完了")

            # テストURL
            test_url = "https://example.com"
            print(f"\n4. {test_url} にアクセス...")

            response = page.goto(test_url, timeout=30000)

            print(f"   ✅ ステータス: {response.status}")
            print(f"   ✅ URL: {response.url}")
            print(f"   ✅ タイトル: {page.title()}")

            # コンテンツの一部を表示
            content = page.content()
            print(f"   ✅ コンテンツサイズ: {len(content)} bytes")

            # スクリーンショット
            screenshot_path = "/home/user/Kagami/investigation/playwright/test_02_screenshot.png"
            page.screenshot(path=screenshot_path)
            print(f"   ✅ スクリーンショット保存: {screenshot_path}")

            browser.close()

            print("\n" + "=" * 70)
            print("✅ テスト成功：proxy.pyを使うことで動作しました！")
            print("=" * 70)
            print("\nアーキテクチャ:")
            print("  Firefox")
            print("      ↓")
            print(f"  localhost:{proxy_port} (proxy.py)")
            print("      ↓ (Proxy-Authorization: Basic)")
            print("  upstream proxy (JWT認証)")
            print("      ↓")
            print("  Internet")
            print("\n結論: proxy.pyが必要です")
            print("理由: proxy.pyがPreemptive Authentication（事前認証）を実現")
            return True

    except Exception as e:
        print("\n" + "=" * 70)
        print("❌ テスト失敗")
        print("=" * 70)
        print(f"\nエラー: {e}")
        print("\nスタックトレース:")
        import traceback
        traceback.print_exc()
        return False

    finally:
        # proxy.pyを停止
        print("\n5. proxy.pyを停止...")
        proxy_process.terminate()
        try:
            proxy_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proxy_process.kill()
        print("   ✅ 停止完了")


if __name__ == "__main__":
    success = test_firefox_with_proxy_py()
    sys.exit(0 if success else 1)
