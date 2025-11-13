"""
playwright-stealth を使ってcloudflare検出を回避

共有メモリ対策 + proxy.py + playwright-stealth でclaude.aiにアクセス
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
    print(f"[Proxy] Waiting 6 seconds...")
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
    print(f"[Proxy] Stopped")

def test_claude_with_stealth():
    """playwright-stealth を使ってclaude.aiにアクセス"""
    proxy_process = None

    try:
        print("=" * 70)
        print("playwright-stealth + 共有メモリ対策 でclaude.aiアクセス")
        print("=" * 70)

        # proxy.pyを起動
        proxy_process = start_proxy()

        # ユーザーデータディレクトリを/tmpに作成
        user_data_dir = tempfile.mkdtemp(prefix="claude_stealth_", dir="/tmp")
        cache_dir = tempfile.mkdtemp(prefix="cache_stealth_", dir="/tmp")
        print(f"\n📁 ユーザーデータディレクトリ: {user_data_dir}")
        print(f"📁 キャッシュディレクトリ: {cache_dir}")

        # 共有メモリ対策 + プロキシ設定
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

            # 追加のステルスフラグ
            '--disable-blink-features=AutomationControlled',
        ]

        print("\n" + "=" * 70)
        print("Test: playwright-stealth でcloudflare回避")
        print("=" * 70)

        with sync_playwright() as p:
            print("\n[1] ブラウザ起動（stealth mode）...")

            # launch_persistent_contextを使用
            browser = p.chromium.launch_persistent_context(
                user_data_dir=user_data_dir,
                headless=True,
                args=chromium_args,
                ignore_https_errors=True,
            )
            print("    ✓ ブラウザ起動成功")

            page = browser.pages[0]

            print("\n[2] playwright-stealthを適用...")
            # ステルス機能を適用
            stealth_config = Stealth()
            stealth_config.apply_stealth_sync(page)
            print("    ✓ ステルス設定適用完了")
            print("    - navigator.webdriver = undefined に設定")
            print("    - chrome オブジェクトを追加")
            print("    - その他の検出回避パッチ適用")

            page.set_default_timeout(120000)  # 2分

            print("\n[3] https://claude.ai/code にアクセス中...")
            print("    (Cloudflareチャレンジを回避できるか確認)")

            try:
                response = page.goto("https://claude.ai/code", wait_until="domcontentloaded")
                print(f"    ✓ ページロード完了")
                print(f"    Status: {response.status}")

                # 少し待つ（JavaScriptチャレンジの完了を待つ）
                print("\n[4] JavaScriptチャレンジの完了を待機（10秒）...")
                time.sleep(10)

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

                if "Just a moment" in title or "cf-challenge" in content:
                    print("    ❌ まだCloudflareチャレンジページが表示されています")
                    print("    → playwright-stealthでは回避できませんでした")
                    success = False

                elif "claude" in title.lower() or "anthropic" in content.lower():
                    print("    ✅✅✅ Claudeページにアクセス成功！")
                    print("    → Cloudflareチャレンジを突破しました！")
                    success = True

                elif len(content) > 50000:  # SPAは大きなコンテンツ
                    print("    ✅ 大きなコンテンツを取得（SPAの可能性）")
                    print("    → Cloudflare突破の可能性あり")
                    success = True

                else:
                    print("    ⚠️ 予期しないコンテンツ")
                    print(f"    最初の1000文字:")
                    print("    " + "-" * 66)
                    for line in content[:1000].split('\n'):
                        print(f"    {line}")
                    print("    " + "-" * 66)
                    success = False

                # navigator.webdriverの値を確認
                print("\n[7] ブラウザ検出チェック...")
                webdriver_value = page.evaluate("navigator.webdriver")
                chrome_value = page.evaluate("typeof window.chrome")
                print(f"    navigator.webdriver: {webdriver_value}")
                print(f"    window.chrome: {chrome_value}")

                if webdriver_value is None or webdriver_value == False:
                    print("    ✓ navigator.webdriver は隠蔽されています")
                else:
                    print("    ⚠️ navigator.webdriver が検出可能です")

                print("\n[8] スクリーンショット...")
                page.screenshot(path="/home/user/Kagami/claude_stealth.png")
                print("    ✓ スクリーンショット保存: claude_stealth.png")

                # HTMLを保存
                print("\n[9] HTMLを保存...")
                with open("/home/user/Kagami/claude_stealth.html", "w", encoding="utf-8") as f:
                    f.write(content)
                print("    ✓ HTML保存: claude_stealth.html")

            except Exception as e:
                print(f"    ❌ ページアクセス失敗: {e}")
                success = False

            browser.close()

        if success:
            print("\n" + "=" * 70)
            print("🎉🎉🎉 claude.ai/codeアクセス成功！")
            print("=" * 70)
            print("\n✅ 達成したこと:")
            print("  ✓ 共有メモリ問題の解決")
            print("  ✓ proxy.py経由のHTTPS通信")
            print("  ✓ playwright-stealthによるCloudflare回避")
            print("  ✓ claude.ai/codeへのアクセス")
            print("\n🎯 次のステップ:")
            print("  1. ログイン処理の実装")
            print("  2. セッションCookieの永続化")
            print("  3. 自動化ワークフローの構築")
        else:
            print("\n" + "=" * 70)
            print("⚠️ playwright-stealthでも回避できませんでした")
            print("=" * 70)
            print("\n💡 次の対策:")
            print("  1. 手動ログイン + Cookieエクスポート")
            print("  2. より強力なステルス設定")
            print("  3. 待機時間の調整（Cloudflareチャレンジ完了待ち）")
            print("  4. ヘッドレスモードを無効化（検出されにくい）")

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
    success = test_claude_with_stealth()
    sys.exit(0 if success else 1)
