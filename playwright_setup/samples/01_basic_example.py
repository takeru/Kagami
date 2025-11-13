#!/usr/bin/env python3
"""
サンプル1: 基本的なPlaywrightの使い方

最もシンプルな例です。プロキシなしでローカルページにアクセスします。

実行方法:
    uv run python playwright_setup/samples/01_basic_example.py
"""
from playwright.sync_api import sync_playwright


def main():
    print("="*60)
    print("Playwright 基本サンプル")
    print("="*60)

    with sync_playwright() as p:
        # ブラウザを起動
        print("\n1. ブラウザを起動...")
        browser = p.chromium.launch(
            headless=True,  # ヘッドレスモード（GUIなし）
            args=[
                '--disable-dev-shm-usage',  # 共有メモリ問題の回避
                '--single-process',         # プロセス分離の無効化
                '--no-sandbox',             # サンドボックス無効化
            ]
        )

        # 新しいページを開く
        print("2. 新しいページを開く...")
        page = browser.new_page()

        # example.com にアクセス
        print("3. example.com にアクセス...")
        page.goto("https://example.com")

        # タイトルを取得
        title = page.title()
        print(f"   ✅ ページタイトル: {title}")

        # コンテンツを取得
        content = page.content()
        print(f"   ✅ コンテンツサイズ: {len(content)} bytes")

        # h1要素のテキストを取得
        h1_text = page.locator("h1").text_content()
        print(f"   ✅ h1テキスト: {h1_text}")

        # スクリーンショットを保存
        print("4. スクリーンショットを保存...")
        page.screenshot(path="example_screenshot.png")
        print("   ✅ 保存完了: example_screenshot.png")

        # ブラウザを閉じる
        browser.close()
        print("\n✅ 完了！")


if __name__ == "__main__":
    main()
