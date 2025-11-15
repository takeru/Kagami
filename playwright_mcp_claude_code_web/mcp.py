#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# ///
"""
Claude Code用 Playwright MCP サーバー起動スクリプト

通信フロー:
  Claude Code → mcp.py → playwright-mcp (Firefox) → proxy.py → JWT認証Proxy → Internet

このスクリプトは:
  1. 初回起動時に必要なセットアップを自動実行
  2. proxy.pyをバックグラウンドで起動
  3. playwright-mcpをstdioモードで起動
  4. 終了時にproxy.pyを停止
"""
import os
import sys
import subprocess
import time
import atexit
import signal
import json
from pathlib import Path
from typing import Optional

# グローバル変数でproxy.pyのプロセスを保持
proxy_process = None


def log(message: str, level: str = "INFO"):
    """ログ出力（stderrに出力）"""
    prefix = {
        "INFO": "✓",
        "WARN": "⚠️",
        "ERROR": "❌",
        "DEBUG": "🔍"
    }.get(level, "ℹ️")
    print(f"{prefix} {message}", file=sys.stderr)


def run_command(cmd: list[str], check: bool = True, capture_output: bool = False) -> Optional[subprocess.CompletedProcess]:
    """コマンドを実行"""
    try:
        result = subprocess.run(
            cmd,
            check=check,
            capture_output=capture_output,
            text=True
        )
        return result
    except subprocess.CalledProcessError as e:
        if check:
            log(f"コマンド実行エラー: {' '.join(cmd)}", "ERROR")
            log(f"エラー詳細: {e.stderr if capture_output else str(e)}", "ERROR")
            raise
        return None


def check_command_exists(command: str) -> bool:
    """コマンドが存在するかチェック"""
    result = run_command(["which", command], check=False, capture_output=True)
    return result and result.returncode == 0


def check_npm_package_installed(package: str) -> bool:
    """npmパッケージがグローバルインストールされているかチェック"""
    result = run_command(
        ["npm", "list", "-g", package],
        check=False,
        capture_output=True
    )
    return result and package in result.stdout


def check_proxy_installed() -> bool:
    """proxy.pyがインストールされているかチェック"""
    result = run_command(
        ["uv", "run", "proxy", "--version"],
        check=False,
        capture_output=True
    )
    return result and result.returncode == 0


def setup_certutil():
    """certutilのインストール確認"""
    log("certutilのインストール状況を確認中...")

    if check_command_exists("certutil"):
        log("certutilは既にインストールされています")
        return

    log("certutilをインストール中...", "WARN")
    run_command(["apt-get", "update", "-qq"])
    run_command(["apt-get", "install", "-y", "libnss3-tools"])
    log("certutilをインストールしました")


def setup_playwright_mcp():
    """@playwright/mcpのインストール確認"""
    log("@playwright/mcpのインストール状況を確認中...")

    if check_npm_package_installed("@playwright/mcp"):
        log("@playwright/mcpは既にインストールされています")
        return

    log("@playwright/mcpをインストール中... (数分かかる場合があります)", "WARN")
    run_command(["npm", "install", "-g", "@playwright/mcp"])
    log("@playwright/mcpをインストールしました")


def setup_proxy_py():
    """proxy.pyのインストール確認"""
    log("proxy.pyのインストール状況を確認中...")

    # uv run proxy --version で確認
    result = run_command(
        ["uv", "run", "proxy", "--version"],
        check=False,
        capture_output=True
    )

    if result and result.returncode == 0:
        log("proxy.pyは既にインストールされています")
        return

    log("proxy.pyをインストール中...", "WARN")
    run_command(["uv", "pip", "install", "proxy.py"])
    log("proxy.pyをインストールしました")


def setup_firefox():
    """Firefox build v1496のインストール"""
    log("Firefox build v1496のインストール状況を確認中...")

    firefox_build = Path("/home/user/.cache/ms-playwright/firefox-1496")

    if firefox_build.exists():
        log(f"Firefox build v1496は既にインストールされています: {firefox_build}")
        return

    log("Firefox build v1496をインストール中... (数分かかる場合があります)", "WARN")

    env = os.environ.copy()
    env["HOME"] = "/home/user"

    run_command([
        "node",
        "/opt/node22/lib/node_modules/@playwright/mcp/node_modules/playwright/cli.js",
        "install",
        "firefox"
    ])

    log("Firefox build v1496をインストールしました")


