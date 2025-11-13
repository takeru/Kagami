"""
SESSIONKEY + 最小限のデバイスCookieでテスト

sessionKey + anthropic-device-id + lastActiveOrg
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

def test_with_minimal_cookies():
    """SESSIONKEY + 最小限のデバイスCookieでアクセス"""
    proxy_process = None

    try:
        print("=" * 70)
        print("SESSIONKEY + 最小限のCookieでclaude.ai/codeアクセス")
        print("=" * 70)

        # 環境変数を取得
        session_key = os.getenv('SESSIONKEY')
        device_id = os.getenv('ANTHROPIC_DEVICE_ID', '8c799d84-2b6c-45f9-9a9c-8e6ffd999999')  # デフォルト値
        org_id = os.getenv('LAST_ACTIVE_ORG', 'ffacd887-9906-4f1d-9503-03aa103f314e')  # デフォルト値

        if not session_key:
            print(f"\n⚠️  環境変数 SESSIONKEY が設定されていません")
            print("\n設定方法:")
            print("  export SESSIONKEY='<sessionKeyの値>'")
            print("\nオプション（推奨）:")
            print("  export ANTHROPIC_DEVICE_ID='<anthropic-device-idの値>'")
            print("  export LAST_ACTIVE_ORG='<lastActiveOrgの値>'")
            return False

        print(f"\n✓ SESSIONKEY: {len(session_key)}文字")
        print(f"✓ ANTHROPIC_DEVICE_ID: {device_id[:30]}...")
        print(f"✓ LAST_ACTIVE_ORG: {org_id[:30]}...")

        # 最小限のCookie配列を作成
        cookies = [
            {
                "name": "sessionKey",
                "value": session_key,
                "domain": ".claude.ai",
                "path": "/",
                "httpOnly": True,
                "secure": True,
                "sameSite": "Lax"
            },
            {
                "name": "anthropic-device-id",
                "value": device_id,
                "domain": ".claude.ai",
                "path": "/",
                "httpOnly": False,
                "secure": True,
                "sameSite": "Lax"
            },
            {
                "name": "lastActiveOrg",
                "value": org_id,
                "domain": ".claude.ai",
                "path": "/",
                "httpOnly": False,
                "secure": True,
                "sameSite": "Lax"
            }
        ]

        print(f"✓ Cookieを準備しました: {len(cookies)}個")

        # proxy.pyを起動
        proxy_process = start_proxy()

        # ユーザーデータディレクトリを/tmpに作成
        user_data_dir = tempfile.mkdtemp(prefix="claude_minimal_", dir="/tmp")
        cache_dir = tempfile.mkdtemp(prefix="cache_minimal_", dir="/tmp")

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
        print("Test: 最小限のCookieでアクセス")
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

            print("\n[3] Cookieをインポート...")
            # まず claude.ai に移動してからCookieを設定
            page.goto("https://claude.ai")
            time.sleep(2)

            # Cookieを追加
            browser.add_cookies(cookies)
            print(f"    ✓ {len(cookies)}個のCookieをインポートしました")

            page.set_default_timeout(120000)

            print("\n[4] https://claude.ai/code にアクセス中...")

            response = page.goto("https://claude.ai/code", wait_until="domcontentloaded")
            print(f"    Status: {response.status}")

            # 待機
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

            # キーワード検索
            keywords = ['claude', 'anthropic', 'conversation', 'chat', 'project', 'workspace']
            found_keywords = [kw for kw in keywords if kw in content.lower()]
            if found_keywords:
                print(f"    検出されたキーワード: {', '.join(found_keywords)}")

            print("\n[8] スクリーンショット...")
            page.screenshot(path="/home/user/Kagami/claude_minimal_cookies.png")
            print("    ✓ スクリーンショット保存")

            print("\n[9] HTMLを保存...")
            with open("/home/user/Kagami/claude_minimal_cookies.html", "w", encoding="utf-8") as f:
                f.write(content)
            print("    ✓ HTML保存")

            browser.close()

        if success:
            print("\n" + "=" * 70)
            print("🎉🎉🎉 アクセス成功！")
            print("=" * 70)
        else:
            print("\n" + "=" * 70)
            print("⚠️ アクセス失敗")
            print("=" * 70)
            print("\n💡 ヒント:")
            print("  開発者ツールのApplicationタブで以下のCookieの値を確認:")
            print("  - sessionKey (最重要)")
            print("  - anthropic-device-id")
            print("  - lastActiveOrg")
            print("\n  設定方法:")
            print("  export SESSIONKEY='...'")
            print("  export ANTHROPIC_DEVICE_ID='...'")
            print("  export LAST_ACTIVE_ORG='...'")

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
    success = test_with_minimal_cookies()
    sys.exit(0 if success else 1)
