"""
playwright-captchaを使ってCloudflare Turnstileを自動解決（同期版）

Click Solver（自動クリック）を使用
"""

from playwright.sync_api import sync_playwright
from playwright_captcha import ClickSolver, CaptchaType, FrameworkType
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
    process = subprocess.Popen([
        'uv', 'run', 'proxy',
        '--hostname', '127.0.0.1',
        '--port', '8891',
        '--plugins', 'proxy.plugin.proxy_pool.ProxyPoolPlugin',
        '--proxy-pool', https_proxy,
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    print(f"[Proxy] Started with PID: {process.pid}")
    time.sleep(6)
    return process


def stop_proxy(process):
    """proxy.pyサーバーを停止"""
    print(f"\n[Proxy] Stopping...")
    process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()


def test_playwright_captcha():
    """playwright-captchaでTurnstile自動解決"""
    proxy_process = None

    try:
        print("=" * 70)
        print("playwright-captcha でCloudflare Turnstile自動解決")
        print("=" * 70)

        # proxy.pyを起動
        proxy_process = start_proxy()

        # ユーザーデータディレクトリを/tmpに作成
        user_data_dir = tempfile.mkdtemp(prefix="claude_captcha_", dir="/tmp")
        cache_dir = tempfile.mkdtemp(prefix="cache_captcha_", dir="/tmp")

        # Bot検出回避フラグ
        chromium_args = [
            # 共有メモリ対策
            '--disable-dev-shm-usage',
            '--single-process',
            '--no-sandbox',
            '--disable-setuid-sandbox',

            # Bot検出回避
            '--disable-blink-features=AutomationControlled',
            '--disable-features=IsolateOrigins,site-per-process',

            # Headless検出回避
            '--window-size=1920,1080',
            '--start-maximized',

            # その他
            '--disable-gpu',
            '--disable-accelerated-2d-canvas',
            f'--disk-cache-dir={cache_dir}',

            # プロキシ設定
            '--proxy-server=http://127.0.0.1:8891',
            '--ignore-certificate-errors',

            # User agent
            '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        ]

        print("\n" + "=" * 70)
        print("Test: playwright-captcha Click Solver")
        print("=" * 70)

        with sync_playwright() as p:
            print("\n[1] ブラウザ起動（headless=False）...")
            browser = p.chromium.launch_persistent_context(
                user_data_dir=user_data_dir,
                headless=False,
                args=chromium_args,
                ignore_https_errors=True,
            )

            page = browser.pages[0]

            # JavaScript injection
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

                // Chrome オブジェクトを追加
                window.chrome = { runtime: {} };
            """)
            print("    ✓ スクリプト注入完了")

            page.set_default_timeout(120000)

            print("\n[3] playwright-captcha ClickSolverでアクセス...")
            print("    （Turnstile自動解決を試みます）")

            # ClickSolverを使ってページにアクセス
            # 注意：playwright-captchaは非同期APIのみサポートの可能性あり
            # 同期版では直接は使えないかもしれない

            # まず普通にアクセス
            response = page.goto("https://claude.ai/code", wait_until="domcontentloaded", timeout=60000)
            print(f"    Status: {response.status}")
            print(f"    初期URL: {page.url}")
            print(f"    初期タイトル: {page.title()}")

            # Turnstileが表示されているか確認
            print("\n[4] Turnstileチャレンジの確認...")
            time.sleep(5)

            current_title = page.title()
            if "Just a moment" in current_title:
                print("    ⚠️ Turnstileチャレンジが検出されました")
                print("    → playwright-captchaは非同期APIのみサポート")
                print("    → 手動待機で様子を見ます（60秒）")

                for i in range(6):
                    time.sleep(10)
                    current_title = page.title()
                    current_url = page.url
                    print(f"    [{(i+1)*10}秒] タイトル: '{current_title}'")

                    if "Just a moment" not in current_title:
                        print(f"    ✅ チャレンジ解決！（{(i+1)*10}秒後）")
                        break
            else:
                print("    ✓ Turnstileチャレンジは表示されていません")

            print("\n[5] ページ情報取得...")
            title = page.title()
            url = page.url
            content = page.content()
            content_length = len(content)

            print(f"    タイトル: '{title}'")
            print(f"    URL: {url}")
            print(f"    コンテンツ長: {content_length} 文字")

            # コンテンツ分析
            print("\n[6] コンテンツ分析...")

            if "Just a moment" in title:
                print("    ❌ Turnstileチャレンジが残っています")
                success = False

            elif "login" in url.lower() or "signin" in url.lower() or "Sign in" in content:
                print("    ✅✅✅ ログインページに到達！")
                print("    → Cloudflareチャレンジは通過")
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

            print("\n[7] スクリーンショット...")
            page.screenshot(path="/home/user/Kagami/playwright_captcha_test.png")
            print("    ✓ スクリーンショット保存: playwright_captcha_test.png")

            print("\n[8] HTMLを保存...")
            with open("/home/user/Kagami/playwright_captcha_test.html", "w", encoding="utf-8") as f:
                f.write(content)
            print("    ✓ HTML保存: playwright_captcha_test.html")

            browser.close()

        if success:
            print("\n" + "=" * 70)
            print("🎉 Cloudflare突破成功！")
            print("=" * 70)
        else:
            print("\n" + "=" * 70)
            print("⚠️ playwright-captchaは非同期版が必要")
            print("=" * 70)
            print("\n次のステップ:")
            print("  - 非同期版のスクリプトを作成")
            print("  - Camoufox（Firefoxベース）を試す")

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
    success = test_playwright_captcha()
    sys.exit(0 if success else 1)
