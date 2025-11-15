# CA証明書インポートガイド - TLS Inspection環境でのFirefox設定

## 📋 概要

このガイドでは、Anthropic Sandbox環境のTLS Inspection環境下で、FirefoxからHTTPSサイトに証明書エラーなしでアクセスする方法を説明します。

## 🔍 背景：TLS Inspectionとは

### この環境の通信フロー

```
クライアント → JWT認証Proxy (TLS Inspection) → インターネット
```

### TLS Inspectionの動作

1. **HTTPS通信を傍受**
   - すべてのHTTPS通信がプロキシで復号化される
   - 通信内容が平文で確認可能（セキュリティチェック）

2. **証明書の置き換え**
   - 本来の証明書（DigiCert、Let's Encryptなど）
   - ↓ プロキシが置き換え
   - Anthropic CA証明書（`sandbox-egress-production TLS Inspection CA`）

3. **クライアント側での証明書エラー**
   - Firefoxが置き換えられた証明書を信頼していない
   - → `SEC_ERROR_UNKNOWN_ISSUER`エラーが発生

### curlとFirefoxの違い

```bash
# curlは成功する（システム証明書ストアを使用）
$ curl https://www.yahoo.co.jp
→ ✅ 正常にアクセス

# Firefoxは失敗する（独自の証明書ストアを使用）
Firefox → https://www.yahoo.co.jp
→ ❌ SEC_ERROR_UNKNOWN_ISSUER
```

## 🎯 解決策の全体像

### 必要な2つの要素

1. **CA証明書のインポート**（TLS Inspectionの証明書を信頼）
2. **proxy.pyの使用**（JWT認証の処理）

### 成功する構成

```
Firefox (CA証明書インポート済み)
  ↓
proxy.py (localhost:18913) ← JWT認証処理
  ↓
JWT認証Proxy (21.0.0.95:15004) ← TLS Inspection
  ↓
Yahoo! JAPAN ← 証明書エラーなし！
```

## 🔧 セットアップ手順

### ステップ1: certutilのインストール

```bash
apt-get update
apt-get install -y libnss3-tools
```

**確認:**
```bash
certutil --version
```

### ステップ2: Firefoxプロファイルの作成

```bash
# プロファイルディレクトリを作成
mkdir -p /home/user/firefox-profile

# 証明書データベースを初期化
certutil -N -d sql:/home/user/firefox-profile --empty-password
```

**確認:**
```bash
ls -la /home/user/firefox-profile/
# 以下のファイルが作成される:
# - cert9.db      (証明書データベース)
# - key4.db       (鍵データベース)
# - pkcs11.txt    (PKCS#11設定)
```

### ステップ3: CA証明書のインポート

#### 3-1. staging環境のCA証明書

```bash
certutil -A \
  -n "Anthropic TLS Inspection CA" \
  -t "C,," \
  -i /usr/local/share/ca-certificates/swp-ca-staging.crt \
  -d sql:/home/user/firefox-profile
```

#### 3-2. production環境のCA証明書

```bash
certutil -A \
  -n "Anthropic TLS Inspection CA Production" \
  -t "C,," \
  -i /usr/local/share/ca-certificates/swp-ca-production.crt \
  -d sql:/home/user/firefox-profile
```

**パラメータの意味:**
- `-A`: 証明書を追加
- `-n`: 証明書のニックネーム
- `-t "C,,"`: 信頼設定（C = SSL CA として信頼）
- `-i`: 証明書ファイルのパス
- `-d`: 証明書データベースのパス

### ステップ4: インポート確認

```bash
certutil -L -d sql:/home/user/firefox-profile
```

**期待される出力:**
```
Certificate Nickname                                         Trust Attributes
                                                             SSL,S/MIME,JAR/XPI

Anthropic TLS Inspection CA                                  C,,
Anthropic TLS Inspection CA Production                       C,,
```

✅ `C,,` が表示されていればインポート成功

### ステップ5: システム証明書ストアの更新（オプション - Firefoxには不要）

```bash
update-ca-certificates --fresh
```

**注意: Firefoxのためには不要です！**

