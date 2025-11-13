# Playwright調査結果 - 重大な問題発見

## 🔴 重大な問題: Playwright DOM操作のハング

### 発見された問題

1. **`page.set_content()`**: 呼び出しは成功するが、その後の操作でハング
2. **`page.title()`**: 無限にハングする
3. **`page.goto()` + プロキシ**: EPIPEエラー（Chromiumのプロキシ認証バグ）

### テスト結果

#### テスト1: ハイブリッドアプローチ (`test_hybrid_approach.py`)
```python
# httpxでHTML取得 → Playwrightでset_content()
page.set_content(html, wait_until="domcontentloaded")  # ❌ ハング
```
**結果**: "Loading HTML content..." から進まず、無限にハング

#### テスト2: 最小限のset_content() (`test_set_content_minimal.py`)
```python
html = "<!DOCTYPE html><html><head><title>Test</title></head>...</html>"
page.set_content(html)  # ✅ 成功
title = page.title()     # ❌ ハング
```
**結果**:
- `set_content()` は成功（パラメータなし）
- しかし `page.title()` で無限にハング

### 原因の仮説

1. **Chromium通信の問題**: PlaywrightとChromiumプロセス間の通信が不安定
2. **環境固有の制約**: Claude Code Web環境特有の制約
3. **Playwrightバージョン/インストールの問題**: 何らかの不完全なインストール

## 🚫 Cloudflare Bot Management

### httpxでのclaude.ai/codeアクセス結果

```
Status: 403 Forbidden
Title: "Just a moment..."
Content: Cloudflare Challenge Page
```

**発見事項:**
- httpxだけではCloudflareのJavaScriptチャレンジをクリアできない
- ブラウザ（JavaScript実行環境）が必須
- **→ Playwrightが必要な理由が判明**

## 📊 状況まとめ

| アプローチ | ネットワーク | DOM操作 | 結果 |
|-----------|------------|---------|------|
| httpx単独 | ✅ 動作 | N/A | ❌ Cloudflare 403 |
| Playwright goto() | ❌ EPIPE | - | ❌ Chromiumバグ |
| Playwright set_content() | ✅ (httpx使用) | ❌ ハング | ❌ 使用不可 |

## 🎯 次の戦略オプション

### オプション1: Playwright goto() を再検証
- 最新のChromiumフラグを試す
- プロキシ設定を変更
- Chromiumのバージョンダウングレード

### オプション2: 別のブラウザ自動化ツール
- **Selenium + ChromeDriver**: より成熟した実装
- **Puppeteer**: Node.js製（Python binding: pyppeteer）
- **undetected-chromedriver**: Cloudflare回避特化

### オプション3: 手動セッション取得 + httpx
1. ローカルでclaude.ai/codeにログイン
2. セッションCookieを手動で抽出
3. httpxに注入して使用
- **制約**: セッションの有効期限、環境依存

### オプション4: プロキシ設定の根本的見直し
- Chromiumのプロキシ認証バグを回避する別の方法を探す
- 認証済みプロキシを別プロセスで立てる（すでに試行済み - proxy.py）

## 🔍 詳細調査が必要な項目

1. **Playwright sync API の制約**
   - asyncio版（`async_playwright`）で動作が異なるか？
   - Playwrightのログレベルを上げて詳細を確認

2. **Chromiumプロセスの状態**
   - strace/lsofで通信を解析
   - Chromium側のログを取得

3. **環境固有の問題**
   - 同じコードがローカル環境では動作するか？
   - Claude Code Web環境の制約ドキュメント確認

## 📝 実装済みファイル

### 成功したテスト
- `test_proxypy_correct.sh`: curlでHTTPS通信成功（proxy.py経由）
- `test_httpx_claude_login.py`: httpxで403取得（Cloudflare判定）

### 失敗したテスト
- `test_hybrid_approach.py`: set_content()後にハング
- `test_set_content_minimal.py`: page.title()でハング
- `test_proxypy_playwright.py`: EPIPEエラー（goto + プロキシ）

### ドキュメント
- `PROXYPY_SUCCESS.md`: proxy.pyの成功記録
- `FINDINGS_PLAYWRIGHT_ISSUES.md`: 本ドキュメント

## 🎬 次のアクション

**推奨**: オプション2（別のツール）またはオプション1（goto再検証）を試す

1. Seleniumの調査・テスト
2. Playwright async API の試行
3. Chromiumデバッグログの取得と分析
