# Playwright MCP for Claude Code Web

Claude Code Web環境でPlaywright MCPを使用して、証明書エラーなしでHTTPSサイトにアクセスするための完全なセットアップ。

## 🎯 概要

このディレクトリには、以下が含まれています：

- **mcp.py**: MCPサーバー起動スクリプト（**自動セットアップ機能付き**）
- **setup.sh**: 手動セットアップスクリプト（オプション）
- **example.py**: Yahoo! JAPANトピック取得のサンプルコード
- **test_mcp_setup.py**: セットアップ確認スクリプト
- **playwright-firefox-config.json**: Firefox設定ファイル（自動生成）

## 📋 通信フロー

```
Python MCP Client
  ↓
playwright-mcp (Firefox + CA証明書)
  ↓
proxy.py (localhost:18915) ← JWT認証処理
  ↓
JWT認証Proxy ← TLS Inspection
  ↓
Internet ✅
```

## 🚀 クイックスタート

### セットアップ不要！

**mcp.pyは初回起動時に自動的にセットアップを実行します。**

Claude Code WebでPlaywrightツールを使用するだけで、自動的に以下がセットアップされます：
- ✅ certutilのインストール
- ✅ @playwright/mcpのグローバルインストール
- ✅ Firefox build v1496のインストール
- ✅ Firefoxプロファイルの作成
- ✅ JWT認証プロキシCA証明書のインポート（staging/production）
- ✅ MCP設定ファイルの作成

### オプション: 手動セットアップ

事前にセットアップを確認したい場合:

```bash
# セットアップ確認スクリプトを実行
uv run python playwright_mcp_claude_code_web/test_mcp_setup.py

# または、手動セットアップスクリプトを実行
HOME=/home/user bash playwright_mcp_claude_code_web/setup.sh
```

### サンプルコードを実行

```bash
# Yahoo! JAPANのトピックを取得
HOME=/home/user uv run python playwright_mcp_claude_code_web/example.py
```

**期待される出力:**
```
📰 Yahoo! JAPANのトピック
======================================================================
 1. 主なサービス
 2. ビジネスで活用するなら
 3. 高市首相 ハードワークの舞台裏
 4. 政府が検討「おこめ券」いつ届く
 ...
✅ 30 件のトピックを取得しました
```

## 📁 ファイル構成

```
playwright_mcp_claude_code_web/
├── README.md                           # このファイル
├── mcp.py                              # MCPサーバー起動スクリプト（自動セットアップ機能付き）
├── setup.sh                            # 手動セットアップスクリプト（オプション）
├── test_mcp_setup.py                   # セットアップ確認スクリプト
├── example.py                          # サンプルコード
└── playwright-firefox-config.json      # Firefox設定（自動生成）
```

## 🔧 詳細な使い方

### MCPサーバー起動スクリプト (mcp.py)

**特徴:**
- 初回起動時に自動セットアップを実行
- セットアップ済みの場合はスキップ
- proxy.pyを自動起動
- playwright-mcpをstdioモードで起動

**.mcp.json設定:**
```json
{
  "mcpServers": {
    "playwright": {
      "command": "uv",
      "args": ["run", "python", "playwright_mcp_claude_code_web/mcp.py"],
      "env": {"HOME": "/home/user"},
      "timeout": 180000
    }
  }
}
```

**自動セットアップ内容:**
1. certutilのインストール確認
2. @playwright/mcpのグローバルインストール
3. Firefox build v1496のインストール
4. Firefoxプロファイルの作成（`/home/user/firefox-profile`）
5. CA証明書のインポート
6. MCP設定ファイルの作成

### セットアップ確認スクリプト (test_mcp_setup.py)

**実行:**
```bash
uv run python playwright_mcp_claude_code_web/test_mcp_setup.py
```

**機能:**
- セットアップ状態をチェック
- 未セットアップの場合は自動セットアップ
- 各コンポーネントの状態を表示

### 手動セットアップスクリプト (setup.sh)

**実行:**
```bash
HOME=/home/user bash playwright_mcp_claude_code_web/setup.sh
```

**用途:**
- 事前にセットアップを完了させたい場合
- セットアップ内容を詳しく確認したい場合

### サンプルコード (example.py)

**機能:**
- playwright-mcp経由でYahoo! JAPANにアクセス
- トピックを抽出して表示
- デバッグ用の詳細なログ出力

**実行:**
```bash
HOME=/home/user uv run python playwright_mcp_claude_code_web/example.py
```

**コードの流れ:**
1. proxy.pyを起動（JWT認証処理）
2. playwright-mcpサーバーに接続
3. Yahoo! JAPANにナビゲート
4. スナップショットを取得
5. トピックを抽出
6. 結果を表示
7. ブラウザを閉じる
8. proxy.pyを停止

