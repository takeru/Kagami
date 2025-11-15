# Firefox + MCP: proxy.pyなし実装

## 概要

Firefox使用時に**proxy.pyを使わずに**、Playwrightの`extraHTTPHeaders`機能を使ってPreemptive Authenticationを実現する実装です。

## 🎯 主な変更点

### Before（従来の実装）

```json
{
  "mcpServers": {
    "playwright": {
      "command": "bash",
      "args": [
        "-c",
        "uv run proxy --hostname 127.0.0.1 --port 18911 ... & PROXY_PID=$!; trap \"kill $PROXY_PID 2>/dev/null\" EXIT; sleep 2; npx @playwright/mcp@latest ..."
      ]
    }
  }
}
```

- proxy.pyを起動して中間プロキシとして動作
- bashスクリプトで複雑なプロセス管理
- バックグラウンドプロセスのライフサイクル管理が必要

### After（新しい実装）

```json
{
  "mcpServers": {
    "playwright": {
      "command": "uv",
      "args": ["run", "python", ".mcp/start_playwright_mcp_firefox.py"]
    }
  }
}
```

- proxy.py不要
- シンプルなPythonラッパースクリプト
- 環境変数から自動的に認証情報を抽出

## 🔧 実装の仕組み

### 1. ラッパースクリプト (`.mcp/start_playwright_mcp_firefox.py`)

このスクリプトが以下の処理を行います：

1. **環境変数の読み取り**
   ```python
   https_proxy = os.getenv('HTTPS_PROXY')
   # 例: "https://user:pass@proxy.example.com:8080"
   ```

2. **認証情報の抽出**
   ```python
   server, username, password = extract_proxy_credentials(https_proxy)
   # server: "https://proxy.example.com:8080"
   # username: "user"
   # password: "pass"
   ```

3. **Basic認証ヘッダーの生成**
   ```python
   auth_string = f"{username}:{password}"
   auth_b64 = base64.b64encode(auth_string.encode('utf-8')).decode('utf-8')
   # auth_b64: "dXNlcjpwYXNz"
   ```

4. **設定ファイルの動的生成**
   ```python
   config['contextOptions']['extraHTTPHeaders'] = {
       'Proxy-Authorization': f'Basic {auth_b64}'
   }
   ```

5. **playwright-mcpの起動**
   ```python
   subprocess.run([
       'npx', '@playwright/mcp@latest',
       '--config', temp_config,
       '--browser', 'firefox',
       '--proxy-server', server
   ])
   ```

### 2. 設定ファイル構造

**ベース設定** (`.mcp/playwright-firefox-config.json`):
```json
{
  "launchOptions": {
    "headless": true,
    "firefoxUserPrefs": {
      "privacy.trackingprotection.enabled": false,
      "network.proxy.allow_hijacking_localhost": true,
      ...
    }
  },
  "contextOptions": {
    "ignoreHTTPSErrors": true
  }
}
```

**動的に生成される設定** (一時ファイル):
```json
{
  "launchOptions": { ... },
  "contextOptions": {
    "ignoreHTTPSErrors": true,
    "extraHTTPHeaders": {
      "Proxy-Authorization": "Basic dXNlcjpwYXNz"
    }
  }
}
```

## 📊 メリット

### 技術的なメリット

1. **依存関係の削減**
   - proxy.py（Pythonパッケージ）が不要
   - 実行時のプロセスが1つ減る

2. **レイテンシの改善**
   - 中間プロキシを経由しない
   - 直接プロキシサーバーに接続

3. **デバッグの簡易化**
   - プロセス管理がシンプル
   - ログの追跡が容易

4. **メンテナンス性の向上**
   - 設定がわかりやすい
   - bashスクリプトの複雑さがない

### ユーザー体験の向上

- **設定がシンプル**: .mcp.jsonの記述が明確
- **起動が速い**: プロセス数が少ない
- **エラーハンドリング**: より明確なエラーメッセージ

## 🔍 技術的な詳細

### なぜFirefoxのみ対応か？

Chromiumでは`Proxy-Authorization`ヘッダーが「Unsafe header」として扱われ、`extraHTTPHeaders`で設定できません。

**Firefox**:
```python
# ✅ 動作する
context = browser.new_context(
    extra_http_headers={
        "Proxy-Authorization": f"Basic {auth_b64}"
    }
)
```

**Chromium**:
```python
# ❌ 動作しない（ヘッダーが無視される）
context = browser.new_context(
    extra_http_headers={
        "Proxy-Authorization": f"Basic {auth_b64}"  # 無視される
    }
)
```

Chromiumでは引き続きproxy.pyが必要です。

### セキュリティ考慮事項

1. **認証情報の取り扱い**
   - 環境変数から読み取り（平文でファイルに保存しない）
   - 一時設定ファイルは使用後に削除
   - ログに認証情報を出力しない

2. **一時ファイルの管理**
   ```python
   temp_fd, temp_path = tempfile.mkstemp(suffix='.json', prefix='playwright-mcp-config-')
   try:
       # MCPサーバーを起動
       subprocess.run(cmd)
   finally:
       os.unlink(temp_path)  # 必ず削除
   ```

## 🧪 テスト

### テストスクリプト

複数のテストスクリプトで段階的に検証しました：

#### 1. `test_08_firefox_mcp_no_proxy.py` - ラッパースクリプトのユニットテスト

プロキシ認証情報の抽出と設定ファイル生成をテスト：

