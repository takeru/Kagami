#!/usr/bin/env python3
"""
Claude Cookie 管理モジュール

セッションが終了してもCookieを永続化するため、暗号化してファイルに保存します。
"""

import os
import json
import base64
from pathlib import Path
from typing import List, Dict, Optional
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from playwright.sync_api import Page, BrowserContext


class ClaudeCookieManager:
    """Claude.aiのCookieを暗号化して永続化するクラス"""

    def __init__(self, storage_path: Optional[str] = None, encryption_key: Optional[str] = None):
        """
        初期化

        Args:
            storage_path: Cookieを保存するファイルパス。
                         Noneの場合は ~/.kagami/claude_cookies.enc を使用
            encryption_key: 暗号化キー。Noneの場合は環境変数 CLAUDE_COOKIE_KEY を使用。
                          環境変数もない場合は新規生成（推奨しない）
        """
        if storage_path is None:
            home = Path.home()
            storage_path = str(home / ".kagami" / "claude_cookies.enc")

        self.storage_path = storage_path
        Path(self.storage_path).parent.mkdir(parents=True, exist_ok=True)

        # 暗号化キーの取得または生成
        if encryption_key is None:
            encryption_key = os.environ.get('CLAUDE_COOKIE_KEY')

        if encryption_key is None:
            print("⚠️  Warning: CLAUDE_COOKIE_KEY not set. Generating a new key.")
            print("   Please save this key to persist cookies across sessions:")
            encryption_key = self._generate_key()
            print(f"   export CLAUDE_COOKIE_KEY='{encryption_key}'")
            print()

        self.encryption_key = encryption_key
        self._fernet = self._create_fernet(encryption_key)

    def _generate_key(self) -> str:
        """新しい暗号化キーを生成"""
        return Fernet.generate_key().decode('utf-8')

    def _create_fernet(self, key: str) -> Fernet:
        """Fernetインスタンスを作成"""
        try:
            # Base64エンコードされたキーの場合
            return Fernet(key.encode('utf-8'))
        except Exception:
            # パスワードからキーを導出
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=b'claude_cookie_salt',  # 固定ソルト（本番環境では動的に生成すべき）
                iterations=100000,
            )
            key_bytes = base64.urlsafe_b64encode(kdf.derive(key.encode('utf-8')))
            return Fernet(key_bytes)

    def export_cookies(self, context: BrowserContext) -> List[Dict]:
        """
        ブラウザコンテキストからCookieをエクスポート

        Args:
            context: PlaywrightのBrowserContext

        Returns:
            Cookie情報のリスト
        """
        cookies = context.cookies()
        print(f"✅ Exported {len(cookies)} cookies")
        return cookies

    def save_cookies(self, cookies: List[Dict], filepath: Optional[str] = None) -> None:
        """
        Cookieを暗号化してファイルに保存

        Args:
            cookies: Cookie情報のリスト
            filepath: 保存先ファイルパス（Noneの場合はデフォルトパスを使用）
        """
        if filepath is None:
            filepath = self.storage_path

        # CookieをJSON文字列に変換
        cookies_json = json.dumps(cookies, ensure_ascii=False)

        # 暗号化
        encrypted_data = self._fernet.encrypt(cookies_json.encode('utf-8'))

        # ファイルに保存
        with open(filepath, 'wb') as f:
            f.write(encrypted_data)

        print(f"✅ Cookies saved to: {filepath}")
        print(f"   ({len(cookies)} cookies, {len(encrypted_data)} bytes)")

    def load_cookies(self, filepath: Optional[str] = None) -> List[Dict]:
        """
        暗号化されたCookieファイルを読み込んで復号化

        Args:
            filepath: 読み込むファイルパス（Noneの場合はデフォルトパスを使用）

        Returns:
            Cookie情報のリスト

        Raises:
            FileNotFoundError: ファイルが存在しない場合
            Exception: 復号化に失敗した場合
        """
        if filepath is None:
            filepath = self.storage_path

        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Cookie file not found: {filepath}")

        # ファイルを読み込み
        with open(filepath, 'rb') as f:
            encrypted_data = f.read()

        # 復号化
        try:
            decrypted_data = self._fernet.decrypt(encrypted_data)
            cookies = json.loads(decrypted_data.decode('utf-8'))
            print(f"✅ Cookies loaded from: {filepath}")
            print(f"   ({len(cookies)} cookies)")
            return cookies
        except Exception as e:
            raise Exception(f"Failed to decrypt cookies. Wrong key? Error: {e}")

    def import_cookies(self, context: BrowserContext, cookies: List[Dict]) -> None:
        """
        Cookieをブラウザコンテキストにインポート

        Args:
            context: PlaywrightのBrowserContext
            cookies: Cookie情報のリスト
        """
        context.add_cookies(cookies)
        print(f"✅ Imported {len(cookies)} cookies to browser")

    def save_from_context(self, context: BrowserContext, filepath: Optional[str] = None) -> None:
        """
        ブラウザコンテキストからCookieをエクスポートして保存（便利メソッド）

        Args:
            context: PlaywrightのBrowserContext
            filepath: 保存先ファイルパス（Noneの場合はデフォルトパスを使用）
        """
        cookies = self.export_cookies(context)
        self.save_cookies(cookies, filepath)

    def load_to_context(self, context: BrowserContext, filepath: Optional[str] = None) -> None:
        """
        暗号化されたCookieを読み込んでブラウザコンテキストにインポート（便利メソッド）

        Args:
            context: PlaywrightのBrowserContext
            filepath: 読み込むファイルパス（Noneの場合はデフォルトパスを使用）
        """
        cookies = self.load_cookies(filepath)
        self.import_cookies(context, cookies)

    def cookies_exist(self, filepath: Optional[str] = None) -> bool:
        """
        Cookieファイルが存在するか確認

        Args:
            filepath: 確認するファイルパス（Noneの場合はデフォルトパスを使用）

        Returns:
            ファイルが存在する場合True
        """
        if filepath is None:
            filepath = self.storage_path
        return os.path.exists(filepath)

    def delete_cookies(self, filepath: Optional[str] = None) -> None:
        """
        保存されたCookieファイルを削除

        Args:
            filepath: 削除するファイルパス（Noneの場合はデフォルトパスを使用）
        """
        if filepath is None:
            filepath = self.storage_path

        if os.path.exists(filepath):
            os.remove(filepath)
            print(f"✅ Deleted cookie file: {filepath}")
        else:
            print(f"⚠️  Cookie file not found: {filepath}")

    def get_cookie_info(self, cookies: List[Dict]) -> Dict:
        """
        Cookie情報のサマリーを取得

        Args:
            cookies: Cookie情報のリスト

        Returns:
            Cookie情報のサマリー
        """
        domains = set()
        names = []

        for cookie in cookies:
            domains.add(cookie.get('domain', ''))
            names.append(cookie.get('name', ''))

        return {
            'count': len(cookies),
            'domains': sorted(domains),
            'names': names,
        }

    def print_cookie_info(self, cookies: List[Dict]) -> None:
        """
        Cookie情報を表示

        Args:
            cookies: Cookie情報のリスト
        """
        info = self.get_cookie_info(cookies)

        print("\n" + "=" * 70)
        print("Cookie Information")
        print("=" * 70)
        print(f"Total cookies: {info['count']}")
        print(f"\nDomains:")
        for domain in info['domains']:
            domain_cookies = [c for c in cookies if c.get('domain') == domain]
            print(f"  {domain} ({len(domain_cookies)} cookies)")

        print(f"\nCookie names:")
        for name in info['names'][:10]:  # 最初の10個だけ表示
            print(f"  - {name}")

        if len(info['names']) > 10:
            print(f"  ... and {len(info['names']) - 10} more")