def setup_firefox_profile():
    """Firefoxプロファイルの作成"""
    log("Firefoxプロファイルの確認中...")

    profile_dir = Path("/home/user/firefox-profile")
    cert_db = profile_dir / "cert9.db"

    if profile_dir.exists() and cert_db.exists():
        log(f"Firefoxプロファイルは既に存在します: {profile_dir}")
        return

    log("Firefoxプロファイルを作成中...")

    profile_dir.mkdir(parents=True, exist_ok=True)

    run_command([
        "certutil",
        "-N",
        "-d", f"sql:{profile_dir}",
        "--empty-password"
    ])

    log(f"Firefoxプロファイルを作成しました: {profile_dir}")


def import_ca_certificates():
    """JWT認証プロキシCA証明書のインポート"""
    log("CA証明書のインポート状況を確認中...")

    profile_dir = Path("/home/user/firefox-profile")
    staging_cert = Path("/usr/local/share/ca-certificates/swp-ca-staging.crt")
    production_cert = Path("/usr/local/share/ca-certificates/swp-ca-production.crt")

    # 証明書ファイルの存在確認
    if not staging_cert.exists():
        log(f"staging CA証明書が見つかりません: {staging_cert}", "ERROR")
        sys.exit(1)

    if not production_cert.exists():
        log(f"production CA証明書が見つかりません: {production_cert}", "ERROR")
        sys.exit(1)

    # staging CA証明書のインポート
    result = run_command([
        "certutil",
        "-L",
        "-d", f"sql:{profile_dir}",
        "-n", "Anthropic TLS Inspection CA"
    ], check=False, capture_output=True)

    if result and result.returncode == 0:
        log("staging CA証明書は既にインポートされています")
    else:
        log("staging CA証明書をインポート中...")
        run_command([
            "certutil",
            "-A",
            "-n", "Anthropic TLS Inspection CA",
            "-t", "C,,",
            "-i", str(staging_cert),
            "-d", f"sql:{profile_dir}"
        ])
        log("staging CA証明書をインポートしました")

    # production CA証明書のインポート
    result = run_command([
        "certutil",
        "-L",
        "-d", f"sql:{profile_dir}",
        "-n", "Anthropic TLS Inspection CA Production"
    ], check=False, capture_output=True)

    if result and result.returncode == 0:
        log("production CA証明書は既にインポートされています")
    else:
        log("production CA証明書をインポート中...")
        run_command([
            "certutil",
            "-A",
            "-n", "Anthropic TLS Inspection CA Production",
            "-t", "C,,",
            "-i", str(production_cert),
            "-d", f"sql:{profile_dir}"
        ])
        log("production CA証明書をインポートしました")


def setup_config_file():
    """MCP設定ファイルの作成"""
    log("MCP設定ファイルの確認中...")

    script_dir = Path(__file__).parent
    config_file = script_dir / "playwright-firefox-config.json"

    if config_file.exists():
        log(f"MCP設定ファイルは既に存在します: {config_file}")
        return

    log("MCP設定ファイルを作成中...")

    config = {
        "browser": {
            "browserName": "firefox",
            "userDataDir": "/home/user/firefox-profile",
            "launchOptions": {
                "headless": True,
                "firefoxUserPrefs": {
                    "privacy.trackingprotection.enabled": False,
                    "network.proxy.allow_hijacking_localhost": True,
                    "network.stricttransportsecurity.preloadlist": False,
                    "security.cert_pinning.enforcement_level": 0,
                    "security.enterprise_roots.enabled": False,
                    "security.ssl.errorReporting.enabled": False,
                    "browser.xul.error_pages.expert_bad_cert": True,
                    "media.navigator.streams.fake": True,
                    "security.insecure_connection_text.enabled": False,
                    "security.insecure_connection_text.pbmode.enabled": False,
                    "security.mixed_content.block_active_content": False,
                    "security.mixed_content.block_display_content": False,
                    "security.OCSP.enabled": 0
                },
                "acceptDownloads": False
            },
            "contextOptions": {
                "ignoreHTTPSErrors": True,
                "bypassCSP": True
            }
        }
    }

    with open(config_file, "w") as f:
        json.dump(config, f, indent=2)

    log(f"MCP設定ファイルを作成しました: {config_file}")


