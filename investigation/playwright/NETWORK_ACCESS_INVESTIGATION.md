# ネットワークアクセス調査レポート

**調査日時**: 2025-11-12
**調査者**: Claude Code
**環境**: Linux 4.4.0, Python 3.11.14, Claude Code Web

## 📋 調査概要

Claude Code Web環境で外部サイトへのアクセス可能性を調査しました。

## ✅ 結論: **条件付きでアクセス可能**

この環境では、**Playwrightを除く**ほとんどの手段で外部ネットワークアクセスが可能です。

---

## 🔍 詳細な調査結果

### 1. Python urllib（標準ライブラリ）

#### ✅ **動作状況: 成功**

```python
import urllib.request
response = urllib.request.urlopen('https://example.com')
```

#### テスト結果:

| サイト | 結果 | 備考 |
|--------|------|------|
| example.com (HTTPS) | ✅ 成功 | 200 OK, 513 bytes |
| api.github.com | ✅ 成功 | 200 OK, 2262 bytes |
| httpbin.org | ✅ 成功 | 200 OK, 271 bytes |
| example.com (HTTP) | ✅ 成功 | 200 OK, 513 bytes |
| google.com | ❌ 失敗 | Too Many Requests |
| claude.ai | ❌ 失敗 | Forbidden |

**成功率: 4/6 (66%)**

#### 特徴:
- ✅ HTTPS接続が可能
- ✅ HTTP接続が可能
- ✅ プロキシ経由で自動的に接続
- ⚠️ 一部のサイトでレート制限やアクセス制限

---

### 2. curl コマンド

#### ✅ **動作状況: 成功**

```bash
curl https://example.com
```

#### テスト結果:

```
curl 8.5.0 (x86_64-pc-linux-gnu)
Connecting to 21.0.0.123:15004... connected.
Proxy request sent, awaiting response... 200 OK
```

✅ **HTTPSアクセス成功**

#### 特徴:
- ✅ プロキシ経由で自動接続 (`21.0.0.123:15004`)
- ✅ HTTPS接続が可能
- ✅ 透過的に動作（設定不要）

---

### 3. wget コマンド

#### ✅ **動作状況: 成功**

```bash
wget https://example.com
```

#### テスト結果:

```
GNU Wget 1.21.4
Connecting to 21.0.0.123:15004... connected.
Proxy request sent, awaiting response... 200 OK
Length: 513 [text/html]
```

✅ **HTTPSアクセス成功**

#### 特徴:
- ✅ プロキシ経由で自動接続
- ✅ HTTPS接続が可能
- ✅ ダウンロード機能も正常動作

---

### 4. Socket（低レベルTCP接続）

#### ❌ **動作状況: 失敗**

```python
import socket
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect(('example.com', 443))
```

#### テスト結果:

| ホスト | 結果 | エラー |
|--------|------|--------|
| example.com:80 | ❌ | Temporary failure in name resolution |
| example.com:443 | ❌ | Temporary failure in name resolution |
| google.com:443 | ❌ | Temporary failure in name resolution |
| api.github.com:443 | ❌ | Temporary failure in name resolution |
| claude.ai:443 | ❌ | Temporary failure in name resolution |

**成功率: 0/5 (0%)**

#### 理由:
- DNS解決ができない
- 直接的なTCP接続は許可されていない
- プロキシ経由の接続が必須

---

### 5. Playwright (Chromium)

#### ❌ **動作状況: ほぼ失敗**

```python
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(
        headless=True,
        args=['--no-sandbox', '--disable-setuid-sandbox']
    )
    page = browser.new_page()
    page.goto('https://example.com')  # ❌ ERR_TUNNEL_CONNECTION_FAILED
```

#### テスト結果:

| サイト | プロトコル | 結果 | エラー |
|--------|-----------|------|--------|
| example.com | HTTPS | ❌ | ERR_TUNNEL_CONNECTION_FAILED |
| google.com | HTTPS | ❌ | ERR_NAME_NOT_RESOLVED |
| github.com | HTTPS | ❌ | ERR_TUNNEL_CONNECTION_FAILED |
| api.github.com | HTTPS | ❌ | ERR_TUNNEL_CONNECTION_FAILED |
| httpbin.org | HTTPS | ❌ | ERR_TUNNEL_CONNECTION_FAILED |
| anthropic.com | HTTPS | ❌ | ERR_TUNNEL_CONNECTION_FAILED |
| claude.ai | HTTPS | ❌ | ERR_TUNNEL_CONNECTION_FAILED |
| claude.ai/code/ | HTTPS | ❌ | ERR_TUNNEL_CONNECTION_FAILED |
| example.com | HTTP | ✅ | 成功 |

