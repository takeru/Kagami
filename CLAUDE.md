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

## Playwright MCP サーバーについて

**このプロジェクトは Claude Code Web 専用です。**

このリポジトリには Claude Code Web 用の Playwright MCP サーバー (`playwright_mcp_claude_code_web/mcp.py`) が含まれています。Claude Code Web 環境でのみ動作するように設計されています。

### 自動セットアップ

MCPサーバーは初回起動時に以下を自動的にセットアップします：

1. certutil のインストール
2. @playwright/mcp のインストール
3. Firefox (build v1496) のインストール
4. Firefoxプロファイルの作成
5. CA証明書のインポート
6. proxy.py の起動

**注意:**
- 初回起動時は30秒以上かかる場合があります
- `HTTPS_PROXY` 環境変数の設定が必須です
- セットアップは自動的に実行されるため、手動での操作は不要です

### 依存関係

`mcp.py` は Python 標準ライブラリのみを使用します（外部パッケージ不要）。

ただし、実行環境には以下がインストールされている必要があります：
- `proxy.py` コマンド（別プロセスとして起動される）
- `node` および `@playwright/mcp` （Firefox 自動化のため）

### MCP Playwright ツールの利用

Claude Code Web 環境では、`mcp__playwright` がインストールされているはずです。

**利用可能なツール:**
- `mcp__playwright__browser_navigate` - ブラウザでURLに移動
- その他のPlaywright MCPツール

**注意:**
- 初回起動時はセットアップに時間がかかるため、すぐには使えないかもしれません
- セットアップが完了するまで待つ必要があります（30秒以上）