def run_setup():
    """初回セットアップを実行"""
    log("=" * 70)
    log("Playwright MCP - 初回セットアップ開始")
    log("=" * 70)

    try:
        setup_certutil()
        setup_playwright_mcp()
        setup_proxy_py()
        setup_firefox()
        setup_firefox_profile()
        import_ca_certificates()
        setup_config_file()

        log("=" * 70)
        log("セットアップが完了しました！")
        log("=" * 70)

    except Exception as e:
        log(f"セットアップ中にエラーが発生しました: {e}", "ERROR")
        import traceback
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)


def check_setup_completed() -> bool:
    """セットアップが完了しているかチェック"""
    checks = [
        ("certutil", lambda: check_command_exists("certutil")),
        ("@playwright/mcp", lambda: check_npm_package_installed("@playwright/mcp")),
        ("proxy.py", lambda: check_proxy_installed()),
        ("Firefox", lambda: Path("/home/user/.cache/ms-playwright/firefox-1496").exists()),
        ("Firefoxプロファイル", lambda: Path("/home/user/firefox-profile/cert9.db").exists()),
        ("MCP設定ファイル", lambda: (Path(__file__).parent / "playwright-firefox-config.json").exists()),
    ]

    all_ok = True
    for name, check_func in checks:
        if not check_func():
            log(f"{name} が未セットアップです", "DEBUG")
            all_ok = False

    return all_ok


def start_proxy():
    """proxy.pyを起動"""
    global proxy_process

    # HTTPS_PROXY環境変数を確認
    https_proxy = os.environ.get('HTTPS_PROXY', '')
    if not https_proxy:
        log("HTTPS_PROXY環境変数が設定されていません", "ERROR")
        sys.exit(1)

    log(f"proxy.pyを起動中... (プロキシ: {https_proxy[:50]}...)")

    proxy_process = subprocess.Popen(
        [
            "uv", "run", "proxy",
            "--hostname", "127.0.0.1",
            "--port", "18915",
            "--plugins", "proxy.plugin.proxy_pool.ProxyPoolPlugin",
            "--proxy-pool", https_proxy
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

    # proxy.pyの起動を待つ
    time.sleep(2)
    log("proxy.py起動完了 (localhost:18915)")


def stop_proxy():
    """proxy.pyを停止"""
    global proxy_process

    if proxy_process is None:
        return

    log("proxy.pyを停止中...")

    try:
        proxy_process.send_signal(signal.SIGTERM)
        proxy_process.wait(timeout=5)
        log("proxy.pyを停止しました")
    except subprocess.TimeoutExpired:
        proxy_process.kill()
        log("proxy.pyを強制終了しました", "WARN")
    except Exception as e:
        log(f"proxy.py停止時にエラー: {e}", "WARN")


def main():
    """メイン処理"""
    # HOME環境変数を設定
    os.environ['HOME'] = '/home/user'

    # セットアップ状態をチェック
    if not check_setup_completed():
        log("初回セットアップを実行します...")
        run_setup()
    else:
        log("セットアップ済みを確認しました")

    # 終了時にproxy.pyを停止するよう登録
    atexit.register(stop_proxy)

    # proxy.pyを起動
    start_proxy()

    # playwright-mcpの設定ファイルパス
    script_dir = Path(__file__).parent
    config_path = str(script_dir / "playwright-firefox-config.json")

    if not os.path.exists(config_path):
        log(f"設定ファイルが見つかりません: {config_path}", "ERROR")
        sys.exit(1)

    log(f"設定ファイル: {config_path}")
    log("playwright-mcpを起動します...")

    # playwright-mcpを起動（stdioモード）
    cmd = [
        'node',
        '/opt/node22/lib/node_modules/@playwright/mcp/cli.js',
        '--config', config_path,
        '--browser', 'firefox',
        '--proxy-server', 'http://127.0.0.1:18915'
    ]

    # 環境変数を準備
    env = os.environ.copy()
    env['HOME'] = '/home/user'

    # playwright-mcpを実行（stdioモード）
    # Claude CodeがstdinからMCPプロトコルのリクエストを送り、
    # stdoutでレスポンスを受け取る
    try:
        subprocess.run(cmd, env=env)
    except KeyboardInterrupt:
        log("\n中断されました")
    except Exception as e:
        log(f"\nエラー: {e}", "ERROR")
        sys.exit(1)


if __name__ == '__main__':
    main()
