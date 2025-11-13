#!/usr/bin/env python3
"""
サンプル4: Cloudflare Bot検出の回避

Cloudflareのbot検出を回避してアクセスします。
claude.ai のようなCloudflare保護されたサイトにアクセスする際に必要です。

実行方法:
    uv run python playwright_setup/samples/04_cloudflare_bypass.py

必要な環境変数:
    HTTPS_PROXY: プロキシを使う場合（オプション）
"""
import subprocess
import time
import os
from playwright.sync_api import sync_playwright


def main():
    print("="*60)
    print("Playwright Cloudflare回避サンプル")
    print("="*60)

    # プロキシの有無を確認
    use_proxy = bool(os.getenv("HTTPS_PROXY"))
    proxy_process = None

    if use_proxy:
        # プロキシを起動
        print("\n1. プロキシを起動...")
        proxy_port = 8911
        proxy_process = subprocess.Popen(
            [
                'uv', 'run', 'proxy',
                '--hostname', '127.0.0.1',
                '--port', str(proxy_port),
                '--plugins', 'proxy.plugin.proxy_pool.ProxyPoolPlugin',
                '--proxy-pool', os.environ['HTTPS_PROXY'],
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        time.sleep(3)
        print(f"   ✅ プロキシ起動: http://127.0.0.1:{proxy_port}")
    else:
        print("\n1. プロキシなしで実行（HTTPS_PROXY未設定）")
        proxy_port = None

    try:
        with sync_playwright() as p:
            # Step 2: Anti-detection設定でブラウザを起動
            print("\n2. ブラウザを起動（Anti-detection設定）...")

            args = [
                # 共有メモリ対策
                '--disable-dev-shm-usage',
                '--single-process',
                '--no-sandbox',
                '--disable-setuid-sandbox',

                # Bot検出回避（重要）
                '--disable-blink-features=AutomationControlled',
                '--disable-features=IsolateOrigins,site-per-process',

                # Headless検出回避
                '--window-size=1920,1080',
                '--start-maximized',

                # その他
                '--disable-gpu',
                '--disable-accelerated-2d-canvas',

                # User agent（実際のブラウザに偽装）
                '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            ]

            # プロキシ設定を追加
            if proxy_port:
                args.extend([
                    f'--proxy-server=http://127.0.0.1:{proxy_port}',
                    '--ignore-certificate-errors',
                ])

            browser = p.chromium.launch(
                headless=True,
                args=args
            )

            page = browser.new_page()

            # Step 3: JavaScript injectionでさらに偽装
            print("\n3. Anti-detectionスクリプトを注入...")
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
            print("   ✅ スクリプト注入完了")

            # Step 4: example.comでテスト
            print("\n4. example.com でテスト...")
            response = page.goto("https://example.com", timeout=30000)
            print(f"   ✅ ステータス: {response.status}")
            print(f"   ✅ タイトル: {page.title()}")

            # JavaScript実行のテスト
            print("\n5. 偽装が機能しているか確認...")
            webdriver_value = page.evaluate("navigator.webdriver")
            plugins_count = page.evaluate("navigator.plugins.length")
            print(f"   ✅ navigator.webdriver: {webdriver_value} (undefinedならOK)")
            print(f"   ✅ navigator.plugins: {plugins_count}個")

            # スクリーンショット
            print("\n6. スクリーンショットを保存...")
            page.screenshot(path="cloudflare_bypass_test.png")
            print("   ✅ 保存完了: cloudflare_bypass_test.png")

            browser.close()

    finally:
        if proxy_process:
            print("\n7. プロキシを停止...")
            proxy_process.terminate()
            try:
                proxy_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proxy_process.kill()
            print("   ✅ 停止完了")

    print("\n✅ 完了！")
    print("\n💡 この設定でCloudflare保護されたサイトにアクセスできます")


if __name__ == "__main__":
    main()
