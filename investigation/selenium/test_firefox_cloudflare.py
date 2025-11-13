"""
Firefoxを使ってCloudflare Turnstileを突破

mainブランチの08_firefox_with_proxy.pyをベースに、
claude.ai/codeへのアクセスを試みる
"""

from playwright.sync_api import sync_playwright
import tempfile
import subprocess
import time
import os
import sys


def start_proxy():
    """proxy.pyサーバーを起動"""
    https_proxy = os.getenv('HTTPS_PROXY')
    if not https_proxy:
        raise Exception("HTTPS_PROXY environment variable is not set")

    print(f"[Proxy] Starting proxy.py...")
    proxy_port = 8910
    process = subprocess.Popen([
        'uv', 'run', 'proxy',
        '--hostname', '127.0.0.1',
        '--port', str(proxy_port),
        '--plugins', 'proxy.plugin.proxy_pool.ProxyPoolPlugin',
        '--proxy-pool', https_proxy,
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    print(f"[Proxy] Started with PID: {process.pid}")
    time.sleep(6)
    return process, proxy_port


def stop_proxy(process):
    """proxy.pyサーバーを停止"""
    print(f"\n[Proxy] Stopping...")
    process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()


def test_firefox_cloudflare():
    """FirefoxでCloudflare Turnstile突破を試みる"""
    proxy_process = None

    try:
        print("=" * 70)
        print("Firefoxを使ってCloudflare Turnstile突破")
        print("=" * 70)

        # proxy.pyを起動
        proxy_process, proxy_port = start_proxy()

        print("\n" + "=" * 70)
        print("Test: Firefox + Anti-detection + Cloudflare Turnstile")
        print("=" * 70)

        with sync_playwright() as p:
            print("\n[1] Firefoxを起動（プロキシ経由、Anti-detection設定）...")

            # 一時的なプロファイルディレクトリを作成
            user_data_dir = tempfile.mkdtemp(prefix="firefox_profile_", dir="/tmp")

            browser = p.firefox.launch_persistent_context(
                user_data_dir=user_data_dir,
                headless=True,  # headlessモードで試す（xvfb経由）
                proxy={
                    "server": f"http://127.0.0.1:{proxy_port}",
                },
                firefox_user_prefs={
                    # プライバシー設定
                    "privacy.trackingprotection.enabled": False,
                    "privacy.resistFingerprinting": False,  # フィンガープリント対策を無効化

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

                    # WebDriver検出回避
                    "dom.webdriver.enabled": False,
                    "useAutomationExtension": False,

                    # User agent
                    "general.useragent.override": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0",
                },
                ignore_https_errors=True,
                ignore_default_args=["--enable-automation"],
            )
            print("   ✅ Firefox起動完了（Anti-detection設定済み）")

            page = browser.pages[0]

            # JavaScript injectionでさらに偽装
            print("\n[2] Anti-detectionスクリプトを注入...")
            page.add_init_script("""
                // navigator.webdriver を隠す
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });

                // プラグインを偽装
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5]
                });

                // 言語設定
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['en-US', 'en']
                });
            """)
            print("    ✓ スクリプト注入完了")

            # webdriverが隠されているか確認
            print("\n[3] 偽装が機能しているか確認...")
            page.goto("about:blank")
            webdriver_value = page.evaluate("navigator.webdriver")
            print(f"    navigator.webdriver: {webdriver_value} (undefinedならOK)")

            page.set_default_timeout(120000)

            print("\n[4] https://claude.ai/code にアクセス中...")
            print("    （Firefoxでcloudflare Turnstile突破を試みます）")

            response = page.goto("https://claude.ai/code", wait_until="domcontentloaded", timeout=60000)
            print(f"    Status: {response.status}")
            print(f"    初期URL: {page.url}")
            print(f"    初期タイトル: {page.title()}")

            # Cloudflareチャレンジの自動解決を待つ（最大90秒）
            print("\n[5] Cloudflareチャレンジの自動解決を待機（最大90秒）...")
            for i in range(9):  # 10秒 × 9回 = 90秒
                time.sleep(10)
                current_title = page.title()
                current_url = page.url
                print(f"    [{(i+1)*10}秒] タイトル: '{current_title}' | URL: {current_url}")

                # チャレンジが解決されたかチェック
                if "Just a moment" not in current_title:
                    if "claude" in current_title.lower():
                        print(f"    ✅ Cloudflareチャレンジが解決されました！（{(i+1)*10}秒後）")
                        break
                    elif "login" in current_url.lower() or "signin" in current_url.lower():
                        print(f"    ✅ ログインページに到達（{(i+1)*10}秒後）")
                        break

            print("\n[6] ページ情報取得...")
            title = page.title()
            url = page.url
            content = page.content()
            content_length = len(content)

            print(f"    タイトル: '{title}'")
            print(f"    URL: {url}")
            print(f"    コンテンツ長: {content_length} 文字")

            # コンテンツ分析
            print("\n[7] コンテンツ分析...")

            if "Just a moment" in title:
                print("    ❌ Turnstileチャレンジが残っています")
                success = False

            elif "login" in url.lower() or "signin" in url.lower() or "Sign in" in content:
                print("    ✅✅✅ ログインページに到達！")
                print("    → Cloudflareチャレンジは通過（Firefox成功！）")
                success = True

            elif response.status == 200 and "claude" in title.lower():
                print("    ✅✅✅ Claudeページアクセス成功！")
                success = True

            elif response.status == 200 and len(content) > 50000:
                print("    ✅ 大きなコンテンツ取得（SPAの可能性）")
                success = True

            else:
                print("    ⚠️ 予期しないコンテンツ")
                success = False

            print("\n[8] スクリーンショット...")
            page.screenshot(path="/home/user/Kagami/firefox_cloudflare_test.png")
            print("    ✓ スクリーンショット保存: firefox_cloudflare_test.png")

            print("\n[9] HTMLを保存...")
            with open("/home/user/Kagami/firefox_cloudflare_test.html", "w", encoding="utf-8") as f:
                f.write(content)
            print("    ✓ HTML保存: firefox_cloudflare_test.html")

            # Cookieが生成されたか確認
            print("\n[10] 生成されたCookieを確認...")
            cookies = browser.cookies()
            print(f"    生成されたCookie数: {len(cookies)}個")
            if len(cookies) > 0:
                print("    Cookie一覧:")
                for cookie in cookies[:10]:  # 最初の10個だけ表示
                    print(f"      - {cookie['name']}: {cookie['value'][:30]}...")

            browser.close()

        if success:
            print("\n" + "=" * 70)
            print("🎉🎉🎉 Firefox でCloudflare突破成功！")
            print("=" * 70)
            print("\n✅ 使用した技術:")
            print("  ✓ Firefox（Chromiumではなく）")
            print("  ✓ firefox_user_prefs による詳細設定")
            print("  ✓ Anti-detectionスクリプト")
            print("  ✓ proxy.py経由のHTTPS通信")
        else:
            print("\n" + "=" * 70)
            print("⚠️ Firefox でもCloudflare突破失敗")
            print("=" * 70)

        return success

    except Exception as e:
        print(f"\n❌ エラー: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        if proxy_process:
            stop_proxy(proxy_process)


if __name__ == "__main__":
    success = test_firefox_cloudflare()
    sys.exit(0 if success else 1)
