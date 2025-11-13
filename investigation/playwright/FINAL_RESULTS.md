# Playwright + Chromium + JWT Proxy 調査結果

## 🎉 成功した内容

### 1. Chromium共有メモリ問題の解決

**問題**: `/tmp`へのアクセス権限がなく、Chromiumが共有メモリを作成できない

**解決策**: `--single-process`フラグを使用

```python
args=[
    '--disable-dev-shm-usage',  # /dev/shmの代わりに/tmpを使用
    '--single-process',         # 単一プロセスモード（最重要！）
    '--no-sandbox',
    '--disable-setuid-sandbox',
]
```

**結果**:
- ✅ `page.title()`のハングを解決
- ✅ DOM操作が正常に動作
- ✅ JavaScript実行が可能

### 2. CA証明書の手動処理

**Anthropic CA証明書**:
- ダウンロードURL: `http://privateca-content-693e503d-0000-2af1-b04c-5c337bc7529b.storage.googleapis.com/7daf77a46936d9192651/ca.crt`
- SPKI Hash: `L+/CZomxifpzjiAVG11S0bTbaTopj+c49s0rBjjSC6A=`

**使用方法**:
```python
args=[
    f'--ignore-certificate-errors-spki-list={CA_SPKI_HASH}',
    '--ignore-certificate-errors',
]
```

### 3. ローカルプロキシの必要性

**発見**: Chromiumは直接JWT認証プロキシをサポートしない

- ❌ `--proxy-server=http://user:jwt_xxx@host:port` - ERR_NO_SUPPORTED_PROXIES
- ✅ ローカルプロキシ経由（localhost:8888） - 成功

**アーキテクチャ**:
```
Chromium
    ↓
localhost:8888 (Python local proxy)
    ↓ (JWT authentication)
21.0.0.x:15004 (JWT proxy)
    ↓
Internet
```

### 4. HTTPS通信の成功

