#!/usr/bin/env python3
"""
Claude Code アクセススクリプト

保存されたセッションを使用して、Claude Codeにアクセスします。
ログイン済みの状態でページを開き、内容を取得・操作できます。

使い方:
    # 基本的な使い方（ヘッドレスモード）
    uv run python scripts/access_claude_code.py

    # ブラウザを表示して確認
    uv run python scripts/access_claude_code.py --show-browser

    # 特定のアクションを実行
    uv run python scripts/access_claude_code.py --action list_projects

注意:
    - 事前に scripts/login_claude.py でログインしておく必要があります
    - HTTPS_PROXY環境変数が設定されている必要があります
"""

import sys
import os
import argparse

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.claude_login import ClaudeLoginManager
from playwright.sync_api import sync_playwright


def list_projects(page):
    """プロジェクト一覧を取得（デモ用）"""
    print("\n" + "=" * 70)
    print("プロジェクト一覧を取得中...")
    print("=" * 70)

    # ページのタイトルとURLを表示
    print(f"Title: {page.title()}")
    print(f"URL: {page.url}")

    # TODO: 実際のプロジェクト一覧の取得ロジックを実装
    # ここでは、デモとしてページのh1要素を取得
    try:
        headings = page.locator("h1, h2").all()
        print(f"\nFound {len(headings)} headings:")
        for i, heading in enumerate(headings[:5], 1):
            try:
                text = heading.text_content(timeout=1000)
                if text:
                    print(f"  [{i}] {text.strip()}")
            except:
                pass
    except Exception as e:
        print(f"⚠️ Error: {e}")


def get_page_info(page):
    """ページ情報を取得"""
    print("\n" + "=" * 70)
    print("ページ情報")
    print("=" * 70)

    print(f"Title: {page.title()}")
    print(f"URL: {page.url}")

    # ボタンとリンクの数を取得
    try:
        buttons = page.locator("button").count()
        links = page.locator("a").count()
        print(f"\nElements:")
        print(f"  Buttons: {buttons}")
        print(f"  Links: {links}")
    except Exception as e:
        print(f"⚠️ Error counting elements: {e}")


def interactive_mode(page):
    """インタラクティブモード"""
    print("\n" + "=" * 70)
    print("インタラクティブモード")
    print("=" * 70)
    print()
    print("利用可能なコマンド:")
    print("  info    - ページ情報を表示")
    print("  list    - プロジェクト一覧を表示")
    print("  url     - 現在のURLを表示")
    print("  title   - ページタイトルを表示")
    print("  screenshot <path> - スクリーンショットを保存")
    print("  quit    - 終了")
    print()

    while True:
        try:
            command = input("Command> ").strip()

            if not command:
                continue

            if command == "quit":
                break

            elif command == "info":
                get_page_info(page)

            elif command == "list":
                list_projects(page)

            elif command == "url":
                print(page.url)

            elif command == "title":
                print(page.title())

            elif command.startswith("screenshot "):
                path = command.split(" ", 1)[1]
                page.screenshot(path=path, full_page=True)
                print(f"✅ Screenshot saved: {path}")

            else:
                print(f"Unknown command: {command}")

        except KeyboardInterrupt:
            print()
            break
        except Exception as e:
            print(f"❌ Error: {e}")


def main():
    """メイン処理"""
    # コマンドライン引数の解析
    parser = argparse.ArgumentParser(description="Claude Codeにアクセス")
    parser.add_argument(
        "--show-browser",
        action="store_true",
        help="ブラウザを表示する（デフォルトはヘッドレスモード）"
    )
    parser.add_argument(
        "--action",
        choices=["list_projects", "info", "interactive"],
        default="info",
        help="実行するアクション"
    )
    parser.add_argument(
        "--screenshot",
        type=str,
        help="スクリーンショットの保存パス"
    )
    parser.add_argument(
        "--save-cookies",
        action="store_true",
        help="アクセス後にCookieを保存（更新）する"
    )
    parser.add_argument(
        "--show-cookie-info",
        action="store_true",
        help="保存されているCookie情報を表示"
    )

    args = parser.parse_args()

    print("=" * 70)
    print("Claude Code アクセス")
    print("=" * 70)
    print()

    # HTTPS_PROXYの確認
    if not os.environ.get('HTTPS_PROXY'):
        print("❌ Error: HTTPS_PROXY environment variable is not set")
        print("   Please set HTTPS_PROXY before running this script.")
        return 1

    # ログインマネージャーを作成
    login_manager = ClaudeLoginManager(headless=not args.show_browser)

    # Cookie情報を表示
    if args.show_cookie_info:
        if login_manager.has_saved_cookies():
            print("=" * 70)
            print("保存されているCookie情報")
            print("=" * 70)
            try:
                cookies = login_manager.cookie_manager.load_cookies()
                login_manager.cookie_manager.print_cookie_info(cookies)
                print()
            except Exception as e:
                print(f"❌ Error loading cookies: {e}")
                print()
        else:
            print("⚠️  保存されているCookieがありません")
            print("   Please run: uv run python scripts/login_claude.py")
            print()
        return 0

    try:
        # プロキシを起動
        login_manager.start_proxy()

        with sync_playwright() as p:
            # ブラウザを起動
            browser = login_manager.create_browser_context(p)
            page = browser.pages[0] if browser.pages else browser.new_page()

            # Bot検出回避スクリプトを注入
            login_manager._inject_anti_detection_scripts(page)

            # Claude Codeにアクセス
            print("Accessing https://claude.ai/code/ ...")
            response = page.goto("https://claude.ai/code/", timeout=60000)
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

            # ログイン状態を確認
            if login_manager.is_logged_in(page):
                print("✅ Logged in!")
            else:
                print("⚠️ Not logged in.")
                print("   Please run: uv run python scripts/login_claude.py")
                browser.close()
                return 1

            # スクリーンショット保存
            if args.screenshot:
                page.screenshot(path=args.screenshot, full_page=True)
                print(f"\n📸 Screenshot saved: {args.screenshot}")

            # アクションを実行
            if args.action == "list_projects":
                list_projects(page)
            elif args.action == "info":
                get_page_info(page)
            elif args.action == "interactive":
                interactive_mode(page)

            # Cookieを保存
            if args.save_cookies:
                print("\n" + "=" * 70)
                print("Cookieを保存中...")
                print("=" * 70)
                login_manager.save_cookies_from_context(browser)

            # ブラウザを表示している場合は待機
            if args.show_browser:
                print("\nブラウザを表示しています。")
                print("終了するには、Enterキーを押してください...")
                input()

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
