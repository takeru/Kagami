#!/usr/bin/env python3
"""
Playwright MCP セットアップ確認スクリプト

このスクリプトは、mcp.pyのセットアップ機能をテストします。
実際のMCPサーバーを起動せず、セットアップ処理のみを実行します。
"""
import sys
from pathlib import Path

# mcp.pyのセットアップ関数をインポート
sys.path.insert(0, str(Path(__file__).parent))
from mcp import (
    check_setup_completed,
    run_setup,
    log
)


def main():
    """セットアップテスト"""
    log("=" * 70)
    log("Playwright MCP - セットアップテスト開始")
    log("=" * 70)

    # セットアップ状態をチェック
    if check_setup_completed():
        log("セットアップは既に完了しています")
        log("テストのため、個別のセットアップ状態を表示します:")
        log("")

        # 個別の状態を表示
        from mcp import (
            check_command_exists,
            check_npm_package_installed,
        )

        checks = [
            ("certutil", lambda: check_command_exists("certutil")),
            ("@playwright/mcp", lambda: check_npm_package_installed("@playwright/mcp")),
            ("Firefox build v1496", lambda: Path("/home/user/.cache/ms-playwright/firefox-1496").exists()),
            ("Firefoxプロファイル", lambda: Path("/home/user/firefox-profile/cert9.db").exists()),
            ("MCP設定ファイル", lambda: (Path(__file__).parent / "playwright-firefox-config.json").exists()),
        ]

        for name, check_func in checks:
            status = "✅" if check_func() else "❌"
            log(f"  {status} {name}")

        log("")
        log("すべてのコンポーネントが正しくセットアップされています")
    else:
        log("セットアップが未完了です。セットアップを実行します...")
        run_setup()

        # 再チェック
        if check_setup_completed():
            log("セットアップが正常に完了しました！")
        else:
            log("セットアップに失敗しました", "ERROR")
            sys.exit(1)

    log("=" * 70)
    log("テスト完了")
    log("=" * 70)


if __name__ == "__main__":
    main()
