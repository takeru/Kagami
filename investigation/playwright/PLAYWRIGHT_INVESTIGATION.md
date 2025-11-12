# Playwright 調査レポート

**調査日時**: 2025-11-12
**調査者**: Claude Code
**環境**: Linux 4.4.0, Python 3.11.14, Node.js v22.21.1

## 📋 調査概要

この環境でPlaywrightまたは類似のブラウザ操作ライブラリをインストールして動作させることができるか調査しました。

## ✅ 結論: **動作可能**

Playwrightはこの環境で動作します。ただし、**サンドボックスを無効化する必要があります**。

## 🔍 調査結果の詳細

### 1. インストール状況

✅ **Playwright for Python**: バージョン 1.56.0
✅ **Chromiumブラウザ**: インストール済み
✅ **システム依存関係**: すべてインストール済み

```bash
pip install playwright
playwright install chromium
playwright install-deps chromium
```

### 2. 動作条件

#### ❌ デフォルト設定では動作しない

- ブラウザがクラッシュする (Target crashed)
- 理由: サンドボックスの制約

#### ✅ サンドボックス無効化で動作する

以下のオプションでブラウザを起動する必要があります:

```python
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(
        headless=True,
        args=[
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-dev-shm-usage',
            '--disable-accelerated-2d-canvas',
            '--disable-gpu'
        ]
    )
    page = browser.new_page()
    # ... 操作 ...
    browser.close()
```

### 3. 動作確認できた機能

| 機能 | 状態 | 備考 |
|------|------|------|
| ブラウザ起動 | ✅ | headlessモードで動作 |
| ページ作成 | ✅ | - |
| HTMLコンテンツ設定 | ✅ | `page.set_content()` |
| 空白ページへのナビゲーション | ✅ | `page.goto("about:blank")` |
| JavaScript実行 | ✅ | `page.evaluate()` |
| スクリーンショット | ✅ | `page.screenshot()` |
| 外部サイトへのアクセス | ❌ | ネットワーク制限あり |

### 4. 制約事項

#### 🚫 外部ネットワークアクセスの制限

この環境では外部サイトへのアクセスができません:

```
Error: Page.goto: net::ERR_TUNNEL_CONNECTION_FAILED at https://example.com/
```

**影響**:
- インターネット上のWebサイトにアクセスできない
- APIエンドポイントへのリクエストができない

**対処法**:
- ローカルHTMLファイルを使用
- ローカルサーバーを立てる
- `page.set_content()`でHTMLを直接設定

#### ⚠️ 複雑なDOM操作のタイムアウト

一部の複雑な要素選択や操作でタイムアウトが発生する場合があります。

## 🆚 代替案との比較

### Claude Codeの組み込みツール

Claude Codeには以下のWeb操作ツールが組み込まれています:

#### 1. **WebFetch** ツール

```python
# Claude Codeの機能として利用可能
# コード例は不要、Claudeがツールとしてアクセスできる
```

**特徴**:
- ✅ URLからコンテンツを取得
- ✅ HTMLをMarkdownに変換
- ✅ AIモデルでコンテンツを解析
- ✅ 外部ネットワークアクセス可能（制限あり）
- ❌ JavaScriptは実行されない
- ❌ インタラクティブな操作は不可

**適している用途**:
- 静的なWebページの情報取得
- ドキュメントの解析
- APIレスポンスの取得

#### 2. **WebSearch** ツール

**特徴**:
- ✅ Web検索が可能
- ✅ 最新情報の取得
- ✅ 複数の検索結果を取得
- ❌ 米国でのみ利用可能

### Playwright vs Claude Code組み込みツール

