# Selenium + undetected-chromedriver 調査結果

**調査日時**: 2025-11-13
**環境**: Claude Code Web (Linux 4.4.0, Python 3.11.14)
**目的**: Selenium + undetected-chromedriverでclaudie.ai/codeへのアクセスを実現する

---

## 📊 調査結果サマリ

### ✅ 成功した部分

1. **Seleniumの基本動作**
   - Chromium 141.0.7390.37 (Playwrightのバイナリ使用)
   - ChromeDriver 141.0.7390.122を自動ダウンロード
   - ローカルHTML (data URI) の読み込み: ✅ 成功
   - タイトルとURL取得: ✅ 成功

2. **proxy.py + curlでのHTTPSアクセス**
   - proxy.py + ProxyPoolPluginの組み合わせ: ✅ 動作
   - curlで`https://example.com`にアクセス: ✅ 成功
   - HTTP/2レスポンス取得: ✅ 成功

### ❌ 失敗した部分

1. **undetected-chromedriverの互換性**
   - バージョン141指定後、起動は成功
   - しかし、`get()`メソッド実行時に**タブクラッシュ**
   - undetected-chromedriverはPlaywrightのChromiumと相性が悪い

2. **Selenium + proxy.pyでのHTTPSアクセス**
   - プロキシ接続: ✅ 確立
   - CONNECTトンネル: ✅ 成功
   - しかし、**90秒タイムアウト**で失敗
   - 原因: CA証明書検証の問題

3. **スクリーンショット機能**
   - Chromiumが起動してページを読み込んだ後
   - `save_screenshot()`実行時に**「tab crashed」**または**「unable to capture screenshot」**
   - この環境固有の問題と推測

---

## 🔬 詳細な調査内容

### 1. Seleniumバージョン互換性の問題

#### 初回テスト結果
```
Error: This version of ChromeDriver only supports Chrome version 142
Current browser version is 141.0.7390.37
```

**解決策**: webdriver-managerを使用してChromeDriver 141を自動ダウンロード

```python
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.os_manager import ChromeType

service = Service(
    ChromeDriverManager(
        chrome_type=ChromeType.CHROMIUM,
        driver_version='141.0.7390.122'
    ).install()
)
```

### 2. undetected-chromedriverの問題

#### エラー内容
```
Message: tab crashed
  (Session info: chrome=141.0.7390.37)
```

**原因分析**:
- undetected-chromedriverは`get()`メソッドをラップして`navigator.webdriver`をチェック
- この処理がPlaywrightのChromiumバイナリと互換性がない
- タブがクラッシュしてしまう

**結論**: **undetected-chromedriverはこの環境では使用不可**

### 3. proxy.py統合テスト

#### proxy.pyの起動
```bash
uv run proxy \
    --hostname 127.0.0.1 \
    --port 8891 \
    --plugins proxy.plugin.proxy_pool.ProxyPoolPlugin \
    --proxy-pool "$HTTPS_PROXY"
```

#### curlテスト: ✅ 成功
```bash
$ curl -x http://127.0.0.1:8891 -k https://example.com -I

HTTP/1.1 200 OK
HTTP/2 200
content-type: text/html
...
```

#### Seleniumテスト: ❌ タイムアウト
```python
options.add_argument('--proxy-server=http://127.0.0.1:8891')
options.add_argument('--ignore-certificate-errors')
driver.get("https://example.com")  # 90秒タイムアウト
```

**エラー**: `timeout: Timed out receiving message from renderer: 89.624`

#### proxy.pyのログ分析

成功時（curl）:
```
127.0.0.1:25130 - CONNECT example.com:443 -> 21.0.0.83:15004 - 2409 bytes - 81.47 ms
```

失敗時（Selenium）:
```
127.0.0.1:45032 - CONNECT example.com:443 -> 21.0.0.83:15004 - 2791 bytes - 10879.36 ms
127.0.0.1:34321 - GET privateca-content-...storage.googleapis.com:80/.../ca.crt - 2011 bytes - 123.33 ms
```

