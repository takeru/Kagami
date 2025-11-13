# ローカルプロキシサーバー実装の調査結果

## 概要
JWT認証プロキシを経由してPlaywrightでHTTPSアクセスを可能にするため、Pythonでローカルプロキシサーバーを実装しました。

## 実装したソリューション

### アーキテクチャ
```
Chromium (認証なし)
    ↓
localhost:8888 (Python local proxy)
    ↓ (JWT認証を追加)
21.0.0.123:15004 (JWT認証プロキシ)
    ↓
インターネット
```

### 実装ファイル

**src/local_proxy.py**
- 標準ライブラリのみを使用（依存関係なし）
- HTTP/HTTPSプロキシサーバー
- CONNECTメソッドによるHTTPSトンネリング
- JWT認証の透過的な処理
- 双方向データトンネリング（select()使用）

## テスト結果

### ✅ 成功: curlによるHTTPSアクセス

```bash
$ curl -x http://127.0.0.1:8888 -k https://example.com -I

HTTP/1.0 200 Connection Established
Server: BaseHTTP/0.6 Python/3.11.14
Proxy-agent: Local-Proxy/1.0

HTTP/2 200
content-type: text/html
...
```

**詳細**:
- CONNECTトンネルが正常に確立
- TLS handshake成功（TLSv1.3）
- HTTP/2レスポンス受信成功
- **証明書**: Anthropic TLS Inspection CA（環境がTLS検査を実施）

### ❌ 失敗: PlaywrightによるHTTPSアクセス

**問題**: タイムアウト（60秒）

**観察された動作**:
1. CONNECTリクエストは成功（"HTTP/1.1 200 OK"）
2. トンネルは確立される
3. **しかし**: Chromiumがタイムアウト

**プロキシサーバーのログ**:
```
[Proxy] 127.0.0.1 - CONNECT request to example.com:443
[Proxy] 127.0.0.1 - Connecting to upstream proxy 21.0.0.123:15004
[Proxy] 127.0.0.1 - Upstream proxy response: HTTP/1.1 200 OK
[Proxy] 127.0.0.1 - "CONNECT example.com:443 HTTP/1.1" 200 -
[Proxy] 127.0.0.1 - "GET http://privateca-content-.../ca.crt HTTP/1.1" 200 -
[Proxy] 127.0.0.1 - HTTP request failed: [Errno 32] Broken pipe
```

### 問題の分析

#### 1. CA証明書ダウンロードの試行
Chromiumは証明書を検証するため、CA証明書をダウンロードしようとします：
```
GET http://privateca-content-693e503d-0000-2af1-b04c-5c337bc7529b.storage.googleapis.com/7daf77a46936d9192651/ca.crt
```

このリクエストが `Broken pipe` エラーで失敗しています。

#### 2. `--ignore-certificate-errors` の効果不足
以下のフラグを使用しましたが、Chromiumは証明書のダウンロードを試行：
```python
args=[
    '--ignore-certificate-errors',
    '--ignore-certificate-errors-spki-list',
]
```

#### 3. Broken pipeエラーの原因
- `urllib.request.open()` がタイムアウトまたは失敗
- クライアント（Chromium）との接続が切断される
- エラーハンドリング中に `Broken pipe` が発生

## テストしたPlaywright設定

### 方法1: proxyパラメータ
```python
browser = p.chromium.launch(
    headless=True,
    args=['--no-sandbox', '--ignore-certificate-errors'],
    proxy={"server": "http://127.0.0.1:8888"}
)
```
**結果**: タイムアウト

### 方法2: --proxy-serverフラグ
```python
browser = p.chromium.launch(
    headless=True,
    args=[
        '--no-sandbox',
        '--ignore-certificate-errors',
        '--proxy-server=http://127.0.0.1:8888',
    ],
)
```
**結果**: タイムアウト

### 方法3: ignore_https_errors
```python
context = browser.new_context(
    ignore_https_errors=True
)
```
**結果**: タイムアウト

## 次のステップ: 追加調査が必要

### オプション1: CA証明書の処理改善
- CA証明書を事前にダウンロード
- Chromiumに信頼させる設定を追加
- または、CA証明書へのアクセスをプロキシで正常に処理

### オプション2: トンネリングロジックのデバッグ
- `_tunnel_data()` のselectループにデバッグログを追加
- データ転送量を記録
- タイムアウトの詳細を調査

### オプション3: alternative実装
- Python urllibでページを取得してPlaywrightに渡す
- Playwright Serverとして実装
- または、他のプロキシライブラリ（mitmproxy等）を検討

### オプション4: Chromiumフラグの追加調査
さらに強力な証明書無視オプション：
```
--disable-web-security
--allow-insecure-localhost
--disable-features=CertificateTransparencyEnforcement
```

## 結論

### 達成したこと
✅ ローカルプロキシサーバーの実装完了
✅ JWT認証の透過的な処理
✅ curlでのHTTPS通信成功

### 未解決の課題
❌ PlaywrightからのHTTPS通信がタイムアウト
❌ CA証明書ダウンロードの失敗
❌ Chromiumの証明書検証回避が不完全

### 技術的な教訓
1. **TLS Inspection**: この環境はAnthropicのCA証明書でTLS検査を実施している
2. **CONNECTトンネル**: socketレベルのトンネリングは正常に動作
3. **Chromiumの制約**: 証明書検証を完全にスキップすることが困難

### 推奨される次のアクション
最も確実な方法は **Option 3: Alternative実装**：
- Python urllib でページ取得
- HTMLをPlaywrightに渡す
- または、Playwright RequestライブラリとHybridアプローチ

これにより、Chromiumの証明書検証を完全に回避できます。
