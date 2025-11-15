#!/usr/bin/env python3
"""
playwright MCPサーバーのブラウザパス設定を調査するスクリプト

調査内容：
1. uv環境でインストールされたPlaywrightのバージョン
2. ブラウザの実行ファイルパス
3. playwright MCPサーバーのバージョン
4. 設定ファイルの例を生成
"""
import os
import subprocess
import json
from pathlib import Path


def get_playwright_version():
    """uv環境のPlaywrightバージョンを取得"""
    try:
        result = subprocess.run(
            ['uv', 'run', 'playwright', '--version'],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except Exception as e:
        return f"Error: {e}"


def get_browser_paths():
    """ブラウザの実行ファイルパスを取得"""
    browsers = {}

    # Firefoxのパス
    try:
        result = subprocess.run(
            ['uv', 'run', 'python', '-c',
             'from playwright.sync_api import sync_playwright; '
             'p = sync_playwright().start(); '
             'print(p.firefox.executable_path)'],
            capture_output=True,
            text=True,
            check=True
        )
        browsers['firefox'] = result.stdout.strip()
    except Exception as e:
        browsers['firefox'] = f"Error: {e}"

    # Chromiumのパス
    try:
        result = subprocess.run(
            ['uv', 'run', 'python', '-c',
             'from playwright.sync_api import sync_playwright; '
             'p = sync_playwright().start(); '
             'print(p.chromium.executable_path)'],
            capture_output=True,
            text=True,
            check=True
        )
        browsers['chromium'] = result.stdout.strip()
    except Exception as e:
        browsers['chromium'] = f"Error: {e}"

    return browsers


def get_mcp_version():
    """playwright MCPサーバーのバージョンを取得"""
    try:
        result = subprocess.run(
            ['npx', '@playwright/mcp@latest', '--version'],
            capture_output=True,
            text=True,
            timeout=30
        )
        return result.stdout.strip()
    except Exception as e:
        return f"Error: {e}"


def generate_config_examples(browser_paths):
    """設定ファイルの例を生成"""
    configs = {}

    # Firefox設定（executable-path指定）
    if 'firefox' in browser_paths and not browser_paths['firefox'].startswith('Error'):
        configs['firefox_executable_path'] = {
            "mcpServers": {
                "playwright": {
                    "command": "npx",
                    "args": [
                        "@playwright/mcp@latest",
                        "--browser", "firefox",
                        "--executable-path", browser_paths['firefox']
                    ]
                }
            }
        }

        # Firefox設定（config file使用）
        firefox_config = {
            "browser": {
                "executablePath": browser_paths['firefox']
            },
            "launchOptions": {
                "headless": True,
                "firefoxUserPrefs": {
                    "privacy.trackingprotection.enabled": False,
                    "network.proxy.allow_hijacking_localhost": True
                }
            }
        }
        configs['firefox_config_file'] = firefox_config

    # Chromium設定
    if 'chromium' in browser_paths and not browser_paths['chromium'].startswith('Error'):
        configs['chromium_executable_path'] = {
            "mcpServers": {
                "playwright": {
                    "command": "npx",
                    "args": [
                        "@playwright/mcp@latest",
                        "--browser", "chromium",
                        "--executable-path", browser_paths['chromium'],
                        "--no-sandbox"
                    ]
                }
            }
        }

    return configs


def main():
    print("=" * 70)
    print("playwright MCPサーバー ブラウザパス設定調査")
    print("=" * 70)
    print()

    # 1. Playwrightバージョン
    print("1. uv環境のPlaywrightバージョン")
    print("-" * 70)
    pw_version = get_playwright_version()
    print(f"   {pw_version}")
    print()

    # 2. ブラウザパス
    print("2. ブラウザ実行ファイルパス")
    print("-" * 70)
    browser_paths = get_browser_paths()
    for browser, path in browser_paths.items():
        print(f"   {browser}: {path}")
    print()

    # 3. MCP バージョン
    print("3. playwright MCPサーバーバージョン")
    print("-" * 70)
    mcp_version = get_mcp_version()
    print(f"   {mcp_version}")
    print()

    # 4. 設定例を生成
    print("4. 推奨設定例")
    print("-" * 70)
    configs = generate_config_examples(browser_paths)

    # 設定ファイルを保存
    output_dir = Path("/home/user/Kagami/investigation/playwright")
    output_dir.mkdir(parents=True, exist_ok=True)

    for name, config in configs.items():
        output_file = output_dir / f"mcp_config_{name}.json"
        with open(output_file, 'w') as f:
            json.dump(config, f, indent=2)
        print(f"   ✅ 保存: {output_file}")

    print()
    print("=" * 70)
    print("推奨される解決策")
    print("=" * 70)
    print()
    print("方法1: --executable-path オプションを使用")
    print("-" * 70)
    if 'firefox' in browser_paths and not browser_paths['firefox'].startswith('Error'):
        print(f"""
.mcp.jsonに以下を設定：

{{
  "mcpServers": {{
    "playwright": {{
      "command": "npx",
      "args": [
        "@playwright/mcp@latest",
        "--browser", "firefox",
        "--executable-path", "{browser_paths['firefox']}"
      ]
    }}
  }}
}}
""")

    print()
    print("方法2: 設定ファイルを使用")
    print("-" * 70)
    print("""
1. mcp_config_firefox_config_file.json を .mcp/ にコピー
2. .mcp.jsonに以下を設定：

{
  "mcpServers": {
    "playwright": {
      "command": "npx",
      "args": [
        "@playwright/mcp@latest",
        "--config", ".mcp/firefox_browser_config.json",
        "--browser", "firefox"
      ]
    }
  }
}
""")

    print()
    print("方法3: proxy.pyと組み合わせる場合")
    print("-" * 70)
    if 'firefox' in browser_paths and not browser_paths['firefox'].startswith('Error'):
        print(f"""
{{
  "mcpServers": {{
    "playwright": {{
      "command": "bash",
      "args": [
        "-c",
        "uv run proxy --hostname 127.0.0.1 --port 18911 --plugins proxy.plugin.proxy_pool.ProxyPoolPlugin --proxy-pool \\"$HTTPS_PROXY\\" >/dev/null 2>&1 & PROXY_PID=$!; trap \\"kill $PROXY_PID 2>/dev/null\\" EXIT; sleep 2; npx @playwright/mcp@latest --browser firefox --executable-path {browser_paths['firefox']} --proxy-server http://127.0.0.1:18911"
      ]
    }}
  }}
}}
""")

    print()
    print("=" * 70)
    print("バージョン互換性について")
    print("=" * 70)
    print(f"""
uv環境のPlaywright: {pw_version}
playwright MCP:     {mcp_version}

playwright MCPサーバーは内部的に独自のPlaywrightを使用する可能性があります。
--executable-pathを指定することで、uv環境のブラウザを直接使用できます。
""")

    print()
    print("=" * 70)
    print("次のステップ")
    print("=" * 70)
    print("""
1. 上記の設定例を .mcp.json に適用
2. Claude Codeを再起動
3. playwright MCPツールをテスト
4. 動作確認できたら、proxy.pyとの組み合わせをテスト
""")


if __name__ == "__main__":
    main()
