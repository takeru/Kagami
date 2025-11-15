# playwright MCPサーバー ブラウザパス問題の解決方法

**作成日**: 2025-11-15
**問題**: npx @playwright/mcpがuv環境でインストールしたPlaywright/ブラウザを見つけられない

## 🔍 調査結果

### 環境情報

| 項目 | 値 |
|------|-----|
| **uv環境のPlaywright** | Version 1.56.0 |
| **playwright MCP** | Version 0.0.47 |
| **Firefoxパス** | `/root/.cache/ms-playwright/firefox-1495/firefox/firefox` |
| **Chromiumパス** | `/root/.cache/ms-playwright/chromium-1194/chrome-linux/chrome` |

### 問題の原因

1. **playwright MCPサーバー（npx）は独自のPlaywrightインスタンスを使用**
   - npxで実行されるMCPサーバーは、uv環境とは別のNode.js環境で動作
   - デフォルトでは、uv環境でインストールしたブラウザを見つけられない

2. **ブラウザの検索パスが異なる**
   - uv環境: `/root/.cache/ms-playwright/` にブラウザをインストール
   - npx環境: 独自のキャッシュディレクトリを検索

3. **バージョンの違い**
   - uv Playwright: 1.56.0
   - playwright MCP: 0.0.47（内部で使用するPlaywrightバージョンは不明）

## ✅ 解決方法

playwright MCPサーバーは `--executable-path` オプションをサポートしており、
これを使ってuv環境のブラウザを直接指定できます。

### 方法1: --executable-path オプションを使用（推奨）⭐

最もシンプルで確実な方法です。

#### Firefox の場合

`.mcp.json`:
```json
{
  "mcpServers": {
    "playwright": {
      "command": "npx",
      "args": [
        "@playwright/mcp@latest",
        "--browser", "firefox",
        "--executable-path", "/root/.cache/ms-playwright/firefox-1495/firefox/firefox"
      ]
    }
  }
}
```

#### Chromium の場合

`.mcp.json`:
```json
{
  "mcpServers": {
    "playwright": {
      "command": "npx",
      "args": [
        "@playwright/mcp@latest",
        "--browser", "chromium",
        "--executable-path", "/root/.cache/ms-playwright/chromium-1194/chrome-linux/chrome",
        "--no-sandbox"
      ]
    }
  }
}
```

**利点**:
- ✅ シンプルで設定が簡単
- ✅ uv環境のブラウザを直接使用
- ✅ 追加の設定ファイル不要

**欠点**:
- ❌ ブラウザバージョンが変わるとパスを更新する必要がある
- ❌ firefoxUserPrefsなどの詳細設定ができない

---

### 方法2: 設定ファイルを使用（詳細設定が必要な場合）

Firefoxの詳細設定（firefoxUserPrefsなど）が必要な場合に使用。

#### 1. 設定ファイルを作成

`.mcp/firefox_browser_config.json`:
```json
{
  "browser": {
    "executablePath": "/root/.cache/ms-playwright/firefox-1495/firefox/firefox"
  },
  "launchOptions": {
    "headless": true,
    "firefoxUserPrefs": {
      "privacy.trackingprotection.enabled": false,
      "network.proxy.allow_hijacking_localhost": true,
      "network.stricttransportsecurity.preloadlist": false,
      "security.cert_pinning.enforcement_level": 0,
      "security.enterprise_roots.enabled": true,
      "security.ssl.errorReporting.enabled": false,
      "browser.xul.error_pages.expert_bad_cert": true,
      "media.navigator.streams.fake": true
    }
  },
  "contextOptions": {
    "ignoreHTTPSErrors": true
  }
}
```

#### 2. .mcp.json で設定ファイルを参照

`.mcp.json`:
```json
{
  "mcpServers": {
    "playwright": {
      "command": "npx",
      "args": [
        "@playwright/mcp@latest",
        "--config", ".mcp/firefox_browser_config.json",
        "--browser", "firefox"
      ]
    }
  }
}
```

**利点**:
- ✅ firefoxUserPrefsなどの詳細設定が可能
- ✅ 設定の再利用が簡単
- ✅ バージョン管理しやすい

**欠点**:
- ❌ 設定ファイルの管理が必要

---

### 方法3: proxy.pyと組み合わせる場合⭐⭐

現在の要件（JWT認証プロキシ経由でのアクセス）に最適な方法。

`.mcp.json`:
```json
{
  "mcpServers": {
    "playwright": {
      "command": "bash",
      "args": [
        "-c",
        "uv run proxy --hostname 127.0.0.1 --port 18911 --plugins proxy.plugin.proxy_pool.ProxyPoolPlugin --proxy-pool \"$HTTPS_PROXY\" >/dev/null 2>&1 & PROXY_PID=$!; trap \"kill $PROXY_PID 2>/dev/null\" EXIT; sleep 2; npx @playwright/mcp@latest --browser firefox --executable-path /root/.cache/ms-playwright/firefox-1495/firefox/firefox --proxy-server http://127.0.0.1:18911"
      ],
      "env": {
        "HOME": "/home/user/Kagami/.mcp/firefox_home"
      }
    }
  }
}
```