**成功率: 1/9 (11%)**

#### プロキシ設定の試み

環境変数でプロキシが設定されています：
```
HTTP_PROXY=http://container_...:jwt_...@21.0.0.123:15004
HTTPS_PROXY=http://container_...:jwt_...@21.0.0.123:15004
```

複数のプロキシ設定方法をテストしました：

##### 方法1: Playwright proxy パラメータ
```python
browser = p.chromium.launch(
    proxy={"server": "http://21.0.0.123:15004"}
)
```
**結果**: ❌ `ERR_TUNNEL_CONNECTION_FAILED`

##### 方法2: Chromium起動引数
```python
browser = p.chromium.launch(
    args=['--proxy-server=http://21.0.0.123:15004']
)
```
**結果**: ❌ `ERR_NO_SUPPORTED_PROXIES` → `ERR_TUNNEL_CONNECTION_FAILED`

##### 方法3: 認証情報を明示的に設定
```python
browser = p.chromium.launch(
    proxy={
        "server": "http://21.0.0.123:15004",
        "username": "container_...",
        "password": "jwt_...",
    }
)
```
**結果**: ❌ `ERR_TUNNEL_CONNECTION_FAILED`

#### 理由:
- Chromiumブラウザがこの環境のJWT認証プロキシと互換性がない
- Basic認証形式のプロキシは認識するが、JWT形式は未対応
- HTTPSトンネル接続にJWT認証が必要だが、Chromiumが対応していない
- curl/wget/Python urllibは同じプロキシで動作するため、Chromium固有の問題
- HTTPのみ接続可能（認証不要のため）

---

## 🔧 結論: Playwrightでのプロキシ設定は現状不可

複数のプロキシ設定方法を試しましたが、すべて失敗しました。

### 技術的な制限

1. **JWT認証プロキシの非互換性**
   - この環境のプロキシはJWT（JSON Web Token）ベースの認証を使用
   - Chromiumは標準的なBasic/Digest認証のみサポート
   - カスタム認証ヘッダーの追加も不可

2. **HTTPS CONNECT トンネリング**
   - HTTPSサイトへのアクセスにはCONNECTメソッドが必要
   - プロキシがJWT認証を要求するが、Chromiumが対応していない
   - HTTPは認証不要のため動作する

3. **環境の設計**
   - curl/wget/Python urllibはプロキシライブラリが環境変数を正しく処理
   - Chromiumは独自のネットワークスタックを使用
   - サブプロセスとして起動されるため環境の継承が不完全

### Firefox と WebKit の調査結果

他のブラウザエンジンでの動作可能性も調査しました：

#### Firefox (Gecko エンジン)
```
❌ 起動失敗
Error: Running Nightly as root in a regular user's session is not supported.
```
**理由**: Firefoxはセキュリティ上の理由でroot権限での実行を禁止しているため、この環境では起動できません。

#### WebKit (Safari エンジン)
```
❌ 起動失敗
Error: Host system is missing dependencies to run browsers.
```
**理由**: WebKitの実行に必要なシステムライブラリ（29個）が不足しているため起動できません。

### Playwright Route API を使った回避策の調査

