#!/usr/bin/env python3
"""
claude.ai/code へのアクセステスト
"""
from playwright.sync_api import sync_playwright
import time

def test_claude_access():
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=[
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-accelerated-2d-canvas',
                '--disable-gpu'
            ]
        )

        try:
            page = browser.new_page()
            print("ブラウザを起動しました")

            print("https://claude.ai/code/ にアクセス中...")
            page.goto("https://claude.ai/code/", timeout=30000)

            print(f"✅ アクセス成功！")
            print(f"URL: {page.url}")
            print(f"タイトル: {page.title()}")

            # スクリーンショットを保存
            page.screenshot(path="investigation/playwright/claude_access_test.png")
            print("スクリーンショットを保存しました: claude_access_test.png")

            # ページの内容を確認
            time.sleep(2)
            content = page.content()
            print(f"\nHTML長さ: {len(content)} 文字")

        except Exception as e:
            print(f"❌ エラー: {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    test_claude_access()
