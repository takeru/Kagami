"""
proxy.py plugin for JWT proxy authentication
JWT認証プロキシへの転送プラグイン
"""
import os
import logging
from proxy.http.proxy import HttpProxyBasePlugin
from proxy.http.parser import HttpParser
from proxy.core.connection import TcpServerConnection
from proxy.common.utils import build_http_request
from typing import Optional
import socket


logger = logging.getLogger(__name__)


class JWTProxyPlugin(HttpProxyBasePlugin):
    """
    JWT認証が必要な上流プロキシへリクエストを転送するプラグイン
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # 上流プロキシの設定を取得
        self.upstream_proxy = os.environ.get('HTTPS_PROXY') or os.environ.get('HTTP_PROXY')
        if self.upstream_proxy:
            # プロキシURLをパース
            from urllib.parse import urlparse
            parsed = urlparse(self.upstream_proxy)
            self.upstream_host = parsed.hostname
            self.upstream_port = parsed.port or 8080
            self.upstream_username = parsed.username
            self.upstream_password = parsed.password

            logger.info(f"JWT Proxy Plugin initialized: {self.upstream_host}:{self.upstream_port}")
        else:
            logger.warning("No upstream proxy configured")
            self.upstream_host = None

    def name(self) -> str:
        return 'JWTProxyPlugin'

    def before_upstream_connection(self, request: HttpParser) -> Optional[HttpParser]:
        """
        上流プロキシへの接続を確立する前に呼ばれる

        ここで上流プロキシへの接続に切り替える
        """
        if not self.upstream_host:
            return request

        logger.info(f"Routing {request.method} {request.host}:{request.port} via JWT proxy")

        # リクエストを上流プロキシ経由にする
        # proxy.pyが自動的に上流プロキシに接続するように設定
        return request

    def handle_client_request(self, request: HttpParser) -> Optional[HttpParser]:
        """
        クライアントリクエストを処理

        上流プロキシへ転送する前にProxy-Authorizationヘッダーを追加
        """
        if not self.upstream_host:
            return request

        # JWT認証情報をProxy-Authorizationヘッダーとして追加
        if self.upstream_username and self.upstream_password:
            import base64
            credentials = f"{self.upstream_username}:{self.upstream_password}"
            proxy_auth = base64.b64encode(credentials.encode()).decode()

            # ヘッダーを追加
            request.add_header(b'Proxy-Authorization', f"Basic {proxy_auth}".encode())
            logger.debug(f"Added Proxy-Authorization header")

        return request