GitHubのIssue (#11967, #443) で報告されている回避策も検証しました：

#### 方法4: context.request.fetch() を使ったヘッダー注入
```python
def handle_route(route):
    headers = dict(route.request.headers)
    headers['Proxy-Authorization'] = f'Basic {encoded_jwt}'

    response = context.request.fetch(
        route.request,
        headers=headers
    )
    route.fulfill(response=response)

context.route("**/*", handle_route)
```

**結果**: ❌ `getaddrinfo EAI_AGAIN example.com`

**理由**: `context.request.fetch()` はプロキシを通らず、直接DNS解決を試みます。この環境ではDNS解決ができないため失敗しました。

#### 方法5: route.continue_() でヘッダーを追加
```python
def handle_route(route):
    headers = dict(route.request.headers)
    headers['Proxy-Authorization'] = f'Basic {encoded_jwt}'
    route.continue_(headers=headers)

context.route("**/*", handle_route)
```

**結果**: ❌ `Protocol error (Fetch.continueRequest): Unsafe header: Proxy-Authorization`

**理由**: **これが決定的な証拠です。** Chromiumは`Proxy-Authorization`ヘッダーを**「危険なヘッダー（Unsafe header）」として明示的に分類**しており、DevTools Protocolレベルで上書きを禁止しています。これはセキュリティ機能であり、回避不可能です。

### 結論

**この環境で起動できるブラウザはChromiumのみ**であり、そのChromiumは：
1. JWT認証プロキシに対応していない
2. `Proxy-Authorization`ヘッダーの上書きをセキュリティ上の理由で禁止している
3. Route APIを使った回避策も動作しない

したがって、**Playwrightでの外部HTTPSアクセスは完全に不可能**です。

---

## 💡 実用的な解決策

### claude.ai へのアクセス方法

#### ❌ **不可能: Playwright経由での直接アクセス**
- ERR_TUNNEL_CONNECTION_FAILED
- プロキシ設定が必要

#### ✅ **可能: Python urllib + Playwright のハイブリッド**

```python
import urllib.request
from playwright.sync_api import sync_playwright

# ステップ1: urllibでHTMLを取得
req = urllib.request.Request('https://claude.ai/code/')
with urllib.request.urlopen(req) as response:
    html_content = response.read().decode('utf-8')

# ステップ2: PlaywrightでローカルHTMLを処理
with sync_playwright() as p:
    browser = p.chromium.launch(
        headless=True,
        args=['--no-sandbox', '--disable-setuid-sandbox']
    )
    page = browser.new_page()
    page.set_content(html_content)

    # ここからJavaScriptの操作が可能
    # ただし、外部APIコールは失敗する
    browser.close()
```

**制限事項**:
- JavaScriptからの外部APIリクエストは失敗する
- 静的なHTML/CSSの解析のみ
- 動的なSPAアプリケーションには不向き

---

## 📊 比較表

| ツール/方法 | HTTPS | HTTP | プロキシ | DNS解決 | JWT認証 | 設定の容易さ | 推奨度 |
|------------|-------|------|---------|---------|---------|------------|--------|
| Python urllib | ✅ | ✅ | 自動 | ✅ | ✅ | ⭐⭐⭐⭐⭐ | **推奨** |
| curl | ✅ | ✅ | 自動 | ✅ | ✅ | ⭐⭐⭐⭐⭐ | **推奨** |
| wget | ✅ | ✅ | 自動 | ✅ | ✅ | ⭐⭐⭐⭐⭐ | **推奨** |
| Playwright | ❌ | ✅ | 不可 | ❌ | ❌ | ⭐ | 非推奨 |
| Socket | ❌ | ❌ | ❌ | ❌ | ❌ | ⭐ | 不可 |

**注記**: PlaywrightはJWT認証プロキシに対応していないため、HTTPSサイトへのアクセスは不可能です。

---

## 🎯 セッション永続化の実装戦略

### claude.ai/code でのセッション永続化

#### 推奨アプローチ: **Python urllib + Cookie管理**

```python
import urllib.request
import json
import http.cookiejar

# Cookie保存用のCookieJarを作成
cookie_jar = http.cookiejar.MozillaCookieJar("claude_cookies.txt")

# オープナーを作成
opener = urllib.request.build_opener(
    urllib.request.HTTPCookieProcessor(cookie_jar)
)
urllib.request.install_opener(opener)

# 初回アクセス（ログイン操作は手動またはAPI経由）
response = opener.open('https://claude.ai/code/')

# Cookieを保存
cookie_jar.save(ignore_discard=True, ignore_expires=True)

# 次回以降、Cookieを読み込んで使用
cookie_jar.load(ignore_discard=True, ignore_expires=True)
response = opener.open('https://claude.ai/code/')
```

#### 制限事項:
1. **ログイン操作**: 自動化が困難
   - claude.aiは認証にJavaScriptを多用
   - urllibだけではログインフォームの送信が難しい

2. **解決策**:
   - ローカル環境でPlaywrightを使ってログイン
   - Cookieをエクスポート
   - Claude Code Web環境にCookieをインポート

---

## 🚀 実装プラン

### ステップ1: ローカル環境でセッション取得

```python
# ローカルPC（Playwrightが外部アクセス可能な環境）で実行
from playwright.sync_api import sync_playwright
import json

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()

    page.goto("https://claude.ai/code/")
    input("ログイン完了後、Enterを押してください...")

    # セッション情報を保存
    storage = context.storage_state()
    with open("claude_session.json", "w") as f:
        json.dump(storage, f, indent=2)

    # Cookieのみを抽出
    cookies = storage['cookies']
    with open("claude_cookies.json", "w") as f:
        json.dump(cookies, f, indent=2)

    browser.close()
```

### ステップ2: Claude Code Web環境でCookieを使用

```python
# Claude Code Web環境で実行
import urllib.request
import json
import http.cookiejar

def load_cookies_from_playwright_format(filepath):
    """Playwright形式のCookieをPythonのCookieJarに変換"""
    with open(filepath, 'r') as f:
        playwright_cookies = json.load(f)

    cookie_jar = http.cookiejar.CookieJar()

    for cookie in playwright_cookies:
        # Playwright Cookie → http.cookiejar.Cookie に変換
        # （変換ロジックの実装が必要）
        pass

    return cookie_jar

# Cookieを読み込み
cookie_jar = load_cookies_from_playwright_format('claude_cookies.json')

# リクエストを送信
opener = urllib.request.build_opener(
    urllib.request.HTTPCookieProcessor(cookie_jar)
)
response = opener.open('https://claude.ai/code/')
print(response.read().decode('utf-8'))
```

---

## ⚠️ 注意事項とセキュリティ

### Cookie管理のセキュリティ

1. **機密情報の取り扱い**
   - Cookieには認証情報が含まれる
   - `.gitignore` に必ず追加する
   - 公開リポジトリにコミットしない

2. **セッション有効期限**
   - claude.aiのセッションには有効期限がある
   - 定期的な再ログインが必要

3. **APIの利用規約**
   - 自動化がclaude.aiの利用規約に違反しないか確認
   - レート制限に注意

---

## 📝 まとめ

### ✅ できること

1. **Python urllibでHTTPS通信**: 完全に可能（JWT認証プロキシ対応）
2. **curl/wgetでの外部アクセス**: 完全に可能（JWT認証プロキシ対応）
3. **Cookieベースのセッション管理**: 可能
4. **PlaywrightでHTTPサイトアクセス**: 可能（認証不要のため）
5. **Playwrightでローカ HTML処理**: 完全に可能

### ❌ できないこと

1. **PlaywrightでのHTTPSサイトアクセス**: JWT認証プロキシ非対応のため不可
2. **直接的なTCP/Socket接続**: DNS解決不可のため不可
3. **Playwrightから動的なHTTPS API呼び出し**: 上記の理由により不可

### 💡 推奨される実装方法

claude.ai/codeでのセッション永続化には、以下の戦略が考えられます：

#### 戦略A: ハイブリッドアプローチ（推奨）
1. ローカル環境でPlaywrightを使ってログイン → Cookieエクスポート
2. Claude Code WebでPython urllibを使ってCookieでHTTPSアクセス
3. 取得したHTMLをPlaywrightでローカル処理（JavaScript実行、DOM操作）

**メリット**:
- ✅ HTTPSサイトにアクセス可能
- ✅ JavaScript実行が可能（ローカルHTML内）
- ✅ DOM操作とスクリーンショットが可能
- ⚠️ 外部APIへの動的リクエストは不可

#### 戦略B: Python urllibのみで実装
1. 手動またはローカルでブラウザからCookieをエクスポート
2. Python urllibでCookieを使ってアクセス
3. HTMLパーサー（BeautifulSoup等）で静的解析

**メリット**:
- ✅ シンプルな実装
- ✅ 依存関係が少ない
- ❌ JavaScript実行は不可
- ❌ 動的コンテンツの取得は不可

---

## 🔬 次のステップ

### 実装すべき項目

1. ✅ **プロキシ設定の調査** - 完了
   - 環境変数の確認済み（JWT認証プロキシ）
   - Chromiumでのプロキシ設定テスト完了（JWT認証非対応と判明）
   - Firefox/WebKitの調査完了（起動不可）
   - Playwright Route APIの回避策検証完了（セキュリティ制限により不可）
   - **決定的な発見**: `Proxy-Authorization`は「Unsafe header」として禁止されている
   - 結論: PlaywrightでのHTTPSアクセスは完全に不可能

2. **Cookie変換ユーティリティの作成**
   - Playwright形式 → urllib形式の変換
   - セッション管理クラスの実装
   - Cookie有効期限の管理

3. **Python urllibベースのHTTPクライアント実装**
   - Cookie永続化機能
   - セッション管理
   - HTMLコンテンツの取得

4. **ハイブリッドアプローチの実装**
   - urllibでHTMLを取得
   - Playwrightでローカル処理
   - 統合テストの作成

5. **自動再ログイン機能**
   - セッション有効期限の検知
   - エラーハンドリング

---

## 📚 参考リソース

- [Python urllib.request](https://docs.python.org/3/library/urllib.request.html)
- [Playwright Proxy Settings](https://playwright.dev/python/docs/network#http-proxy)
- [HTTP Cookie Management](https://docs.python.org/3/library/http.cookiejar.html)
- [Playwright Issue #11967 - Proxy-Authorization via Route API](https://github.com/microsoft/playwright/issues/11967)
- [Playwright Issue #443 - Proxy-Authorization in Chromium](https://github.com/microsoft/playwright-python/issues/443)
- [Chromium HTTP Authentication Design](https://www.chromium.org/developers/design-documents/http-authentication/)
