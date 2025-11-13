#!/usr/bin/env python3
"""
サンプル2: プロキシを使ったアクセス

proxy.py を使ってJWT認証プロキシ経由でアクセスします。

実行方法:
    uv run python playwright_setup/samples/02_with_proxy.py

必要な環境変数:
    HTTPS_PROXY: 上流プロキシのURL（JWT認証情報を含む）
"""
import subprocess
import time
import os
import sys
from playwright.sync_api import sync_playwright


def main():
    print("="*60)
    print("Playwright プロキシサンプル")
    print("="*60)

    # 環境変数のチェック
    if not os.getenv("HTTPS_PROXY"):
        print("\n❌ エラー: HTTPS_PROXY 環境変数が設定されていません")
        print("   プロキシを使用する場合は環境変数を設定してください")
        sys.exit(1)

    # Step 1: proxy.py を起動
    print("\n1. ローカルプロキシ (proxy.py) を起動...")
    proxy_port = 8910
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

    # プロキシの起動を待機
    time.sleep(3)
    print(f"   ✅ プロキシ起動: http://127.0.0.1:{proxy_port}")

    try:
        with sync_playwright() as p:
            # Step 2: ブラウザを起動（プロキシ設定付き）
            print("\n2. ブラウザを起動（プロキシ経由）...")
            browser = p.chromium.launch(
                headless=True,
                args=[
                    # 共有メモリ対策
                    '--disable-dev-shm-usage',
                    '--single-process',
                    '--no-sandbox',

                    # プロキシ設定
                    f'--proxy-server=http://127.0.0.1:{proxy_port}',
                    '--ignore-certificate-errors',  # 証明書エラーを無視
                ]
            )

            # Step 3: ページにアクセス
            print("\n3. example.com にアクセス（プロキシ経由）...")
            page = browser.new_page()
            response = page.goto("https://example.com", timeout=30000)

            print(f"   ✅ ステータス: {response.status}")
            print(f"   ✅ URL: {response.url}")
            print(f"   ✅ タイトル: {page.title()}")

            # スクリーンショット
            print("\n4. スクリーンショットを保存...")
            page.screenshot(path="example_with_proxy.png")
            print("   ✅ 保存完了: example_with_proxy.png")

            browser.close()

    finally:
        # Step 4: プロキシを停止
        print("\n5. プロキシを停止...")
        proxy_process.terminate()
        try:
            proxy_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proxy_process.kill()
        print("   ✅ 停止完了")

    print("\n✅ 完了！")


if __name__ == "__main__":
    main()
