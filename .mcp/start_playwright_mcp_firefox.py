#!/usr/bin/env python3
"""
Firefoxでproxy.pyなしでPlaywright MCPを起動するラッパースクリプト

環境変数HTTPS_PROXYから認証情報を抽出し、
extraHTTPHeadersでProxy-Authorizationヘッダーを設定します。
"""
import os
import sys
import json
import base64
import tempfile
import subprocess
from urllib.parse import urlparse


def extract_proxy_credentials(proxy_url):
    """プロキシURLから認証情報を抽出"""
    if not proxy_url:
        return None, None, None

    parsed = urlparse(proxy_url)
    username = parsed.username or ""
    password = parsed.password or ""

    if parsed.port:
        server = f"{parsed.scheme}://{parsed.hostname}:{parsed.port}"
    else:
        server = f"{parsed.scheme}://{parsed.hostname}"

    return server, username, password


def create_config_with_auth(base_config_path, proxy_url):
    """
    ベース設定ファイルを読み込み、プロキシ認証情報を追加した
    一時設定ファイルを作成
    """
    # ベース設定を読み込み
    with open(base_config_path, 'r') as f:
        config = json.load(f)

    # プロキシ認証情報を抽出
    server, username, password = extract_proxy_credentials(proxy_url)

    if server and username and password:
        # Basic認証ヘッダーを作成
        auth_string = f"{username}:{password}"
        auth_b64 = base64.b64encode(auth_string.encode('utf-8')).decode('utf-8')

        # contextOptionsにextraHTTPHeadersを追加
        if 'contextOptions' not in config:
            config['contextOptions'] = {}

        if 'extraHTTPHeaders' not in config['contextOptions']:
            config['contextOptions']['extraHTTPHeaders'] = {}

        config['contextOptions']['extraHTTPHeaders']['Proxy-Authorization'] = f'Basic {auth_b64}'

        print(f"✓ プロキシ認証情報を設定に追加しました（サーバー: {server}）", file=sys.stderr)
    else:
        print(f"⚠ HTTPS_PROXY環境変数が設定されていないか、認証情報がありません", file=sys.stderr)

    # 一時ファイルに保存
    temp_fd, temp_path = tempfile.mkstemp(suffix='.json', prefix='playwright-mcp-config-')
    with os.fdopen(temp_fd, 'w') as f:
        json.dump(config, f, indent=2)

    print(f"✓ 設定ファイルを生成しました: {temp_path}", file=sys.stderr)
    # デバッグ: 設定内容を表示（認証情報の最初の20文字のみ）
    debug_config = json.loads(json.dumps(config))
    if 'contextOptions' in debug_config and 'extraHTTPHeaders' in debug_config['contextOptions']:
        if 'Proxy-Authorization' in debug_config['contextOptions']['extraHTTPHeaders']:
            auth_val = debug_config['contextOptions']['extraHTTPHeaders']['Proxy-Authorization']
            debug_config['contextOptions']['extraHTTPHeaders']['Proxy-Authorization'] = auth_val[:30] + '...'
    print(f"✓ 設定内容:\n{json.dumps(debug_config, indent=2, ensure_ascii=False)}", file=sys.stderr)

    return temp_path


def main():
    """メイン処理"""
    # HTTPS_PROXY環境変数を取得
    https_proxy = os.getenv('HTTPS_PROXY')

    # ベース設定ファイルのパス
    script_dir = os.path.dirname(os.path.abspath(__file__))
    base_config = os.path.join(script_dir, 'playwright-firefox-config.json')

    if not os.path.exists(base_config):
        print(f"❌ エラー: 設定ファイルが見つかりません: {base_config}", file=sys.stderr)
        sys.exit(1)

    # 認証情報を追加した設定ファイルを作成
    temp_config = create_config_with_auth(base_config, https_proxy)

    try:
        # playwright-mcpを起動（グローバルインストール版を使用）
        cmd = [
            'node',
            '/opt/node22/lib/node_modules/@playwright/mcp/cli.js',
            '--config', temp_config,
            '--browser', 'firefox'
        ]

        # プロキシサーバーを指定（認証なし）
        if https_proxy:
            server, _, _ = extract_proxy_credentials(https_proxy)
            if server:
                cmd.extend(['--proxy-server', server])

        print(f"✓ Playwright MCPを起動します: {' '.join(cmd)}", file=sys.stderr)

        # 環境変数を準備（HOMEを含める）
        env = os.environ.copy()

        # MCPサーバーを起動（stdioモード）
        subprocess.run(cmd, check=False, env=env)

    finally:
        # デバッグ: 一時ファイルを削除しない（検証のため）
        print(f"✓ 設定ファイルは削除せずに残します: {temp_config}", file=sys.stderr)


if __name__ == '__main__':
    main()
