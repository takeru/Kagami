# Playwright クイックスタートガイド

まっさらな状態から5分でPlaywrightを使えるようにします。

---

## 📦 1分セットアップ

```bash
# セットアップスクリプトを実行
uv run python playwright_setup/setup_playwright.py
```

これで完了です！

---

## 🚀 すぐに試す

### 基本的な使い方（プロキシ付き）

```bash
uv run python playwright_setup/samples/02_with_proxy.py
```

**結果**:
- ✅ example.com にアクセス
- ✅ Status 200
- ✅ スクリーンショット保存

---

## 📖 次のステップ

### ステップ1: 基本を理解する

```bash
# サンプル2: プロキシ付きアクセス
uv run python playwright_setup/samples/02_with_proxy.py
```

### ステップ2: セッション永続化を試す

```bash
# サンプル3: セッション永続化（※要プロキシ対応）
# または完全版を使用
uv run python playwright_setup/samples/05_full_example.py https://example.com
```

### ステップ3: Cloudflare回避を学ぶ

```bash
uv run python playwright_setup/samples/04_cloudflare_bypass.py
```

### ステップ4: 完全版で実践

```bash
# あらゆるサイトにアクセス可能
uv run python playwright_setup/samples/05_full_example.py https://example.com
uv run python playwright_setup/samples/05_full_example.py https://claude.ai/login
```

---

## 💡 よく使うパターン

### パターンA: 1回だけ実行

```bash
# サンプル02, 04, 05 を使用
uv run python playwright_setup/samples/02_with_proxy.py
```

**メリット**:
- 自動でプロキシが起動・停止
- クリーンアップ不要

---

### パターンB: 何度も実行（高速）

```bash
# 1. プロキシをバックグラウンドで起動（1回だけ）
uv run python playwright_setup/proxy_manager.py start

# 2. スクリプトを何度でも実行（プロキシ起動待機なし）
uv run python playwright_setup/samples/06_with_shared_proxy.py
uv run python playwright_setup/samples/06_with_shared_proxy.py
uv run python playwright_setup/samples/06_with_shared_proxy.py

# 3. 終わったらプロキシを停止
uv run python playwright_setup/proxy_manager.py stop
```

**メリット**:
- 起動時間3秒節約
- 複数スクリプトでプロキシ共有

**デメリット**:
- 手動停止が必要
- メモリ約78MB使用

---

## 🎯 自分のコードを書く

### テンプレート: 基本（プロキシ付き）

```python
import subprocess
import time
import os
from playwright.sync_api import sync_playwright

# プロキシを起動
proxy_process = subprocess.Popen([
    'uv', 'run', 'proxy',
    '--hostname', '127.0.0.1',
    '--port', '8910',
    '--plugins', 'proxy.plugin.proxy_pool.ProxyPoolPlugin',
    '--proxy-pool', os.environ['HTTPS_PROXY'],
], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(3)

try:
    with sync_playwright() as p:
        # ブラウザ起動
        browser = p.chromium.launch(
            headless=True,
            args=[
                '--disable-dev-shm-usage',  # 必須
                '--single-process',         # 必須
                '--no-sandbox',
                '--proxy-server=http://127.0.0.1:8910',
                '--ignore-certificate-errors',
            ]
        )

        # ページにアクセス
        page = browser.new_page()
        page.goto("https://example.com")

        # 処理をここに書く
        print(page.title())

        browser.close()
finally:
    # プロキシを停止
    proxy_process.terminate()
    proxy_process.wait(timeout=5)
```

### テンプレート: 完全版（Cloudflare回避 + セッション永続化）

サンプル05 (`samples/05_full_example.py`) をコピーして編集してください。

---

## ❓ 困ったら

### プロキシが起動しない

```bash
# 環境変数を確認
echo $HTTPS_PROXY

# なければ設定（Claude Code Webでは自動設定済み）
```

### Chromiumが見つからない

```bash
uv run playwright install chromium
```

### DOM操作でクラッシュ

必須フラグが設定されているか確認:
- `--disable-dev-shm-usage`
- `--single-process`

### Cloudflareを通過できない

サンプル04または05を参照してください。
Anti-detectionフラグとJavaScriptインジェクションが必要です。

---

## 📚 詳しい情報

- **README.md**: 全機能の詳細説明
- **TROUBLESHOOTING.md**: トラブルシューティング
- **samples/**: 実行可能なサンプルコード5つ

---

## ✅ チェックリスト

セットアップ完了の確認:

- [ ] `uv run python playwright_setup/setup_playwright.py` が成功
- [ ] `uv run python playwright_setup/samples/02_with_proxy.py` が成功
- [ ] スクリーンショット `example_with_proxy.png` が作成された

これで完了です！🎉

---

## 🎓 次に学ぶこと

1. **セッション永続化**: ログイン状態の保持
2. **要素操作**: ボタンクリック、フォーム入力
3. **待機処理**: 動的コンテンツの読み込み待ち
4. **エラーハンドリング**: 安定したスクリプト作成

詳しくは [Playwright公式ドキュメント](https://playwright.dev/python/) を参照してください。
