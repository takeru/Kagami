"""
Selenium + proxy.py でのHTTPSアクセステスト

proxy.pyをJWT認証プロキシと連携させて、Seleniumで外部サイトにアクセスする
"""

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.os_manager import ChromeType
import subprocess
import time
import os
import signal

def start_proxy():
    """proxy.pyサーバーを起動"""
    https_proxy = os.getenv('HTTPS_PROXY')
    if not https_proxy:
        raise Exception("HTTPS_PROXY environment variable is not set")

    print(f"[Proxy] Starting proxy.py with upstream proxy...")
    print(f"[Proxy] Upstream: {https_proxy}")

    # proxy.pyをProxyPoolPluginと共に起動
    process = subprocess.Popen([
        'uv', 'run', 'proxy',
        '--hostname', '127.0.0.1',
        '--port', '8891',
        '--plugins', 'proxy.plugin.proxy_pool.ProxyPoolPlugin',
        '--proxy-pool', https_proxy,
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    print(f"[Proxy] Started with PID: {process.pid}")
    print(f"[Proxy] Waiting for proxy to be ready...")
    time.sleep(5)

    return process

def stop_proxy(process):
    """proxy.pyサーバーを停止"""
    print(f"\n[Proxy] Stopping proxy (PID: {process.pid})...")
    process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
    print(f"[Proxy] Stopped")

def test_https_with_proxy():
    """proxy.py経由でHTTPSサイトにアクセス"""
    print("=" * 60)
    print("Test: proxy.py経由でのHTTPSアクセス")
    print("=" * 60)

    proxy_process = None

    try:
        # proxy.pyを起動
        proxy_process = start_proxy()

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
        driver.set_page_load_timeout(30)
        driver.get("https://example.com")

        print(f"[Result] タイトル: {driver.title}")
        print(f"[Result] URL: {driver.current_url}")

        page_source = driver.page_source
        print(f"[Result] ページソースの長さ: {len(page_source)} 文字")

        # 一部のコンテンツを表示
        if "Example Domain" in page_source:
            print(f"[Result] ✅ 正常にコンテンツを取得できました！")
        else:
            print(f"[Result] ⚠️ コンテンツが期待と異なります")
            print(f"[Result] 最初の500文字: {page_source[:500]}")

        # HTTPサイトもテスト
        print("\n[Test 2] http://example.com にアクセス中...")
        driver.get("http://example.com")
        print(f"[Result] タイトル: {driver.title}")
        print(f"[Result] ページソースの長さ: {len(driver.page_source)} 文字")

        driver.quit()
        print("\n✅ テスト成功！proxy.py経由でHTTPSアクセスできました")
        return True

    except Exception as e:
        print(f"\n❌ エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        if proxy_process:
            stop_proxy(proxy_process)

if __name__ == "__main__":
    print("Selenium + proxy.py HTTPS アクセステスト\n")

    result = test_https_with_proxy()

    print("\n" + "=" * 60)
    print("テスト結果サマリ")
    print("=" * 60)
    print(f"proxy.py経由のHTTPSアクセス: {'✅ 成功' if result else '❌ 失敗'}")
    print("=" * 60)
