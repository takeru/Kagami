#!/usr/bin/env python3
"""
Claude.ai ログイン管理クラス

このモジュールは、Claude.aiへのログインとセッション管理を提供します。
プロキシ経由でのアクセスとセッション永続化に対応しています。
Cookie永続化により、セッション終了後も再ログイン不要でアクセスできます。
"""

import os
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Optional
from playwright.sync_api import sync_playwright, Browser, Page, BrowserContext

from .claude_cookie_manager import ClaudeCookieManager


class ClaudeLoginManager:
    """Claude.aiへのログインとセッション管理を行うクラス"""

    def __init__(
        self,
        session_dir: Optional[str] = None,
        proxy_port: int = 8900,
        headless: bool = True,
        use_cookie_storage: bool = True,
        encryption_key: Optional[str] = None,
    ):
        """
        初期化

        Args:
            session_dir: セッションデータを保存するディレクトリ。
                        Noneの場合は ~/.kagami/claude_session を使用
            proxy_port: プロキシサーバーのポート番号
            headless: ヘッドレスモードで実行するかどうか
            use_cookie_storage: Cookie永続化を使用するかどうか
            encryption_key: Cookie暗号化キー（Noneの場合は環境変数から取得）
        """
        if session_dir is None:
            home = Path.home()
            session_dir = str(home / ".kagami" / "claude_session")

        self.session_dir = session_dir
        self.cache_dir = str(Path(session_dir).parent / "claude_cache")
        self.proxy_port = proxy_port
        self.headless = headless
        self.proxy_process: Optional[subprocess.Popen] = None
        self.use_cookie_storage = use_cookie_storage

        # ディレクトリを作成
        Path(self.session_dir).mkdir(parents=True, exist_ok=True)
        Path(self.cache_dir).mkdir(parents=True, exist_ok=True)

        # Cookie管理マネージャーを初期化
        if self.use_cookie_storage:
            self.cookie_manager = ClaudeCookieManager(encryption_key=encryption_key)
        else:
            self.cookie_manager = None

    def _get_chromium_args(self) -> list[str]:
        """Chromium起動時の引数を取得"""
        return [
            # 共有メモリ対策
            '--disable-dev-shm-usage',
            '--single-process',

            # サンドボックス無効化
            '--no-sandbox',
            '--disable-setuid-sandbox',

            # プロキシ設定
            f'--proxy-server=http://127.0.0.1:{self.proxy_port}',
            '--ignore-certificate-errors',

            # Bot検出回避
            '--disable-blink-features=AutomationControlled',
            '--disable-features=IsolateOrigins,site-per-process',

            # Headless検出回避
            '--window-size=1920,1080',
            '--start-maximized',

            # その他
            '--disable-gpu',
            '--disable-accelerated-2d-canvas',
            f'--disk-cache-dir={self.cache_dir}',

            # User agent
            '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        ]

    def _inject_anti_detection_scripts(self, page: Page) -> None:
        """Bot検出回避のJavaScriptを注入"""
        script = """
        Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
        Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
        Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});
        window.chrome = { runtime: {} };
        """
        page.add_init_script(script)

    def start_proxy(self) -> None:
        """プロキシサーバーを起動"""
        if self.proxy_process is not None:
            return

        https_proxy = os.environ.get('HTTPS_PROXY')
        if not https_proxy:
            raise ValueError("HTTPS_PROXY environment variable is not set")

        print(f"Starting proxy on port {self.proxy_port}...")
        self.proxy_process = subprocess.Popen(
            [
                'uv', 'run', 'proxy',
                '--hostname', '127.0.0.1',
                '--port', str(self.proxy_port),
                '--plugins', 'proxy.plugin.proxy_pool.ProxyPoolPlugin',
                '--proxy-pool', https_proxy,
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        time.sleep(3)  # プロキシ起動待ち
        print("✅ Proxy started")

    def stop_proxy(self) -> None:
        """プロキシサーバーを停止"""
        if self.proxy_process is None:
            return

        print("Stopping proxy...")
        self.proxy_process.terminate()
        try:
            self.proxy_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            self.proxy_process.kill()
        self.proxy_process = None
        print("✅ Proxy stopped")

    def create_browser_context(self, playwright, load_cookies: bool = True) -> BrowserContext:
        """
        永続化コンテキストでブラウザを起動

        Args:
            playwright: Playwrightインスタンス
            load_cookies: 保存されたCookieをロードするかどうか

        Returns:
            BrowserContext
        """
        print("Launching Chromium...")
        browser = playwright.chromium.launch_persistent_context(
            user_data_dir=self.session_dir,
            headless=self.headless,
            args=self._get_chromium_args()
        )
        print("✅ Browser launched")

        # 保存されたCookieをロード
        if load_cookies and self.cookie_manager and self.cookie_manager.cookies_exist():
            try:
                self.cookie_manager.load_to_context(browser)
            except Exception as e:
                print(f"⚠️  Failed to load cookies: {e}")
                print("   Continuing without cookies...")

        return browser

    def wait_for_cloudflare_challenge(self, page: Page, max_attempts: int = 20) -> bool:
        """
        Cloudflareチャレンジが完了するまで待機

        Args:
            page: Playwrightのページオブジェクト
            max_attempts: 最大試行回数

        Returns:
            チャレンジが完了したかどうか
        """
        print("Waiting for Cloudflare challenge...")
        for i in range(max_attempts):
            time.sleep(2)

            title = page.title()
            content_sample = page.content()[:500]

            # Cloudflareチャレンジのチェック
            is_challenge = (
                "Just a moment" in title or
                "Verifying you are human" in content_sample or
                "challenge" in content_sample.lower()
            )

            if not is_challenge:
                print(f"  ✅ Challenge passed! (attempt {i+1}/{max_attempts})")
                return True

            if (i + 1) % 5 == 0:
                print(f"  [{i+1}/{max_attempts}] Still waiting... Title: {title}")

        print(f"  ⚠️ Challenge not completed after {max_attempts * 2}s")
        return False

    def is_logged_in(self, page: Page) -> bool:
        """
        ログイン状態を確認

        Args:
            page: Playwrightのページオブジェクト

        Returns:
            ログインしているかどうか
        """
        try:
            # URLをチェック
            url = page.url
            if "/login" in url or "/auth" in url:
                return False

            # タイトルをチェック
            title = page.title()
            if "Log in" in title or "Sign in" in title:
                return False

            # ページ内容からログインボタンを探す
            login_buttons = page.locator("button:has-text('Log in'), button:has-text('Sign in'), a:has-text('Log in')").count()
            if login_buttons > 0:
                return False

            return True

        except Exception as e:
            print(f"⚠️ Error checking login status: {e}")
            return False

    def access_claude_code(
        self,
        timeout: int = 60000,
        wait_for_network_idle: bool = True
    ) -> tuple[BrowserContext, Page]:
        """
        Claude Codeにアクセス

        Args:
            timeout: タイムアウト時間（ミリ秒）
            wait_for_network_idle: ネットワークがアイドル状態になるまで待つか

        Returns:
            (browser_context, page) のタプル
        """
        with sync_playwright() as p:
            browser = self.create_browser_context(p)
            page = browser.pages[0] if browser.pages else browser.new_page()

            # Bot検出回避スクリプトを注入
            self._inject_anti_detection_scripts(page)

            print("Accessing https://claude.ai/code/ ...")
            response = page.goto("https://claude.ai/code/", timeout=timeout)
            print(f"✅ Status: {response.status}")
            print(f"✅ URL: {response.url}")

            # Cloudflareチャレンジを待機
            self.wait_for_cloudflare_challenge(page)

            # ネットワークアイドルを待機
            if wait_for_network_idle:
                try:
                    page.wait_for_load_state("networkidle", timeout=30000)
                    print("✅ Network idle")
                except Exception as e:
                    print(f"⚠️ Network idle timeout: {e}")

            # ログイン状態を確認
            if self.is_logged_in(page):
                print("✅ Logged in!")
            else:
                print("⚠️ Not logged in. Please run login script first.")

            return browser, page

    def save_cookies_from_context(self, context: BrowserContext) -> None:
        """
        ブラウザコンテキストからCookieを保存

        Args:
            context: PlaywrightのBrowserContext
        """
        if self.cookie_manager:
            self.cookie_manager.save_from_context(context)
        else:
            print("⚠️  Cookie storage is disabled")

    def delete_saved_cookies(self) -> None:
        """保存されたCookieを削除"""
        if self.cookie_manager:
            self.cookie_manager.delete_cookies()
        else:
            print("⚠️  Cookie storage is disabled")

    def has_saved_cookies(self) -> bool:
        """
        保存されたCookieが存在するか確認

        Returns:
            Cookieが保存されている場合True
        """
        if self.cookie_manager:
            return self.cookie_manager.cookies_exist()
        return False

    def __enter__(self):
        """コンテキストマネージャー: 開始"""
        self.start_proxy()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """コンテキストマネージャー: 終了"""
        self.stop_proxy()
