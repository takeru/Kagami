# Playwright + ローカルプロキシ調査結果（JavaScript版）

**調査日**: 2025-11-13
**環境**: Claude Code Web (Linux 4.4.0, Node.js v22.21.1)
**ステータス**: ⚠️ **部分的成功** - HTTPSアクセスは可能だが、DOM操作でハング

---

## 🎯 調査目的

Python版の調査（`claude/playwright-session-persistence-011CV4qqFsKhe8DN7yoLL25A`）をJavaScriptで再実装し、Playwright（Node.js版）でも同じ問題が発生するかを検証。

## 📊 調査結果サマリー

### ✅ 成功した部分

1. **ローカルプロキシサーバーの実装**
   - Node.js標準ライブラリ（`http`, `net`）を使用
   - CONNECTトンネルの確立に成功
   - JWT認証プロキシへの透過的な転送に成功

2. **HTTPSアクセスの成功**
   - `page.goto('https://example.com')` が HTTP 200 を返す
   - プロキシログでトンネル確立を確認
   - ネットワークレベルでの通信は正常

### ❌ 失敗した部分

1. **DOM操作のハング**
   - `page.goto()` の後、`page.title()` を呼ぶと無限にハング
   - Python版と**全く同じ問題**が発生
   - タイムアウトも発生せず、プロセスが応答停止

## 🔍 詳細テスト結果

### テスト実行ログ

```
🎭 Starting simple Playwright test...

📍 Proxy: http://127.0.0.1:8888
🔗 URL: https://example.com

⏳ Launching browser...
✅ Browser launched

⏳ Navigating to page...
✅ Response: 200
```

**この後、`page.title()` 呼び出しでハング（30秒以上待機しても応答なし）**

### プロキシサーバーログ

```
🔵 CONNECT example.com:443
   Client: 127.0.0.1:44768
   ✓ Connected to upstream proxy (2ms)
   → Sending CONNECT to upstream proxy
   ← Response from upstream proxy: HTTP/1.1 200 OK
   ✓ Tunnel established (11ms)

🟢 GET http://privateca-content-693e503d-0000-2af1-b04c-5c337bc7529b.storage.googleapis.com/7daf77a46936d9192651/ca.crt
   Headers: 4
   ← Status: 200 (56ms)
   ⚫ Client connection closed (92ms)
   ⚫ Proxy connection closed (93ms)

🔵 CONNECT example.com:443
   Client: 127.0.0.1:57752
   ✓ Connected to upstream proxy (1ms)
   → Sending CONNECT to upstream proxy
   ← Response from upstream proxy: HTTP/1.1 200 OK
   ✓ Tunnel established (5ms)
   ⚫ Client connection closed (14ms)
   ⚫ Proxy connection closed (14ms)

... (複数のCONNECTリクエストが成功)
```

**観察:**
- プロキシサーバーは正常に動作
- CONNECTトンネルは確立されている
- CA証明書のダウンロードも成功している
- しかし、Playwright側でDOM操作がブロックされている

## 🧐 Python版との比較

| 項目 | Python版 | JavaScript版 |
|------|----------|--------------|
| プロキシ実装 | ✅ 成功 | ✅ 成功 |
| CONNECTトンネル | ✅ 成功 | ✅ 成功 |
| `page.goto()` | ✅ 成功 | ✅ 成功 |
| `page.title()` | ❌ ハング | ❌ ハング |
| 問題の再現性 | 100% | 100% |

**結論**: Python版とJavaScript版で**全く同じ問題**が発生

## 🔬 技術的な考察

### 問題の原因（仮説）

1. **Chromium DevTools Protocolの問題**
   - PlaywrightはChromium DevTools Protocol (CDP)を使用
   - CDPとChromiumプロセス間の通信が不安定
   - 環境固有の制約により、一部のCDPメッセージが応答しない

2. **Claude Code Web環境の制約**
   - サンドボックス環境での特殊な制限
   - プロセス間通信（IPC）の制約
   - リソース制限（CPU、メモリ、プロセス数）

3. **Chromiumプロキシの内部バグ**
   - プロキシ経由でページをロードした後、内部状態が不整合
   - Python版の調査でも指摘されている「EPIPEエラー」に関連する可能性

### なぜ `page.goto()` は成功するのか

- `goto()` は基本的にHTTPリクエスト/レスポンスのみを扱う
- DOMContentLoadedイベントまでは正常に動作
- ネットワーク層（プロキシ）は正常に機能している

### なぜ `page.title()` でハングするのか

