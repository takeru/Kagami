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

### 遅延ツール登録（Lazy Tool Registration）

MCPサーバーは**起動時のタイムアウトを回避**するため、遅延ツール登録方式を採用しています：

**初回起動時の動作：**
1. MCPサーバーとして即座に応答（タイムアウト回避）
2. バックグラウンドでセットアップを実行：
   - certutil のインストール
   - @playwright/mcp のインストール
   - proxy.py のインストール（uv pip install proxy.py）
   - Firefox (build v1496) のインストール
   - Firefoxプロファイルの作成
   - CA証明書のインポート
3. セットアップ中は「セットアップ中」というステータスツールを返す
4. セットアップ完了後、playwright-mcpプロセスを起動
5. 以降のリクエストをplaywright-mcpにプロキシ

**注意:**
- 初回起動時はセットアップに数分かかります
- セットアップ中は`mcp_setup_status`ツールのみが利用可能です
- セットアップ完了後、Playwright MCPの全ツールが利用可能になります
- `HTTPS_PROXY` 環境変数の設定が必須です

### 依存関係

`mcp.py` は Python 標準ライブラリのみを使用します（外部パッケージ不要）。

実行環境には以下のコンポーネントが必要ですが、**初回起動時に自動的にインストールされます**：
- `proxy.py` - JWTプロキシへの接続に使用（`uv pip install proxy.py` で自動インストール）
- `@playwright/mcp` - Playwright MCPサーバー（`npm install -g` で自動インストール）
- `node` - Node.jsランタイム（Claude Code Web環境に標準装備）

### MCP Playwright ツールの利用

Claude Code Web 環境では、`mcp__playwright` がインストールされているはずです。

**利用可能なツール:**
- `mcp__playwright__browser_navigate` - ブラウザでURLに移動
- その他のPlaywright MCPツール

**注意:**
- 初回起動時はセットアップに時間がかかるため、すぐには使えないかもしれません
- セットアップが完了するまで待つ必要があります（30秒以上）
