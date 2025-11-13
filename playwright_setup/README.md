# Playwright セットアップガイド

Claude Code Web環境でPlaywrightをすぐに使えるようにするためのセットアップとサンプル集です。

## 📋 目次

- [クイックスタート](#クイックスタート)
- [環境要件](#環境要件)
- [セットアップ手順](#セットアップ手順)
- [サンプルコード](#サンプルコード)
- [重要な設定](#重要な設定)
- [トラブルシューティング](#トラブルシューティング)

---

## 🚀 クイックスタート

### 1. セットアップスクリプトを実行

```bash
uv run python playwright_setup/setup_playwright.py
```

### 2. サンプルコードを実行

```bash
# 基本的な使い方
uv run python playwright_setup/samples/01_basic_example.py

# プロキシ付き
uv run python playwright_setup/samples/02_with_proxy.py

# Cloudflare回避
uv run python playwright_setup/samples/04_cloudflare_bypass.py
```

---

## 📦 環境要件

### 必須

- Python 3.9以上
- uv (パッケージマネージャー)
- playwright >= 1.56.0
- Chromium（自動インストール可能）

### オプション（プロキシを使う場合）

- proxy.py >= 2.4.0
- 環境変数 `HTTPS_PROXY` の設定

---

## 🔧 セットアップ手順

### Step 1: 依存関係の追加

`pyproject.toml` に以下を追加:

```toml
dependencies = [
    "playwright>=1.56.0",
    "proxy.py>=2.4.0",
]
```

### Step 2: 依存関係のインストール

```bash
uv sync
```

### Step 3: Chromiumのインストール

```bash
uv run playwright install chromium
```

### Step 4: 環境変数の設定（プロキシを使う場合）

```bash
export HTTPS_PROXY="http://username:password@proxy.example.com:8080"
```

---

## 📚 サンプルコード

### サンプル1: 基本的な使い方

**ファイル**: `samples/01_basic_example.py`

最もシンプルな例。プロキシなしでローカルページにアクセスします。

```bash
uv run python playwright_setup/samples/01_basic_example.py
```

**学べる内容**:
- ブラウザの起動と終了
- ページへのアクセス
- 要素の取得
- スクリーンショット

---

### サンプル2: プロキシを使ったアクセス

**ファイル**: `samples/02_with_proxy.py`

proxy.py を使ってJWT認証プロキシ経由でアクセスします。

```bash
uv run python playwright_setup/samples/02_with_proxy.py
```

**学べる内容**:
- proxy.pyの起動と停止
- プロキシ経由のアクセス
- 証明書エラーの回避

**必要な環境変数**:
```bash
export HTTPS_PROXY="http://your-proxy-url"
```

---

### サンプル3: セッション永続化

**ファイル**: `samples/03_session_persistence.py`

ブラウザのデータ（Cookie、localStorage等）を保存して再利用します。

```bash
# 1回目: セッションデータを作成
uv run python playwright_setup/samples/03_session_persistence.py

# 2回目以降: 保存されたセッションを再利用
uv run python playwright_setup/samples/03_session_persistence.py
```

**学べる内容**:
- `launch_persistent_context` の使い方
- localStorage/Cookie の永続化
- セッションデータの管理

---

### サンプル4: Cloudflare回避

**ファイル**: `samples/04_cloudflare_bypass.py`

Cloudflareのbot検出を回避してアクセスします。

```bash
uv run python playwright_setup/samples/04_cloudflare_bypass.py
```

**学べる内容**:
- Anti-detectionフラグの設定
- JavaScriptインジェクション
- navigator.webdriverの隠蔽

---

### サンプル5: 完全版 - 全機能統合

**ファイル**: `samples/05_full_example.py`

すべての機能を統合した実用的な例です。

```bash
# example.com にアクセス
uv run python playwright_setup/samples/05_full_example.py https://example.com

# claude.ai にアクセス
uv run python playwright_setup/samples/05_full_example.py https://claude.ai/login
```

**含まれる機能**:
- ✅ プロキシ経由アクセス
- ✅ セッション永続化
- ✅ Cloudflare回避
- ✅ エラーハンドリング
- ✅ チャレンジ待機

---

### サンプル6: 共有プロキシの使用

**ファイル**: `samples/06_with_shared_proxy.py`

バックグラウンドで起動したプロキシを複数のスクリプトで共有します。

```bash
# 1. プロキシをバックグラウンドで起動（1回だけ）
uv run python playwright_setup/proxy_manager.py start

# 2. このスクリプトを何度でも実行可能
uv run python playwright_setup/samples/06_with_shared_proxy.py

# 3. プロキシを停止
uv run python playwright_setup/proxy_manager.py stop
```

**メリット**:
- 🚀 起動時間の節約（3秒 → 0秒）
- 🔄 複数スクリプトで同じプロキシを共有
- 💾 リソース効率が良い

**プロキシマネージャーのコマンド**:
```bash
# 起動
uv run python playwright_setup/proxy_manager.py start

# 状態確認
uv run python playwright_setup/proxy_manager.py status

# ログ表示
uv run python playwright_setup/proxy_manager.py logs

# 停止
uv run python playwright_setup/proxy_manager.py stop
```

---

## ⚙️ 重要な設定

### Claude Code Web環境で必須のフラグ

```python
args = [
    '--disable-dev-shm-usage',  # 共有メモリ問題の回避
    '--single-process',         # プロセス分離の無効化
    '--no-sandbox',             # サンドボックス無効化
]
```

#### なぜ必要？

Claude Code Web環境では以下の制約があります:

1. **共有メモリ (`/dev/shm`) の容量制限**
   - Chromiumはデフォルトで `/dev/shm` を使用
   - コンテナ環境では容量が小さい
   - `--disable-dev-shm-usage` で `/tmp` を使用

2. **プロセス分離の問題**
   - マルチプロセスモードで不具合が発生
   - `--single-process` でシングルプロセス化

3. **サンドボックスの互換性**
   - コンテナ環境ではサンドボックスが機能しない
   - `--no-sandbox` で無効化

### Cloudflare回避に必須のフラグ

```python
args = [
    # Bot検出回避
    '--disable-blink-features=AutomationControlled',
    '--disable-features=IsolateOrigins,site-per-process',

    # Headless検出回避
    '--window-size=1920,1080',
    '--start-maximized',

    # User agent
    '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
]
```

#### JavaScript インジェクション

```python
page.add_init_script("""
    Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
    Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
    Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});
    window.chrome = { runtime: {} };
""")
```

### プロキシ設定（JWT認証対応）

Claude Code Web環境では、JWT認証プロキシを使用します。

```python
# proxy.py を起動
proxy_process = subprocess.Popen([
    'uv', 'run', 'proxy',
    '--hostname', '127.0.0.1',
    '--port', '8910',
    '--plugins', 'proxy.plugin.proxy_pool.ProxyPoolPlugin',
    '--proxy-pool', os.environ['HTTPS_PROXY'],  # JWT認証プロキシ
])

# Chromiumでプロキシを使用
args = [
    '--proxy-server=http://127.0.0.1:8910',
    '--ignore-certificate-errors',  # 証明書エラーを無視
]
```

#### 仕組み

```
Chromium → proxy.py (127.0.0.1:890x) → HTTPS_PROXY (JWT認証) → インターネット
           ローカルプロキシ             上流プロキシ
```

proxy.py が JWT 認証を透過的に処理します。

---

## 🔍 トラブルシューティング

### 問題1: Chromiumが起動しない

**症状**:
```
Error: Executable doesn't exist
```

**解決方法**:
```bash
uv run playwright install chromium
```

---

### 問題2: DOM操作でクラッシュ

**症状**:
```python
page.title()  # ここでハング/クラッシュ
```

**原因**: 共有メモリ (`/dev/shm`) の容量不足

**解決方法**: 必須フラグを追加
```python
args = [
    '--disable-dev-shm-usage',
    '--single-process',
    '--no-sandbox',
]
```

---

### 問題3: プロキシ接続エラー

**症状**:
```
net::ERR_PROXY_CONNECTION_FAILED
```

**確認事項**:
1. proxy.py が起動しているか
2. 環境変数 `HTTPS_PROXY` が設定されているか
3. ポート番号が正しいか

**解決方法**:
```bash
# 環境変数を確認
echo $HTTPS_PROXY

# proxy.py を手動起動して確認
uv run proxy --hostname 127.0.0.1 --port 8910 \
  --plugins proxy.plugin.proxy_pool.ProxyPoolPlugin \
  --proxy-pool "$HTTPS_PROXY"
```

---

### 問題4: Cloudflareチャレンジを通過できない

**症状**:
- "Just a moment..." のまま進まない
- Status 403 が返される

**解決方法**:

1. **Anti-detectionフラグを確認**
   ```python
   '--disable-blink-features=AutomationControlled'
   ```

2. **JavaScriptインジェクションを追加**
   ```python
   page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined});")
   ```

3. **待機時間を増やす**
   ```python
   for i in range(10):
       time.sleep(3)
       if page.title() != "Just a moment...":
           break
   ```

---

### 問題5: セッションが保存されない

**症状**:
- Cookie やlocalStorageが次回実行時に消える

**原因**: `launch()` を使用している

**解決方法**: `launch_persistent_context()` を使用
```python
# ❌ 間違い
browser = p.chromium.launch(headless=True)

# ✅ 正しい
browser = p.chromium.launch_persistent_context(
    user_data_dir="/tmp/my_session",
    headless=True
)
```

---

## 📖 参考リンク

- [Playwright公式ドキュメント](https://playwright.dev/python/)
- [proxy.py GitHubリポジトリ](https://github.com/abhinavsingh/proxy.py)
- [Chromiumコマンドラインフラグ一覧](https://peter.sh/experiments/chromium-command-line-switches/)

---

## 🤝 サポート

問題が発生した場合は:

1. このREADMEのトラブルシューティングセクションを確認
2. サンプルコードを参考に設定を確認
3. エラーメッセージをコピーして検索

---

## 📝 まとめ

このガイドで以下が学べます:

- ✅ Claude Code Web環境でPlaywrightを動作させる方法
- ✅ プロキシ（JWT認証）の設定方法
- ✅ Cloudflare回避のテクニック
- ✅ セッション永続化の実装方法
- ✅ 実用的なサンプルコード

すべてのサンプルコードはそのまま実行可能です。
ぜひ試してみてください！