## 🔍 トラブルシューティング

### 証明書エラーが発生する

**症状:**
```
❌ 証明書エラーが発生しました
SEC_ERROR_UNKNOWN_ISSUER
```

**解決策:**
```bash
# セットアップ確認スクリプトを実行
uv run python playwright_mcp_claude_code_web/test_mcp_setup.py

# または、手動セットアップを再実行
HOME=/home/user bash playwright_mcp_claude_code_web/setup.sh

# CA証明書を確認
certutil -L -d sql:/home/user/firefox-profile | grep Anthropic
```

**期待される出力:**
```
Anthropic TLS Inspection CA                                  C,,
Anthropic TLS Inspection CA Production                       C,,
```

### Firefoxが見つからない

**症状:**
```
Browser specified in your config is not installed
```

**解決策:**
```bash
# HOME=/home/userでFirefoxをインストール
HOME=/home/user node /opt/node22/lib/node_modules/@playwright/mcp/node_modules/playwright/cli.js install firefox
```

### proxy.pyが起動しない

**症状:**
```
❌ HTTPS_PROXY環境変数が設定されていません
```

**解決策:**
- Claude Code Web環境であることを確認
- `echo $HTTPS_PROXY` でプロキシ設定を確認

## 💡 重要なポイント

### 1. HOME=/home/user が必須

```bash
# ❌ これは失敗する
bash playwright_mcp_claude_code_web/setup.sh

# ✅ これが正しい
HOME=/home/user bash playwright_mcp_claude_code_web/setup.sh
```

**理由:** Firefoxはプロファイルの所有者とHOMEディレクトリの所有者が一致している必要があります。

### 2. proxy.pyが必須

**なぜ必要？**
- JWT認証を処理するため
- Firefoxは複雑なJWT認証を直接処理できない

**HTTPS_PROXY環境変数の中身:**
```
http://user:jwt_eyJ0eXAi...@host:port
```

### 3. CA証明書のインポートが必須

**なぜ必要？**
- TLS Inspectionで証明書が置き換えられる
- システム証明書ストアではなく、Firefoxプロファイルにインポート

**比較:**
```
curl   → システム証明書ストア → アクセス成功
Firefox → 独自の証明書ストア → インポートしないと失敗
```

## 📚 関連ドキュメント

- [CA証明書インポートガイド](../investigation/playwright/CA_CERTIFICATE_IMPORT_GUIDE.md)
- [HOME=/home/user環境でのFirefoxセットアップ](../investigation/playwright/HOME_USER_FIREFOX_SETUP.md)
- [Playwright調査まとめ](../PLAYWRIGHT_INVESTIGATION.md)

## 🧪 テストコード

検証済みテストコード:
- `test_24_firefox_profile_with_proxy_py.py` - 完全成功版 ✅
- `test_25_verify_system_cert_not_needed.py` - システム証明書ストア不要の検証

## ✅ チェックリスト

セットアップが正しく完了したか確認:

```bash
# セットアップ確認スクリプトを実行
uv run python playwright_mcp_claude_code_web/test_mcp_setup.py
```

以下が✅になっていれば成功:
- [ ] certutilがインストールされている
- [ ] @playwright/mcpがグローバルにインストールされている
- [ ] Firefox build v1496が`/home/user/.cache/ms-playwright/firefox-1496`にある
- [ ] Firefoxプロファイルが`/home/user/firefox-profile`にある
- [ ] MCP設定ファイルが存在する

手動確認:
```bash
# CA証明書の確認
certutil -L -d sql:/home/user/firefox-profile | grep Anthropic
```

期待される出力:
```
Anthropic TLS Inspection CA                                  C,,
Anthropic TLS Inspection CA Production                       C,,
```

すべてチェックできれば、証明書エラーなしでHTTPSサイトにアクセスできます！

## 🎓 学んだこと

このセットアップを通じて学べること:

1. **TLS Inspectionの仕組み**
   - すべてのHTTPS通信が傍受される
   - 証明書が置き換えられる
   - セキュリティチェックのための仕組み

2. **Firefoxの証明書管理**
   - 独自の証明書ストアを使用
   - システム証明書ストアとは別
   - プロファイルに直接インポートが必要

3. **JWT認証の処理**
   - proxy.pyが必須
   - Firefoxは直接処理できない
   - シンプルなHTTPプロキシとして提供

4. **両方が必要**
   - CA証明書のインポート ✅
   - proxy.pyの使用 ✅
   - → 初めて成功！

## 🤝 サポート

問題が発生した場合:

1. `test_mcp_setup.py`でセットアップ状態を確認
2. 必要に応じて`setup.sh`を再実行
3. 詳細なドキュメントを確認
4. テストコードを参照
5. CA証明書のインポート状態を確認

---

**Happy Coding with Playwright MCP! 🎉**