- **Firefox**: 独自の証明書ストア（`cert9.db`）を使用
- **curl/wget/Python等**: システム証明書ストア（`/etc/ssl/certs`）を使用

このステップは、curl等の他のツールでHTTPSアクセスする場合に有用です。

**検証済み:**
- `security.enterprise_roots.enabled = false`でもFirefoxは動作
- システム証明書ストアを見ていないことを確認済み
- 詳細: [`test_25_verify_system_cert_not_needed.py`](./test_25_verify_system_cert_not_needed.py)

## 🐍 Playwrightでの使用方法

### 基本的な使い方

```python
import asyncio
import os
import signal
import subprocess
import time
from playwright.async_api import async_playwright


async def access_with_imported_cert():
    """CA証明書インポート済みプロファイル + proxy.py経由でアクセス"""

    # プロキシ設定を取得
    https_proxy = os.environ.get('HTTPS_PROXY', '')

    # 1. proxy.pyを起動
    proxy_process = subprocess.Popen([
        "uv", "run", "proxy",
        "--hostname", "127.0.0.1",
        "--port", "18913",
        "--plugins", "proxy.plugin.proxy_pool.ProxyPoolPlugin",
        "--proxy-pool", https_proxy
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    time.sleep(2)  # proxy.pyの起動を待つ

    try:
        async with async_playwright() as p:
            # 2. CA証明書インポート済みプロファイルでFirefoxを起動
            context = await p.firefox.launch_persistent_context(
                user_data_dir="/home/user/firefox-profile",
                executable_path="/home/user/.cache/ms-playwright/firefox-1496/firefox/firefox",
                headless=True,
                proxy={
                    "server": "http://127.0.0.1:18913"  # proxy.py経由
                },
                firefox_user_prefs={
                    "privacy.trackingprotection.enabled": False,
                    "network.proxy.allow_hijacking_localhost": True,
                    "security.cert_pinning.enforcement_level": 0,
                    "security.enterprise_roots.enabled": True,
                    "security.OCSP.enabled": 0,
                },
                ignore_https_errors=True,
                bypass_csp=True
            )

            page = await context.new_page()

            # 3. HTTPSサイトにアクセス
            response = await page.goto(
                "https://www.yahoo.co.jp/",
                wait_until="domcontentloaded",
                timeout=30000
            )

            print(f"ステータス: {response.status}")
            print(f"タイトル: {await page.title()}")

            await context.close()

    finally:
        # proxy.pyを停止
        proxy_process.send_signal(signal.SIGTERM)
        proxy_process.wait(timeout=5)


# 実行
if __name__ == "__main__":
    os.environ['HOME'] = '/home/user'  # 重要！
    asyncio.run(access_with_imported_cert())
```

### 重要なポイント

#### 1. `HOME=/home/user` の設定

```python
os.environ['HOME'] = '/home/user'
```

または実行時に指定:
```bash
HOME=/home/user uv run python script.py
```

**理由:** Firefoxはプロファイルの所有者とHOMEディレクトリの所有者が一致していることを要求します。

#### 2. `launch_persistent_context` の使用

```python
context = await p.firefox.launch_persistent_context(
    user_data_dir="/home/user/firefox-profile",  # プロファイルパス
    ...
)
```

**`launch` + `new_context`ではダメ:**
```python
# ❌ これではプロファイルが適用されない
browser = await p.firefox.launch(args=['-profile', '/home/user/firefox-profile'])
```

#### 3. executable_pathの指定

```python
executable_path="/home/user/.cache/ms-playwright/firefox-1496/firefox/firefox"
```

**理由:** HOME=/home/userにFirefox build v1496をインストールしているため。

## ⚠️ proxy.pyが必須な理由

### JWT認証の問題

**HTTPS_PROXY環境変数の中身:**
```
http://container_xxx:jwt_eyJ0eXAiOiJKV1QiLCJhbGc...@21.0.0.95:15004
```

この複雑なJWT認証形式をFirefoxは直接処理できません。

### proxy.pyの役割

```python
# proxy.pyを起動
uv run proxy \
  --hostname 127.0.0.1 \
  --port 18913 \
  --plugins proxy.plugin.proxy_pool.ProxyPoolPlugin \
  --proxy-pool "$HTTPS_PROXY"
```