**成功したサイト**:
- ✅ **example.com** - 完全成功（タイトル、コンテンツ取得）
- ✅ **claude.ai/** - アクセス成功（Cloudflareチャレンジページ表示）

**失敗したサイト**:
- ❌ example.org - タイムアウト
- ❌ httpbin.org - タイムアウト
- ❌ claude.ai/code - タイムアウト
- ❌ www.anthropic.com - タイムアウト

## 📝 動作確認済みテストコード

### 基本テスト

**test_chromium_fixed.py**:
- Chromium単体の動作確認
- `--single-process`フラグの有効性を確認
- 100% 成功

**test_proxy_https_simple.py**:
- ローカルプロキシ経由でのHTTPSアクセス
- example.comで成功

### Claude AI アクセステスト

**test_claude_debug.py**:
- claude.ai/へのアクセス成功
- Cloudflareチャレンジページを確認
- スクリーンショット保存成功

## 🔍 技術的な発見

### Cloudflareボット保護

claude.aiは **Cloudflare Turnstile** でボット保護されています：

```
Title: "Just a moment..."
Status: 403 Forbidden
Failed: challenges.cloudflare.com
```

**対策の可能性**:
1. セッション永続化（Cookie保存）
2. より人間らしいブラウザ設定
3. `--disable-blink-features=AutomationControlled`
4. カスタムUser-Agent

### プロキシトンネルの問題

一部のサイトで「Tunnel exception detected」が発生：
- claude.ai/code
- example.org
- httpbin.org

**原因**:
- TLS handshake失敗
- プロキシ経由の接続がクローズされる
- サイト側のタイムアウト設定

### 成功の条件

**example.comが成功する理由**:
1. シンプルな静的HTML
2. JavaScriptが少ない
3. サードパーティリソースが少ない
4. ボット保護なし

**claude.aiが部分的に成功**:
1. HTTPSトンネルは確立される
2. HTMLは取得できる
3. ただしCloudflareチャレンジに引っかかる

## 📊 テスト結果まとめ

| テスト項目 | 結果 | 備考 |
|-----------|------|------|
| Chromium起動（プロキシなし） | ✅ | `--single-process`で解決 |
| data: URL navigation | ✅ | 完全成功 |
| page.title() | ✅ | ハング問題を解決 |
| DOM操作 | ✅ | 正常動作 |
| JavaScript実行 | ✅ | 正常動作 |
| example.com (HTTPS) | ✅ | プロキシ経由で成功 |
| claude.ai/ (HTTPS) | ⚠️ | アクセス成功、Cloudflareチャレンジ |
| claude.ai/code | ❌ | タイムアウト |
| 複雑なサイト全般 | ❌ | タイムアウト傾向 |

## 💡 推奨される使用方法

### 最小限の設定で動作するコード

```python
import sys
import os
import threading
import time
from playwright.sync_api import sync_playwright

sys.path.insert(0, '/home/user/Kagami')
from src.local_proxy import run_proxy_server

CA_SPKI_HASH = "L+/CZomxifpzjiAVG11S0bTbaTopj+c49s0rBjjSC6A="

# ローカルプロキシ起動
def start_proxy():
    def run():
        run_proxy_server(port=8888)
    t = threading.Thread(target=run, daemon=True)
    t.start()
    time.sleep(2)

start_proxy()

# Chromium起動
with sync_playwright() as p:
    browser = p.chromium.launch(
        headless=True,
        args=[
            '--disable-dev-shm-usage',
            '--single-process',
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--proxy-server=http://127.0.0.1:8888',
            f'--ignore-certificate-errors-spki-list={CA_SPKI_HASH}',
            '--ignore-certificate-errors',
            '--disable-gpu',
        ]
    )

    context = browser.new_context(ignore_https_errors=True)
    page = context.new_page()

    # HTTPS通信
    page.goto("https://example.com", timeout=15000)
    print(f"Title: {page.title()}")

    browser.close()
```

## 🚫 制約事項

1. **複雑なサイトは不安定**
   - JavaScript多用サイト
   - 多数のサードパーティリソース
   - WebSocket使用サイト

2. **Cloudflareボット保護**
   - Turnstileチャレンジを自動で突破できない
   - 手動でCookie取得が必要な場合がある

3. **タイムアウトが頻発**
   - プロキシ経由の複数接続で不安定
   - `--single-process`の副作用の可能性

## 🎯 次のステップ

### 実用化のために

1. **シンプルなサイトに限定**
   - example.com のような静的サイト
   - APIエンドポイント（JSON返すだけ）

2. **httpx への切り替え**
   - ブラウザ不要なAPIアクセスには httpx が推奨
   - Playwrightはブラウザ操作が必須な場合のみ

3. **手動Cookie取得**
   - ローカル環境でclaude.aiにログイン
   - DevToolsでCookie抽出
   - httpxに注入して使用

### 調査継続の場合

1. **非headlessモード**
   - Cloudflareチャレンジを視覚的に確認
   - 手動で突破してからautomation

2. **別のブラウザ**
   - Firefox/WebKit（Playwrightサポート）
   - Selenium + ChromeDriver

3. **プロキシ実装の改善**
   - より高度なトンネリング
   - エラーハンドリングの強化

## 📁 関連ファイル

### テストスクリプト
- `test_chromium_fixed.py` - Chromium単体テスト（成功）
- `test_proxy_https_simple.py` - シンプルHTTPSテスト（成功）
- `test_ca_spki_hash.py` - CA証明書テスト（部分成功）
- `test_claude_debug.py` - Claude AIデバッグ（Cloudflare検出）
- `test_direct_jwt_proxy.py` - 直接JWT接続（失敗）

### ソースコード
- `src/local_proxy.py` - ローカルプロキシサーバー

### スクリーンショット
- `test_example.png` - example.com成功
- `claude_ai_.png` - claude.ai Cloudflareチャレンジ
- `claude_ai_code_error.png` - claude.ai/codeタイムアウト

### 証明書
- `anthropic_ca.crt` - Anthropic CA証明書

## 結論

**Playwright + Chromium + JWT Proxyの組み合わせは動作します**が、以下の制約があります：

✅ **できること**:
- シンプルなHTTPSサイトへのアクセス（example.com）
- 基本的なブラウザ操作（ナビゲーション、DOM操作）
- スクリーンショット保存

❌ **できないこと**:
- 複雑なサイトへの安定したアクセス
- Cloudflareボット保護の自動突破
- claude.ai/codeのような重いサイト

**実用的な用途**:
- 簡単なウェブサイトのスクレイピング
- APIテスト（ブラウザ必須の場合）
- 学習・実験目的

**推奨しない用途**:
- 本格的なウェブ自動化（別環境を推奨）
- Claude AIの自動操作（API使用を推奨）
