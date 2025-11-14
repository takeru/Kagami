# Claude.ai ログイン機能

このドキュメントでは、Claude.aiへのログインとClaude Codeへのアクセス方法を説明します。

## 概要

Claude.aiのログインには**認証コード（ワンタイムパスワード）**が必要なため、完全自動化は難しいです。そのため、以下の2段階アプローチを採用しています：

1. **初回ログイン（手動）**: ユーザーが手動でログインし、セッション情報を保存
2. **セッション再利用（自動）**: 保存したセッションを使って、自動的にログイン状態でアクセス

## 前提条件

- `HTTPS_PROXY` 環境変数が設定されていること
- Playwrightがセットアップ済みであること

## ファイル構成

```
src/
  ├── claude_login.py          # ログイン管理クラス
  └── claude_cookie_manager.py # Cookie永続化管理クラス

scripts/
  ├── login_claude.py          # 手動ログインスクリプト
  └── access_claude_code.py    # Claude Codeアクセススクリプト
```

## Cookie永続化

**重要**: Claude Code Web環境では、セッション終了時にストレージがクリアされます。そのため、Cookieを暗号化して外部ストレージに保存する機能を実装しています。

### セキュリティ

- Cookieは**Fernet（対称暗号化）**で暗号化されて保存されます
- 暗号化キーは環境変数 `CLAUDE_COOKIE_KEY` から取得します
- キーが設定されていない場合は自動生成されますが、**セッション間で保持するには環境変数に設定する必要があります**

### 暗号化キーの設定

```bash
# 新しいキーを生成（初回のみ）
export CLAUDE_COOKIE_KEY="$(uv run python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())')"

# .envファイルに保存（推奨）
echo "CLAUDE_COOKIE_KEY=$CLAUDE_COOKIE_KEY" >> ~/.env
```

## 使い方

### 1. 初回ログイン（手動）

最初に、ブラウザを開いて手動でログインします：

```bash
uv run python scripts/login_claude.py
```

**手順:**

1. スクリプトを実行すると、ブラウザウィンドウが開きます
2. ログインページが表示されるので、以下の手順でログインします：
   - "Continue with email" ボタンをクリック
   - メールアドレスを入力
   - メールで受け取った認証コードを入力
3. ログインが完了したら、ターミナルに戻って **Enterキー** を押します
4. セッション情報が `~/.kagami/claude_session` に保存されます

### 2. Claude Codeへのアクセス（自動）

初回ログイン後は、保存したセッションを使って自動的にアクセスできます：

```bash
# 基本的な使い方（ヘッドレスモード）
uv run python scripts/access_claude_code.py

# ブラウザを表示して確認
uv run python scripts/access_claude_code.py --show-browser

# ページ情報を表示
uv run python scripts/access_claude_code.py --action info

# インタラクティブモード
uv run python scripts/access_claude_code.py --action interactive

# スクリーンショットを保存
uv run python scripts/access_claude_code.py --screenshot claude_code.png

# Cookie情報を表示
uv run python scripts/access_claude_code.py --show-cookie-info

# アクセス後にCookieを保存（更新）
uv run python scripts/access_claude_code.py --save-cookies
```

### 3. インタラクティブモード

インタラクティブモードでは、以下のコマンドが使えます：

```bash
uv run python scripts/access_claude_code.py --action interactive
```

**利用可能なコマンド:**

- `info` - ページ情報を表示
- `list` - プロジェクト一覧を表示（デモ）
- `url` - 現在のURLを表示
- `title` - ページタイトルを表示
- `screenshot <path>` - スクリーンショットを保存
- `quit` - 終了

## プログラムからの使用

Pythonプログラムから直接使用する場合：

```python
from src.claude_login import ClaudeLoginManager

# ログインマネージャーを作成
with ClaudeLoginManager() as login_manager:
    # プロキシは自動的に起動・停止されます

    # Claude Codeにアクセス
    browser, page = login_manager.access_claude_code()

    # ログイン状態を確認
    if login_manager.is_logged_in(page):
        print("✅ Logged in!")

        # ページ操作
        print(f"Title: {page.title()}")
        print(f"URL: {page.url}")

        # スクリーンショット
        page.screenshot(path="claude_code.png")

    browser.close()
```

## セッション管理

### セッションの保存場所

セッション情報は以下のディレクトリとファイルに保存されます：

- セッションデータ: `~/.kagami/claude_session` (ブラウザプロファイル)
- キャッシュデータ: `~/.kagami/claude_cache`
- **暗号化Cookie**: `~/.kagami/claude_cookies.enc` (永続化用)

### Cookie永続化の仕組み

Claude Code Web環境では、セッション終了時に一時ストレージがクリアされます。そのため：

1. **ログイン時**: Cookieを暗号化して `~/.kagami/claude_cookies.enc` に保存
2. **アクセス時**: 暗号化されたCookieを復号化してブラウザにロード
3. **更新時**: `--save-cookies` オプションで最新のCookieを保存

この仕組みにより、セッション間でログイン状態を維持できます。

### セッションのクリア

