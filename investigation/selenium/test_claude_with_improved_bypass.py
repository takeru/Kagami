"""
mainブランチの改良されたCloudflare回避方法 + Cookie認証

mainブランチの04_cloudflare_bypass.pyで発見された新しいアプローチ：
- --disable-blink-features=AutomationControlled
- --disable-features=IsolateOrigins,site-per-process
- add_init_script()によるJavaScript注入
- User agent偽装

これらをCookie認証と組み合わせます。
"""

from playwright.sync_api import sync_playwright
import tempfile
import subprocess
import time
import os
import sys
import json
import base64


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


def load_cookies_from_env():
    """環境変数からCookieを読み込む"""
    cookies_base64 = os.getenv('CLAUDE_COOKIES_BASE64')

    if not cookies_base64:
        print("\n⚠️  環境変数 CLAUDE_COOKIES_BASE64 が設定されていません")
        return None

    try:
        # base64デコード
        cookies_json = base64.b64decode(cookies_base64).decode('utf-8')
        # JSONパース
        cookies = json.loads(cookies_json)

        # Cookieのフォーマットを正規化
        for cookie in cookies:
            same_site = cookie.get('sameSite', 'Lax')
            if same_site not in ['Strict', 'Lax', 'None']:
                cookie['sameSite'] = 'Lax'
            if 'httpOnly' not in cookie:
                cookie['httpOnly'] = False
            if 'secure' not in cookie:
                cookie['secure'] = True

        return cookies
    except Exception as e:
        print(f"❌ Cookie解析エラー: {e}")
        return None


def test_improved_bypass():
    """改良されたCloudflare回避方法でテスト"""
    proxy_process = None

    try:
        print("=" * 70)
        print("改良されたCloudflare回避 + Cookie認証")
        print("=" * 70)

        # Cookieを読み込む
        cookies = load_cookies_from_env()
        if cookies is None:
            print("❌ Cookie読み込みに失敗")
            return False

        print(f"\n✓ Cookieを読み込みました: {len(cookies)}個")

        # proxy.pyを起動
        proxy_process = start_proxy()

        # ユーザーデータディレクトリを/tmpに作成
        user_data_dir = tempfile.mkdtemp(prefix="claude_improved_", dir="/tmp")
        cache_dir = tempfile.mkdtemp(prefix="cache_improved_", dir="/tmp")

        # mainブランチの改良されたフラグ
        chromium_args = [
            # 共有メモリ対策
            '--disable-dev-shm-usage',
            '--single-process',
            '--no-sandbox',
            '--disable-setuid-sandbox',

            # Bot検出回避（重要）★mainブランチから
            '--disable-blink-features=AutomationControlled',
            '--disable-features=IsolateOrigins,site-per-process',

            # Headless検出回避★mainブランチから
            '--window-size=1920,1080',
            '--start-maximized',

            # その他
            '--disable-gpu',
            '--disable-accelerated-2d-canvas',
            f'--disk-cache-dir={cache_dir}',

            # プロキシ設定
            '--proxy-server=http://127.0.0.1:8891',
            '--ignore-certificate-errors',

            # User agent★mainブランチから
            '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        ]

        print("\n" + "=" * 70)
        print("Test: mainブランチの改良手法 + Cookie認証")
        print("=" * 70)

        with sync_playwright() as p:
            print("\n[1] ブラウザ起動（改良されたAnti-detection設定）...")
            browser = p.chromium.launch_persistent_context(
                user_data_dir=user_data_dir,
                headless=True,
                args=chromium_args,
                ignore_https_errors=True,
            )

            page = browser.pages[0]

            # ★mainブランチのJavaScript injection
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

            print("\n[3] Cookieをインポート...")
            # まず claude.ai に移動してからCookieを設定
            page.goto("https://claude.ai", timeout=30000)
            time.sleep(2)

            # Cookieを追加
            browser.add_cookies(cookies)
            print(f"    ✓ {len(cookies)}個のCookieをインポートしました")

            # 偽装が機能しているか確認
            print("\n[4] 偽装が機能しているか確認...")
            webdriver_value = page.evaluate("navigator.webdriver")
            plugins_count = page.evaluate("navigator.plugins.length")
            print(f"    navigator.webdriver: {webdriver_value} (undefinedならOK)")
            print(f"    navigator.plugins: {plugins_count}個")

            page.set_default_timeout(120000)

            print("\n[5] https://claude.ai/code にアクセス中...")
            print("    （改良されたAnti-detection + Cookie認証）")

            response = page.goto("https://claude.ai/code", wait_until="domcontentloaded", timeout=60000)
            print(f"    Status: {response.status}")

            # 少し待つ
            print("\n[6] ページロード待機（10秒）...")
            time.sleep(10)

            print("\n[7] ページ情報取得...")
            title = page.title()
            url = page.url
            content = page.content()
            content_length = len(content)

            print(f"    タイトル: '{title}'")
            print(f"    URL: {url}")
            print(f"    コンテンツ長: {content_length} 文字")

            # コンテンツ分析
            print("\n[8] コンテンツ分析...")

            if "Just a moment" in title or "cf-challenge" in content:
                print("    ❌ まだCloudflareチャレンジが表示されています")
                success = False

            elif response.status == 200 and "claude" in title.lower():
                print("    ✅✅✅ Claudeページアクセス成功！")
                success = True

            elif response.status == 200 and len(content) > 50000:
                print("    ✅ 大きなコンテンツ取得（SPAの可能性）")
                success = True

            elif "login" in url.lower() or "signin" in url.lower():
                print("    ⚠️ ログインページにリダイレクトされました")
                success = False

            else:
                print("    ⚠️ 予期しないコンテンツ")
                success = False

            print("\n[9] スクリーンショット...")
            page.screenshot(path="/home/user/Kagami/claude_improved_bypass.png")
            print("    ✓ スクリーンショット保存: claude_improved_bypass.png")

            print("\n[10] HTMLを保存...")
            with open("/home/user/Kagami/claude_improved_bypass.html", "w", encoding="utf-8") as f:
                f.write(content)
            print("    ✓ HTML保存: claude_improved_bypass.html")

            browser.close()

        if success:
            print("\n" + "=" * 70)
            print("🎉🎉🎉 claude.ai/code アクセス成功！")
            print("=" * 70)
            print("\n✅ 使用した技術:")
            print("  ✓ mainブランチの改良されたChromiumフラグ")
            print("  ✓ add_init_script()によるJavaScript注入")
            print("  ✓ User agent偽装")
            print("  ✓ 共有メモリ問題の解決")
            print("  ✓ proxy.py経由のHTTPS通信")
            print("  ✓ Cookie認証")
        else:
            print("\n" + "=" * 70)
            print("⚠️ アクセス失敗")
            print("=" * 70)
            print("\n考えられる原因:")
            print("  - IPアドレスバインディング（最も可能性が高い）")
            print("  - Cookieが無効または期限切れ")
            print("  - さらに高度なフィンガープリント検出")

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
    success = test_improved_bypass()
    sys.exit(0 if success else 1)
