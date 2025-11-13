"""
webdriver-managerを使ったSeleniumテスト

ChromeDriver 141を自動的にダウンロードして使用する
"""

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.os_manager import ChromeType
import time

def test_basic_with_manager():
    """webdriver-managerを使った基本テスト"""
    print("=" * 60)
    print("Test 1: webdriver-managerを使った動作確認")
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

        print("\n[1] ChromeDriver 141をダウンロード中...")
        # webdriver-managerでChrome 141用のdriverを取得
        service = Service(ChromeDriverManager(chrome_type=ChromeType.CHROMIUM, driver_version='141.0.7390.122').install())

        print("[2] Seleniumを起動中...")
        print(f"    Chromium binary: {chromium_path}")

        driver = webdriver.Chrome(service=service, options=options)

        print("[3] ローカルHTMLをロード中...")
        driver.get("data:text/html,<html><head><title>Test Page</title></head><body><h1>Hello World</h1></body></html>")

        print(f"[4] タイトル取得: {driver.title}")
        print(f"[5] URL: {driver.current_url}")

        time.sleep(1)

        print("[6] スクリーンショットを撮影...")
        driver.save_screenshot("investigation/selenium/test_manager_basic.png")
        print("    スクリーンショット保存: investigation/selenium/test_manager_basic.png")

        driver.quit()
        print("\n✅ テスト成功！webdriver-managerで正常に動作しています")
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

        print("\n[1] ChromeDriver 141を取得中...")
        service = Service(ChromeDriverManager(chrome_type=ChromeType.CHROMIUM, driver_version='141.0.7390.122').install())

        print("[2] Seleniumを起動中...")
        driver = webdriver.Chrome(service=service, options=options)

        print("[3] http://example.com にアクセス中...")
        driver.set_page_load_timeout(30)
        driver.get("http://example.com")

        print(f"[4] タイトル: {driver.title}")
        print(f"[5] URL: {driver.current_url}")

        page_source = driver.page_source
        print(f"[6] ページソースの長さ: {len(page_source)} 文字")

        driver.save_screenshot("investigation/selenium/test_manager_http.png")
        print("[7] スクリーンショット保存: investigation/selenium/test_manager_http.png")

        driver.quit()
        print("\n✅ HTTPサイトへのアクセス成功！")
        return True

    except Exception as e:
        print(f"\n❌ エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Selenium + webdriver-manager 動作テスト\n")

    result1 = test_basic_with_manager()
    result2 = test_http_site()

    print("\n" + "=" * 60)
    print("テスト結果サマリ")
    print("=" * 60)
    print(f"1. 基本動作: {'✅ 成功' if result1 else '❌ 失敗'}")
    print(f"2. HTTPサイト: {'✅ 成功' if result2 else '❌ 失敗'}")
    print("=" * 60)
