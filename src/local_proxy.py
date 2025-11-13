#!/usr/bin/env python3
"""
Local Proxy Server for Chromium to access JWT-authenticated proxy

Chromium → localhost:8888 (this proxy) → JWT proxy → Internet

Features:
- HTTP and HTTPS support
- CONNECT method for HTTPS tunneling
- JWT authentication to upstream proxy using urllib
- No external dependencies (stdlib only)
"""
import socket
import select
import threading
import urllib.request
import urllib.parse
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
import ssl

class ProxyHandler(BaseHTTPRequestHandler):
    """HTTP/HTTPS Proxy handler"""

    # 上流プロキシの設定を環境変数から取得
    upstream_proxy = os.environ.get('HTTPS_PROXY') or os.environ.get('HTTP_PROXY')

    def log_message(self, format, *args):
        """ログ出力"""
        print(f"[Proxy] {self.address_string()} - {format % args}")

    def do_CONNECT(self):
        """
        HTTPS用のCONNECTメソッド処理
        クライアント ← トンネル → ローカルプロキシ ← urllib → 上流プロキシ → サーバー
        """
        try:
            # 接続先を取得 (例: example.com:443)
            host, port = self.path.split(':')
            port = int(port)

            self.log_message(f"CONNECT request to {host}:{port}")

            # 上流プロキシ経由でHTTPSサーバーに接続
            # urllibのopenerを使ってプロキシ経由で接続
            proxy_handler = urllib.request.ProxyHandler({
                'https': self.upstream_proxy,
                'http': self.upstream_proxy,
            })
            opener = urllib.request.build_opener(proxy_handler)

            # CONNECTメソッドで上流プロキシにトンネルを確立
            # これが重要: urllibで上流プロキシに接続
            connect_req = urllib.request.Request(
                f'https://{host}:{port}',
                method='CONNECT'
            )

            # 実際には、socketレベルで上流プロキシに接続する必要がある
            # urllibではCONNECTメソッドの完全な制御が難しいため、
            # socketで直接上流プロキシに接続

            if self.upstream_proxy:
                # プロキシURLをパース
                parsed = urllib.parse.urlparse(self.upstream_proxy)
                proxy_host = parsed.hostname
                proxy_port = parsed.port
                proxy_auth = None

                if parsed.username and parsed.password:
                    # Basic認証ヘッダーを作成
                    import base64
                    credentials = f"{parsed.username}:{parsed.password}"
                    proxy_auth = base64.b64encode(credentials.encode()).decode()

                # 上流プロキシに接続
                upstream_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                upstream_sock.settimeout(30)

                self.log_message(f"Connecting to upstream proxy {proxy_host}:{proxy_port}")
                upstream_sock.connect((proxy_host, proxy_port))

                # CONNECTリクエストを送信
                connect_request = f"CONNECT {host}:{port} HTTP/1.1\r\n"
                connect_request += f"Host: {host}:{port}\r\n"

                if proxy_auth:
                    connect_request += f"Proxy-Authorization: Basic {proxy_auth}\r\n"

                connect_request += "\r\n"

                upstream_sock.sendall(connect_request.encode())

                # レスポンスを受信
                response = b""
                while b"\r\n\r\n" not in response:
                    chunk = upstream_sock.recv(1024)
                    if not chunk:
                        raise Exception("No response from upstream proxy")
                    response += chunk

                # ステータスコードをチェック
                status_line = response.split(b"\r\n")[0].decode()
                self.log_message(f"Upstream proxy response: {status_line}")

                if b"200" not in response.split(b"\r\n")[0]:
                    raise Exception(f"Upstream proxy refused connection: {status_line}")

                # クライアントに成功を通知
                self.send_response(200, 'Connection Established')
                self.send_header('Proxy-agent', 'Local-Proxy/1.0')
                self.end_headers()

                # トンネルを確立: クライアント ↔ 上流プロキシ
                self._tunnel_data(self.connection, upstream_sock)

            else:
                # プロキシなしで直接接続（この環境では動作しないが、念のため）
                remote_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                remote_sock.connect((host, port))

                self.send_response(200, 'Connection Established')
                self.end_headers()

                self._tunnel_data(self.connection, remote_sock)

        except Exception as e:
            self.log_message(f"CONNECT failed: {e}")
            try:
                self.send_error(502, f"Proxy Error: {e}")
            except:
                pass

    def _tunnel_data(self, client_sock, server_sock):
        """
        双方向のデータトンネリング
        client_sock ↔ server_sock
        """
        try:
            sockets = [client_sock, server_sock]
            timeout = 60

            while True:
                readable, _, exceptional = select.select(sockets, [], sockets, timeout)

                if exceptional:
                    break

                if not readable:
                    break

                for sock in readable:
                    try:
                        data = sock.recv(8192)
                        if not data:
                            return

                        if sock is client_sock:
                            server_sock.sendall(data)
                        else:
                            client_sock.sendall(data)
                    except:
                        return
        finally:
            try:
                server_sock.close()
            except:
                pass

    def do_GET(self):
        """HTTPリクエスト処理"""
        self._proxy_request()

    def do_POST(self):
        """HTTPリクエスト処理"""
        self._proxy_request()

    def do_PUT(self):
        """HTTPリクエスト処理"""
        self._proxy_request()

    def do_DELETE(self):
        """HTTPリクエスト処理"""
        self._proxy_request()

    def _proxy_request(self):
        """
        HTTP リクエストを上流プロキシに転送
        """
        try:
            # リクエストボディを読み取り
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length) if content_length > 0 else None

            # urllibでリクエストを転送
            req = urllib.request.Request(
                self.path,
                data=body,
                headers=dict(self.headers),
                method=self.command
            )

            # プロキシ経由でリクエスト
            opener = urllib.request.build_opener(
                urllib.request.ProxyHandler({
                    'http': self.upstream_proxy,
                    'https': self.upstream_proxy,
                })
            )

            response = opener.open(req, timeout=30)

            # レスポンスを返す
            self.send_response(response.status)

            for header, value in response.headers.items():
                if header.lower() not in ['transfer-encoding', 'connection']:
                    self.send_header(header, value)

            self.end_headers()
            self.wfile.write(response.read())

        except Exception as e:
            self.log_message(f"HTTP request failed: {e}")
            try:
                self.send_error(502, f"Proxy Error: {e}")
            except:
                pass


def run_proxy_server(host='127.0.0.1', port=8888):
    """プロキシサーバーを起動"""
    server = HTTPServer((host, port), ProxyHandler)

    print(f"="*60)
    print(f"Local Proxy Server Starting")
    print(f"="*60)
    print(f"Listening on: {host}:{port}")

    upstream = os.environ.get('HTTPS_PROXY') or os.environ.get('HTTP_PROXY')
    if upstream:
        parsed = urllib.parse.urlparse(upstream)
        print(f"Upstream proxy: {parsed.scheme}://{parsed.hostname}:{parsed.port}")
        print(f"Authentication: {'Yes (JWT)' if parsed.username else 'No'}")
    else:
        print(f"⚠️  No upstream proxy configured")

    print(f"\nTo use with Playwright:")
    print(f'  browser = p.chromium.launch(')
    print(f'      proxy={{"server": "http://{host}:{port}"}}')
    print(f'  )')
    print(f"="*60)
    print()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n\nShutting down proxy server...")
        server.shutdown()


if __name__ == "__main__":
    import sys

    # ポート指定オプション
    port = 8888
    if len(sys.argv) > 1:
        port = int(sys.argv[1])

    run_proxy_server(port=port)
