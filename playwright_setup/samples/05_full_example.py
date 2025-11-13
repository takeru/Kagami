#!/usr/bin/env python3
"""
サンプル5: 完全版 - 全機能統合

以下の機能をすべて含んだ実用的な例です:
- プロキシ経由アクセス (proxy.py)
- セッション永続化
- Cloudflare回避
- エラーハンドリング

実行方法:
    uv run python playwright_setup/samples/05_full_example.py [URL]

    # 例:
    uv run python playwright_setup/samples/05_full_example.py https://example.com
    uv run python playwright_setup/samples/05_full_example.py https://claude.ai/login

必要な環境変数:
    HTTPS_PROXY: プロキシのURL（JWT認証情報を含む）
"""
import subprocess
import time
import os
import sys
import tempfile
from pathlib import Path
from playwright.sync_api import sync_playwright


def print_header(text):
    """ヘッダーを表示"""
    print("\n" + "="*60)
    print(f"  {text}")
    print("="*60)


def start_proxy(port=8912):
    """proxy.pyを起動"""
    if not os.getenv("HTTPS_PROXY"):
        print("  ⚠️  HTTPS_PROXY未設定 - プロキシなしで実行")
        return None

    print(f"  ▶ プロキシを起動: http://127.0.0.1:{port}")
    process = subprocess.Popen(
        [
            'uv', 'run', 'proxy',
            '--hostname', '127.0.0.1',
            '--port', str(port),
            '--plugins', 'proxy.plugin.proxy_pool.ProxyPoolPlugin',
            '--proxy-pool', os.environ['HTTPS_PROXY'],
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    time.sleep(3)
    print("  ✅ プロキシ起動完了")
    return process


def stop_proxy(process):
    """proxy.pyを停止"""
    if not process:
        return

    print("  ▶ プロキシを停止...")
    process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
    print("  ✅ プロキシ停止完了")


def main():
    # URLを引数から取得
    target_url = sys.argv[1] if len(sys.argv) > 1 else "https://example.com"

    print_header("Playwright 完全版サンプル")
    print(f"\nターゲットURL: {target_url}")

    # セッションデータの保存先
    session_dir = Path("/tmp/playwright_full_session")
    session_dir.mkdir(parents=True, exist_ok=True)
    cache_dir = tempfile.mkdtemp(prefix="cache_", dir="/tmp")

    # プロキシを起動
    print_header("1. プロキシの起動")
    proxy_port = 8912
    use_proxy = bool(os.getenv("HTTPS_PROXY"))
    proxy_process = start_proxy(proxy_port) if use_proxy else None

    try:
        with sync_playwright() as p:
            # ブラウザの起動オプション
            print_header("2. ブラウザの起動")

            args = [
                # 共有メモリ対策（Claude Code Web環境で必須）
                '--disable-dev-shm-usage',
                '--single-process',

                # サンドボックス無効化
                '--no-sandbox',
                '--disable-setuid-sandbox',

                # Bot検出回避
                '--disable-blink-features=AutomationControlled',
                '--disable-features=IsolateOrigins,site-per-process',

                # Headless検出回避
                '--window-size=1920,1080',
                '--start-maximized',

                # その他の最適化
                '--disable-gpu',
                '--disable-accelerated-2d-canvas',
                f'--disk-cache-dir={cache_dir}',

                # User agent
                '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            ]

            # プロキシ設定
            if use_proxy:
                args.extend([
                    f'--proxy-server=http://127.0.0.1:{proxy_port}',
                    '--ignore-certificate-errors',
                ])

            # セッション永続化モードで起動
            browser = p.chromium.launch_persistent_context(
                user_data_dir=str(session_dir),
                headless=True,
                args=args
            )

            print(f"  ✅ ブラウザ起動完了")
            print(f"  ✅ セッションデータ: {session_dir}")

            # Anti-detectionスクリプトを注入
            print_header("3. Anti-detectionスクリプトの注入")
            page = browser.pages[0]
            page.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
                Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});
                window.chrome = { runtime: {} };
            """)
            print("  ✅ スクリプト注入完了")

            # ページにアクセス
            print_header("4. ページへのアクセス")
            print(f"  ▶ アクセス中: {target_url}")

            try:
                response = page.goto(target_url, timeout=60000)
                print(f"  ✅ ステータス: {response.status}")
                print(f"  ✅ URL: {response.url}")

                # タイトル取得
                title = page.title()
                print(f"  ✅ タイトル: {title}")

                # Cloudflareチャレンジの検出
                content = page.content()
                if "Just a moment" in content or "Cloudflare" in title:
                    print("\n  ⚠️  Cloudflareチャレンジを検出")
                    print("  ▶ チャレンジ完了を待機中...")

                    # チャレンジ完了まで待機
                    for i in range(10):
                        time.sleep(3)
                        new_title = page.title()
                        print(f"     [{i+1}/10] タイトル: {new_title}")

                        if new_title != "Just a moment...":
                            print(f"  ✅ チャレンジ通過！")
                            break
                    else:
                        print(f"  ⚠️  チャレンジ未完了（30秒経過）")

                # 結果の表示
                print_header("5. 結果")
                final_title = page.title()
                final_url = page.url
                final_content_size = len(page.content())

                print(f"  タイトル: {final_title}")
                print(f"  URL: {final_url}")
                print(f"  コンテンツサイズ: {final_content_size} bytes")

                # スクリーンショット
                screenshot_name = "full_example_result.png"
                page.screenshot(path=screenshot_name, full_page=True)
                print(f"  ✅ スクリーンショット: {screenshot_name}")

                # ボタンとリンクを検出（オプション）
                print_header("6. ページ要素の検出（サンプル）")
                try:
                    buttons = page.locator("button").all()
                    print(f"  ✅ ボタン数: {len(buttons)}個")

                    links = page.locator("a").all()
                    print(f"  ✅ リンク数: {len(links)}個")
                except Exception as e:
                    print(f"  ⚠️  要素検出エラー: {e}")

            except Exception as e:
                print(f"  ❌ エラー: {e}")
                # エラー時もスクリーンショットを保存
                try:
                    page.screenshot(path="full_example_error.png")
                    print(f"  📸 エラー時のスクリーンショット: full_example_error.png")
                except:
                    pass

            browser.close()

    finally:
        # プロキシを停止
        if proxy_process:
            print_header("7. クリーンアップ")
            stop_proxy(proxy_process)

    print_header("完了")
    print(f"\n✅ すべての処理が完了しました")
    print(f"\nセッションデータは保持されています: {session_dir}")
    print("次回実行時も同じセッションが使用されます。")


if __name__ == "__main__":
    main()
