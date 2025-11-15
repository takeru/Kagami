# 現状と推奨される使用方法

## ⚠️ 重要な制限事項

### playwright-mcpでのプロファイル指定の制限

現在の`@playwright/mcp@0.0.47`では、Firefoxプロファイルを指定する機能が十分にサポートされていません。

**問題:**
- 設定ファイルで`args: ["-profile", "/path/to/profile"]`を指定しても反映されない
- CA証明書をインポートしたプロファイルが使用されない
- → 証明書エラー（`SEC_ERROR_UNKNOWN_ISSUER`）が発生

## ✅ 推奨される方法

### Playwright APIを直接使用（完全動作版）

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

| 方法 | 証明書エラー | JWT認証 | 推奨度 |
|------|------------|---------|--------|
| **Playwright API直接** | ✅ なし | ✅ proxy.py経由 | ⭐⭐⭐ 推奨 |
| playwright-mcp経由 | ❌ あり | ✅ proxy.py経由 | ⚠️ 現状は非推奨 |
| playwright-mcp (将来) | ? | ✅ | 待機中 |

## 🎯 このディレクトリの目的

このディレクトリ（`playwright_mcp_claude_code_web/`）は、将来的にplaywright-mcpがプロファイル指定をサポートした際に、すぐに使えるようにセットアップと設定を準備しています。

**含まれるもの:**
- ✅ setup.sh: 環境セットアップスクリプト
- ✅ playwright-firefox-config.json: Firefox設定
- ✅ start_playwright_mcp.py: MCPサーバー起動スクリプト
- ⚠️ example.py: サンプルコード（現状は証明書エラーあり）

## 💡 実際の使用方法

### 1. セットアップは実行する

```bash
# 環境をセットアップ（CA証明書インポート等）
HOME=/home/user bash playwright_mcp_claude_code_web/setup.sh
```

このセットアップにより:
- Firefoxプロファイルが作成される
- CA証明書がインポートされる
- → **Playwright API直接使用時に必要**

### 2. 実際のアクセスはPlaywright API直接で

```bash
# 完全動作版を使用
HOME=/home/user uv run python investigation/playwright/test_24_firefox_profile_with_proxy_py.py
```

### 3. 独自のスクリプトを作成する場合

`test_24_firefox_profile_with_proxy_py.py`を参考にしてください:

```python
# 必要なインポート
import asyncio
import os
import signal
import subprocess
import time
from playwright.async_api import async_playwright

# 1. proxy.pyを起動
proxy_process = subprocess.Popen([
    "uv", "run", "proxy",
    "--hostname", "127.0.0.1",
    "--port", "18915",
    "--plugins", "proxy.plugin.proxy_pool.ProxyPoolPlugin",
    "--proxy-pool", os.environ['HTTPS_PROXY']
], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

time.sleep(2)

# 2. Playwright APIで起動
async with async_playwright() as p:
    context = await p.firefox.launch_persistent_context(
        user_data_dir="/home/user/firefox-profile",
        executable_path="/home/user/.cache/ms-playwright/firefox-1496/firefox/firefox",
        proxy={"server": "http://127.0.0.1:18915"},
        headless=True,
        firefox_user_prefs={
            "privacy.trackingprotection.enabled": False,
            "network.proxy.allow_hijacking_localhost": True,
            "security.cert_pinning.enforcement_level": 0,
            "security.OCSP.enabled": 0,
        },
        ignore_https_errors=True,
        bypass_csp=True
    )

    page = await context.new_page()
    await page.goto("https://www.yahoo.co.jp/")
    # ...
```

## 🔮 将来の展望

### playwright-mcpがプロファイル指定をサポートした場合

以下の設定で動作するようになる可能性があります:

```json
{
  "launchOptions": {
    "userDataDir": "/home/user/firefox-profile",
    ...
  }
}
```

または:

```json
{
  "launchOptions": {
    "args": ["-profile", "/home/user/firefox-profile"],
    ...
  }
}
```

そうなれば、`example.py`が正常に動作するようになります。

## 📚 参考リンク

- [CA証明書インポートガイド](../investigation/playwright/CA_CERTIFICATE_IMPORT_GUIDE.md)
- [test_24 完全動作版](../investigation/playwright/test_24_firefox_profile_with_proxy_py.py)
- [test_25 システム証明書ストア不要の検証](../investigation/playwright/test_25_verify_system_cert_not_needed.py)

## ✅ 結論

**現在の推奨方法:**
1. `setup.sh`でセットアップを完了させる
2. **Playwright APIを直接使用する**（test_24のアプローチ）
3. playwright-mcpの今後のアップデートを待つ

これにより、証明書エラーなしで確実にHTTPSサイトにアクセスできます！