**重要な発見**:
1. CONNECTトンネルは確立されている（10.8秒）
2. ChromiumがCA証明書をダウンロードしようとしている
3. Googleサービス（update, accounts等）への接続も試みている
4. 最終的にタイムアウト

### 4. より強力な証明書無視フラグのテスト

#### 追加したフラグ
```python
options.add_argument('--ignore-certificate-errors')
options.add_argument('--ignore-ssl-errors')
options.add_argument('--disable-web-security')
options.add_argument('--allow-insecure-localhost')
options.add_argument('--disable-features=CertificateTransparencyEnforcement')
options.add_argument('--disable-features=NetworkService')
options.add_argument('--disable-background-networking')
options.add_argument('--disable-component-update')
```

**結果**: ❌ 依然として90秒タイムアウト

**結論**: Chromiumの証明書検証を完全にバイパスすることは不可能

---

## 🔍 根本原因の分析

### Playwritightの調査結果との比較

| 項目 | Playwright | Selenium |
|------|-----------|----------|
| ローカルHTML | ✅ 動作 | ✅ 動作 |
| タイトル取得 | ❌ ハング | ✅ 動作 |
| proxy.py + curl | ✅ 動作 | ✅ 動作 |
| proxy.py + ブラウザ | ❌ タイムアウト | ❌ タイムアウト |
| スクリーンショット | ✅ 動作 | ❌ クラッシュ |

**共通する問題**:
- Chromium + proxy.py経由のHTTPS通信がタイムアウト
- CA証明書検証が原因
- curlでは成功するが、ブラウザ自動化では失敗

**違い**:
- Seleniumの方がDOM操作は安定している
- しかし、スクリーンショット機能に問題あり

### なぜcurlは成功してChromiumは失敗するのか

1. **curlの動作**:
   - シンプルなHTTPクライアント
   - `-k`フラグで証明書検証をスキップ
   - CA証明書のダウンロードは不要

2. **Chromiumの動作**:
   - 複雑なセキュリティモデル
   - 証明書検証は複数の層で実施
   - CA証明書を自動的にダウンロード・検証しようとする
   - `--ignore-certificate-errors`でも一部の検証は実行される
   - Googleサービスへの接続も試みる

3. **この環境の特性**:
   - TLS Inspection (Anthropic CA証明書)
   - 証明書のダウンロードに時間がかかる (10秒以上)
   - Chromiumがハングまたはタイムアウト

---

## 💡 突破口になりそうなアイデア

### 🎯 優先度: 高

#### 1. Playwright Async API ⭐⭐⭐ 最有力
```python
import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        # DOM操作がハングしない可能性
```

**理由**:
- Playwrightの調査で`page.title()`がハング
- Async APIなら異なる動作をする可能性
- Seleniumよりも制御レベルが高い

#### 2. ハイブリッドアプローチ ⭐⭐⭐ 確実な方法
```python
# Step 1: httpx/urllibでHTMLを取得（proxy.py経由）
import httpx
client = httpx.Client(proxy="http://127.0.0.1:8891")
html = client.get("https://claude.ai/code").text

# Step 2: Seleniumでローカル処理
driver.get("data:text/html," + html)
driver.execute_script("...")  # JavaScript実行可能
```

**メリット**:
- ネットワークアクセス: httpx (proxy.py経由) ✅
- JavaScript実行: Selenium ✅
- Cloudflare回避は困難だが、セッションCookie使用で可能かも

**デメリット**:
- 動的なAPIリクエストは不可
- SPAの完全な再現は困難

#### 3. CA証明書の事前ダウンロード ⭐⭐ 試す価値あり
```bash
# CA証明書を手動でダウンロード
curl -x http://127.0.0.1:8891 \
  http://privateca-content-...storage.googleapis.com/.../ca.crt \
  -o anthropic_ca.crt

# Chromiumに信頼させる
--ssl-cert-authority=/path/to/anthropic_ca.crt
```

