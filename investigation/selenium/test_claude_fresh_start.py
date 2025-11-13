"""
Cookie一切なし、まっさらな状態からclaude.ai/codeにアクセス

Cloudflareチャレンジが自動的に解決されるかテスト
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


def test_fresh_start():
    """Cookieなし、まっさらな状態でテスト"""
    proxy_process = None

    try:
        print("=" * 70)
        print("まっさらな状態からclaude.ai/codeアクセス（Cookie一切なし）")
        print("=" * 70)

        # proxy.pyを起動
        proxy_process = start_proxy()

        # ユーザーデータディレクトリを/tmpに作成
        user_data_dir = tempfile.mkdtemp(prefix="claude_fresh_", dir="/tmp")
        cache_dir = tempfile.mkdtemp(prefix="cache_fresh_", dir="/tmp")

        # mainブランチの改良されたフラグ
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
        print("Test: まっさらな状態でCloudflareチャレンジ")
        print("=" * 70)

        with sync_playwright() as p:
            print("\n[1] ブラウザ起動（headless=False、Cookie一切なし）...")
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

            # 偽装が機能しているか確認（まずabout:blankで）
            print("\n[3] 偽装が機能しているか確認...")
            page.goto("about:blank")
            webdriver_value = page.evaluate("navigator.webdriver")
            plugins_count = page.evaluate("navigator.plugins.length")
            print(f"    navigator.webdriver: {webdriver_value} (undefinedならOK)")
            print(f"    navigator.plugins: {plugins_count}個")

            page.set_default_timeout(120000)

            print("\n[4] https://claude.ai/code にアクセス中...")
            print("    （Cookie一切なし、まっさらな状態）")

            response = page.goto("https://claude.ai/code", wait_until="domcontentloaded", timeout=60000)
            print(f"    Status: {response.status}")

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

                # URLが変更されても、"Just a moment"が消えるまで待機を続ける

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
                print("    ❌ Cloudflareチャレンジが解決されませんでした")
                success = False

            elif "login" in url.lower() or "signin" in url.lower() or "Sign in" in content:
                print("    ✅ ログインページに到達！")
                print("    → Cloudflareチャレンジは通過したが、未ログイン状態")
                success = True

            elif response.status == 200 and "claude" in title.lower():
                print("    ✅✅✅ Claudeページアクセス成功！")
                success = True

            elif response.status == 200 and len(content) > 50000:
                print("    ✅ 大きなコンテンツ取得（SPAの可能性）")
                success = True

            else:
                print("    ⚠️ 予期しないコンテンツ")
                print(f"    最初の500文字:")
                print("    " + "-" * 66)
                for line in content[:500].split('\n')[:10]:
                    print(f"    {line}")
                print("    " + "-" * 66)
                success = False

            print("\n[8] スクリーンショット...")
            page.screenshot(path="/home/user/Kagami/claude_fresh_start.png")
            print("    ✓ スクリーンショット保存: claude_fresh_start.png")

            print("\n[9] HTMLを保存...")
            with open("/home/user/Kagami/claude_fresh_start.html", "w", encoding="utf-8") as f:
                f.write(content)
            print("    ✓ HTML保存: claude_fresh_start.html")

            # Cookieが生成されたか確認
            print("\n[10] 生成されたCookieを確認...")
            cookies = browser.cookies()
            print(f"    生成されたCookie数: {len(cookies)}個")
            if len(cookies) > 0:
                print("    Cookie一覧:")
                for cookie in cookies[:5]:  # 最初の5個だけ表示
                    print(f"      - {cookie['name']}: {cookie['value'][:20]}...")

            browser.close()

        if success:
            print("\n" + "=" * 70)
            print("🎉 Cloudflareチャレンジ通過！")
            print("=" * 70)
        else:
            print("\n" + "=" * 70)
            print("⚠️ Cloudflareチャレンジ通過失敗")
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
    success = test_fresh_start()
    sys.exit(0 if success else 1)
