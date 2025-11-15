# Python版 vs Node.js版 Playwright の違い

## 🔍 なぜtest_10（Python版）はHOME=/rootで動いたのか？

### 観察された現象

- **test_10（Python版Playwright直接使用）**: ✅ `HOME=/root` で動作
- **test_17（Node.js版playwright-mcp使用）**: ❌ `HOME=/root` では動作せず、`HOME=/home/user` が必要

## 📊 Firefoxバイナリの探索方法の違い

### Python版Playwright

**パッケージ**:
```
.venv/lib/python3.11/site-packages/playwright/
```

**Firefoxバイナリの探索**:
- Playwrightライブラリが**自動的に標準的な場所**を探す
- デフォルト: `$HOME/.cache/ms-playwright/`
- 実行時のHOME環境変数: `/root`
- 探索先: `/root/.cache/ms-playwright/firefox-1495` ✅

**コード例（test_10）**:
```python
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.firefox.launch(
        headless=True,
        proxy={"server": server},
        firefox_user_prefs={...},
        env={**os.environ, "HOME": temp_home}  # ← Firefox起動後の環境変数
    )
```

**重要**: `env` パラメータはFirefox**プロセス起動後**の環境変数であり、Firefoxバイナリを探す場所ではない！

### Node.js版playwright-mcp

**パッケージ**:
```
/opt/node22/lib/node_modules/@playwright/mcp/
  └── node_modules/playwright@1.57.0-alpha
```

**Firefoxバイナリの探索**:
- Node.js Playwrightは**実行時のHOME環境変数**を使う
- `HOME=/root` → `/root/.cache/ms-playwright/` を探す
- `HOME=/home/user` → `/home/user/.cache/ms-playwright/` を探す

**コード例（test_17）**:
```bash
# ❌ これだとFirefoxが見つからない（HOME=/home/userで実行）
HOME=/home/user node /opt/node22/lib/node_modules/@playwright/mcp/cli.js

# 理由: /home/user/.cache/ms-playwright/ にFirefoxがない
```

**解決策**:
```bash
# 1. HOME=/home/userでFirefoxをインストール
HOME=/home/user node /opt/node22/lib/node_modules/@playwright/mcp/node_modules/playwright/cli.js install firefox

# 2. 同じHOME環境変数で実行
HOME=/home/user node /opt/node22/lib/node_modules/@playwright/mcp/cli.js
```

## 🗂️ Firefoxインストール先の確認

### 現在の状態

```bash
/root/.cache/ms-playwright/
├── chromium-1194/              # セットアップ時にインストール
├── firefox-1495/               # Python版Playwright用（test_10で使用）
└── firefox-1496/               # Node.js版@playwright/mcp用

/home/user/.cache/ms-playwright/
├── firefox-1495/               # HOME=/home/userでインストール
├── firefox-1496/               # HOME=/home/userでインストール（test_17で使用）
└── mcp-firefox/                # その他
```

## 📝 実行環境の違い

### test_10（Python版）の実行環境

```bash
$ uv run python investigation/playwright/test_10_firefox_extra_headers_real_proxy.py

# 内部的に:
# - HOME=/root（デフォルト）
# - Pythonのplaywrightパッケージを使用
# - Firefoxバイナリ: /root/.cache/ms-playwright/firefox-1495
# - 結果: ✅ 成功
```

### test_17（Node.js版）の実行環境

```bash
$ uv run python investigation/playwright/test_17_mcp_with_cli_direct.py

# test_17内で実行されるコマンド:
server_params = StdioServerParameters(
    command="bash",
    args=["-c", "... node /opt/node22/lib/node_modules/@playwright/mcp/cli.js ..."],
    env={**os.environ, "HOME": "/home/user"}  # ← これが重要！
)

# 内部的に:
# - HOME=/home/user（明示的に設定）
# - Node.js版playwright-mcpを使用
# - Firefoxバイナリ: /home/user/.cache/ms-playwright/firefox-1496
# - 結果: ✅ 成功（HOME=/home/userでFirefoxをインストール済みの場合）
```

## ⚙️ MCP設定での注意点

### .mcp/start_playwright_mcp_firefox.py

```python
def main():
    # 環境変数を準備（HOMEを含める）
    env = os.environ.copy()
    # デフォルトでHOME環境変数を継承
    # 実行時のHOMEが /root なら /root/.cache/ms-playwright/ を探す
    # 実行時のHOMEが /home/user なら /home/user/.cache/ms-playwright/ を探す

    # MCPサーバーを起動（stdioモード）
    subprocess.run(cmd, check=False, env=env)
```

**MCP実行時のHOME**:
```bash
# Python MCPクライアントから実行する場合
server_params = StdioServerParameters(
    command="uv",
    args=["run", "python", ".mcp/start_playwright_mcp_firefox.py"],
    env={
        **os.environ,
        "HOME": "/home/user"  # ← これを設定！
    }
)
```

## 🎯 推奨セットアップ

### オプション1: HOME=/home/user で統一（推奨）

**理由**:
- MCPサーバー実行時のHOMEと一致
- パーミッションの問題を回避

**手順**:
```bash
# 1. @playwright/mcpをインストール
npm install -g @playwright/mcp

# 2. HOME=/home/userでFirefoxをインストール
HOME=/home/user node /opt/node22/lib/node_modules/@playwright/mcp/node_modules/playwright/cli.js install firefox

# 3. MCPサーバー起動時にHOME=/home/userを設定
env={"HOME": "/home/user"}
```

### オプション2: HOME=/root で統一

**理由**:
- デフォルト環境
- セットアップスクリプトでインストール済み

**手順**:
```bash
# 1. すでにインストール済み
ls /root/.cache/ms-playwright/firefox-1496

# 2. MCPサーバー起動時にHOME=/rootを設定（またはデフォルト）
env={"HOME": "/root"}  # または省略
```

**問題**: パーミッションやセキュリティの観点から `/home/user` の方が推奨

## 🔍 デバッグ方法

### Firefoxバイナリが見つからない場合

```bash
# 1. 実行時のHOMEを確認
echo $HOME

# 2. そのHOMEでFirefoxがインストールされているか確認
ls -la $HOME/.cache/ms-playwright/

# 3. もしなければ、そのHOMEでインストール
HOME=$HOME node /opt/node22/lib/node_modules/@playwright/mcp/node_modules/playwright/cli.js install firefox
```

### 実行時のHOME環境変数を確認

```python
# Python MCPクライアント側
import os
print(f"Client HOME: {os.getenv('HOME')}")

# server_params でHOMEを明示的に設定
server_params = StdioServerParameters(
    command="bash",
    args=["-c", "echo HOME=$HOME; ..."],  # デバッグ用
    env={**os.environ, "HOME": "/home/user"}
)
```

## 📚 まとめ

| 項目 | Python版Playwright | Node.js版playwright-mcp |
|------|-------------------|------------------------|
| **パッケージ** | `.venv/lib/.../playwright/` | `/opt/node22/lib/.../playwright/` |
| **Firefoxバイナリ探索** | 自動的に標準パスを探す | HOME環境変数を使う |
| **HOME依存** | 低い（デフォルトパスを使う） | 高い（HOMEに依存） |
| **test_10での動作** | ✅ HOME=/rootで動作 | - |
| **test_17での動作** | - | ✅ HOME=/home/userで動作 |
| **推奨インストール先** | `/root/.cache/ms-playwright/` | `/home/user/.cache/ms-playwright/` |

**重要**: MCP経由で使う場合、**HOME環境変数とFirefoxインストール先を一致させる**ことが重要！