セッションをクリアする場合は、以下のファイルとディレクトリを削除してください：

```bash
rm -rf ~/.kagami/claude_session
rm -rf ~/.kagami/claude_cache
rm -f ~/.kagami/claude_cookies.enc
```

その後、再度 `scripts/login_claude.py` を実行してログインしてください。

## トラブルシューティング

### ログインできない

1. **HTTPS_PROXY が設定されているか確認**:
   ```bash
   echo $HTTPS_PROXY
   ```

2. **セッションをクリアして再ログイン**:
   ```bash
   rm -rf ~/.kagami/claude_session
   uv run python scripts/login_claude.py
   ```

### Cloudflareチャレンジで止まる

- スクリプトは自動的にCloudflareチャレンジの完了を待機します
- 最大40秒待機しても完了しない場合は、タイムアウトします
- 手動ログインスクリプト（`--show-browser`）を使って、ブラウザで確認してください

### "Not logged in" と表示される

初回ログインが完了していない可能性があります：

```bash
uv run python scripts/login_claude.py
```

### Cookie復号化エラー

Cookieの復号化に失敗する場合は、暗号化キーが間違っている可能性があります：

```bash
# 暗号化キーを確認
echo $CLAUDE_COOKIE_KEY

# Cookieを削除して再ログイン
rm -f ~/.kagami/claude_cookies.enc
uv run python scripts/login_claude.py
```

### セッション間でログイン状態が維持されない

1. **暗号化キーが設定されているか確認**:
   ```bash
   echo $CLAUDE_COOKIE_KEY
   ```

2. **Cookieファイルが存在するか確認**:
   ```bash
   ls -la ~/.kagami/claude_cookies.enc
   ```

3. **Cookie情報を表示**:
   ```bash
   uv run python scripts/access_claude_code.py --show-cookie-info
   ```

## 技術的な詳細

### セッション永続化

Playwrightの `launch_persistent_context` を使用して、ブラウザのセッション情報を永続化しています。これにより、ログイン状態（Cookie、LocalStorageなど）が保持されます。

### プロキシ設定

外部サイトへのアクセスには、`HTTPS_PROXY` 環境変数で指定されたプロキシ経由でアクセスします。プロキシは自動的に起動・停止されます。

### Cookie永続化の技術的実装

セッション終了時にストレージがクリアされる環境でも、ログイン状態を維持するために以下の仕組みを実装しています：

1. **暗号化**: Fernet（対称暗号化）を使用してCookieを暗号化
2. **保存**: 暗号化されたCookieをファイルシステムに保存
3. **復元**: ブラウザ起動時に暗号化されたCookieを復号化してロード
4. **更新**: 必要に応じて最新のCookieを保存

暗号化には以下のライブラリを使用：
- `cryptography`: Fernet暗号化
- `PBKDF2HMAC`: パスワードベースのキー導出関数

### Bot検出回避

以下の対策を実施しています：

- `--disable-blink-features=AutomationControlled` フラグ
- `navigator.webdriver` プロパティの書き換え
- User-Agent の設定
- その他の検出回避スクリプトの注入

## 注意事項

1. **認証コードの自動入力はできません**: Claude.aiのログインには、メールで送信される認証コードが必要です。これは自動化できないため、初回ログイン時は手動で入力してください。

2. **セッションの有効期限**: Claude.aiのセッションには有効期限があります。期限が切れた場合は、再度ログインしてください。

3. **複数アカウント**: 複数のアカウントを使い分ける場合は、`session_dir` パラメータで異なるディレクトリを指定してください：
   ```python
   login_manager = ClaudeLoginManager(session_dir="/tmp/claude_account1")
   ```

## サンプルコード

### 基本的な使用例

```python
#!/usr/bin/env python3
from src.claude_login import ClaudeLoginManager

with ClaudeLoginManager() as manager:
    browser, page = manager.access_claude_code()

    if manager.is_logged_in(page):
        print(f"✅ Logged in as: {page.url}")

        # ページの情報を取得
        title = page.title()
        print(f"Title: {title}")

        # スクリーンショットを保存
        page.screenshot(path="claude_code.png")
    else:
        print("❌ Not logged in")

    browser.close()
```

### カスタムアクション

```python
#!/usr/bin/env python3
from src.claude_login import ClaudeLoginManager

def get_project_list(page):
    """プロジェクト一覧を取得"""
    # TODO: 実際のプロジェクト取得ロジックを実装
    headings = page.locator("h1, h2").all()
    for heading in headings:
        print(heading.text_content())

with ClaudeLoginManager(headless=False) as manager:
    browser, page = manager.access_claude_code()

    if manager.is_logged_in(page):
        get_project_list(page)

    input("Press Enter to close...")
    browser.close()
```

## まとめ

- 初回は手動ログインが必要ですが、セッションを保存することで、次回以降は自動的にログイン状態でアクセスできます
- `scripts/login_claude.py` で初回ログイン
- `scripts/access_claude_code.py` でClaude Codeにアクセス
- Pythonプログラムから `ClaudeLoginManager` クラスを使用することもできます
