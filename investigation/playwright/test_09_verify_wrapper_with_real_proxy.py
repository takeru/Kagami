#!/usr/bin/env python3
"""
テスト9: 実際のHTTPS_PROXY環境変数でラッパースクリプトを検証

実際の環境変数を使って、ラッパースクリプトが正しく動作するか確認します。
"""
import os
import sys
import json
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / '.mcp'))

# ラッパースクリプトのモジュールをインポート
import start_playwright_mcp_firefox as mcp_wrapper


def test_real_proxy_extraction():
    """実際のHTTPS_PROXY環境変数から認証情報を抽出"""
    print("=" * 70)
    print("テスト: 実際のHTTPS_PROXY環境変数から認証情報を抽出")
    print("=" * 70)
    print()

    https_proxy = os.getenv("HTTPS_PROXY")

    if not https_proxy:
        print("❌ HTTPS_PROXY環境変数が設定されていません")
        return False

    # URLの構造を表示（認証情報はマスク）
    import re
    masked_url = re.sub(r'(://[^:]+:)[^@]+(@)', r'\1***\2', https_proxy)
    print(f"HTTPS_PROXY: {masked_url}")
    print()

    try:
        # 認証情報を抽出
        server, username, password = mcp_wrapper.extract_proxy_credentials(https_proxy)

        print("抽出結果:")
        print(f"  サーバー: {server}")
        print(f"  ユーザー名: {username[:10]}..." if username else "  ユーザー名: None")
        print(f"  パスワード: {'*' * min(len(password), 20)}..." if password else "  パスワード: None")
        print()

        if server and username and password:
            print("✅ 認証情報の抽出に成功しました")
            return True
        else:
            print("❌ 認証情報の抽出に失敗しました")
            return False

    except Exception as e:
        print(f"❌ エラー: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_real_config_generation():
    """実際の環境変数で設定ファイルを生成"""
    print("\n")
    print("=" * 70)
    print("テスト: 実際の環境変数で設定ファイルを生成")
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
        # 設定ファイルを生成
        print("設定ファイルを生成中...")
        temp_config_path = mcp_wrapper.create_config_with_auth(
            str(base_config_path),
            https_proxy
        )

        # 生成された設定を読み込み
        with open(temp_config_path, 'r') as f:
            generated_config = json.load(f)

        print("✅ 設定ファイルの生成に成功しました")
        print()

        # 設定の検証
        checks = []

        # extraHTTPHeadersが存在するか
        if ('contextOptions' in generated_config and
            'extraHTTPHeaders' in generated_config['contextOptions']):
            headers = generated_config['contextOptions']['extraHTTPHeaders']

            if 'Proxy-Authorization' in headers:
                auth_header = headers['Proxy-Authorization']
                print(f"✅ Proxy-Authorizationヘッダー: {auth_header[:30]}...")

                # Base64エンコードされているか確認
                if auth_header.startswith('Basic '):
                    print("✅ Basic認証形式です")

                    # Base64デコードして検証（デバッグ用）
                    import base64
                    try:
                        auth_b64 = auth_header.replace('Basic ', '')
                        decoded = base64.b64decode(auth_b64).decode('utf-8')
                        # ユーザー名部分のみ表示
                        username_part = decoded.split(':')[0]
                        print(f"✅ デコード確認: ユーザー名={username_part[:10]}...")
                        checks.append(True)
                    except Exception as e:
                        print(f"⚠ デコードエラー: {e}")
                        checks.append(False)
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
        print("✅ 一時ファイルを削除しました")

        return all(checks)

    except Exception as e:
        print(f"❌ エラー: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    print("実際のHTTPS_PROXY環境変数でのラッパースクリプト検証")
    print()

    results = []

    # テスト1: 認証情報の抽出
    results.append(("認証情報の抽出", test_real_proxy_extraction()))

    # テスト2: 設定ファイルの生成
    results.append(("設定ファイルの生成", test_real_config_generation()))

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
        print("🎉 実際の環境変数でラッパースクリプトが正しく動作しました！")
        print()
        print("次のステップ: Firefoxでの実際のアクセステスト")
    else:
        print("⚠️ 一部のテストが失敗しました")

    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
