#!/usr/bin/env python3
"""
proxy.pyライブラリを使用したシンプルなプロキシサーバー
プラグインなしで上流プロキシに転送
"""
import os
import sys
import logging


# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='[ProxyPy] %(message)s'
)
logger = logging.getLogger(__name__)


def run_proxy_server(host='127.0.0.1', port=8888):
    """
    proxy.pyを使用してシンプルなプロキシサーバーを起動
    """
    logger.info("="*60)
    logger.info("proxy.py Simple Proxy Server")
    logger.info("="*60)

    # 上流プロキシの設定を取得
    upstream_proxy = os.environ.get('HTTPS_PROXY') or os.environ.get('HTTP_PROXY')
    if not upstream_proxy:
        logger.error("HTTPS_PROXY or HTTP_PROXY environment variable not set")
        sys.exit(1)

    logger.info(f"Upstream proxy: {upstream_proxy[:80]}...")
    logger.info(f"Listening on: {host}:{port}")
    logger.info("")

    # proxy.pyをコマンドライン経由で起動
    # これが最もシンプルな方法
    import subprocess

    cmd = [
        'uv', 'run', 'proxy',
        '--hostname', host,
        '--port', str(port),
        '--proxy-pool', upstream_proxy,
    ]

    logger.info(f"Starting: {' '.join(cmd)}")
    logger.info("="*60)
    logger.info("")

    try:
        subprocess.run(cmd)
    except KeyboardInterrupt:
        logger.info("\nShutting down proxy server...")


if __name__ == "__main__":
    run_proxy_server()
