#!/usr/bin/env python3
"""
サンプル6: 共有プロキシの使用

バックグラウンドで起動したプロキシを使用します。
複数のスクリプトで同じプロキシを共有できます。

事前準備:
    # プロキシを起動（1回だけ）
    uv run python playwright_setup/proxy_manager.py start

実行方法:
    # このスクリプトを何度でも実行可能
    uv run python playwright_setup/samples/06_with_shared_proxy.py

後片付け:
    # プロキシを停止
    uv run python playwright_setup/proxy_manager.py stop
"""
import socket
from playwright.sync_api import sync_playwright


# プロキシ設定（proxy_manager.pyと同じ）
PROXY_HOST = "127.0.0.1"
PROXY_PORT = 8900


def is_proxy_running():
    """プロキシが動作中かチェック"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex((PROXY_HOST, PROXY_PORT))
        sock.close()
        return result == 0
    except:
        return False


def main():
    print("="*60)
    print("Playwright 共有プロキシサンプル")
    print("="*60)

    # プロキシの確認
    print("\n1. プロキシの確認...")
    if is_proxy_running():
        print(f"   ✅ プロキシが動作中: http://{PROXY_HOST}:{PROXY_PORT}")
    else:
        print(f"   ❌ プロキシが起動していません")
        print(f"\n   以下のコマンドでプロキシを起動してください:")
        print(f"   uv run python playwright_setup/proxy_manager.py start")
        return

    with sync_playwright() as p:
        # ブラウザを起動（プロキシ設定のみ）
        print("\n2. ブラウザを起動...")
        browser = p.chromium.launch(
            headless=True,
            args=[
                # 必須フラグ
                '--disable-dev-shm-usage',
                '--single-process',
                '--no-sandbox',

                # プロキシ設定（既存のプロキシを使用）
                f'--proxy-server=http://{PROXY_HOST}:{PROXY_PORT}',
                '--ignore-certificate-errors',
            ]
        )

        print("   ✅ ブラウザ起動完了")

        # ページにアクセス
        print("\n3. example.com にアクセス...")
        page = browser.new_page()
        response = page.goto("https://example.com", timeout=30000)

        print(f"   ✅ ステータス: {response.status}")
        print(f"   ✅ URL: {response.url}")
        print(f"   ✅ タイトル: {page.title()}")

        # スクリーンショット
        print("\n4. スクリーンショットを保存...")
        page.screenshot(path="shared_proxy_example.png")
        print("   ✅ 保存完了: shared_proxy_example.png")

        browser.close()

    print("\n✅ 完了！")
    print(f"\n💡 プロキシは起動したままです")
    print(f"   このスクリプトを何度でも実行できます")
    print(f"\n   プロキシを停止する場合:")
    print(f"   uv run python playwright_setup/proxy_manager.py stop")


if __name__ == "__main__":
    main()
