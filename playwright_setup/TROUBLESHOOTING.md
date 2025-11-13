# トラブルシューティングガイド

Playwrightの使用中に発生する可能性のある問題と解決方法をまとめました。

---

## 🔴 よくある問題

### 1. Chromiumが起動しない

#### 症状
```
playwright._impl._api_types.Error: Executable doesn't exist at /root/.cache/ms-playwright/chromium-1148/chrome-linux/chrome
```

#### 原因
Chromiumがインストールされていない

#### 解決方法
```bash
uv run playwright install chromium
```

#### 確認方法
```bash
uv run playwright install --dry-run chromium
```

---

### 2. DOM操作でクラッシュ・ハング

#### 症状
```python
page.goto("https://example.com")  # OK
page.title()  # ← ここでハング/クラッシュ
```

#### 原因
共有メモリ (`/dev/shm`) の容量不足

Claude Code Web環境（コンテナ）では `/dev/shm` の容量が非常に小さく、Chromiumのデフォルト設定では動作しません。

#### 解決方法
以下のフラグを**必ず**追加してください：

```python
browser = p.chromium.launch(
    headless=True,
    args=[
        '--disable-dev-shm-usage',  # /tmpを使用（重要）
        '--single-process',         # シングルプロセス化（重要）
        '--no-sandbox',             # サンドボックス無効化
    ]
)
```

#### 詳細説明
- `--disable-dev-shm-usage`: `/dev/shm` の代わりに `/tmp` を使用
- `--single-process`: プロセス間通信を回避
- `--no-sandbox`: コンテナ環境でのサンドボックス問題を回避

---

### 3. プロキシ接続エラー

#### 症状A: 接続拒否
```
net::ERR_PROXY_CONNECTION_FAILED
```

#### 原因
proxy.py が起動していない

#### 解決方法
```python
# proxy.pyを起動
proxy_process = subprocess.Popen([
    'uv', 'run', 'proxy',
    '--hostname', '127.0.0.1',
    '--port', '8910',
    '--plugins', 'proxy.plugin.proxy_pool.ProxyPoolPlugin',
    '--proxy-pool', os.environ['HTTPS_PROXY'],
])

# 起動を待機
time.sleep(3)
```

#### 症状B: 環境変数未設定エラー
```
KeyError: 'HTTPS_PROXY'
```

#### 解決方法
```bash
export HTTPS_PROXY="http://your-proxy-url"
```

確認方法:
```bash
echo $HTTPS_PROXY
```

#### 症状C: JWT認証エラー
```
407 Proxy Authentication Required
```

#### 原因
proxy.py が JWT 認証を正しく処理できていない

#### 解決方法
1. `ProxyPoolPlugin` が有効か確認
   ```python
   '--plugins', 'proxy.plugin.proxy_pool.ProxyPoolPlugin'
   ```

2. `HTTPS_PROXY` に JWT トークンが含まれているか確認
   ```bash
   echo $HTTPS_PROXY | grep -o "eyJ[^:]*"
   ```

---

### 4. Cloudflareチャレンジを通過できない

#### 症状A: "Just a moment..." のまま進まない
```python
page.goto("https://claude.ai")
print(page.title())  # → "Just a moment..."
```

#### 原因
1. Anti-detectionフラグが不足
2. 待機時間が不足

#### 解決方法
```python
# 必須フラグ
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
for i in range(10):
    time.sleep(3)
    if page.title() != "Just a moment...":
        print("✅ チャレンジ通過")
        break
```

#### 症状B: Status 403 が返される
```
response.status == 403
```

#### 原因
Cloudflareがbotと判定

#### 解決方法
1. `page.content()` を頻繁に呼ばない（bot判定の原因）
2. ページ遷移後は適度に待機する
   ```python
   page.goto(url)
   time.sleep(2)  # 待機
   ```

3. User Agentを実際のブラウザに設定
   ```python
   '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
   ```

---

### 5. セッションが保存されない

#### 症状
Cookie や localStorage が次回実行時に消える

```python
# 1回目
page.goto("https://example.com")
page.evaluate("localStorage.setItem('key', 'value')")

# 2回目（別の実行）
page.goto("https://example.com")
value = page.evaluate("localStorage.getItem('key')")
print(value)  # → None （消えている）
```

#### 原因
`launch()` を使用している（非永続化モード）

#### 解決方法
`launch_persistent_context()` を使用

```python
# ❌ 間違い - セッションが保存されない
browser = p.chromium.launch(headless=True)
page = browser.new_page()

# ✅ 正しい - セッションが保存される
browser = p.chromium.launch_persistent_context(
    user_data_dir="/tmp/my_session",  # セッション保存先
    headless=True,
    args=[...]
)
page = browser.pages[0]  # 既に開いているページを取得
```