| 項目 | Playwright | WebFetch | WebSearch |
|------|-----------|----------|-----------|
| 外部サイトアクセス | ❌ (この環境) | ✅ | ✅ |
| JavaScript実行 | ✅ | ❌ | ❌ |
| DOM操作 | ✅ | ❌ | ❌ |
| スクリーンショット | ✅ | ❌ | ❌ |
| フォーム入力 | ✅ | ❌ | ❌ |
| クリック操作 | ✅ | ❌ | ❌ |
| セットアップ | 必要 | 不要 | 不要 |
| ローカルHTML操作 | ✅ | ❌ | ❌ |

## 💡 推奨される使い分け

### Playwrightを使うべき場合

1. **JavaScriptで動的に生成されるコンテンツの取得**
   - Single Page Applications (SPA)
   - クライアントサイドレンダリングされるページ

2. **ユーザー操作のシミュレーション**
   - フォームの入力と送信
   - ボタンクリック
   - スクロール操作

3. **スクリーンショットの取得**
   - ページの視覚的な確認
   - テストの証跡

4. **ローカルHTMLファイルの操作**
   - 生成したHTMLの動作確認
   - ローカルでのテスト

### WebFetch/WebSearchを使うべき場合

1. **外部Webサイトからの情報取得**
   - ドキュメントの参照
   - APIレスポンスの取得
   - ニュースや最新情報の収集

2. **静的コンテンツの解析**
   - HTMLの構造解析
   - メタ情報の取得

3. **簡単なWeb操作**
   - セットアップ不要で即座に使える
   - メンテナンスの手間がない

## 📝 実装例

### Playwrightを使ったGitHub Issue監視の例

```python
from playwright.sync_api import sync_playwright

def monitor_local_issue_page(html_file_path):
    """ローカルに保存したIssueページを解析"""
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=['--no-sandbox', '--disable-setuid-sandbox']
        )
        page = browser.new_page()

        # ローカルHTMLファイルを読み込み
        with open(html_file_path, 'r') as f:
            html_content = f.read()

        page.set_content(html_content)

        # Issue情報を抽出
        title = page.locator('h1.issue-title').text_content()
        status = page.locator('.issue-status').text_content()
        comments = page.locator('.comment').count()

        browser.close()

        return {
            'title': title,
            'status': status,
            'comments': comments
        }
```

## 🎯 結論と提案

### この環境での最適な戦略

1. **外部Webサイトの情報取得**: WebFetch/WebSearchツールを使用
2. **ローカルHTMLの操作**: Playwrightを使用
3. **動的コンテンツの処理**:
   - 可能であれば外部でHTMLを取得してローカル保存
   - Playwrightで処理

### プロジェクトへの組み込み

requirements.txtに追加:
```
playwright>=1.56.0
```

初回セットアップスクリプト:
```bash
#!/bin/bash
pip install playwright
playwright install chromium
playwright install-deps chromium
```

### セキュリティ上の注意

⚠️ **サンドボックス無効化のリスク**

`--no-sandbox`オプションはセキュリティリスクを伴います:
- 信頼できるコンテンツのみを処理してください
- 本番環境では使用を避けてください
- 可能であれば適切にサンドボックスが動作する環境を用意してください

## 📂 テストファイル

調査中に作成したテストファイル:

- `test_playwright_nosandbox.py` - 動作確認済みの基本テスト ✅
- `playwright_example.py` - 実用例（一部制限あり）
- `test_playwright.py` - 外部アクセステスト（失敗）
- `test_page.html` - テスト用HTMLファイル

## ✨ まとめ

**Playwrightはこの環境で動作します**が、以下の点に注意が必要です:

1. ✅ ブラウザ操作、JavaScript実行、スクリーンショットが可能
2. ⚠️ サンドボックスを無効化する必要がある
3. ❌ 外部ネットワークアクセスは制限されている
4. 💡 ローカルコンテンツの処理に最適
5. 🔄 外部コンテンツにはWebFetch/WebSearchツールを併用

**推奨**:
- GitHubのIssue監視など、外部APIから取得したHTMLをローカルで処理する用途に適しています
- WebFetchで取得 → Playwrightで処理、というハイブリッドアプローチが効果的です
