# Playwright Chromium 共有メモリ問題の解決方法

## 問題

Chromiumが `/tmp` や `/dev/shm` に共有メモリを作れない環境（特にコンテナ環境）で、Playwrightが正常に動作しない問題があります。

## 解決策

以下の5つの対策を組み合わせることで、共有メモリ問題を完全に回避できます：

### 1. `--disable-dev-shm-usage` （最重要）

Chromiumが `/dev/shm` の代わりに `/tmp` を使用するようにします。

```python
args=['--disable-dev-shm-usage']
```

### 2. `--single-process`

単一プロセスモードで実行し、プロセス間通信の問題を回避します。

```python
args=['--single-process']
```

### 3. サンドボックス無効化

コンテナ環境での権限問題を回避します。

```python
args=[
    '--no-sandbox',
    '--disable-setuid-sandbox',
]
```

### 4. キャッシュディレクトリの明示的指定

キャッシュディレクトリを `/tmp` 配下に指定します。

```python
import tempfile

cache_dir = tempfile.mkdtemp(prefix="playwright_cache_", dir="/tmp")
args=[f'--disk-cache-dir={cache_dir}']
```

### 5. ユーザーデータディレクトリを `/tmp` に配置

セッション永続化が必要な場合、ユーザーデータディレクトリを `/tmp` 配下に作成します。

```python
import tempfile

user_data_dir = tempfile.mkdtemp(prefix="playwright_session_", dir="/tmp")
browser = p.chromium.launch_persistent_context(
    user_data_dir=user_data_dir,
    ...
)
```

## 完全な実装例

### 通常のlaunch()を使う場合

```python
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(
        headless=True,
        args=[
            '--disable-dev-shm-usage',      # 最重要
            '--no-sandbox',                 # コンテナ環境用
            '--disable-setuid-sandbox',     # コンテナ環境用
            '--single-process',             # プロセス管理
            '--disable-gpu',                # GPU無効化
            '--disable-accelerated-2d-canvas',
        ]
    )

    page = browser.new_page()
    # ... 処理 ...
    browser.close()
```

### セッション永続化（launch_persistent_context）を使う場合

```python
import tempfile
from playwright.sync_api import sync_playwright

# ユーザーデータディレクトリを/tmpに作成
user_data_dir = tempfile.mkdtemp(prefix="chrome_", dir="/tmp")
cache_dir = tempfile.mkdtemp(prefix="cache_", dir="/tmp")

with sync_playwright() as p:
    browser = p.chromium.launch_persistent_context(
        user_data_dir=user_data_dir,
        headless=True,
        args=[
            '--disable-dev-shm-usage',      # 最重要
            '--no-sandbox',                 # コンテナ環境用
            '--disable-setuid-sandbox',     # コンテナ環境用
            '--single-process',             # プロセス管理
            '--disable-gpu',                # GPU無効化
            '--disable-accelerated-2d-canvas',
            f'--disk-cache-dir={cache_dir}',
        ]
    )

    page = browser.pages[0]
    # ... 処理 ...
    browser.close()

# 不要になったら一時ディレクトリを削除
import shutil
shutil.rmtree(user_data_dir, ignore_errors=True)
shutil.rmtree(cache_dir, ignore_errors=True)
```

## テストコード

動作確認済みのテストコードは以下にあります：

- `session_persistence_working.py` - セッション永続化の完全な実装例
- `test_playwright_nosandbox.py` - 基本的な動作確認

## まとめ

Chromiumが `/tmp` に共有メモリを作れない問題は、主に以下の2つのフラグで解決できます：

1. **`--disable-dev-shm-usage`** - `/dev/shm` の代わりに `/tmp` を使用
2. **`--single-process`** - 単一プロセスモードで実行

その他のフラグは、コンテナ環境での安定動作やメモリ使用量の削減に役立ちます。

## 参考資料

- [Chromium Issue #736452](https://bugs.chromium.org/p/chromium/issues/detail?id=736452)
- [Playwright CI Documentation](https://playwright.bootcss.com/python/docs/ci)
- [Stack Overflow - Headless Chromium on Docker](https://stackoverflow.com/questions/56218242/headless-chromium-on-docker-fails)
