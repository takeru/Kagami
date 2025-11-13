"""
playwright-stealth + より長い待機時間

CloudflareのJavaScriptチャレンジが完了するまで待機
"""

from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth
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

def test_claude_longer_wait():
    """より長い待機時間でCloudflareチャレンジ完了を待つ"""
    proxy_process = None

    try:
        print("=" * 70)
        print("playwright-stealth + 長時間待機でCloudflare回避")
        print("=" * 70)

        proxy_process = start_proxy()

        user_data_dir = tempfile.mkdtemp(prefix="claude_wait_", dir="/tmp")
        cache_dir = tempfile.mkdtemp(prefix="cache_wait_", dir="/tmp")

        chromium_args = [
            '--disable-dev-shm-usage',
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--single-process',
            '--disable-gpu',
            '--disable-accelerated-2d-canvas',
            f'--disk-cache-dir={cache_dir}',
            '--proxy-server=http://127.0.0.1:8891',
            '--ignore-certificate-errors',
            '--disable-blink-features=AutomationControlled',
        ]

        with sync_playwright() as p:
            print("\n[1] ブラウザ起動...")
            browser = p.chromium.launch_persistent_context(
                user_data_dir=user_data_dir,
                headless=True,
                args=chromium_args,
                ignore_https_errors=True,
            )

            page = browser.pages[0]

            print("[2] playwright-stealthを適用...")
            stealth_config = Stealth()
            stealth_config.apply_stealth_sync(page)
            print("    ✓ ステルス適用完了")

            page.set_default_timeout(120000)

            print("\n[3] https://claude.ai/code にアクセス...")
            response = page.goto("https://claude.ai/code", wait_until="domcontentloaded")
            print(f"    Status: {response.status}")

            # 段階的に待機して進捗を確認
            wait_intervals = [5, 10, 15, 20, 30]  # 合計80秒

            for i, interval in enumerate(wait_intervals, 1):
                print(f"\n[4-{i}] {interval}秒待機中...")
                time.sleep(interval)

                title = page.title()
                url = page.url
                content_length = len(page.content())

                print(f"    タイトル: '{title}'")
                print(f"    URL長: {len(url)}")
                print(f"    コンテンツ長: {content_length} 文字")

                # チャレンジページかチェック
                if "Just a moment" not in title and "cf-challenge" not in page.content()[:1000]:
                    print(f"    ✅ Cloudflareチャレンジを突破した可能性！")
                    break
                else:
                    print(f"    ⏳ まだチャレンジページ（累計{sum(wait_intervals[:i])}秒待機）")

            print("\n[5] 最終確認...")
            title = page.title()
            content = page.content()

            print(f"    最終タイトル: '{title}'")
            print(f"    最終コンテンツ長: {len(content)} 文字")

            if "Just a moment" in title or "cf-challenge" in content:
                print("    ❌ Cloudflareチャレンジ未突破")
                success = False
            elif "claude" in title.lower() or "anthropic" in content.lower():
                print("    ✅✅✅ Claudeページアクセス成功！")
                success = True
            elif len(content) > 50000:
                print("    ✅ 大きなコンテンツ取得（SPAの可能性）")
                success = True
            else:
                print("    ⚠️ 予期しないコンテンツ")
                success = False

            # navigator.webdriver確認
            webdriver = page.evaluate("navigator.webdriver")
            print(f"\n[6] navigator.webdriver: {webdriver}")

            print("\n[7] スクリーンショット...")
            page.screenshot(path="/home/user/Kagami/claude_longer_wait.png")

            with open("/home/user/Kagami/claude_longer_wait.html", "w", encoding="utf-8") as f:
                f.write(content)

            browser.close()

        if success:
            print("\n" + "=" * 70)
            print("🎉 claude.ai/code アクセス成功！")
            print("=" * 70)
        else:
            print("\n" + "=" * 70)
            print("⚠️ 長時間待機でも突破できませんでした")
            print("=" * 70)
            print("\n💡 Cloudflareは以下を検出している可能性:")
            print("  - ヘッドレスモード（headless=True）")
            print("  - WebGL/Canvas指紋")
            print("  - その他の高度な検出手法")
            print("\n次の対策: 手動ログイン + Cookieエクスポート")

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
    success = test_claude_longer_wait()
    sys.exit(0 if success else 1)
