#!/usr/bin/env python3
"""
Claude.ai ログインスクリプト

このスクリプトは、メールアドレスを自動入力してClaude.aiにログインします。
認証コードの入力は対話的に行います。

使い方:
    export EMAIL="your@email.com"
    uv run python scripts/login_claude.py

注意:
    - HTTPS_PROXY環境変数が設定されている必要があります
    - EMAIL環境変数にメールアドレスを設定してください
    - メールで受け取った認証コードを入力する必要があります
"""

import sys
import os
import time

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.claude_login import ClaudeLoginManager
from playwright.sync_api import sync_playwright


def main():
    """メイン処理"""
    print("=" * 70)
    print("Claude.ai ログイン")
    print("=" * 70)
    print()

    # HTTPS_PROXYの確認
    if not os.environ.get('HTTPS_PROXY'):
        print("❌ Error: HTTPS_PROXY environment variable is not set")
        print("   Please set HTTPS_PROXY before running this script.")
        return 1

    # EMAILの確認
    email = os.environ.get('EMAIL')
    if not email:
        print("❌ Error: EMAIL environment variable is not set")
        print("   Please set EMAIL before running this script.")
        print("   Example: export EMAIL='your@email.com'")
        return 1

    print(f"ログインメールアドレス: {email}")
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

            # Step 2: "Continue with email" ボタンをクリック
            print("\n" + "=" * 70)
            print("Step 2: 'Continue with email' ボタンをクリック")
            print("=" * 70)

            try:
                # ボタンを探してクリック
                email_button = page.locator("button:has-text('Continue with email')").first
                email_button.wait_for(state="visible", timeout=10000)
                print("✅ Found 'Continue with email' button")

                email_button.click()
                print("✅ Clicked 'Continue with email' button")

                # ページ遷移を待機
                time.sleep(2)

            except Exception as e:
                print(f"❌ Failed to click 'Continue with email' button: {e}")
                print("   Please click the button manually in the browser window.")
                input("   Press Enter when ready...")

            # Step 3: メールアドレスを入力
            print("\n" + "=" * 70)
            print("Step 3: メールアドレスを入力")
            print("=" * 70)
            print(f"Current URL: {page.url}")

            try:
                # メール入力フィールドを探す
                # 複数のパターンを試す
                email_input = None
                selectors = [
                    "input[type='email']",
                    "input[name='email']",
                    "input[placeholder*='email' i]",
                    "input[placeholder*='メール' i]",
                ]

                for selector in selectors:
                    try:
                        input_field = page.locator(selector).first
                        if input_field.is_visible(timeout=2000):
                            email_input = input_field
                            print(f"✅ Found email input field: {selector}")
                            break
                    except:
                        continue

                if email_input:
                    # メールアドレスを入力
                    email_input.fill(email)
                    print(f"✅ Entered email: {email}")

                    # 送信ボタンを探してクリック
                    submit_selectors = [
                        "button[type='submit']",
                        "button:has-text('Continue')",
                        "button:has-text('送信')",
                        "button:has-text('次へ')",
                    ]

                    submit_button = None
                    for selector in submit_selectors:
                        try:
                            btn = page.locator(selector).first
                            if btn.is_visible(timeout=2000):
                                submit_button = btn
                                print(f"✅ Found submit button: {selector}")
                                break
                        except:
                            continue

                    if submit_button:
                        submit_button.click()
                        print("✅ Clicked submit button")
                        time.sleep(3)  # 送信処理を待つ
                    else:
                        print("⚠️  Submit button not found. Please submit manually.")
                        input("   Press Enter after submitting...")

                else:
                    print("❌ Email input field not found")
                    print("   Please enter your email manually in the browser window.")
                    input("   Press Enter when ready...")

            except Exception as e:
                print(f"❌ Failed to enter email: {e}")
                print("   Please enter your email manually in the browser window.")
                input("   Press Enter when ready...")

            # Step 4: 認証コードを入力
            print("\n" + "=" * 70)
            print("Step 4: 認証コードを入力")
            print("=" * 70)
            print()
            print("メールで受け取った認証コードを入力してください。")
            print("認証URLを開いて、表示された番号を入力してください。")
            print()

            # 認証コードを入力してもらう
            auth_code = input("認証コード (6桁): ").strip()

            if auth_code:
                try:
                    # 認証コード入力フィールドを探す
                    code_input = None
                    code_selectors = [
                        "input[type='text']",
                        "input[name='code']",
                        "input[placeholder*='code' i]",
                        "input[placeholder*='コード' i]",
                    ]

                    for selector in code_selectors:
                        try:
                            inp = page.locator(selector).first
                            if inp.is_visible(timeout=2000):
                                code_input = inp
                                print(f"✅ Found code input field: {selector}")
                                break
                        except:
                            continue

                    if code_input:
                        code_input.fill(auth_code)
                        print(f"✅ Entered auth code: {auth_code}")

                        # 送信ボタンをクリック
                        time.sleep(1)
                        submit_btn = page.locator("button[type='submit']").first
                        if submit_btn.is_visible(timeout=2000):
                            submit_btn.click()
                            print("✅ Clicked submit button")
                        else:
                            print("⚠️  Please click submit button manually")
                            input("   Press Enter after clicking...")

                        # ログイン処理を待つ
                        time.sleep(3)

                    else:
                        print("❌ Auth code input field not found")
                        print("   Please enter the code manually in the browser window.")
                        input("   Press Enter after entering the code...")

                except Exception as e:
                    print(f"❌ Failed to enter auth code: {e}")
                    print("   Please enter the code manually in the browser window.")
                    input("   Press Enter after entering the code...")
            else:
                print("⚠️  No auth code provided. Please enter manually in the browser.")
                input("   Press Enter after completing login...")

            # Step 5: ログイン状態を確認
            print("\n" + "=" * 70)
            print("Step 5: ログイン状態を確認")
            print("=" * 70)

            # Claude Codeにアクセスして確認
            print("Accessing Claude Code to verify login...")
            page.goto("https://claude.ai/code/", timeout=60000)
            login_manager.wait_for_cloudflare_challenge(page)

            # ログイン状態を確認
            if login_manager.is_logged_in(page):
                print("✅ ログイン成功！")
                print()

                # Cookieを保存
                print("=" * 70)
                print("Cookieを保存中...")
                print("=" * 70)
                login_manager.save_cookies_from_context(browser)
                print()

                print("セッション情報が保存されました:")
                print(f"  📁 セッションディレクトリ: {login_manager.session_dir}")
                if login_manager.cookie_manager:
                    print(f"  🔐 暗号化Cookie: {login_manager.cookie_manager.storage_path}")
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
