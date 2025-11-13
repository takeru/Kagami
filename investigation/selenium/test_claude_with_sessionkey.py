"""
SESSIONKEY環境変数だけを使ってclaude.ai/codeにアクセス

最小限のCookie構成でテスト
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

def test_with_sessionkey_only():
    """SESSIONKEY環境変数だけを使ってアクセス"""
    proxy_process = None

    try:
        print("=" * 70)
        print("SESSIONKEY環境変数のみでclaude.ai/codeアクセス")
        print("=" * 70)

        # SESSIONKEY環境変数を取得
        session_key = os.getenv('SESSIONKEY')

        if not session_key:
            print(f"\n⚠️  環境変数 SESSIONKEY が設定されていません")
            print("\n設定方法:")
            print("  export SESSIONKEY='<sessionKeyの値>'")
            return False

        print(f"\n✓ SESSIONKEY環境変数を読み込みました ({len(session_key)}文字)")

        # sessionKeyだけのCookie配列を作成
        cookies = [
            {
                "name": "sessionKey",
                "value": session_key,
                "domain": ".claude.ai",
                "path": "/",
                "httpOnly": True,
                "secure": True,
                "sameSite": "Lax"
            }
        ]

        print(f"✓ Cookieを準備しました: {len(cookies)}個")

        # proxy.pyを起動
        proxy_process = start_proxy()

        # ユーザーデータディレクトリを/tmpに作成
        user_data_dir = tempfile.mkdtemp(prefix="claude_sessionkey_", dir="/tmp")
        cache_dir = tempfile.mkdtemp(prefix="cache_sessionkey_", dir="/tmp")

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

        print("\n" + "=" * 70)
        print("Test: sessionKeyのみでclaude.ai/codeアクセス")
        print("=" * 70)

        with sync_playwright() as p:
            print("\n[1] ブラウザ起動...")
            browser = p.chromium.launch_persistent_context(
                user_data_dir=user_data_dir,
                headless=True,
                args=chromium_args,
                ignore_https_errors=True,
            )

            page = browser.pages[0]

            print("\n[2] playwright-stealthを適用...")
            stealth_config = Stealth()
            stealth_config.apply_stealth_sync(page)
            print("    ✓ ステルス適用完了")

            print("\n[3] sessionKey Cookieをインポート...")
            # まず claude.ai に移動してからCookieを設定
            page.goto("https://claude.ai")
            time.sleep(2)

            # Cookieを追加
            browser.add_cookies(cookies)
            print(f"    ✓ sessionKey Cookieをインポートしました")

            page.set_default_timeout(120000)

            print("\n[4] https://claude.ai/code にアクセス中...")
            print("    （sessionKeyで認証）")

            response = page.goto("https://claude.ai/code", wait_until="domcontentloaded")
            print(f"    Status: {response.status}")

            # 少し待つ
            print("\n[5] ページロード待機（10秒）...")
            time.sleep(10)

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

            if "Just a moment" in title or "cf-challenge" in content:
                print("    ❌ Cloudflareチャレンジが表示されています")
                print("    → sessionKeyだけでは不十分、または無効")
                success = False

            elif response.status == 200 and "claude" in title.lower():
                print("    ✅✅✅ Claudeページアクセス成功！")
                print("    → sessionKeyによる認証成功")
                success = True

            elif response.status == 200 and len(content) > 50000:
                print("    ✅ 大きなコンテンツ取得（SPAの可能性）")
                print("    → アクセス成功の可能性が高い")
                success = True

            elif "login" in url.lower() or "signin" in url.lower():
                print("    ⚠️ ログインページにリダイレクトされました")
                print("    → sessionKeyが無効または期限切れ")
                success = False

            else:
                print("    ⚠️ 予期しないコンテンツ")
                print(f"    最初の500文字:")
                print("    " + "-" * 66)
                for line in content[:500].split('\n')[:10]:
                    print(f"    {line}")
                print("    " + "-" * 66)
                success = False

            # コンテンツにClaudeっぽいキーワードがあるかチェック
            keywords = ['claude', 'anthropic', 'conversation', 'chat', 'project']
            found_keywords = [kw for kw in keywords if kw in content.lower()]
            if found_keywords:
                print(f"\n    検出されたキーワード: {', '.join(found_keywords)}")

            print("\n[8] スクリーンショット...")
            page.screenshot(path="/home/user/Kagami/claude_sessionkey_only.png")
            print("    ✓ スクリーンショット保存: claude_sessionkey_only.png")

            print("\n[9] HTMLを保存...")
            with open("/home/user/Kagami/claude_sessionkey_only.html", "w", encoding="utf-8") as f:
                f.write(content)
            print("    ✓ HTML保存: claude_sessionkey_only.html")

            browser.close()

        if success:
            print("\n" + "=" * 70)
            print("🎉🎉🎉 claude.ai/code アクセス成功！")
            print("=" * 70)
            print("\n✅ 達成:")
            print("  ✓ 共有メモリ問題の解決")
            print("  ✓ proxy.py経由のHTTPS通信")
            print("  ✓ sessionKeyによる認証")
            print("  ✓ Cloudflareチャレンジ回避")
            print("  ✓ claude.ai/codeへのアクセス")
        else:
            print("\n" + "=" * 70)
            print("⚠️ アクセス失敗")
            print("=" * 70)
            print("\n考えられる原因:")
            print("  - sessionKeyが無効または期限切れ")
            print("  - sessionKeyだけでは不十分（他のCookieも必要）")
            print("  - セッションがIPアドレスにバインドされている")

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
    success = test_with_sessionkey_only()
    sys.exit(0 if success else 1)
