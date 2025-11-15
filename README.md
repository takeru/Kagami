# Kagami

Claude Code Web 用の Playwright MCP サーバー。JWT 認証プロキシ経由でブラウザ自動化を実現します。

## 概要

このプロジェクトは Claude Code Web 環境で Playwright を使用するための MCP (Model Context Protocol) サーバーを提供します。

**主な特徴:**

- 自動セットアップ機能（初回起動時に必要なコンポーネントを自動インストール）
- JWT 認証プロキシ経由での外部アクセス
- Firefox ブラウザによる自動化
- CA 証明書の自動インポート
- MCP プロトコル対応

## アーキテクチャ

```
Claude Code → mcp.py → playwright-mcp (Firefox) → proxy.py → JWT認証Proxy → Internet
```

1. **mcp.py**: MCP サーバーのエントリーポイント。初回セットアップと proxy.py の起動を担当
2. **@playwright/mcp**: Playwright の MCP サーバー実装（Node.js）
3. **Firefox**: ブラウザエンジン（build v1496）
4. **proxy.py**: ローカルプロキシサーバー
5. **JWT認証Proxy**: 外部アクセス用の認証プロキシ

## セットアップ

### 自動セットアップ（推奨）

初回起動時に自動的に以下がセットアップされます：

1. certutil のインストール
2. @playwright/mcp のインストール
3. Firefox (build v1496) のインストール
4. Firefox プロファイルの作成
5. CA 証明書のインポート
6. 設定ファイルの生成

**注意:**
- 初回起動時は 30 秒以上かかる場合があります
- `HTTPS_PROXY` 環境変数の設定が必須です

### 環境変数

```bash
export HTTPS_PROXY="your_jwt_proxy_url"
export HOME="/home/user"
```

## 使用方法

### MCP サーバーとして起動

`.mcp.json` に設定を記述することで、Claude Code が自動的に起動します：

```json
{
  "mcpServers": {
    "playwright": {
      "command": "uv",
      "args": [
        "run",
        "playwright_mcp_claude_code_web/mcp.py"
      ],
      "env": {
        "HOME": "/home/user"
      }
    }
  }
}
```

### 手動起動（デバッグ用）

```bash
uv run playwright_mcp_claude_code_web/mcp.py
```

**注意:** `uv` が [PEP 723](https://peps.python.org/pep-0723/) のインラインメタデータを読み取り、必要な依存パッケージ（playwright, proxy.py, httpx, mcp）を自動的にインストールします。

## ファイル構成

```
.
├── playwright_mcp_claude_code_web/
│   └── mcp.py                          # MCP サーバー本体（PEP 723インラインメタデータ付き）
├── .mcp.json                           # MCP サーバー設定
└── README.md                           # このファイル
```

**PEP 723 インラインメタデータ**: `mcp.py` の先頭にスクリプトの依存関係が記述されており、`uv` が自動的に読み取って環境を構築します。

## トラブルシューティング

### 接続タイムアウト

初回起動時は Firefox のダウンロードとインストールに時間がかかります（30秒以上）。`.mcp.json` の `timeout` を 180000 (3分) に設定することを推奨します。

### プロキシエラー

`HTTPS_PROXY` 環境変数が設定されていることを確認してください：

```bash
echo $HTTPS_PROXY
```

### CA 証明書エラー

CA 証明書が正しくインポートされているか確認：

```bash
certutil -L -d sql:/home/user/firefox-profile
```

以下の証明書が表示されるはずです：
- Anthropic TLS Inspection CA
- Anthropic TLS Inspection CA Production

## 技術詳細

### 通信フロー

1. Claude Code が MCP プロトコルで `mcp.py` にリクエスト（stdin/stdout）
2. `mcp.py` が `proxy.py` を起動（localhost:18915）
3. `mcp.py` が `@playwright/mcp` を起動
4. Playwright が Firefox を起動（プロキシ設定: localhost:18915）
5. `proxy.py` が JWT 認証プロキシに転送
6. 外部サイトにアクセス

### セキュリティ

- TLS 検査用の CA 証明書を Firefox プロファイルにインポート
- すべての HTTPS 通信は JWT 認証プロキシ経由
- Firefox は専用プロファイルで動作（/home/user/firefox-profile）

## 参考資料

- [Playwright Documentation](https://playwright.dev/)
- [@playwright/mcp GitHub](https://github.com/microsoft/playwright)
- [MCP Protocol](https://modelcontextprotocol.io/)
- [proxy.py Documentation](https://github.com/abhinavsingh/proxy.py)

## ライセンス

MIT
