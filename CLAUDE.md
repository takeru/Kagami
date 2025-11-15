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

このリポジトリには Claude Code Web 用の Playwright MCP サーバー (`playwright_mcp_claude_code_web/mcp.py`) が含まれています。

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

### 依存関係の管理

`mcp.py` には [PEP 723](https://peps.python.org/pep-0723/) のインラインメタデータが記述されており、`uv run` で実行すると依存パッケージ（playwright, proxy.py, httpx, mcp）が自動的にインストールされます。
