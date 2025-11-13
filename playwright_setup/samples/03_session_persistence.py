#!/usr/bin/env python3
"""
サンプル3: セッション永続化

ブラウザのデータ（Cookie、localStorage等）を保存して再利用します。
ログイン状態を保持する場合などに有効です。

実行方法:
    # 1回目: セッションデータを作成
    uv run python playwright_setup/samples/03_session_persistence.py

    # 2回目以降: 保存されたセッションを再利用
    uv run python playwright_setup/samples/03_session_persistence.py
"""
import tempfile
from pathlib import Path
from playwright.sync_api import sync_playwright


# セッションデータの保存先
SESSION_DIR = Path("/tmp/playwright_session_example")


def main():
    print("="*60)
    print("Playwright セッション永続化サンプル")
    print("="*60)

    # セッションディレクトリを作成
    SESSION_DIR.mkdir(parents=True, exist_ok=True)

    # セッションが既に存在するかチェック
    is_new_session = not any(SESSION_DIR.iterdir())

    if is_new_session:
        print(f"\n📁 新しいセッションを作成: {SESSION_DIR}")
    else:
        print(f"\n📁 既存のセッションを使用: {SESSION_DIR}")
        file_count = len(list(SESSION_DIR.rglob("*")))
        print(f"   ✅ {file_count} 個のファイルが存在")

    with sync_playwright() as p:
        # launch_persistent_context を使用（セッション永続化）
        print("\n1. ブラウザを起動（セッション永続化モード）...")
        browser = p.chromium.launch_persistent_context(
            user_data_dir=str(SESSION_DIR),  # セッションデータの保存先
            headless=True,
            args=[
                '--disable-dev-shm-usage',
                '--single-process',
                '--no-sandbox',
            ]
        )

        # 最初のページを取得（persistent_contextでは既にページが開いている）
        page = browser.pages[0]

        # Step 1: ページにアクセス
        print("\n2. example.com にアクセス...")
        page.goto("https://example.com")
        print(f"   ✅ タイトル: {page.title()}")

        # Step 2: JavaScriptでlocalStorageにデータを保存
        print("\n3. localStorageにデータを保存...")
        page.evaluate("""
            localStorage.setItem('visit_count',
                parseInt(localStorage.getItem('visit_count') || '0') + 1);
            localStorage.setItem('last_visit', new Date().toISOString());
        """)

        # 保存されたデータを取得
        visit_count = page.evaluate("localStorage.getItem('visit_count')")
        last_visit = page.evaluate("localStorage.getItem('last_visit')")

        print(f"   ✅ 訪問回数: {visit_count}")
        print(f"   ✅ 最終訪問: {last_visit}")

        # Step 3: セッションデータの確認
        print("\n4. セッションデータの確認...")
        file_count_after = len(list(SESSION_DIR.rglob("*")))
        print(f"   ✅ ファイル数: {file_count_after}")

        browser.close()

    print("\n✅ 完了！")
    print(f"\nセッションデータは保持されています: {SESSION_DIR}")
    print("このスクリプトを再度実行すると、訪問回数がカウントアップされます。")


if __name__ == "__main__":
    main()
