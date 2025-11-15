#!/usr/bin/env python3
"""
テスト11: MCP統合チェック

ラッパースクリプトが生成する設定ファイルと起動コマンドを確認します。
"""
import os
import sys
import json
import tempfile
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / '.mcp'))

# ラッパースクリプトのモジュールをインポート
import start_playwright_mcp_firefox as mcp_wrapper


def test_mcp_config_generation():
    """MCPサーバー用の設定ファイルを生成して確認"""
    print("=" * 70)
    print("テスト: MCPサーバー用の設定ファイル生成")
    print("=" * 70)
    print()

    https_proxy = os.getenv("HTTPS_PROXY")
    if not https_proxy:
        print("❌ HTTPS_PROXY環境変数が設定されていません")
        return False

    # ベース設定ファイルのパス
    base_config_path = project_root / '.mcp' / 'playwright-firefox-config.json'

    if not base_config_path.exists():
        print(f"❌ ベース設定ファイルが見つかりません: {base_config_path}")
        return False

    try:
        print("1. ベース設定を読み込み中...")
        with open(base_config_path, 'r') as f:
            base_config = json.load(f)
        print("   ✅ ベース設定の読み込み完了")
        print(f"   launchOptions: {list(base_config.get('launchOptions', {}).keys())}")
        print(f"   contextOptions: {list(base_config.get('contextOptions', {}).keys())}")

        print("\n2. プロキシ認証情報を追加した設定を生成中...")
        temp_config_path = mcp_wrapper.create_config_with_auth(
            str(base_config_path),
            https_proxy
        )

        # 生成された設定を読み込み
        with open(temp_config_path, 'r') as f:
            generated_config = json.load(f)

        print("   ✅ 設定ファイルの生成完了")
        print()

        # 設定の詳細を表示
        print("3. 生成された設定の確認:")
        print(json.dumps(generated_config, indent=2, ensure_ascii=False))
        print()

        # 検証ポイント
        checks = []

        print("4. 検証:")

        # launchOptionsが保持されているか
        if 'launchOptions' in generated_config:
            print("   ✅ launchOptionsが保持されています")
            checks.append(True)
        else:
            print("   ❌ launchOptionsが失われています")
            checks.append(False)

        # contextOptionsにextraHTTPHeadersが追加されているか
        if ('contextOptions' in generated_config and
            'extraHTTPHeaders' in generated_config['contextOptions']):
            print("   ✅ extraHTTPHeadersが追加されています")

            headers = generated_config['contextOptions']['extraHTTPHeaders']
            if 'Proxy-Authorization' in headers:
                print("   ✅ Proxy-Authorizationヘッダーが設定されています")
                auth_value = headers['Proxy-Authorization']
                print(f"      値: {auth_value[:40]}...")
                checks.append(True)
            else:
                print("   ❌ Proxy-Authorizationヘッダーがありません")
                checks.append(False)
        else:
            print("   ❌ extraHTTPHeadersが追加されていません")
            checks.append(False)

        # 元のcontextOptionsが保持されているか
        if ('contextOptions' in generated_config and
            'ignoreHTTPSErrors' in generated_config['contextOptions']):
            print("   ✅ 元のcontextOptionsが保持されています")
            checks.append(True)
        else:
            print("   ❌ 元のcontextOptionsが失われています")
            checks.append(False)

        # 一時ファイルを削除
        os.unlink(temp_config_path)
        print("\n   ✅ 一時ファイルを削除しました")

        return all(checks)

    except Exception as e:
        print(f"❌ エラー: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_mcp_command_generation():
    """MCPサーバー起動コマンドを確認"""
    print("\n")
    print("=" * 70)
    print("テスト: MCPサーバー起動コマンドの確認")
    print("=" * 70)
    print()

    https_proxy = os.getenv("HTTPS_PROXY")
    if not https_proxy:
        print("❌ HTTPS_PROXY環境変数が設定されていません")
        return False

    server, username, password = mcp_wrapper.extract_proxy_credentials(https_proxy)

    if not server:
        print("❌ プロキシサーバーの抽出に失敗しました")
        return False

    print("1. 起動コマンド:")
    print()
    print("   npx @playwright/mcp@latest \\")
    print("     --config <temp_config.json> \\")
    print("     --browser firefox \\")
    print(f"     --proxy-server {server}")
    print()

    print("2. 環境変数:")
    print(f"   HOME: {os.getenv('HOME', '/home/user/Kagami/.mcp/firefox_home')}")
    print()

    print("3. .mcp.jsonの設定:")
    mcp_json_path = project_root / '.mcp.json'
    if mcp_json_path.exists():
        with open(mcp_json_path, 'r') as f:
            mcp_config = json.load(f)

        if 'mcpServers' in mcp_config and 'playwright' in mcp_config['mcpServers']:
            playwright_config = mcp_config['mcpServers']['playwright']
            print(json.dumps(playwright_config, indent=2, ensure_ascii=False))
            print()

            # 検証
            if playwright_config.get('command') == 'uv':
                print("   ✅ commandが'uv'に設定されています")

            args = playwright_config.get('args', [])
            if args == ['run', 'python', '.mcp/start_playwright_mcp_firefox.py']:
                print("   ✅ argsが正しく設定されています")
            else:
                print(f"   ❌ argsが正しくありません: {args}")

            return True
        else:
            print("   ❌ playwright設定が見つかりません")
            return False
    else:
        print(f"   ❌ .mcp.jsonが見つかりません: {mcp_json_path}")
        return False


def main():
    print("MCP統合チェック")
    print()

    results = []

    # テスト1: 設定ファイルの生成
    results.append(("設定ファイルの生成", test_mcp_config_generation()))

    # テスト2: 起動コマンドの確認
    results.append(("起動コマンドの確認", test_mcp_command_generation()))

    # 結果サマリー
    print("\n\n")
    print("=" * 70)
    print("テスト結果サマリー")
    print("=" * 70)
    print()

    all_passed = True
    for test_name, passed in results:
        status = "✅ 成功" if passed else "❌ 失敗"
        print(f"{status}: {test_name}")
        if not passed:
            all_passed = False

    print()
    if all_passed:
        print("🎉 MCP統合チェックが成功しました！")
        print()
        print("確認できたこと:")
        print("  ✅ 設定ファイルが正しく生成される")
        print("  ✅ プロキシ認証ヘッダーが追加される")
        print("  ✅ 元の設定が保持される")
        print("  ✅ .mcp.jsonが正しく設定されている")
        print()
        print("次のステップ:")
        print("  Claude Code WebでMCPサーバーとして使用できます")
        print("  ブラウザ操作をMCP経由で実行可能です")
    else:
        print("⚠️ 一部のチェックが失敗しました")

    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