**やっていること:**
1. JWT認証を処理
2. Firefoxにはシンプルな`http://127.0.0.1:18913`を提供
3. プロキシプールの管理

### 比較

| 構成 | 結果 | 理由 |
|------|------|------|
| Firefox → proxy.py → JWT認証Proxy | ✅ 成功 | JWT認証が正しく処理される |
| Firefox → 直接HTTPS_PROXY | ❌ unknown error | FirefoxがJWT認証を処理できない |
| Firefox (CA証明書あり) → proxy.pyなし | ❌ 接続エラー | JWT認証が処理されない |
| Firefox (CA証明書なし) → proxy.py経由 | ❌ 証明書エラー | TLS Inspectionの証明書を信頼していない |
| **Firefox (CA証明書あり) → proxy.py経由** | **✅ 完全成功** | **両方が揃っている** |

## 📝 実例：Yahoo! JAPANのトピック取得

完全なサンプルコード: [`test_24_firefox_profile_with_proxy_py.py`](./test_24_firefox_profile_with_proxy_py.py)

```bash
# 実行
HOME=/home/user uv run python investigation/playwright/test_24_firefox_profile_with_proxy_py.py
```

**期待される出力:**
```
✅ Yahoo! JAPANに正常にアクセスできました！
   → CA証明書が正しく認識されています！

📰 Yahoo! JAPANのコンテンツ（20件）:
   1. Yahoo! JAPAN
   2. 主なサービス
   3. 高市首相 ハードワークの舞台裏
   4. 政府が検討「おこめ券」いつ届く
   ...
```

## 🔍 トラブルシューティング

### 1. `SEC_ERROR_UNKNOWN_ISSUER` エラーが出る

**症状:**
```
Warning: Potential Security Risk Ahead
SEC_ERROR_UNKNOWN_ISSUER
```

**原因:**
- CA証明書がインポートされていない
- プロファイルが正しく読み込まれていない

**解決策:**
```bash
# CA証明書を確認
certutil -L -d sql:/home/user/firefox-profile | grep Anthropic

# インポートされていなければ再度インポート
certutil -A -n "Anthropic TLS Inspection CA Production" -t "C,," \
  -i /usr/local/share/ca-certificates/swp-ca-production.crt \
  -d sql:/home/user/firefox-profile
```

### 2. `unknown error` が出る

**症状:**
```
Page.goto: <unknown error>
```

**原因:**
- proxy.pyが起動していない
- プロキシ設定が間違っている

**解決策:**
```python
# proxy.pyを起動
proxy_process = subprocess.Popen([...])
time.sleep(2)  # 十分な待ち時間

# プロキシサーバーはproxy.pyを指定
proxy={"server": "http://127.0.0.1:18913"}  # ✅ 正しい
proxy={"server": https_proxy}  # ❌ これだとJWT認証が処理されない
```

### 3. Firefoxが起動しない

**症状:**
```
Firefox is unable to launch if the $HOME folder isn't owned by the current user.
```

**原因:**
- HOME環境変数が正しく設定されていない

**解決策:**
```python
os.environ['HOME'] = '/home/user'
```

または:
```bash
HOME=/home/user uv run python script.py
```

### 4. `Executable doesn't exist` エラー

**症状:**
```
Executable doesn't exist at /home/user/.cache/ms-playwright/firefox-1495
```

**原因:**
- HOME=/home/userでFirefoxがインストールされていない

**解決策:**
```bash
HOME=/home/user node /opt/node22/lib/node_modules/@playwright/mcp/node_modules/playwright/cli.js install firefox
```

## 📊 証明書の確認方法

### curlで証明書を確認

```bash
curl -v https://www.yahoo.co.jp 2>&1 | grep -A 5 "Server certificate"
```

**出力例:**
```
* Server certificate:
*  subject: CN=*.yahoo.co.jp
*  issuer: O=Anthropic; CN=sandbox-egress-production TLS Inspection CA
*  SSL certificate verify ok.
```

→ 発行者がAnthropicになっていることがTLS Inspectionの証拠

### システム証明書ストアを確認

