# Playwright ネットワークアクセス調査

**調査期間**: 2025-11-12
**環境**: Claude Code Web (Linux 4.4.0, Python 3.11.14)
**ステータス**: ✅ **調査完了** - Playwright経由のHTTPSアクセスは不可能と確定

---

## 🎯 調査目的

Claude Code Web環境でPlaywrightを使ってclaude.ai/codeにアクセスし、セッション永続化を実現する方法を調査。

## 📊 最終結論

**Playwright経由でのHTTPSサイトアクセスは完全に不可能**

### 理由

1. **JWT認証プロキシの非互換性**
   - 環境のプロキシはJWT（JSON Web Token）認証を使用
   - Chromiumは Basic/Digest/NTLM/Negotiate のみサポート
   - JWT認証は未対応

2. **Chromiumのセキュリティ制限**
   - `Proxy-Authorization`ヘッダーは「Unsafe header」として分類
   - DevTools Protocolレベルで上書きを明示的に禁止
   - Route APIを使った回避策も無効

3. **他のブラウザも利用不可**
   - Firefox: root実行の制限で起動不可
   - WebKit: システムライブラリ不足で起動不可

### 検証した方法（すべて失敗）

| # | 方法 | 結果 |
|---|------|------|
| 1 | Proxy パラメータ | ❌ ERR_TUNNEL_CONNECTION_FAILED |
| 2 | Chromium起動引数 | ❌ ERR_NO_SUPPORTED_PROXIES |
| 3 | 認証情報を明示的に設定 | ❌ ERR_TUNNEL_CONNECTION_FAILED |
| 4 | Firefox/WebKit | ❌ 起動不可 |
| 5 | Route API (fetch) | ❌ DNS解決失敗 |
| 6 | Route API (continue) | ❌ Unsafe header エラー |

---

## 💡 推奨される解決策

**ハイブリッドアプローチ（Python urllib + Playwright）**

### 実装フロー

```
1. ローカル環境
   └─ Playwrightでclaude.aiにログイン
   └─ Cookieをエクスポート

2. Claude Code Web環境
   └─ Python urllibでCookieを使ってHTTPSアクセス ✅
   └─ HTMLコンテンツを取得
   └─ Playwrightでローカル処理（JavaScript実行、DOM操作）
```

### メリット・デメリット

✅ **できること**:
- HTTPSサイトへのアクセス
- JavaScript実行（ローカルHTML内）
- DOM操作とスクリーンショット

⚠️ **制限事項**:
- 外部APIへの動的リクエストは不可
- SPAの完全な再現は困難

---

## 📁 ディレクトリ構成

### 📋 主要ドキュメント

| ファイル | 説明 | ステータス |
|---------|------|-----------|
| **[NETWORK_ACCESS_INVESTIGATION.md](./NETWORK_ACCESS_INVESTIGATION.md)** | **メイン調査レポート**（560行以上）<br>ネットワークアクセスの完全な調査結果 | ✅ 完了 |
| **[PLAYWRIGHT_INVESTIGATION.md](./PLAYWRIGHT_INVESTIGATION.md)** | 初期調査レポート<br>Playwrightの基本動作確認 | ✅ 完了 |
| **[README.md](./README.md)** | このファイル（索引とサマリ） | ✅ 完了 |

### 🧪 テストスクリプト

#### ネットワークアクセステスト

| ファイル | テスト内容 | 結果 |
|---------|----------|------|
| `test_network_access.py` | 複数サイトへのPlaywrightアクセステスト | ❌ HTTPS失敗 |
| `test_python_https.py` | Python urllib/socketでのHTTPSテスト | ✅ urllib成功 |
| `test_claude_access.py` | claude.ai特化アクセステスト | ❌ 失敗 |

#### プロキシ設定テスト

| ファイル | テスト内容 | 結果 |
|---------|----------|------|
| `test_playwright_with_proxy.py` | 4種類のプロキシ設定方法を検証 | ❌ 全失敗 |
| `test_playwright_proxy_args.py` | Chromium起動引数でプロキシ指定 | ❌ 失敗 |
| `test_playwright_proxy_auth.py` | 認証情報を明示的に設定 | ❌ 失敗 |
| `test_playwright_simple_proxy.py` | シンプルなプロキシアドレステスト | ❌ 失敗 |
| **`test_route_api_proxy.py`** | **Route API回避策テスト** | ❌ Unsafe header |

#### ブラウザエンジンテスト

| ファイル | テスト内容 | 結果 |
|---------|----------|------|
| `test_playwright_firefox.py` | Firefox/WebKitマルチブラウザテスト | ❌ 起動不可 |
| `test_firefox_webkit_simple.py` | Firefox/WebKitシンプルテスト | ❌ 起動不可 |

#### 基本動作確認テスト

