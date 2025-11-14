# Playwright調査サマリー

Claude Code Web環境でPlaywrightを動作させるために直面した問題とその解決策をまとめます。

---

## Network

### curlやwgetは動いているがPlaywrightがだめ

**問題の原因:**
- Claude Code Web環境では外部ネットワークへのアクセスにプロキシが必要
- `HTTPS_PROXY` 環境変数が設定されていないとPlaywrightから外部にアクセスできない

**解決策:**
```bash
# 環境変数の設定（SessionStartフックで自動設定）
export HTTPS_PROXY="http://your-proxy-url"
```

**Playwright/Chromiumに設定する方法:**
```python
# proxy.pyを使用してローカルプロキシを立てる
proxy_process = subprocess.Popen([
    'uv', 'run', 'proxy',
    '--hostname', '127.0.0.1',
    '--port', '8910',
    '--plugins', 'proxy.plugin.proxy_pool.ProxyPoolPlugin',
    '--proxy-pool', os.environ['HTTPS_PROXY'],
])

# Chromiumにプロキシを設定
browser = p.chromium.launch(
    args=[
        '--proxy-server=http://127.0.0.1:8910',
        '--ignore-certificate-errors',
    ]
)
```

**Firefoxに設定する方法:**
```python
# Firefoxはproxy引数で設定可能
browser = p.firefox.launch(
    proxy={"server": f"http://127.0.0.1:{proxy_port}"},
    firefox_user_prefs={
        "network.proxy.allow_hijacking_localhost": True,
    }
)
```

---

## Chromium

### 認証headerの問題（JWT認証プロキシ）

**問題の原因:**
- Claude Code Web環境のプロキシはJWT認証を使用
- ChromiumはJWT認証ヘッダーを直接サポートしていない
- `--proxy-server` にJWTトークンを含めることができない

**解決策:**
- Pythonライブラリ `proxy.py` を使ってローカルプロキシを立てる
- `proxy.py` がJWT認証を処理し、ChromiumにはシンプルなHTTPプロキシとして見せる

**ローカルプロキシのコード:**
```python
# playwright_setup/samples/02_with_proxy.py を参照
import subprocess

proxy_process = subprocess.Popen([
    'uv', 'run', 'proxy',
    '--hostname', '127.0.0.1',
    '--port', '8910',
    '--plugins', 'proxy.plugin.proxy_pool.ProxyPoolPlugin',
    '--proxy-pool', os.environ['HTTPS_PROXY'],  # JWT認証付きプロキシ
])
time.sleep(3)  # 起動待機

# Chromiumからはシンプルなプロキシとしてアクセス
browser = p.chromium.launch(
    args=['--proxy-server=http://127.0.0.1:8910']
)
```

**Firefoxはローカルプロキシ不要？**
- Firefoxでも同様にローカルプロキシが必要
- Firefoxの `proxy` パラメータでも JWT 認証は直接サポートされていない
- 参考: `playwright_setup/samples/08_firefox_with_proxy.py`

---

### フリーズする/クラッシュする

**問題の原因:**
- Claude Code Web環境（コンテナ）では `/dev/shm`（共有メモリ）の容量が非常に小さい
- Chromiumはデフォルトで `/dev/shm` を使用するため、容量不足でクラッシュ・ハングする
- 特に `page.title()` や `page.content()` などDOM操作時に発生

**設定方法:**
```python
browser = p.chromium.launch(
    headless=True,
    args=[
        '--disable-dev-shm-usage',  # /tmpを使用（必須）
        '--single-process',         # シングルプロセス化（必須）
        '--no-sandbox',             # サンドボックス無効化（必須）
    ]
)
```

**詳細:**
- `--disable-dev-shm-usage`: `/dev/shm` の代わりに `/tmp` を使用
- `--single-process`: プロセス間通信を回避（共有メモリを使わない）
- `--no-sandbox`: コンテナ環境でのサンドボックス問題を回避

参考: `playwright_setup/TROUBLESHOOTING.md` - 問題2

---

## Playwright

### フリーズする/クラッシュする

**問題の原因:**
- Playwrightそのものではなく、Chromiumの共有メモリ問題が原因
- 上記「Chromium > フリーズする/クラッシュする」を参照

**解決策:**
- Chromiumの起動引数に `--disable-dev-shm-usage`、`--single-process`、`--no-sandbox` を追加
- または Firefox を使用（Firefoxは共有メモリ問題が発生しにくい）

---

## Firefox

### HOME問題

**問題の原因:**
- Firefoxはプロファイルディレクトリを `$HOME/.mozilla` に作成しようとする
- Claude Code Web環境では `$HOME` が設定されていないか、書き込み権限がない場合がある
- エラー: `Could not create directory: /root/.mozilla`

**設定方法:**
```python
import tempfile
import os

# 一時的なHOMEディレクトリを作成
temp_home = tempfile.mkdtemp(prefix="firefox_home_")

# Firefoxに環境変数を渡す
browser = p.firefox.launch(
    headless=True,
    env={
        **os.environ,
        "HOME": temp_home,
    }
)
```

参考: `playwright_setup/samples/08_firefox_with_proxy.py:56-83`

---

## Cloudflare

### Javascriptチャレンジ

**問題の原因:**
- CloudflareはPlaywrightの自動化を検出（bot検出）
- Chromiumでは `navigator.webdriver` などで自動化を検知される
- "Just a moment..." チャレンジが表示され、先に進めない

**解決策（Chromium）:**
```python
# Anti-detectionフラグを設定
args = [
    '--disable-blink-features=AutomationControlled',  # 必須
    '--disable-features=IsolateOrigins,site-per-process',
    '--window-size=1920,1080',
    '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
]

# JavaScriptインジェクション
page.add_init_script("""
    Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
    Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
    Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});
    window.chrome = { runtime: {} };
""")

# チャレンジ完了を待機
page.goto("https://example.com")
for i in range(10):
    time.sleep(3)
    if page.title() != "Just a moment...":
        break
```

参考: `playwright_setup/samples/04_cloudflare_bypass.py`

**解決策（Firefox）:**
- **ChromiumではなくFirefoxを使ったら通過できていた**
- Firefoxはbot検出がChromiumより甘い傾向がある
- 特にJavaScriptチャレンジの通過率が高い

```python
# Firefoxで同じサイトにアクセス
browser = p.firefox.launch(headless=True)
page = browser.new_page()
page.goto("https://example.com")  # Cloudflareチャレンジを通過しやすい
```

参考: `playwright_setup/samples/07_firefox_basic.py`

---

## まとめ

主要な問題と解決策：

1. **ネットワーク**: プロキシ設定（HTTPS_PROXY + proxy.py）
2. **Chromium JWT認証**: ローカルプロキシで中継
3. **Chromium クラッシュ**: 共有メモリ問題（--disable-dev-shm-usage）
4. **Firefox HOME**: 一時ディレクトリを作成してenv設定
5. **Cloudflare**: Anti-detection設定 or Firefoxを使用

すべての解決策は `playwright_setup/samples/` に実装されています。