- `title()` はJavaScript評価とDOM操作が必要
- CDP経由でChromiumにコマンドを送信
- このコマンドが応答を返さない（タイムアウトも発生しない）
- おそらくChromium側で処理がブロックまたは無限待機

## 📂 実装ファイル

### 1. ローカルプロキシサーバー

**ファイル**: `src/local-proxy.js`

**特徴**:
- Node.js標準ライブラリのみ使用（外部依存なし）
- HTTP/HTTPSリクエストの透過的な転送
- CONNECTメソードのサポート
- JWT認証の透過的な処理
- 詳細なロギング

**主要機能**:
```javascript
// CONNECTトンネル処理
server.on('connect', (req, clientSocket, head) => {
  // 上流プロキシへの接続
  const proxySocket = net.connect({
    host: upstreamProxy.hostname,
    port: parseInt(upstreamProxy.port),
  });

  // CONNECTリクエストを送信（JWT認証付き）
  proxySocket.write(`CONNECT ${host}:${port} HTTP/1.1\r\n...`);

  // 双方向トンネルの確立
  proxySocket.pipe(clientSocket);
  clientSocket.pipe(proxySocket);
});
```

### 2. Playwrightテストスクリプト

**ファイル**: `tests/test-simple.js`

**設定**:
```javascript
const browser = await chromium.launch({
  headless: true,
  proxy: { server: 'http://127.0.0.1:8888' },
  args: [
    '--no-sandbox',
    '--disable-setuid-sandbox',
  ],
});

const context = await browser.newContext({
  ignoreHTTPSErrors: true,
});
```

## 🎯 次のステップと推奨事項

### オプション1: DOM操作を避ける

**アプローチ**:
- `page.goto()` でHTMLコンテンツを取得
- `page.content()` でHTML文字列を取得（ハングしない可能性）
- サーバーサイドでHTMLパース（cheerio等）

**メリット**:
- DOM操作のハング問題を回避
- シンプルな実装

**デメリット**:
- JavaScriptレンダリングが必要なSPAには対応できない

### オプション2: 別のブラウザ自動化ツール

**候補**:
- **Puppeteer**: Playwrightと似た仕組みだが、同じ問題が発生する可能性
- **Selenium**: より成熟しているが、プロキシ設定の問題は同じ
- **CDP直接利用**: より低レベルな制御が可能

### オプション3: ハイブリッドアプローチ

**推奨**: Python版調査と同じ結論

1. **ローカル環境**:
   - Playwrightで`claude.ai/code`にログイン
   - Cookieをエクスポート

2. **Claude Code Web環境**:
   - `fetch`/`axios`でCookieを使ってHTTPSアクセス
   - HTMLコンテンツを取得
   - Playwrightでローカル処理（`setContent()`）

### オプション4: 環境の制約調査

**必要なアクション**:
- Claude Code Webの技術ドキュメントを確認
- プロセス制限、IPC制限の詳細を調査
- サポートに問い合わせ

## 📝 学んだこと

### 技術的な発見

1. **言語非依存の問題**
   - PlaywrightのDOM操作ハング問題は、Python/JavaScript共通
   - 言語バインディングではなく、Chromium/CDP層の問題

2. **プロキシ実装の成功**
   - Node.js標準ライブラリでも十分に機能的なプロキシサーバーが実装可能
   - CONNECTトンネルの実装は言語によらず同じパターン

3. **デバッグの重要性**
   - 詳細なロギングにより、どこで問題が発生しているかを特定できた
   - プロキシ側は正常に動作していることが証明された

### 実装上の教訓

- 環境の制約は、どの言語でも同じように影響する
- ハイブリッドアプローチが最も現実的な解決策
- 完全な自動化が難しい場合は、手動ステップを組み込むことも検討すべき

## 📚 関連ファイル

- **Python版の調査**: `../playwright/FINDINGS_PLAYWRIGHT_ISSUES.md`
- **Python版のプロキシ実装**: `../../src/local_proxy.py`
- **ネットワークアクセス調査**: `../playwright/NETWORK_ACCESS_INVESTIGATION.md`

## 🔗 参考資料

- [Playwright Documentation (Node.js)](https://playwright.dev/)
- [Node.js HTTP Module](https://nodejs.org/api/http.html)
- [Node.js Net Module](https://nodejs.org/api/net.html)
- [Chromium DevTools Protocol](https://chromedevtools.github.io/devtools-protocol/)

---

**Last Updated**: 2025-11-13
**Status**: ⚠️ 調査完了 - Python版と同じ制約を確認
