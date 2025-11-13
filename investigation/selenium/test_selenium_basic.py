"""
通常のSeleniumでのテスト（undetected-chromedriverなし）

undetected-chromedriverでタブクラッシュが発生したため、
通常のSeleniumで動作するか確認する。
"""

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import time
import os

def test_basic_selenium():
    """基本的なSeleniumテスト"""
    print("=" * 60)
    print("Test 1: 基本的なSeleniumの動作確認")
    print("=" * 60)

    try:
        # Chrome optionsの設定
        options = Options()
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--headless=new')
        options.add_argument('--disable-blink-features=AutomationControlled')

        # Playwrightがインストールしたchromiumバイナリを使用
        chromium_path = '/root/.cache/ms-playwright/chromium-1194/chrome-linux/chrome'
        options.binary_location = chromium_path

        print("\n[1] Seleniumを起動中...")
        print(f"    Chromium binary: {chromium_path}")

        driver = webdriver.Chrome(options=options)

        print("[2] ローカルHTMLをロード中...")
        driver.get("data:text/html,<html><head><title>Test Page</title></head><body><h1>Hello World</h1></body></html>")

        print(f"[3] タイトル取得: {driver.title}")
        print(f"[4] URL: {driver.current_url}")

        time.sleep(1)

        print("[5] スクリーンショットを撮影...")
        driver.save_screenshot("investigation/selenium/test_selenium_basic.png")
        print("    スクリーンショット保存: investigation/selenium/test_selenium_basic.png")

        driver.quit()
        print("\n✅ テスト成功！通常のSeleniumは正常に動作しています")
        return True

    except Exception as e:
        print(f"\n❌ エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_http_site():
    """HTTPサイトへのアクセステスト"""
    print("\n" + "=" * 60)
    print("Test 2: HTTPサイトへのアクセス（example.com）")
    print("=" * 60)

    try:
        options = Options()
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--headless=new')
        options.add_argument('--disable-blink-features=AutomationControlled')

        chromium_path = '/root/.cache/ms-playwright/chromium-1194/chrome-linux/chrome'
        options.binary_location = chromium_path

        print("\n[1] Seleniumを起動中...")
        driver = webdriver.Chrome(options=options)

        print("[2] http://example.com にアクセス中...")
        driver.set_page_load_timeout(30)
        driver.get("http://example.com")

        print(f"[3] タイトル: {driver.title}")
        print(f"[4] URL: {driver.current_url}")

        page_source = driver.page_source
        print(f"[5] ページソースの長さ: {len(page_source)} 文字")

        driver.save_screenshot("investigation/selenium/test_selenium_http.png")
        print("[6] スクリーンショット保存: investigation/selenium/test_selenium_http.png")

        driver.quit()
        print("\n✅ HTTPサイトへのアクセス成功！")
        return True

    except Exception as e:
        print(f"\n❌ エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("通常のSelenium 基本動作テスト\n")

    result1 = test_basic_selenium()
    result2 = test_http_site()

    print("\n" + "=" * 60)
    print("テスト結果サマリ")
    print("=" * 60)
    print(f"1. 基本動作: {'✅ 成功' if result1 else '❌ 失敗'}")
    print(f"2. HTTPサイト: {'✅ 成功' if result2 else '❌ 失敗'}")
    print("=" * 60)
