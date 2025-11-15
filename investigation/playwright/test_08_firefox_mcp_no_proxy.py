#!/usr/bin/env python3
"""
テスト8: Firefox + extraHTTPHeaders方式でproxy.pyなしのMCP設定を検証

.mcp/start_playwright_mcp_firefox.py が正しく動作し、
環境変数から認証情報を抽出して設定ファイルに追加できることを確認します。
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


def test_extract_proxy_credentials():
    """プロキシ認証情報の抽出をテスト"""
    print("=" * 70)
    print("テスト1: プロキシ認証情報の抽出")
    print("=" * 70)
    print()

    test_cases = [
        {
            "url": "https://user:pass@proxy.example.com:8080",
            "expected_server": "https://proxy.example.com:8080",
            "expected_user": "user",
            "expected_pass": "pass"
        },
        {
            "url": "http://alice:secret123@10.0.0.1:3128",
            "expected_server": "http://10.0.0.1:3128",
            "expected_user": "alice",
            "expected_pass": "secret123"
        },
        {
            "url": None,
            "expected_server": None,
            "expected_user": None,
            "expected_pass": None
        }
    ]

    all_passed = True
    for i, tc in enumerate(test_cases, 1):
        print(f"テストケース {i}: {tc['url']}")
        server, user, password = mcp_wrapper.extract_proxy_credentials(tc['url'])

        if (server == tc['expected_server'] and
            user == tc['expected_user'] and
            password == tc['expected_pass']):
            print(f"  ✅ 成功")
            print(f"     サーバー: {server}")
            print(f"     ユーザー: {user}")
            print(f"     パスワード: {'*' * len(password) if password else None}")
        else:
            print(f"  ❌ 失敗")
            print(f"     期待: server={tc['expected_server']}, user={tc['expected_user']}")
            print(f"     実際: server={server}, user={user}")
            all_passed = False
        print()

    return all_passed


def test_config_generation():
    """設定ファイル生成をテスト"""
    print("=" * 70)
    print("テスト2: 設定ファイルの生成")
    print("=" * 70)
    print()

    # ベース設定ファイルのパス
    base_config_path = project_root / '.mcp' / 'playwright-firefox-config.json'

    if not base_config_path.exists():
        print(f"❌ ベース設定ファイルが見つかりません: {base_config_path}")
        return False

    # テスト用のプロキシURL
    test_proxy_url = "https://testuser:testpass@proxy.example.com:8080"

    try:
        # 設定ファイルを生成
        temp_config_path = mcp_wrapper.create_config_with_auth(
            str(base_config_path),
            test_proxy_url
        )

        # 生成された設定を読み込み
        with open(temp_config_path, 'r') as f:
            generated_config = json.load(f)

        print("生成された設定:")
        print(json.dumps(generated_config, indent=2, ensure_ascii=False))
        print()

        # 検証
        checks = []

        # contextOptionsが存在するか
        if 'contextOptions' in generated_config:
            print("✅ contextOptionsが存在します")
            checks.append(True)
        else:
            print("❌ contextOptionsが存在しません")
            checks.append(False)

        # extraHTTPHeadersが存在するか
        if ('contextOptions' in generated_config and
            'extraHTTPHeaders' in generated_config['contextOptions']):
            print("✅ extraHTTPHeadersが存在します")
            checks.append(True)

            # Proxy-Authorizationヘッダーが存在するか
            headers = generated_config['contextOptions']['extraHTTPHeaders']
            if 'Proxy-Authorization' in headers:
                print("✅ Proxy-Authorizationヘッダーが設定されています")
                print(f"   値: {headers['Proxy-Authorization'][:20]}...")
                checks.append(True)

                # Base64エンコードされているか確認
                if headers['Proxy-Authorization'].startswith('Basic '):
                    print("✅ Basic認証形式です")
                    checks.append(True)
                else:
                    print("❌ Basic認証形式ではありません")
                    checks.append(False)
            else:
                print("❌ Proxy-Authorizationヘッダーが設定されていません")
                checks.append(False)
        else:
            print("❌ extraHTTPHeadersが存在しません")
            checks.append(False)

        # 一時ファイルを削除
        os.unlink(temp_config_path)

        print()
        return all(checks)

    except Exception as e:
        print(f"❌ エラー: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_config_without_proxy():
    """プロキシなしの設定ファイル生成をテスト"""
    print("=" * 70)
    print("テスト3: プロキシなしの設定ファイル生成")
    print("=" * 70)
    print()

    # ベース設定ファイルのパス
    base_config_path = project_root / '.mcp' / 'playwright-firefox-config.json'

    if not base_config_path.exists():
        print(f"❌ ベース設定ファイルが見つかりません: {base_config_path}")
        return False

    try:
        # プロキシなしで設定ファイルを生成
        temp_config_path = mcp_wrapper.create_config_with_auth(
            str(base_config_path),
            None  # プロキシなし
        )

        # 生成された設定を読み込み
        with open(temp_config_path, 'r') as f:
            generated_config = json.load(f)

        print("✅ プロキシなしでも設定ファイルが生成されました")
        print()

        # 一時ファイルを削除
        os.unlink(temp_config_path)

        return True

    except Exception as e:
        print(f"❌ エラー: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    print("Firefox + extraHTTPHeaders方式のMCP設定検証")
    print()

    results = []

    # テスト1: プロキシ認証情報の抽出
    results.append(("プロキシ認証情報の抽出", test_extract_proxy_credentials()))

    # テスト2: 設定ファイルの生成
    results.append(("設定ファイルの生成", test_config_generation()))

    # テスト3: プロキシなしの設定ファイル生成
    results.append(("プロキシなしの設定", test_config_without_proxy()))

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
        print("🎉 すべてのテストが成功しました！")
        print()
        print("次のステップ:")
        print("  1. 実際のHTTPS_PROXY環境変数を設定")
        print("  2. .mcp.jsonの設定でMCPサーバーを起動")
        print("  3. MCPクライアントから接続して動作確認")
    else:
        print("⚠️ 一部のテストが失敗しました")

    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
