#!/usr/bin/env python3
"""
HTTP/2 Compatible Local Proxy Server
httpxを使用したHTTP/2対応ローカルプロキシサーバー

Chromium → localhost:8888 (this proxy) → JWT proxy → Internet

Features:
- HTTP/1.1 and HTTP/2 support via httpx
- CONNECT method for HTTPS tunneling with HTTP/2
- JWT authentication to upstream proxy
- Proper connection handling
"""
import socket
import threading
import os
import logging
from http.server import BaseHTTPRequestHandler, HTTPServer
import httpx


# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='[Proxy] %(message)s'
)
logger = logging.getLogger(__name__)


class HTTP2ProxyHandler(BaseHTTPRequestHandler):
    """HTTP/2対応プロキシハンドラー"""

    # クラス変数
    upstream_proxy = None
    proxy_auth = None
    httpx_client = None

    @classmethod
    def setup_upstream_proxy(cls):
        """上流プロキシの設定を初期化"""
        proxy_url = os.environ.get('HTTPS_PROXY') or os.environ.get('HTTP_PROXY')
        if not proxy_url:
            raise ValueError("HTTPS_PROXY or HTTP_PROXY environment variable not set")

        cls.upstream_proxy = proxy_url
        logger.info(f"Upstream proxy: {proxy_url[:80]}...")

        # httpxクライアントを作成（HTTP/2サポート）
        cls.httpx_client = httpx.Client(
            proxy=proxy_url,
            http2=True,  # HTTP/2を有効化
            verify=True,  # SSL検証を有効化（環境のCA証明書を使用）
            timeout=30.0,
        )
        logger.info("httpx client created with HTTP/2 support")

    def log_message(self, format, *args):
        """カスタムログメッセージ"""
        logger.info(f"{self.address_string()} - {format % args}")

    def do_CONNECT(self):
        """
        CONNECTメソッド処理（HTTPS tunneling）

        httpxはCONNECTメソッドを直接サポートしていないため、
        標準ライブラリのsocketでトンネリングを行う
        """
        try:
            # 接続先を取得
            host, port = self.path.split(':')
            port = int(port)

            self.log_message(f"CONNECT request to {host}:{port}")

            # 上流プロキシに接続
            from urllib.parse import urlparse
            parsed = urlparse(self.upstream_proxy)

            proxy_host = parsed.hostname
            proxy_port = parsed.port or 8080

            self.log_message(f"Connecting to upstream proxy {proxy_host}:{proxy_port}")

            # 上流プロキシへのソケット接続
            remote_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            remote_sock.settimeout(30)

            try:
                remote_sock.connect((proxy_host, proxy_port))

                # Proxy-Authorizationヘッダーを準備
                import base64
                if parsed.username and parsed.password:
                    credentials = f"{parsed.username}:{parsed.password}"
                    proxy_auth = base64.b64encode(credentials.encode()).decode()
                else:
                    proxy_auth = None

                # CONNECTリクエストを送信
                connect_request = f"CONNECT {host}:{port} HTTP/1.1\r\n"
                connect_request += f"Host: {host}:{port}\r\n"
                if proxy_auth:
                    connect_request += f"Proxy-Authorization: Basic {proxy_auth}\r\n"
                connect_request += "\r\n"

                remote_sock.sendall(connect_request.encode())

                # プロキシからのレスポンスを読み取り
                response = b""
                while b"\r\n\r\n" not in response:
                    chunk = remote_sock.recv(1024)
                    if not chunk:
                        raise Exception("Connection closed by upstream proxy")
                    response += chunk

                response_line = response.split(b"\r\n")[0].decode()
                self.log_message(f"Upstream proxy response: {response_line}")

                if not response_line.startswith("HTTP/1.1 200") and not response_line.startswith("HTTP/1.0 200"):
                    raise Exception(f"Upstream proxy returned: {response_line}")

                # クライアントに成功を通知
                self.send_response(200, 'Connection Established')
                self.end_headers()

                # 双方向トンネリングを開始
                self._tunnel_bidirectional(self.connection, remote_sock)

            except Exception as e:
                self.log_message(f"CONNECT failed: {e}")
                try:
                    self.send_error(502, f"Proxy Error: {e}")
                except:
                    pass
                raise

        except Exception as e:
            self.log_message(f"CONNECT handler error: {e}")

    def _tunnel_bidirectional(self, client_sock, server_sock):
        """
        双方向トンネリング（改善版）

        HTTP/2フレームを正しく処理するため、
        より積極的なデータ転送を行う
        """
        import select

        total_client_to_server = 0
        total_server_to_client = 0

        try:
            sockets = [client_sock, server_sock]

            # タイムアウト設定（より柔軟に）
            idle_timeout = 30.0  # 30秒に延長
            last_activity = None

            while True:
                readable, _, exceptional = select.select(sockets, [], sockets, idle_timeout)

                if exceptional:
                    self.log_message(f"Tunnel exception detected")
                    break

                if not readable:
                    # アイドルタイムアウト
                    if last_activity is None:
                        # 初回は何もデータが来ていない
                        self.log_message(f"Tunnel timeout (no data)")
                        break
                    else:
                        # データ転送後のアイドル - 正常終了の可能性
                        self.log_message(f"Tunnel idle timeout (sent: {total_client_to_server}B, recv: {total_server_to_client}B)")
                        break

                for sock in readable:
                    try:
                        data = sock.recv(8192)
                        if not data:
                            self.log_message(f"Tunnel closed normally (sent: {total_client_to_server}B, recv: {total_server_to_client}B)")
                            return

                        import time
                        last_activity = time.time()

                        if sock is client_sock:
                            server_sock.sendall(data)
                            total_client_to_server += len(data)
                        else:
                            client_sock.sendall(data)
                            total_server_to_client += len(data)
                    except Exception as e:
                        self.log_message(f"Tunnel transfer error: {e}")
                        return
        finally:
            self.log_message(f"Tunnel stats: sent {total_client_to_server}B, received {total_server_to_client}B")
            try:
                server_sock.close()
            except:
                pass

    def do_GET(self):
        """HTTPリクエスト処理（httpx使用）"""
        self._proxy_request_http2()

    def do_POST(self):
        """HTTPリクエスト処理（httpx使用）"""
        self._proxy_request_http2()

    def do_PUT(self):
        """HTTPリクエスト処理（httpx使用）"""
        self._proxy_request_http2()

    def do_DELETE(self):
        """HTTPリクエスト処理（httpx使用）"""
        self._proxy_request_http2()

    def do_HEAD(self):
        """HTTPリクエスト処理（httpx使用）"""
        self._proxy_request_http2()

    def _proxy_request_http2(self):
        """
        HTTP リクエストを上流プロキシに転送（httpx使用）
        HTTP/2をサポート
        """
        try:
            # リクエストボディを読み取り
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length) if content_length > 0 else None

            # httpxでリクエストを転送
            self.log_message(f"{self.command} {self.path}")

            response = self.httpx_client.request(
                method=self.command,
                url=self.path,
                content=body,
                headers=dict(self.headers),
                follow_redirects=False,
            )

            # レスポンスを返す
            self.send_response(response.status_code)

            # ヘッダーを転送
            for header, value in response.headers.items():
                if header.lower() not in ['transfer-encoding', 'connection']:
                    self.send_header(header, value)

            self.end_headers()

            # ボディを転送
            self.wfile.write(response.content)

            self.log_message(f"{self.command} {self.path} - {response.status_code}")

        except Exception as e:
            self.log_message(f"HTTP request failed: {e}")
            try:
                self.send_error(502, f"Proxy Error: {e}")
            except:
                pass


def run_proxy_server(host='127.0.0.1', port=8888):
    """プロキシサーバーを起動"""
    logger.info("="*60)
    logger.info("HTTP/2 Local Proxy Server Starting")
    logger.info("="*60)

    # 上流プロキシの設定
    HTTP2ProxyHandler.setup_upstream_proxy()

    # サーバー起動
    server = HTTPServer((host, port), HTTP2ProxyHandler)

    logger.info(f"Listening on: {host}:{port}")
    logger.info(f"HTTP/2: Enabled via httpx")
    logger.info("")
    logger.info("To use with Playwright:")
    logger.info("  browser = p.chromium.launch(")
    logger.info(f"      proxy={{\"server\": \"http://{host}:{port}\"}}")
    logger.info("  )")
    logger.info("="*60)
    logger.info("")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("\nShutting down proxy server...")
    finally:
        HTTP2ProxyHandler.httpx_client.close()
        server.server_close()


if __name__ == "__main__":
    run_proxy_server()