---

### 6. タイムアウトエラー

#### 症状
```
playwright._impl._api_types.TimeoutError: Timeout 30000ms exceeded.
```

#### 原因A: ネットワークが遅い

#### 解決方法
タイムアウトを延長

```python
page.goto(url, timeout=60000)  # 60秒
```

#### 原因B: Cloudflareチャレンジで待機

#### 解決方法
ページ読み込み後にチャレンジ完了を待機

```python
page.goto(url)

# チャレンジ待機
if "Just a moment" in page.content():
    for i in range(10):
        time.sleep(3)
        if page.title() != "Just a moment...":
            break
```

---

### 7. 証明書エラー

#### 症状
```
net::ERR_CERT_AUTHORITY_INVALID
```

#### 原因
プロキシ使用時に証明書検証が失敗

#### 解決方法
証明書エラーを無視

```python
args = [
    '--proxy-server=http://127.0.0.1:8910',
    '--ignore-certificate-errors',  # ← これを追加
]
```

---

### 8. 要素が見つからない

#### 症状
```python
button = page.locator("button:has-text('Login')")
button.click()  # → Error: locator.click: Target closed
```

#### 原因A: ページが読み込まれていない

#### 解決方法
```python
# 要素が表示されるまで待機
button.wait_for(state="visible", timeout=10000)
button.click()
```

#### 原因B: セレクタが間違っている

#### 解決方法
```python
# すべてのボタンを確認
buttons = page.locator("button").all()
for btn in buttons:
    print(btn.text_content())

# より具体的なセレクタを使用
button = page.locator("button[type='submit']")
```

---

## 🛠️ デバッグ方法

### 1. スクリーンショットで確認

```python
try:
    page.goto(url)
    page.screenshot(path="debug_screenshot.png")
except Exception as e:
    page.screenshot(path="error_screenshot.png")
    print(f"Error: {e}")
```

### 2. HTMLを保存して確認

```python
content = page.content()
with open("debug.html", "w") as f:
    f.write(content)
```

### 3. ログを有効化

```python
# 環境変数でログレベルを設定
import os
os.environ["DEBUG"] = "pw:api"

# または
with sync_playwright() as p:
    browser = p.chromium.launch(
        headless=True,
        slow_mo=1000,  # 操作を1秒遅延（デバッグ用）
    )
```

### 4. ヘッドフルモードで実行

```python
# GUIで動作確認（Claude Code Web環境では不可）
browser = p.chromium.launch(
    headless=False,  # GUIモード
    args=[...]
)
```

---

## 📋 チェックリスト

問題が発生したら以下を確認してください：

### 基本設定
- [ ] Chromiumがインストールされている (`playwright install chromium`)
- [ ] 必須フラグが設定されている (`--disable-dev-shm-usage`, `--single-process`)
- [ ] `pyproject.toml` に playwright が追加されている

### プロキシ使用時
- [ ] `HTTPS_PROXY` 環境変数が設定されている
- [ ] proxy.py が起動している
- [ ] `--ignore-certificate-errors` フラグが設定されている
- [ ] ポート番号が正しい

### Cloudflare回避
- [ ] `--disable-blink-features=AutomationControlled` が設定されている
- [ ] JavaScriptインジェクションが実行されている
- [ ] チャレンジ完了の待機処理がある
- [ ] User Agentが設定されている

### セッション永続化
- [ ] `launch_persistent_context()` を使用している
- [ ] `user_data_dir` が指定されている
- [ ] ディレクトリの書き込み権限がある

---

## 💡 ベストプラクティス

### 1. エラーハンドリングを実装

```python
try:
    page.goto(url, timeout=30000)
except Exception as e:
    print(f"Error: {e}")
    page.screenshot(path="error.png")
    raise
```

### 2. プロキシの終了処理を確実に

```python
proxy_process = None
try:
    proxy_process = subprocess.Popen([...])
    # 処理
finally:
    if proxy_process:
        proxy_process.terminate()
        proxy_process.wait(timeout=5)
```

### 3. 適度に待機する

```python
# ページ遷移後
page.goto(url)
time.sleep(2)  # Cloudflareチャレンジ開始を待つ

# 要素操作前
element.wait_for(state="visible")
```

### 4. リトライロジックを実装

```python
for attempt in range(3):
    try:
        page.goto(url, timeout=30000)
        break
    except Exception as e:
        if attempt == 2:
            raise
        print(f"Retry {attempt + 1}/3...")
        time.sleep(5)
```

---

## 🔍 さらに詳しい情報

- README.md: 基本的な使い方
- samples/: 実用的なサンプルコード
- [Playwright公式ドキュメント](https://playwright.dev/python/)

---

問題が解決しない場合は、エラーメッセージとスクリーンショットを確認してください。
