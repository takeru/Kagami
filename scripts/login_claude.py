#!/usr/bin/env python3
"""
Claude.ai 手動ログインスクリプト

このスクリプトは、ブラウザを開いてClaude.aiのログインページを表示します。
ユーザーが手動でログインすると、セッション情報が保存されます。

使い方:
    uv run python scripts/login_claude.py

注意:
    - HTTPS_PROXY環境変数が設定されている必要があります
    - ブラウザウィンドウが開くので、手動でログインしてください
    - ログイン完了後、Enterキーを押してください
"""

import sys
import os

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.claude_login import ClaudeLoginManager
from playwright.sync_api import sync_playwright


def main():
    """メイン処理"""
    print("=" * 70)
    print("Claude.ai 手動ログイン")
    print("=" * 70)
    print()

    # HTTPS_PROXYの確認
    if not os.environ.get('HTTPS_PROXY'):
        print("❌ Error: HTTPS_PROXY environment variable is not set")
        print("   Please set HTTPS_PROXY before running this script.")
        return 1

    print("このスクリプトは、ブラウザを開いてログインページを表示します。")
    print("手動でログインしてください。")
    print()

    # ログインマネージャーを作成（ヘッドレスモードOFF）
    login_manager = ClaudeLoginManager(headless=False)

    try:
        # プロキシを起動
        login_manager.start_proxy()

        with sync_playwright() as p:
            # ブラウザを起動
            browser = login_manager.create_browser_context(p)
            page = browser.pages[0] if browser.pages else browser.new_page()

            # Bot検出回避スクリプトを注入
            login_manager._inject_anti_detection_scripts(page)

            # ログインページにアクセス
            print("\n" + "=" * 70)
            print("Step 1: ログインページにアクセス")
            print("=" * 70)
            response = page.goto("https://claude.ai/login?returnTo=%2Fcode", timeout=60000)
            print(f"✅ Status: {response.status}")
            print(f"✅ URL: {response.url}")

            # Cloudflareチャレンジを待機
            login_manager.wait_for_cloudflare_challenge(page)

            # ネットワークアイドルを待機
            try:
                page.wait_for_load_state("networkidle", timeout=30000)
                print("✅ Network idle")
            except Exception as e:
                print(f"⚠️ Network idle timeout: {e}")

            print("\n" + "=" * 70)
            print("Step 2: 手動ログイン")
            print("=" * 70)
            print()
            print("ブラウザウィンドウが開いています。")
            print("以下の手順でログインしてください：")
            print()
            print("  1. 'Continue with email' ボタンをクリック")
            print("  2. メールアドレスを入力")
            print("  3. メールで受け取った認証コードを入力")
            print("  4. ログインが完了したら、このターミナルに戻ってください")
            print()

            # ユーザーがログインするまで待機
            input("ログインが完了したら、Enterキーを押してください...")

            print("\n" + "=" * 70)
            print("Step 3: ログイン状態を確認")
            print("=" * 70)

            # Claude Codeにアクセスして確認
            page.goto("https://claude.ai/code/", timeout=60000)
            login_manager.wait_for_cloudflare_challenge(page)

            # ログイン状態を確認
            if login_manager.is_logged_in(page):
                print("✅ ログイン成功！")
                print()
                print("セッション情報が保存されました:")
                print(f"  📁 {login_manager.session_dir}")
                print()
                print("次回からは、以下のコマンドでログイン不要でアクセスできます:")
                print("  uv run python scripts/access_claude_code.py")
            else:
                print("⚠️ ログインが完了していないようです。")
                print("   もう一度ログインを試してください。")

            # スクリーンショットを保存
            screenshot_path = "/home/user/Kagami/claude_login_success.png"
            page.screenshot(path=screenshot_path, full_page=True)
            print(f"\n📸 スクリーンショット保存: {screenshot_path}")

            browser.close()

        print("\n" + "=" * 70)
        print("✅ 完了")
        print("=" * 70)
        return 0

    except KeyboardInterrupt:
        print("\n\n⚠️ ユーザーによって中断されました")
        return 1

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

    finally:
        # プロキシを停止
        login_manager.stop_proxy()


if __name__ == "__main__":
    sys.exit(main())
