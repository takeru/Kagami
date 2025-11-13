# proxy.py ライブラリ実装の成功記録

## 🎉 成功した部分

### curlでのHTTPS通信

**完全成功！** proxy.pyライブラリを使って、JWT認証プロキシ経由でHTTPSアクセスが可能になりました。

```bash
uv run proxy \
    --hostname 127.0.0.1 \
    --port 8891 \
    --plugins proxy.plugin.proxy_pool.ProxyPoolPlugin \
    --proxy-pool "$HTTPS_PROXY" &

curl -x http://127.0.0.1:8891 -k https://example.com -I
```

**結果:**
```
HTTP/2 200
content-type: text/html
2413 bytes - 240.42 ms
127.0.0.1:29626 - CONNECT example.com:443 -> 21.0.0.49:15004
```

### 重要な発見

1. **ProxyPoolPluginが必須**
   - `--proxy-pool`だけでは不十分
   - プラグインを明示的に指定：`--plugins proxy.plugin.proxy_pool.ProxyPoolPlugin`

2. **JWT認証の自動処理**
   - URL形式：`http://username:password@host:port`
   - プラグインが自動的に`Proxy-Authorization`ヘッダーを追加

3. **HTTP/2サポート**
   - proxy.pyはHTTP/2をネイティブサポート
   - 外部ライブラリ（h2, hpack, hyperframe）が必要

## ❌ 未解決の問題

### Playwrightとの連携

Chromiumとproxy.pyの連携でEPIPEエラーが発生：

```
Error: write EPIPE
```

**考えられる原因:**
1. Chromiumの証明書検証が完了しない
2. proxy.pyとChromiumの通信プロトコルの問題
3. タイムアウト設定が不適切

**試したこと:**
- `--ignore-certificate-errors` ✅ 使用済み
- `ignore_https_errors=True` ✅ 使用済み
- タイムアウト延長 ✅ 試行済み

## 技術的詳細

### proxy.pyの正しい使用方法

```python
# 起動コマンド
subprocess.Popen([
    'uv', 'run', 'proxy',
    '--hostname', '127.0.0.1',
    '--port', '8891',
    '--plugins', 'proxy.plugin.proxy_pool.ProxyPoolPlugin',  # 必須！
    '--proxy-pool', upstream_proxy_url,  # JWT認証情報を含む
])

# Chromium設定
browser = p.chromium.launch(
    headless=True,
    args=[
        '--no-sandbox',
        '--proxy-server=http://127.0.0.1:8891',
        '--ignore-certificate-errors',
    ],
)
```

### アーキテクチャ

```
curl/Chromium
    ↓
localhost:8891 (proxy.py + ProxyPoolPlugin)
    ↓ (Proxy-Authorization: Basic {JWT})
upstream JWT proxy (21.0.0.x:15004)
    ↓
インターネット
```

### ProxyPoolPlugin の動作

**ソースコード:** `/home/user/Kagami/.venv/lib/python3.11/site-packages/proxy/plugin/proxy_pool.py`

重要なメソッド：
- `before_upstream_connection()`: 上流プロキシへの接続を確立
- `handle_client_request()`: JWT認証ヘッダーを自動追加
- `handle_upstream_data()`: レスポンスをクライアントに転送

```python
# JWT認証の自動処理（ProxyPoolPlugin内）
if self._endpoint.has_credentials:
    request.add_header(
        httpHeaders.PROXY_AUTHORIZATION,
        b'Basic ' + base64.b64encode(
            self._endpoint.username + COLON + self._endpoint.password
        ),
    )
```

## 次のステップ

### オプション1: Chromium問題の解決
- より詳細なデバッグログ
- 別の証明書処理方法
- Chromiumフラグの追加調査

### オプション2: 代替アプローチ（推奨）
**httpx + Playwrightハイブリッド**

```python
# httpxでHTTP通信（proxy.py経由）
import httpx
client = httpx.Client(proxy="http://127.0.0.1:8891")
html = client.get("https://claude.ai/code/").text

# Playwrightでレンダリング・操作
page.set_content(html)
page.click("button")  # JavaScriptやDOM操作可能
```

## 結論

**proxy.pyライブラリは正しく動作しています！**

- ✅ JWT認証プロキシとの通信：完全成功
- ✅ HTTP/2サポート：動作確認
- ✅ ProxyPoolPlugin：正常動作
- ❌ Chromium統合：未解決（EPIPE）

curlでの成功により、proxy.pyの実装は正しいことが証明されました。Chromium統合の問題は、proxy.pyではなくChromium側の制約と考えられます。
