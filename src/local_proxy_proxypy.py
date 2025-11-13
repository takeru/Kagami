#!/usr/bin/env python3
"""
proxy.pyライブラリを使用したHTTP/2対応プロキシサーバー

Chromium → localhost:8888 (proxy.py) → JWT proxy → Internet

Features:
- proxy.pyライブラリ使用（HTTP/2ネイティブサポート）
- JWT認証の透過的な処理
- プラグインシステムでカスタマイズ可能
"""
import os
import sys
import logging
from proxy import Proxy
from proxy.http.proxy import HttpProxyBasePlugin
from proxy.http.parser import HttpParser
from proxy.common.utils import build_http_request


# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='[ProxyPy] %(message)s'
)
logger = logging.getLogger(__name__)


class JWTProxyPlugin(HttpProxyBasePlugin):
    """
    JWT認証プロキシへの転送を処理するプラグイン
    """

    def name(self) -> str:
        return 'JWTProxyPlugin'

    def before_upstream_connection(self, request: HttpParser):
        """
        上流プロキシへの接続前に呼ばれる
        ここでProxy-Authorizationヘッダーを追加できる
        """
        logger.info(f"Request: {request.method} {request.host}:{request.port}")
        return request

    def handle_client_request(self, request: HttpParser):
        """
        クライアントリクエストを処理
        """
        logger.info(f"Handling: {request.method} {request.path}")
        return request

    def handle_upstream_chunk(self, chunk: memoryview):
        """
        上流サーバーからのレスポンスチャンクを処理
        """
        return chunk


def run_proxy_server(host='127.0.0.1', port=8888):
    """
    proxy.pyを使用してプロキシサーバーを起動
    """
    logger.info("="*60)
    logger.info("proxy.py HTTP/2 Proxy Server Starting")
    logger.info("="*60)

    # 上流プロキシの設定を取得
    upstream_proxy = os.environ.get('HTTPS_PROXY') or os.environ.get('HTTP_PROXY')
    if not upstream_proxy:
        logger.error("HTTPS_PROXY or HTTP_PROXY environment variable not set")
        sys.exit(1)

    logger.info(f"Upstream proxy: {upstream_proxy[:80]}...")
    logger.info(f"Listening on: {host}:{port}")
    logger.info(f"Plugin: JWTProxyPlugin")
    logger.info("")
    logger.info("To use with Playwright:")
    logger.info("  browser = p.chromium.launch(")
    logger.info(f"      proxy={{\"server\": \"http://{host}:{port}\"}}")
    logger.info("  )")
    logger.info("="*60)
    logger.info("")

    # proxy.pyの起動オプション
    # proxy-poolで上流プロキシを指定
    # upstream_proxyにはJWT認証情報が含まれている
    # 形式: http://username:password@host:port

    try:
        with Proxy(
            input_args=[
                '--hostname', host,
                '--port', str(port),
                '--plugins', 'src.local_proxy_proxypy.JWTProxyPlugin',
                '--proxy-pool', upstream_proxy,  # 上流プロキシを指定
                '--enable-conn-pool',  # コネクションプール有効化
            ]
        ):
            logger.info("Proxy server running... Press Ctrl+C to stop")
            # メインスレッドで待機
            import time
            while True:
                time.sleep(1)
    except KeyboardInterrupt:
        logger.info("\nShutting down proxy server...")


if __name__ == "__main__":
    run_proxy_server()
