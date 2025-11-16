#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# ///
"""
Playwright MCP サーバー用セットアップスクリプト

このスクリプトは以下をセットアップします：
  1. certutilのインストール
  2. @playwright/mcpのインストール
  3. proxy.pyのインストール
  4. Firefox build v1496のインストール
  5. Firefoxプロファイルの作成
  6. CA証明書のインポート
  7. MCP設定ファイルの作成

SessionStart hookから自動的に呼び出されます。
"""
import os
import sys
import subprocess
import json
from pathlib import Path
from typing import Optional


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


def check_setup_completed() -> bool:
    """セットアップが完了しているかチェック"""
    script_dir = Path(__file__).parent

    checks = [
        ("certutil", lambda: check_command_exists("certutil")),
        ("@playwright/mcp", lambda: check_npm_package_installed("@playwright/mcp")),
        ("proxy.py", lambda: check_proxy_installed()),
        ("Firefox", lambda: Path("/home/user/.cache/ms-playwright/firefox-1496").exists()),
        ("Firefoxプロファイル", lambda: Path("/home/user/firefox-profile/cert9.db").exists()),
        ("MCP設定ファイル", lambda: (script_dir / "playwright-firefox-config.json").exists()),
    ]

    all_ok = True
    for name, check_func in checks:
        if not check_func():
            log(f"{name} が未セットアップです", "DEBUG")
            all_ok = False

    return all_ok


def main():
    """メイン処理"""
    # HOME環境変数を設定
    os.environ['HOME'] = '/home/user'

    log("=" * 70)
    log("Playwright MCP - セットアップ開始")
    log("=" * 70)

    try:
        # セットアップ状態をチェック
        if check_setup_completed():
            log("セットアップは既に完了しています")
            log("=" * 70)
            return 0

        # セットアップ実行
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
        return 0

    except Exception as e:
        log(f"セットアップ中にエラーが発生しました: {e}", "ERROR")
        import traceback
        traceback.print_exc(file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