```bash
uv run python investigation/playwright/test_08_firefox_mcp_no_proxy.py
```

**結果**:
```
✅ 成功: プロキシ認証情報の抽出
✅ 成功: 設定ファイルの生成
✅ 成功: プロキシなしの設定
🎉 すべてのテストが成功しました！
```

#### 2. `test_09_verify_wrapper_with_real_proxy.py` - 実際のプロキシでの検証

実際のHTTPS_PROXY環境変数を使ってテスト：

```bash
uv run python investigation/playwright/test_09_verify_wrapper_with_real_proxy.py
```

**結果**:
```
✅ 成功: 認証情報の抽出
✅ 成功: 設定ファイルの生成
🎉 実際の環境変数でラッパースクリプトが正しく動作しました！
```

#### 3. `test_10_firefox_extra_headers_real_proxy.py` - Firefoxでの実際のアクセステスト

proxy.pyなしで実際に外部サイトにアクセス：

```bash
uv run python investigation/playwright/test_10_firefox_extra_headers_real_proxy.py
```

**結果**:
```
✅ ステータス: 200
✅ URL: https://example.com/
✅ タイトル: Example Domain
🎉 成功: proxy.pyなしでFirefoxから外部サイトにアクセスできました！
```

#### 4. `test_11_mcp_integration_check.py` - MCP統合チェック

MCP設定の最終確認：

```bash
uv run python investigation/playwright/test_11_mcp_integration_check.py
```

**結果**:
```
✅ 成功: 設定ファイルの生成
✅ 成功: 起動コマンドの確認
🎉 MCP統合チェックが成功しました！
```

### 検証済みの動作

- ✅ 実際のHTTPS_PROXY環境変数から認証情報を抽出
- ✅ extraHTTPHeadersでProxy-Authorizationヘッダーを設定
- ✅ proxy.pyなしで外部サイト（example.com）にアクセス成功
- ✅ MCP設定が正しく生成される
- ✅ すべての既存設定が保持される

## 📁 ファイル構成

```
.mcp/
├── start_playwright_mcp_firefox.py  # ラッパースクリプト（環境変数から認証情報抽出）
├── playwright-firefox-config.json   # ベース設定（Firefox用）
└── .mcp.json                        # MCP設定（ラッパースクリプトを起動）

investigation/playwright/
├── test_07_extra_http_headers.py                # Playwrightでの動作確認
├── test_08_firefox_mcp_no_proxy.py              # ラッパースクリプトのユニットテスト
├── test_09_verify_wrapper_with_real_proxy.py    # 実際のプロキシでの検証
├── test_10_firefox_extra_headers_real_proxy.py  # Firefoxでの実際のアクセステスト
├── test_11_mcp_integration_check.py             # MCP統合チェック
└── FIREFOX_MCP_NO_PROXY_IMPLEMENTATION.md       # このドキュメント
```

## 🚀 使い方

### 1. 環境変数の設定

```bash
export HTTPS_PROXY="https://username:password@proxy.example.com:8080"
```

### 2. MCPサーバーの起動

`.mcp.json`の設定により自動的に起動されます：

```bash
# Claude Code Web環境では、MCPサーバーが自動的に起動
# 手動で起動する場合：
uv run python .mcp/start_playwright_mcp_firefox.py
```

### 3. 動作確認

MCPクライアントから接続して、ブラウザ操作を実行します。

## 🔄 既存実装との比較

| 項目 | 従来の実装（proxy.py） | 新しい実装（extraHTTPHeaders） |
|------|----------------------|-------------------------------|
| **プロセス数** | 2つ（proxy.py + playwright-mcp） | 1つ（playwright-mcpのみ） |
| **設定の複雑さ** | 高い（bashスクリプト） | 低い（シンプルなPython） |
| **レイテンシ** | やや高い（中間プロキシ経由） | 低い（直接接続） |
| **ブラウザ対応** | Chromium/Firefox両対応 | Firefoxのみ |
| **依存関係** | proxy.py必要 | proxy.py不要 |
| **デバッグ** | やや難しい | 容易 |

## ⚠️ 制限事項

1. **Firefoxのみ対応**
   - Chromiumでは`Proxy-Authorization`ヘッダーが設定できない
   - Chromium使用時は従来のproxy.py方式が必要

2. **環境変数の必須**
   - `HTTPS_PROXY`環境変数が必須
   - 認証情報を含む必要がある

3. **playwright-mcpのバージョン依存**
   - `contextOptions.extraHTTPHeaders`をサポートするバージョンが必要
   - 古いバージョンでは動作しない可能性

## 📚 参考資料

### Playwright API

- [Browser.new_context()](https://playwright.dev/python/docs/api/class-browser#browser-new-context)
- [extraHTTPHeaders option](https://playwright.dev/python/docs/api/class-browser#browser-new-context-option-extra-http-headers)

### 関連PR

- [#21: Firefoxでproxy.pyなしでのPreemptive Auth実現](https://github.com/takeru/Kagami/pull/21)

### 動作確認済み実装

- `investigation/playwright/test_07_extra_http_headers.py` - Playwrightでの動作例

## 🎉 まとめ

この実装により、Firefox使用時には：

✅ proxy.py不要でシンプルな構成
✅ レイテンシの改善
✅ デバッグが容易
✅ メンテナンスしやすいコード

を実現できました。

ただし、Chromiumとの互換性を維持する必要がある場合は、引き続きproxy.py方式を使用することをお勧めします。