| ファイル | テスト内容 | 結果 |
|---------|----------|------|
| `test_playwright_nosandbox.py` | --no-sandboxオプション動作確認 | ✅ 成功 |
| `test_playwright_simple.py` | 基本的なPlaywright動作テスト | ✅ 成功 |
| `test_playwright_local.py` | ローカルHTML処理テスト | ✅ 成功 |
| `test_playwright_wait.py` | 待機処理とタイムアウトテスト | ✅ 成功 |
| `test_playwright.py` | 外部サイトアクセステスト（初期） | ❌ 失敗 |

### 📦 サポートファイル

| ファイル | 説明 |
|---------|------|
| `playwright_example.py` | Playwright実装例 |
| `test_page.html` | テスト用HTMLファイル |
| `playwright_nosandbox.png` | スクリーンショット（動作確認用） |

---

## 🔬 調査の経緯

### Phase 1: 基本動作確認
- Playwrightのインストールと動作確認 ✅
- `--no-sandbox`オプションでの起動成功 ✅
- ローカルHTMLの処理成功 ✅

### Phase 2: 外部アクセステスト
- HTTPSサイトへのアクセス試行 ❌
- エラー: `ERR_TUNNEL_CONNECTION_FAILED`
- 原因: プロキシ認証の問題と判明

### Phase 3: プロキシ設定の調査
- 環境変数からJWT認証プロキシを発見
- 複数のプロキシ設定方法をテスト
- すべて失敗（JWT認証非対応）

### Phase 4: 代替手段の検証
- Python urllib: ✅ HTTPS成功（4/6サイト）
- curl/wget: ✅ HTTPS成功
- Playwright: ❌ HTTPS失敗（HTTPのみ成功）

### Phase 5: ブラウザエンジンの検証
- Chromium: 起動可能だがHTTPS不可
- Firefox: 起動不可（root制限）
- WebKit: 起動不可（ライブラリ不足）

### Phase 6: Route API回避策
- GitHub Issue #11967/#443の方法を検証
- `context.request.fetch()`: ❌ DNS解決失敗
- `route.continue_()`: ❌ **「Unsafe header」エラー**
- **決定的な証拠**: Chromiumが意図的にブロック

---

## 📈 統計

- **作成したテストスクリプト**: 21個
- **実行したテスト**: 6種類の方法
- **検証したブラウザ**: 3種類（Chromium, Firefox, WebKit）
- **ドキュメント行数**: 800行以上
- **調査時間**: 約3時間

---

## 🎓 学んだこと

### 技術的な発見

1. **Chromiumのセキュリティ設計**
   - `Proxy-Authorization`は「Unsafe header」として保護
   - DevTools Protocolレベルでの制限
   - 回避不可能なセキュリティ機能

2. **プロキシ認証の種類**
   - Basic/Digest: 標準的な認証方式
   - JWT/Bearer Token: 未対応（Chromium）
   - 環境依存の認証方式の難しさ

3. **Claude Code Web環境の特性**
   - JWT認証プロキシを使用
   - DNS解決が制限されている
   - Python urllib/curl/wgetは動作する

### 実装上の教訓

- ブラウザ自動化の限界を理解する
- プロキシ認証の互換性を事前確認する
- ハイブリッドアプローチの有効性
- セキュリティ制限は回避できない場合がある

---

## 🔗 参考リソース

### 公式ドキュメント
- [Playwright Documentation](https://playwright.dev/python/)
- [Chromium HTTP Authentication Design](https://www.chromium.org/developers/design-documents/http-authentication/)
- [Python urllib.request](https://docs.python.org/3/library/urllib.request.html)

### GitHub Issues
- [microsoft/playwright#11967 - Proxy-Authorization](https://github.com/microsoft/playwright/issues/11967)
- [microsoft/playwright-python#443 - Proxy-Authorization in Chromium](https://github.com/microsoft/playwright-python/issues/443)

### 関連調査
- [Playwright Proxy Settings](https://playwright.dev/python/docs/network#http-proxy)
- [HTTP Cookie Management](https://docs.python.org/3/library/http.cookiejar.html)

---

## 📝 次のステップ

調査は完了しました。実装フェーズに進むための選択肢：

1. **ハイブリッドアプローチの実装** ⭐ 推奨
   - Cookie変換ユーティリティの作成
   - Python urllibベースのHTTPクライアント
   - Playwrightでのローカル処理統合

2. **Python urllibのみで実装**
   - シンプルな実装
   - JavaScript実行は不可
   - 静的コンテンツの処理のみ

3. **別のアプローチを検討**
   - Claude APIを使用
   - 別の環境での実行

---

## 📞 お問い合わせ

このディレクトリの調査結果についての質問や追加調査が必要な場合は、`NETWORK_ACCESS_INVESTIGATION.md`の詳細レポートを参照してください。

---

**Last Updated**: 2025-11-12
**Status**: ✅ Investigation Complete
