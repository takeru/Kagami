"""
claude.ai/codeへのアクセステスト

共有メモリ対策 + proxy.py でclaude.aiにアクセス
Cloudflareチャレンジの確認
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

def test_claude_ai_access():
    """claude.ai/codeへのアクセステスト"""
    proxy_process = None

    try:
        print("=" * 70)
        print("claude.ai/code アクセステスト")
        print("=" * 70)

        # proxy.pyを起動
        proxy_process = start_proxy()

        # ユーザーデータディレクトリを/tmpに作成
        user_data_dir = tempfile.mkdtemp(prefix="claude_session_", dir="/tmp")
        cache_dir = tempfile.mkdtemp(prefix="claude_cache_", dir="/tmp")
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
        ]

        print("\n" + "=" * 70)
        print("Test: https://claude.ai/code にアクセス")
        print("=" * 70)

        with sync_playwright() as p:
            print("\n[1] ブラウザ起動...")
            browser = p.chromium.launch_persistent_context(
                user_data_dir=user_data_dir,
                headless=True,
                args=chromium_args,
                ignore_https_errors=True,
            )
            print("    ✓ 成功")

            page = browser.pages[0]
            page.set_default_timeout(120000)  # 2分

            print("\n[2] https://claude.ai/code にアクセス中...")
            print("    (Cloudflareチャレンジがある可能性があります)")

            try:
                response = page.goto("https://claude.ai/code", wait_until="domcontentloaded")
                print(f"    ✓ ページロード成功")
                print(f"    Status: {response.status}")

                print("\n[3] ページ情報取得...")
                title = page.title()
                url = page.url
                content = page.content()
                content_length = len(content)

                print(f"    タイトル: '{title}'")
                print(f"    URL: {url}")
                print(f"    コンテンツ長: {content_length} 文字")

                # コンテンツ分析
                print("\n[4] コンテンツ分析...")

                if "Cloudflare" in content or "Just a moment" in content:
                    print("    ⚠️ Cloudflareチャレンジページが表示されています")
                    print("    → ブラウザ自動化検出されている可能性")

                    # チャレンジページの一部を表示
                    if "cf-challenge" in content:
                        print("    検出: cf-challenge")
                    if "ray ID" in content.lower():
                        print("    検出: Cloudflare Ray ID")

                    success = False

                elif "claude" in title.lower() or "anthropic" in content.lower():
                    print("    ✅ Claudeページにアクセスできました！")
                    print("    → Cloudflareチャレンジを突破")
                    success = True

                else:
                    print("    ⚠️ 予期しないコンテンツ")
                    print(f"    最初の1000文字:")
                    print("    " + "-" * 66)
                    print("    " + content[:1000].replace("\n", "\n    "))
                    print("    " + "-" * 66)
                    success = False

                print("\n[5] スクリーンショット...")
                page.screenshot(path="/home/user/Kagami/claude_ai_access.png")
                print("    ✓ スクリーンショット保存: claude_ai_access.png")

                # HTMLを保存
                print("\n[6] HTMLを保存...")
                with open("/home/user/Kagami/claude_ai_page.html", "w", encoding="utf-8") as f:
                    f.write(content)
                print("    ✓ HTML保存: claude_ai_page.html")

            except Exception as e:
                print(f"    ❌ ページアクセス失敗: {e}")
                success = False

            browser.close()

        if success:
            print("\n" + "=" * 70)
            print("✅ claude.ai/codeアクセス成功！")
            print("=" * 70)
            print("\n🎯 次のステップ:")
            print("  1. セッションCookieを手動で取得")
            print("  2. Cookieを使って認証済みアクセス")
            print("  3. セッション永続化の実装")
        else:
            print("\n" + "=" * 70)
            print("⚠️ Cloudflareチャレンジが表示されました")
            print("=" * 70)
            print("\n💡 対策案:")
            print("  1. undetected-chromedriverの使用")
            print("  2. Playwright stealthプラグイン")
            print("  3. 手動ログイン + Cookieエクスポート")
            print("  4. Cloudflare回避ヘッダーの追加")

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
    success = test_claude_ai_access()
    sys.exit(0 if success else 1)
