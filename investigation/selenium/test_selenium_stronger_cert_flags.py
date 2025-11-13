"""
より強力な証明書無視フラグを使ったSeleniumテスト

CA証明書検証を完全にバイパスする試み
"""

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.os_manager import ChromeType
import time

def test_with_stronger_flags():
    """より強力なフラグでHTTPSアクセス"""
    print("=" * 60)
    print("Test: より強力な証明書無視フラグを使用")
    print("=" * 60)

    try:
        # Chrome optionsの設定
        options = Options()
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--headless=new')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--proxy-server=http://127.0.0.1:8891')

        # より強力な証明書無視フラグ
        options.add_argument('--ignore-certificate-errors')
        options.add_argument('--ignore-ssl-errors')
        options.add_argument('--ignore-certificate-errors-spki-list')
        options.add_argument('--disable-web-security')
        options.add_argument('--allow-insecure-localhost')
        options.add_argument('--disable-features=CertificateTransparencyEnforcement')
        options.add_argument('--disable-features=NetworkService')

        # Googleサービスへのアクセスを無効化
        options.add_argument('--disable-background-networking')
        options.add_argument('--disable-sync')
        options.add_argument('--disable-translate')
        options.add_argument('--disable-default-apps')
        options.add_argument('--disable-extensions')
        options.add_argument('--no-first-run')
        options.add_argument('--no-default-browser-check')
        options.add_argument('--disable-component-update')

        # Playwrightがインストールしたchromiumバイナリを使用
        chromium_path = '/root/.cache/ms-playwright/chromium-1194/chrome-linux/chrome'
        options.binary_location = chromium_path

        print("\n[Selenium] ChromeDriver 141を取得中...")
        service = Service(ChromeDriverManager(chrome_type=ChromeType.CHROMIUM, driver_version='141.0.7390.122').install())

        print("[Selenium] Seleniumを起動中...")
        print(f"[Selenium] Chromium binary: {chromium_path}")
        print(f"[Selenium] Proxy: http://127.0.0.1:8891")
        print(f"[Selenium] 追加フラグ: 証明書検証完全無効化 + Googleサービス無効化")

        driver = webdriver.Chrome(service=service, options=options)

        print("\n[Test 1] https://example.com にアクセス中...")
        driver.set_page_load_timeout(90)  # タイムアウトを90秒に延長

        start_time = time.time()
        driver.get("https://example.com")
        elapsed = time.time() - start_time

        print(f"[Result] ページロード時間: {elapsed:.2f}秒")
        print(f"[Result] タイトル: '{driver.title}'")
        print(f"[Result] URL: {driver.current_url}")

        page_source = driver.page_source
        print(f"[Result] ページソースの長さ: {len(page_source)} 文字")

        # 一部のコンテンツを表示
        if "Example Domain" in page_source:
            print(f"[Result] ✅ 正常にコンテンツを取得できました！")
            success = True
        else:
            print(f"[Result] ⚠️ コンテンツが期待と異なります")
            print(f"[Result] 最初の500文字: {page_source[:500]}")
            success = False

        driver.quit()
        print("\n" + ("✅ テスト成功！" if success else "⚠️ テスト完了（コンテンツ確認失敗）"))
        return success

    except Exception as e:
        print(f"\n❌ エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
        try:
            driver.quit()
        except:
            pass
        return False

if __name__ == "__main__":
    print("Selenium + 強力な証明書無視フラグ HTTPS アクセステスト\n")
    print("⚠️  前提: proxy.pyが127.0.0.1:8891で起動していること\n")

    result = test_with_stronger_flags()

    print("\n" + "=" * 60)
    print("テスト結果サマリ")
    print("=" * 60)
    print(f"証明書無視フラグでのHTTPSアクセス: {'✅ 成功' if result else '❌ 失敗'}")
    print("=" * 60)
