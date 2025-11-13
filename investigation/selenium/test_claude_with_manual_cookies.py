"""
手動Cookie取得を使ったclaude.ai/codeアクセス

1. ローカル環境でclaude.ai/codeにログイン
2. Cookieをbase64エンコードしてエクスポート
3. 環境変数 CLAUDE_COOKIES_BASE64 に設定
4. このスクリプトでCookieをインポートしてアクセス
"""

from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth
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
        return None

    try:
        # base64デコード
        cookies_json = base64.b64decode(cookies_base64).decode('utf-8')
        # JSONパース
        return json.loads(cookies_json)
    except Exception as e:
        print(f"❌ Cookie解析エラー: {e}")
        return None

def print_cookie_instructions():
    """Cookie取得方法を表示"""
    print("\n" + "=" * 70)
    print("📋 Cookie取得方法（base64エンコード版）")
    print("=" * 70)
    print("\n【ローカル環境で実行してください】")
    print("\n1. ローカルのブラウザでhttps://claude.ai/codeを開く")
    print("2. ログインする")
    print("3. 開発者ツールを開く（F12キー）")
    print("4. Consoleタブを開く")
    print("5. 以下のコードを貼り付けて実行:")
    print("\n" + "-" * 70)
    print("""
// Cookieを取得してbase64エンコードしてコピー
(function() {
  const cookies = document.cookie.split('; ').map(c => {
    const [name, value] = c.split('=');
    return {
      name: name,
      value: value,
      domain: '.claude.ai',
      path: '/',
      httpOnly: false,
      secure: true,
      sameSite: 'Lax'
    };
  });

  const cookiesJson = JSON.stringify(cookies);
  const cookiesBase64 = btoa(unescape(encodeURIComponent(cookiesJson)));

  copy(cookiesBase64);
  console.log('✅ Cookieをbase64エンコードしてクリップボードにコピーしました！');
  console.log('Cookie数:', cookies.length);
  console.log('エンコード後のサイズ:', cookiesBase64.length, '文字');
})();
""")
    print("-" * 70)
    print("\n6. クリップボードの内容（base64文字列）をコピー")
    print("7. この環境で以下のコマンドを実行:")
    print("\n   export CLAUDE_COOKIES_BASE64='<コピーしたbase64文字列>'")
    print("\n8. このスクリプトを再実行")
    print("\n" + "=" * 70)

def test_with_manual_cookies():
    """手動Cookie取得を使ってアクセス"""
    proxy_process = None

    try:
        print("=" * 70)
        print("手動Cookie取得でclaude.ai/codeアクセス（環境変数版）")
        print("=" * 70)

        # 環境変数からCookieを読み込む
        cookies = load_cookies_from_env()

        if cookies is None:
            print(f"\n⚠️  環境変数 CLAUDE_COOKIES_BASE64 が設定されていません")
            print_cookie_instructions()
            return False

        print(f"\n✓ 環境変数からCookieを読み込みました: {len(cookies)}個のCookie")

        # Cookieのフォーマットを修正（sameSite値の正規化）
        for cookie in cookies:
            # sameSiteの値を正規化
            same_site = cookie.get('sameSite', 'Lax')
            if same_site not in ['Strict', 'Lax', 'None']:
                cookie['sameSite'] = 'Lax'
            # httpOnlyがない場合はFalseに設定
            if 'httpOnly' not in cookie:
                cookie['httpOnly'] = False
            # secureがない場合はTrueに設定
            if 'secure' not in cookie:
                cookie['secure'] = True

        print(f"✓ Cookieフォーマットを正規化しました")

        # proxy.pyを起動
        proxy_process = start_proxy()

        # ユーザーデータディレクトリを/tmpに作成
        user_data_dir = tempfile.mkdtemp(prefix="claude_cookie_", dir="/tmp")
        cache_dir = tempfile.mkdtemp(prefix="cache_cookie_", dir="/tmp")

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
        print("Test: 手動Cookieでclaude.ai/codeアクセス")
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
            print("    （認証済みセッションでアクセス）")

            response = page.goto("https://claude.ai/code", wait_until="domcontentloaded")
            print(f"    Status: {response.status}")

            # 少し待つ
            print("\n[5] ページロード待機（5秒）...")
            time.sleep(5)

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
                print("    ❌ まだCloudflareチャレンジが表示されています")
                print("    → Cookieが無効または期限切れの可能性")
                success = False

            elif response.status == 200 and "claude" in title.lower():
                print("    ✅✅✅ Claudeページアクセス成功！")
                print("    → Cookieによる認証成功")
                success = True

            elif response.status == 200 and len(content) > 50000:
                print("    ✅ 大きなコンテンツ取得（SPAの可能性）")
                print("    → アクセス成功の可能性が高い")
                success = True

            elif "login" in url.lower() or "signin" in url.lower():
                print("    ⚠️ ログインページにリダイレクトされました")
                print("    → Cookieが無効または期限切れ")
                success = False

            else:
                print("    ⚠️ 予期しないコンテンツ")
                print(f"    最初の500文字:")
                print("    " + "-" * 66)
                for line in content[:500].split('\n')[:10]:
                    print(f"    {line}")
                print("    " + "-" * 66)
                success = False

            print("\n[8] スクリーンショット...")
            page.screenshot(path="/home/user/Kagami/claude_with_cookies.png")
            print("    ✓ スクリーンショット保存: claude_with_cookies.png")

            print("\n[9] HTMLを保存...")
            with open("/home/user/Kagami/claude_with_cookies.html", "w", encoding="utf-8") as f:
                f.write(content)
            print("    ✓ HTML保存: claude_with_cookies.html")

            browser.close()

        if success:
            print("\n" + "=" * 70)
            print("🎉🎉🎉 claude.ai/code アクセス成功！")
            print("=" * 70)
            print("\n✅ 達成:")
            print("  ✓ 共有メモリ問題の解決")
            print("  ✓ proxy.py経由のHTTPS通信")
            print("  ✓ 手動Cookieによる認証")
            print("  ✓ Cloudflareチャレンジ回避")
            print("  ✓ claude.ai/codeへのアクセス")
            print("\n🎯 次のステップ:")
            print("  1. セッション永続化の実装")
            print("  2. 自動化ワークフローの構築")
            print("  3. Cookie更新メカニズムの実装")
        else:
            print("\n" + "=" * 70)
            print("⚠️ アクセス失敗")
            print("=" * 70)
            print("\n考えられる原因:")
            print("  - Cookieが無効または期限切れ")
            print("  - Cookieのフォーマットが正しくない")
            print("  - セッションがIPアドレスにバインドされている")
            print("\n対策:")
            print("  1. 新しいCookieを取得し直す")
            print("  2. Cookieのフォーマットを確認")

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
    success = test_with_manual_cookies()
    sys.exit(0 if success else 1)
