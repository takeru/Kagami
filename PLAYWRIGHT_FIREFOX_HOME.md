# Playwright Firefox HOME環境変数の設定

## 問題

Playwright で Firefox を使用する際、HOME環境変数が適切に設定されていないと以下のエラーが発生します：

```
╔══════════════════════════════════════════════════════════════════════════════════╗
║ Firefox is unable to launch if the $HOME folder isn't owned by the current user. ║
║ Workaround: Set the HOME=/root environment variable when running Playwright.     ║
╚══════════════════════════════════════════════════════════════════════════════════╝

Running Nightly as root in a regular user's session is not supported.
($HOME is /root which is owned by claude.)
```

この問題は、HOMEディレクトリの所有者と実行ユーザーが異なる場合に発生します。

## 解決策

### 1. MCP経由でPlaywrightを使用する場合

`.mcp.json` に既に設定済みです：

```json
{
  "mcpServers": {
    "playwright": {
      "env": {
        "HOME": "/home/user/Kagami/.mcp/firefox_home"
      }
    }
  }
}
```

MCPサーバー経由で使用する場合は追加設定は不要です。

### 2. Pythonスクリプトから直接Playwrightを実行する場合

環境変数を設定してから実行する必要があります：

```bash
export HOME="/home/user/Kagami/.mcp/firefox_home"
export PLAYWRIGHT_BROWSERS_PATH="/root/.cache/ms-playwright"
uv run python your_script.py
```

または、`.envrc` を作成してsourceしてから実行：

**`.envrc` の作成（1回のみ）：**
```bash
cat > .envrc << 'EOF'
# Playwright Firefox requires HOME environment variable
# to be set to a directory owned by the current user
export HOME="/home/user/Kagami/.mcp/firefox_home"
mkdir -p "$HOME"

# Use existing Playwright browser installation
export PLAYWRIGHT_BROWSERS_PATH="/root/.cache/ms-playwright"
EOF
```

**実行時：**
```bash
source .envrc
uv run python your_script.py
```

**注意**: `.envrc` は `.gitignore` に含まれているため、各環境で作成する必要があります。

### 3. セットアップスクリプト

`.claude/claude_code_web_setup.sh` にも設定を追加済みです。
SessionStartフックで自動的に実行されます。

## 環境変数の説明

- **HOME**: Firefox がユーザー設定やキャッシュを保存するディレクトリ
  - `/home/user/Kagami/.mcp/firefox_home` を使用

- **PLAYWRIGHT_BROWSERS_PATH**: Playwright がインストールしたブラウザバイナリの場所
  - `/root/.cache/ms-playwright` を使用（既存のインストールを再利用）

## インストール方法

### MCP経由のインストール

MCPサーバーは `.mcp.json` の設定に従って自動的にセットアップされます。
追加のインストール作業は不要です。

### 手動インストール

1. セットアップスクリプトを実行：
```bash
./.claude/claude_code_web_setup.sh
```

2. または、環境変数を設定してPlaywrightをインストール：
```bash
export HOME="/home/user/Kagami/.mcp/firefox_home"
uv run playwright install firefox
```

## 動作確認

環境変数が正しく設定されているか確認：

```bash
echo "HOME=$HOME"
echo "PLAYWRIGHT_BROWSERS_PATH=$PLAYWRIGHT_BROWSERS_PATH"
```

Firefoxの起動テスト：

```python
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.firefox.launch(headless=True)
    page = browser.new_page()
    page.goto("https://example.com")
    print(f"✅ Title: {page.title()}")
    browser.close()
```

## 関連ファイル

- `.mcp.json`: MCPサーバーの設定
- `.envrc`: シェル環境変数の設定
- `.claude/claude_code_web_setup.sh`: セットアップスクリプト
- `.mcp/firefox_home/`: Firefox用のHOMEディレクトリ