**理由**: CA証明書ダウンロードがボトルネックなら、これで解決する可能性

### 🔧 優先度: 中

#### 4. Puppeteer (pyppeteer2) ⭐
Playwrightの調査でも推奨されていた代替ツール。
プロキシ処理の実装が異なる可能性。

#### 5. 通常のSeleniumの継続改善 ⭐
- 基本動作は確認済み
- タイムアウト時間のさらなる延長
- プロキシ設定の微調整

### 📚 優先度: 低

#### 6. Chrome DevTools Protocol (CDP) 直接使用
Seleniumを経由せず、CDPで直接Chromiumを制御。
実装の複雑さが高い。

---

## 📝 次のステップ

### 推奨アクション (優先順)

1. **Playwright Async API を試す** (15分)
   - 最も有望なアプローチ
   - Playwright調査で発見された問題の解決策

2. **ハイブリッドアプローチを実装** (30分)
   - 確実に動作する方法
   - httpx + Seleniumの組み合わせ

3. **CA証明書の事前ダウンロード** (15分)
   - 比較的簡単に試せる
   - 効果がある可能性

4. **セッションCookieを使った手動認証** (30分)
   - ローカル環境でclaude.aiにログイン
   - Cookieをエクスポート
   - httpx + Seleniumでセッション維持

---

## 🎓 学んだこと

### 技術的な発見

1. **undetected-chromedriverの限界**
   - Playwrightのchromiumバイナリとの互換性問題
   - タブクラッシュは回避不可能
   - 標準的なChromeバイナリが必要

2. **proxy.pyの有効性**
   - JWT認証プロキシの透過的な処理: ✅ 完璧
   - curlやhttpxでは完全に動作
   - Chromium統合は未解決

3. **Chromiumの証明書検証**
   - 多層的なセキュリティモデル
   - `--ignore-certificate-errors`でも完全には無効化できない
   - TLS Inspection環境では特に問題が発生しやすい

4. **環境固有の制約**
   - Claude Code Web環境は特殊な制約がある
   - スクリーンショット機能の不安定さ
   - CA証明書ダウンロードの遅延

### 実装上の教訓

- ブラウザ自動化ツールの選択は環境依存
- プロキシ経由のHTTPS通信は複雑
- curlで動作≠ブラウザで動作
- ハイブリッドアプローチの重要性

---

## 📂 作成したテストファイル

| ファイル | 説明 | 結果 |
|---------|------|------|
| `test_undetected_chrome_basic.py` | undetected-chromedriverの基本テスト | ❌ タブクラッシュ |
| `test_selenium_basic.py` | 通常のSeleniumテスト | ⚠️ 一部成功 |
| `test_selenium_with_manager.py` | webdriver-managerを使用 | ⚠️ 一部成功 |
| `test_selenium_with_proxypy.py` | proxy.py統合テスト | ❌ タイムアウト |
| `test_selenium_with_running_proxy.py` | 既存proxy.py使用 | ❌ タイムアウト |
| `test_selenium_stronger_cert_flags.py` | 強力な証明書無視フラグ | ❌ タイムアウト |

---

## 🔗 関連ドキュメント

- [../playwright/README.md](../playwright/README.md) - Playwright調査の全体サマリ
- [../playwright/FINDINGS_PLAYWRIGHT_ISSUES.md](../playwright/FINDINGS_PLAYWRIGHT_ISSUES.md) - Playwright DOM操作ハング問題
- [../playwright/PROXYPY_SUCCESS.md](../playwright/PROXYPY_SUCCESS.md) - proxy.pyの成功記録
- [../playwright/LOCAL_PROXY_INVESTIGATION.md](../playwright/LOCAL_PROXY_INVESTIGATION.md) - ローカルプロキシ詳細調査

---

**Last Updated**: 2025-11-13
**Status**: 🔄 調査継続中 - Playwright Async APIとハイブリッドアプローチを次に試す
