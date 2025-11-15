# 現状と推奨される使用方法

## ✅ 問題解決済み（2025-11-15更新）

### playwright-mcpでのプロファイル指定方法が判明

`@playwright/mcp@0.0.47`でFirefoxプロファイルを正しく指定する方法がわかりました。

**解決策:**
- 設定ファイルで`browser.userDataDir`を使用する
- `args: ["-profile", ...]`ではなく、`userDataDir`パラメータを使う
- → CA証明書インポート済みプロファイルが正しく使用される
- → 証明書エラーなしで成功！

**正しい設定例（playwright-firefox-config.json）:**
```json
{
  "browser": {
    "browserName": "firefox",
    "userDataDir": "/home/user/firefox-profile",
    "launchOptions": {
      "headless": true,
      "firefoxUserPrefs": {...}
    }
  }
}
```

## ✅ 推奨される方法（2つの選択肢）

### 方法1: playwright-mcp経由（推奨）

**成功例: example.py**

```bash
HOME=/home/user uv run python playwright_mcp_claude_code_web/example.py
```

**成功の理由:**
- 正しい設定ファイル（`browser.userDataDir`を使用）
- CA証明書インポート済みプロファイルが正しく使用される
- proxy.py経由でJWT認証を処理
- → 証明書エラーなしで成功！

**コードの要点:**
```python
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

server_params = StdioServerParameters(
    command="node",
    args=[
        "/opt/node22/lib/node_modules/@playwright/mcp/cli.js",
        "--config", "playwright_mcp_claude_code_web/playwright-firefox-config.json",
        "--browser", "firefox",
        "--proxy-server", "http://127.0.0.1:18915"
    ],
    env={**os.environ, "HOME": "/home/user"}
)

async with stdio_client(server_params) as (read, write):
    async with ClientSession(read, write) as session:
        await session.initialize()
        await session.call_tool("browser_navigate", arguments={"url": "..."})
```

### 方法2: Playwright APIを直接使用

**成功例: test_24_firefox_profile_with_proxy_py.py**

```bash
HOME=/home/user uv run python investigation/playwright/test_24_firefox_profile_with_proxy_py.py
```

**成功の理由:**
- `launch_persistent_context`でプロファイルを指定
- CA証明書インポート済みプロファイルが正しく使用される
- proxy.py経由でJWT認証を処理
- → 証明書エラーなしで成功！

**コードの要点:**
```python
from playwright.async_api import async_playwright

async with async_playwright() as p:
    context = await p.firefox.launch_persistent_context(
        user_data_dir="/home/user/firefox-profile",  # ← プロファイル指定
        executable_path="/home/user/.cache/ms-playwright/firefox-1496/firefox/firefox",
        proxy={"server": "http://127.0.0.1:18915"},  # ← proxy.py経由
        headless=True,
        ...
    )
```

## 📊 方法の比較

| 方法 | 証明書エラー | JWT認証 | MCP対応 | 推奨度 |
|------|------------|---------|---------|--------|
| **playwright-mcp経由** | ✅ なし | ✅ proxy.py経由 | ✅ あり | ⭐⭐⭐ 推奨 |
| Playwright API直接 | ✅ なし | ✅ proxy.py経由 | ❌ なし | ⭐⭐ 代替手段 |

**両方とも正常動作します！** MCPプロトコルを使用したい場合はplaywright-mcp経由を、より直接的な制御が必要な場合はPlaywright API直接をご利用ください。

## 🎯 このディレクトリの目的

このディレクトリ（`playwright_mcp_claude_code_web/`）は、playwright-mcpをClaude Code Web環境で使用するための完全なセットアップと動作サンプルを提供します。

**含まれるもの:**
- ✅ setup.sh: 環境セットアップスクリプト（完全動作）
- ✅ playwright-firefox-config.json: Firefox設定（正しいuserDataDir設定）
- ✅ start_playwright_mcp.py: MCPサーバー起動スクリプト
- ✅ example.py: サンプルコード（**証明書エラーなしで完全動作**）
- ✅ test_setup.py: セットアップ検証テスト

## 💡 実際の使用方法

### 1. 初回セットアップ

```bash
# 環境をセットアップ（CA証明書インポート等）
HOME=/home/user bash playwright_mcp_claude_code_web/setup.sh
```

このセットアップにより:
- playwright-mcpがグローバルインストールされる
- Firefox build v1496がインストールされる
- Firefoxプロファイルが作成される
- CA証明書がインポートされる
- MCP設定ファイルが生成される

### 2. サンプルコードの実行（playwright-mcp経由）

```bash
# Yahoo! JAPANトピック取得サンプル
HOME=/home/user uv run python playwright_mcp_claude_code_web/example.py
```

### 3. 独自のMCPクライアントを作成する場合

`example.py`を参考にしてください:

```python
# 必要なインポート
import asyncio
import os
import subprocess
import time
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# 1. proxy.pyを起動
proxy_process = subprocess.Popen([
    "uv", "run", "proxy",
    "--hostname", "127.0.0.1",
    "--port", "18915",
    "--plugins", "proxy.plugin.proxy_pool.ProxyPoolPlugin",
    "--proxy-pool", os.environ['HTTPS_PROXY']
], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

time.sleep(2)

# 2. playwright-mcpサーバーに接続
server_params = StdioServerParameters(
    command="node",
    args=[
        "/opt/node22/lib/node_modules/@playwright/mcp/cli.js",
        "--config", "playwright_mcp_claude_code_web/playwright-firefox-config.json",
        "--browser", "firefox",
        "--proxy-server", "http://127.0.0.1:18915"
    ],
    env={**os.environ, "HOME": "/home/user"}
)

async with stdio_client(server_params) as (read, write):
    async with ClientSession(read, write) as session:
        await session.initialize()

        # 3. ページにアクセス
        await session.call_tool(
            "browser_navigate",
            arguments={"url": "https://www.yahoo.co.jp/"}
        )

        # 4. スナップショット取得
        result = await session.call_tool("browser_snapshot", arguments={})
        snapshot = result.content[0].text
        # ...
```

### 4. Playwright API直接を使用する場合

`investigation/playwright/test_24_firefox_profile_with_proxy_py.py`を参考にしてください。

## 🔮 今後の改善点

### より簡単な設定方法の検討

現在は以下の設定が必要です:

```json
{
  "browser": {
    "browserName": "firefox",
    "userDataDir": "/home/user/firefox-profile",
    "launchOptions": {...}
  }
}
```

将来的には、より簡潔な設定方法が提供される可能性があります。ただし、**現在の方法で完全に動作します**。

## 📚 参考リンク

- [CA証明書インポートガイド](../investigation/playwright/CA_CERTIFICATE_IMPORT_GUIDE.md)
- [test_24 完全動作版](../investigation/playwright/test_24_firefox_profile_with_proxy_py.py)
- [test_25 システム証明書ストア不要の検証](../investigation/playwright/test_25_verify_system_cert_not_needed.py)

## ✅ 結論

**現在の推奨方法:**
1. `setup.sh`でセットアップを完了させる
2. **playwright-mcp経由で使用する**（example.pyのアプローチ）
3. 必要に応じてPlaywright API直接も利用可能

**完全動作確認済み：**
- ✅ 証明書エラーなしでHTTPSサイトにアクセス可能
- ✅ Yahoo! JAPANなどの実サイトで動作確認済み
- ✅ MCPプロトコルによる統一的なインターフェース
- ✅ proxy.py経由でJWT認証を正しく処理
