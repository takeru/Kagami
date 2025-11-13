"""
既に起動しているproxy.pyを使ってSeleniumでHTTPSアクセス

前提: proxy.pyが127.0.0.1:8891で起動している
"""

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.os_manager import ChromeType
import time

def test_https_with_existing_proxy():
    """既存のproxy.py経由でHTTPSサイトにアクセス"""
    print("=" * 60)
    print("Test: proxy.py経由でのHTTPSアクセス (proxy.pyは起動済み)")
    print("=" * 60)

    try:
        # Chrome optionsの設定
        options = Options()
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--headless=new')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--proxy-server=http://127.0.0.1:8891')
        options.add_argument('--ignore-certificate-errors')

        # Playwrightがインストールしたchromiumバイナリを使用
        chromium_path = '/root/.cache/ms-playwright/chromium-1194/chrome-linux/chrome'
        options.binary_location = chromium_path

        print("\n[Selenium] ChromeDriver 141を取得中...")
        service = Service(ChromeDriverManager(chrome_type=ChromeType.CHROMIUM, driver_version='141.0.7390.122').install())

        print("[Selenium] Seleniumを起動中...")
        print(f"[Selenium] Chromium binary: {chromium_path}")
        print(f"[Selenium] Proxy: http://127.0.0.1:8891")

        driver = webdriver.Chrome(service=service, options=options)

        print("\n[Test 1] https://example.com にアクセス中...")
        driver.set_page_load_timeout(60)
        driver.get("https://example.com")

        print(f"[Result] タイトル: '{driver.title}'")
        print(f"[Result] URL: {driver.current_url}")

        page_source = driver.page_source
        print(f"[Result] ページソースの長さ: {len(page_source)} 文字")

        # 一部のコンテンツを表示
        if "Example Domain" in page_source:
            print(f"[Result] ✅ 正常にコンテンツを取得できました！")
            print(f"[Result] ページ内容の一部: {page_source[page_source.find('Example Domain'):page_source.find('Example Domain')+100]}")
        else:
            print(f"[Result] ⚠️ コンテンツが期待と異なります")
            print(f"[Result] 最初の1000文字: {page_source[:1000]}")

        # HTTPサイトもテスト
        print("\n[Test 2] http://example.com にアクセス中...")
        driver.get("http://example.com")
        print(f"[Result] タイトル: '{driver.title}'")
        print(f"[Result] ページソースの長さ: {len(driver.page_source)} 文字")
        if "Example Domain" in driver.page_source:
            print(f"[Result] ✅ HTTPアクセスも成功")

        # claude.ai にもアクセスしてみる (Cloudflareテスト)
        print("\n[Test 3] https://claude.ai にアクセス中...")
        driver.get("https://claude.ai")
        print(f"[Result] タイトル: '{driver.title}'")
        print(f"[Result] URL: {driver.current_url}")
        print(f"[Result] ページソースの長さ: {len(driver.page_source)} 文字")

        if "Cloudflare" in driver.page_source or "Just a moment" in driver.page_source:
            print(f"[Result] ⚠️ Cloudflareチャレンジが表示されています")
        elif "Claude" in driver.title or "claude" in driver.page_source.lower():
            print(f"[Result] ✅ Claudeページにアクセスできました！")
        else:
            print(f"[Result] 最初の1000文字: {driver.page_source[:1000]}")

        driver.quit()
        print("\n✅ テスト完了！")
        return True

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
    print("Selenium + proxy.py (既存プロキシ使用) HTTPS アクセステスト\n")
    print("⚠️  このスクリプトを実行する前に、proxy.pyを別のターミナルで起動してください:")
    print("    uv run proxy --hostname 127.0.0.1 --port 8891 --plugins proxy.plugin.proxy_pool.ProxyPoolPlugin --proxy-pool \"$HTTPS_PROXY\"\n")

    result = test_https_with_existing_proxy()

    print("\n" + "=" * 60)
    print("テスト結果サマリ")
    print("=" * 60)
    print(f"proxy.py経由のHTTPSアクセス: {'✅ 成功' if result else '❌ 失敗'}")
    print("=" * 60)