**利点**:
- ✅ JWT認証プロキシ経由でアクセス可能
- ✅ uv環境のブラウザを使用
- ✅ proxy.pyを自動起動・停止

**欠点**:
- ❌ 設定が複雑
- ❌ ブラウザパスの手動更新が必要

---

## 🔧 バージョン互換性について

### 現在の状況

- **uv環境のPlaywright**: 1.56.0
- **playwright MCP**: 0.0.47

### 重要な点

1. **playwright MCPは内部的に独自のPlaywrightを使用**
   - MCPサーバー自体が特定バージョンのPlaywrightに依存
   - `--executable-path`を指定することで、uv環境のブラウザを使える

2. **ブラウザバイナリの互換性**
   - Playwright 1.56.0でインストールしたブラウザは、
   - playwright MCP 0.0.47でも使用可能（ブラウザバイナリは基本的に互換性あり）

3. **推奨される運用**
   - uv環境でブラウザをインストール: `uv run playwright install firefox`
   - MCPサーバーで `--executable-path` を指定して使用
   - ブラウザのアップデートはuv環境で実施

### バージョン更新時の注意

Firefoxのバージョンが変わると、パスも変わります：

```
firefox-1495 → firefox-1500 （例）
```

この場合、`.mcp.json` のパスを更新する必要があります。

**自動化スクリプトの例**:
```bash
# 最新のFirefoxパスを取得
FIREFOX_PATH=$(uv run python -c "from playwright.sync_api import sync_playwright; p = sync_playwright().start(); print(p.firefox.executable_path)")

# .mcp.jsonを更新（sedなどで置換）
```

---

## 📝 テスト手順

### 1. 設定を適用

上記の方法1、2、3のいずれかを選択して `.mcp.json` を更新。

### 2. Claude Code Web を再起動

設定を反映させるため、セッションを再起動。

### 3. MCPツールが利用可能か確認

Claude Codeで以下のようなリクエストを送信：
```
playwright MCPツールを使ってexample.comにアクセスしてください
```

### 4. 動作確認

成功すれば、以下のような応答が返ってくるはず：
```
✅ example.comにアクセスしました
✅ タイトル: Example Domain
```

---

## 🚨 トラブルシューティング

### 問題1: ブラウザが見つからないエラー

```
Error: Browser specified in your config is not installed.
```

**解決策**:
1. ブラウザが本当にインストールされているか確認
   ```bash
   uv run playwright install firefox
   ```

2. パスが正しいか確認
   ```bash
   uv run python -c "from playwright.sync_api import sync_playwright; p = sync_playwright().start(); print(p.firefox.executable_path)"
   ```

3. `.mcp.json` のパスを更新

### 問題2: HOME環境変数の問題

一部の環境で `HOME` が空になる場合があります。

**解決策**:
`.mcp.json` で明示的に `HOME` を設定：
```json
{
  "mcpServers": {
    "playwright": {
      "command": "npx",
      "args": [...],
      "env": {
        "HOME": "/home/user/Kagami/.mcp/firefox_home"
      }
    }
  }
}
```

### 問題3: バージョン不一致

MCPサーバーとブラウザのバージョンが合わない場合。

**解決策**:
通常は問題ありませんが、エラーが出る場合は：
1. uv環境のPlaywrightを更新
   ```bash
   uv pip install -U playwright
   uv run playwright install firefox
   ```

2. 新しいパスを `.mcp.json` に反映

---

## 📊 推奨される設定

### 開発環境（Claude Code Web）

**方法3（proxy.py + executable-path）を推奨**

理由：
- JWT認証プロキシが必要
- Firefoxの詳細設定が不要
- シンプルで確実

### ローカル環境

**方法1（executable-pathのみ）を推奨**

理由：
- proxy.pyが不要な場合が多い
- 設定がシンプル
- トラブルシューティングが簡単

---

## 🎯 まとめ

### 解決策

✅ **`--executable-path` オプションを使用することで解決**

- npx @playwright/mcpがuv環境のブラウザを見つけられない問題を解決
- uv環境でインストールしたブラウザを直接指定できる
- バージョン互換性の問題もクリア

### 次のステップ

1. ✅ 調査完了
2. ⏳ `.mcp.json` を更新
3. ⏳ 実際の動作確認
4. ⏳ proxy.pyとの組み合わせテスト
5. ⏳ ドキュメント更新

### 生成された設定ファイル

以下のファイルが自動生成されています：

- `investigation/playwright/mcp_config_firefox_executable_path.json`
- `investigation/playwright/mcp_config_firefox_config_file.json`
- `investigation/playwright/mcp_config_chromium_executable_path.json`

これらを参考に `.mcp.json` を更新してください。
