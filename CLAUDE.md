**重要**: ユーザーとの対話は必ず日本語で行うこと

## Gitコミットに関する注意事項

**以下のファイルはコミットしないでください：**

- スクリーンショット（*.png, *.jpg, *.jpeg, *.gif など）
- ブラウザから取得したHTML（*.html など）
- テストの一時成果物

これらのファイルはテストやデバッグの際に生成されますが、リポジトリには不要です。
.gitignoreに適切なパターンを設定してください。

**コミットすべきファイル：**
- ソースコード（*.py, *.js, *.ts など）
- ドキュメント（*.md）
- 設定ファイル（*.json, *.yaml など）
- テストスクリプト

## Claude Code Webかどうかの判断
```
if [ -n "$CLAUDE_CODE_REMOTE" ]; then echo "Claude Code Webです"; else echo "Claude Code Webではありません"; fi
```

Claude Code Webの環境では @CLAUDE_CODE_WEB.md を参照してください。

## Playwrightのセットアップと動作確認（最短ルート）

### 1. セットアップ（1分）
```bash
uv run python playwright_setup/setup_playwright.py
```

### 2. 動作確認（1分）

**Chromium - プロキシ経由の基本アクセス:**
```bash
uv run python playwright_setup/samples/02_with_proxy.py
```

**Chromium - 全機能統合版（推奨）:**
```bash
uv run python playwright_setup/samples/05_full_example.py https://example.com
```

**Firefox - プロキシ経由のアクセス:**
```bash
# Firefoxのインストール（初回のみ）
uv run playwright install firefox

# Firefoxでのアクセス
uv run python playwright_setup/samples/08_firefox_with_proxy.py
```

**注意:** 外部サイトへのアクセスには `HTTPS_PROXY` 環境変数が必須です。プロキシなしでは接続エラーになります。