```bash
ls -la /usr/local/share/ca-certificates/
```

**出力例:**
```
-rw-r--r-- 1 claude ubuntu 1309 Nov 13 02:38 swp-ca-production.crt
-rw-r--r-- 1 claude ubuntu 1301 Nov 13 02:38 swp-ca-staging.crt
```

### Firefoxプロファイルの証明書を確認

```bash
certutil -L -d sql:/home/user/firefox-profile
```

## 🎓 学んだこと

### 1. TLS Inspectionの仕組み

- すべてのHTTPS通信が傍受され、復号化される
- プロキシが独自のCA証明書で証明書を置き換える
- セキュリティチェックのための仕組み

### 2. Firefoxの証明書管理

- Firefoxは独自の証明書ストアを使用
- システム証明書ストアとは別
- `security.enterprise_roots.enabled: true` だけでは不十分

### 3. proxy.pyの重要性

- JWT認証処理のために必須
- シンプルなHTTPプロキシとしてブラウザに提供
- プロキシプールの管理機能

### 4. 両方が必要

- CA証明書のインポートだけでは不十分（JWT認証エラー）
- proxy.pyだけでは不十分（証明書エラー）
- **両方を組み合わせて初めて成功**

## 📚 関連ドキュメント

- [HOME=/home/user 環境でのFirefoxセットアップ手順](./HOME_USER_FIREFOX_SETUP.md)
- [Playwright調査まとめ](../../PLAYWRIGHT_INVESTIGATION.md)

## 🔗 参考テストコード

- `test_17_mcp_with_cli_direct.py` - MCP経由でのアクセス（証明書エラーまで到達）
- `test_22_firefox_with_imported_cert.py` - MCP + CA証明書インポート（失敗）
- `test_23_firefox_playwright_direct.py` - Playwright直接実行（失敗）
- **`test_24_firefox_profile_with_proxy_py.py`** - **完全成功版** ✅

## ✅ チェックリスト

セットアップが正しく完了したか確認:

- [ ] certutilがインストールされている
- [ ] `/home/user/firefox-profile`が作成されている
- [ ] `cert9.db`, `key4.db`, `pkcs11.txt`が存在する
- [ ] `certutil -L`でCA証明書が表示される（Trust Attributes: `C,,`）
- [ ] Firefox build v1496が`/home/user/.cache/ms-playwright/firefox-1496`にインストールされている
- [ ] proxy.pyが起動できる
- [ ] `HOME=/home/user`環境変数が設定されている
- [ ] test_24が成功する

すべてチェックできれば、証明書エラーなしでHTTPSサイトにアクセスできます！

## 💡 よくある誤解

### Q: `security.enterprise_roots.enabled: true` が必要？

**A: いいえ、不要です。**

検証結果（test_25）:
- `security.enterprise_roots.enabled = false`でも動作
- この設定はシステム証明書ストアを見るかどうかの設定
- Firefoxプロファイル（cert9.db）に直接インポートすれば不要

### Q: `update-ca-certificates` が必要？

**A: Firefoxのためには不要です。curl等のためには必要です。**

| ツール | 証明書ストア | update-ca-certificates必要？ |
|--------|------------|---------------------------|
| Firefox | `/home/user/firefox-profile/cert9.db` | ❌ 不要 |
| curl | `/etc/ssl/certs/ca-certificates.crt` | ✅ 必要 |
| wget | `/etc/ssl/certs/ca-certificates.crt` | ✅ 必要 |
| Python requests | `/etc/ssl/certs/ca-certificates.crt` | ✅ 必要 |

### Q: なぜtest_23（proxy.pyなし）は失敗する？

**A: JWT認証が処理されないからです。**

HTTPS_PROXY環境変数:
```
http://user:jwt_eyJ0eXAi...@host:port
```

この複雑なJWT認証形式をFirefoxは直接処理できません。proxy.pyが必須です。

### Q: 両方が必要？

**A: はい、CA証明書インポートとproxy.pyの両方が必要です。**

```
CA証明書のみ → ❌ JWT認証エラー
proxy.pyのみ → ❌ 証明書エラー
両方 → ✅ 成功！
```
