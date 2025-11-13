# Playwright + Local Proxy (JavaScript/Node.js版)

このディレクトリには、Python版の調査をJavaScriptで再実装したものが含まれています。

## 🎯 目的

Claude Code Web環境でPlaywright（JavaScript）を使用してHTTPSサイトにアクセスするため、ローカルプロキシサーバーを経由してJWT認証プロキシに接続します。

## 📁 ファイル構成

```
investigation/playwright-js/
├── package.json              # Node.jsプロジェクト設定
├── README.md                 # このファイル
├── src/
│   └── local-proxy.js       # ローカルプロキシサーバー実装
└── tests/
    └── test-playwright-proxy.js  # Playwright統合テスト
```

## 🚀 セットアップ

### 1. 依存関係のインストール

```bash
cd investigation/playwright-js
npm install
```

### 2. Playwrightブラウザのインストール

```bash
npx playwright install chromium
```

## 🧪 使用方法

### オプション1: 統合テスト（推奨）

テストスクリプトが自動的にプロキシサーバーを起動してテストを実行します。

```bash
npm test
```

### オプション2: 手動でプロキシを起動

**ターミナル1: プロキシサーバーを起動**

```bash
npm run proxy
```

**ターミナル2: Playwrightテストを実行**

```bash
node tests/test-playwright-proxy.js
```

## 📊 テスト内容

以下のURLに対してアクセステストを実行します：

1. **HTTPBin HTTPS** - `https://httpbin.org/html`
2. **Google** - `https://www.google.com`
3. **Example.com** - `https://example.com`
4. **Claude.ai Login** - `https://claude.ai/login`

各テストで以下を確認：
- ページへのアクセス成功/失敗
- HTTPレスポンスステータス
- ページタイトル
- スクリーンショット保存

## 🔍 技術的な詳細

### ローカルプロキシサーバー (src/local-proxy.js)

**機能:**
- HTTPリクエストの転送
- HTTPSトンネル（CONNECTメソード）対応
- JWT認証情報の透過的な処理
- 詳細なロギング

**動作フロー:**

```
Playwright/Chromium
    ↓
localhost:8888 (ローカルプロキシ)
    ↓
JWT認証プロキシ (HTTPS_PROXY環境変数)
    ↓
インターネット
```

### Playwrightテスト (tests/test-playwright-proxy.js)

**設定:**
- プロキシサーバー: `http://127.0.0.1:8888`
- ブラウザ: Chromium (headless)
- タイムアウト: 30秒
- 証明書エラー: 無視 (`ignoreHTTPSErrors: true`)

**Chromiumフラグ:**
- `--no-sandbox`: サンドボックス無効化（Claude Code Web環境では必須）
- `--disable-setuid-sandbox`: setuidサンドボックス無効化
- `--disable-dev-shm-usage`: 共有メモリの使用を無効化

## 🔧 トラブルシューティング

### プロキシサーバーが起動しない

**原因:** `HTTPS_PROXY`または`HTTP_PROXY`環境変数が設定されていない

**解決策:**
```bash
echo $HTTPS_PROXY
# 何も表示されない場合は設定されていない
```

### Playwrightがブラウザを起動できない

**原因:** Chromiumがインストールされていない

**解決策:**
```bash
npx playwright install chromium
```

### 接続がタイムアウトする

**原因:**
1. 上流プロキシのJWT認証が失敗している
2. ネットワーク接続の問題
3. Chromiumのプロキシ設定の問題

**デバッグ方法:**
1. プロキシサーバーのログを確認
2. curlで直接テスト:
   ```bash
   curl -x http://127.0.0.1:8888 https://httpbin.org/get -v
   ```

### Cloudflare Bot Managementでブロックされる

**原因:** claude.aiはCloudflareで保護されており、自動化が検出される可能性がある

**対策:**
- User-Agentを設定
- リクエスト間隔を空ける
- 手動でログインしてCookieを取得するハイブリッドアプローチ

## 📝 Python版との違い

| 項目 | Python版 | JavaScript版 |
|------|----------|--------------|
| 言語 | Python 3.11+ | Node.js 18+ |
| プロキシライブラリ | proxy.py または標準ライブラリ | 標準ライブラリ (http, net) |
| Playwright | playwright-python | @playwright/test |
| 非同期処理 | asyncio | Promises/async-await |
| 型チェック | なし（オプションでmypy） | なし（オプションでTypeScript） |

## 🎯 次のステップ

1. **成功率の測定**
   - 各URLのアクセス成功率を記録
   - 失敗パターンの分析

2. **Cloudflare回避**
   - User-Agent偽装
   - Cookie管理
   - 手動ログインフロー

3. **パフォーマンス最適化**
   - 接続プーリング
   - Keep-Alive設定
   - タイムアウト調整

4. **エラーハンドリング**
   - リトライロジック
   - Fallback機能
   - より詳細なエラーログ

## 📚 参考資料

- [Playwright Documentation](https://playwright.dev/)
- [Node.js HTTP Module](https://nodejs.org/api/http.html)
- [Node.js Net Module](https://nodejs.org/api/net.html)
- [HTTP CONNECT Method (RFC 7231)](https://tools.ietf.org/html/rfc7231#section-4.3.6)

## 📞 関連ファイル

- Python版の調査結果: `../playwright/NETWORK_ACCESS_INVESTIGATION.md`
- Python版のプロキシ実装: `../../src/local_proxy.py`
- Playwright問題の調査: `../playwright/FINDINGS_PLAYWRIGHT_ISSUES.md`

---

**Last Updated**: 2025-11-13
**Status**: 🔄 Implementation Complete, Testing in Progress
