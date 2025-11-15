# HOME=/home/user 環境でのFirefoxセットアップ手順

## 概要

playwright-mcpでFirefoxを使用する際、HOMEディレクトリの設定が重要です。
この手順書では、HOME=/home/userでFirefoxを正しくインストールし、MCPから利用できるようにする方法を説明します。

## 問題の背景

### 問題
- デフォルトのHOMEは `/root`
- Firefoxを通常の方法でインストールすると `/root/.cache/ms-playwright/` にインストールされる
- MCP実行時にHOME=/home/userを設定すると、Firefoxが見つからない

### 解決策
- **HOME=/home/user を明示的に指定してFirefoxをインストール**
- これにより `/home/user/.cache/ms-playwright/` にFirefoxがインストールされる

## 📋 セットアップ手順

### ステップ1: 環境確認

```bash
# 現在のHOMEを確認
echo "Current HOME: $HOME"

# 既存のFirefoxインストールを確認
ls -la /root/.cache/ms-playwright/ 2>/dev/null || echo "No Firefox in /root"
ls -la /home/user/.cache/ms-playwright/ 2>/dev/null || echo "No Firefox in /home/user"
```

### ステップ2: @playwright/mcpをグローバルインストール

```bash
npm install -g @playwright/mcp
```

**確認:**
```bash
npm list -g @playwright/mcp
# 出力例: @playwright/mcp@0.0.47
```

### ステップ3: HOME=/home/userでFirefoxをインストール

#### 3-1. 通常のPlaywright用Firefox (build v1495)

```bash
HOME=/home/user npx playwright install firefox
```

**期待される出力:**
```
Downloading Firefox 142.0.1 (playwright build v1495) from ...
Firefox 142.0.1 (playwright build v1495) downloaded to /home/user/.cache/ms-playwright/firefox-1495
```

#### 3-2. @playwright/mcp内蔵のPlaywright用Firefox (build v1496)

```bash
HOME=/home/user node /opt/node22/lib/node_modules/@playwright/mcp/node_modules/playwright/cli.js install firefox
```

**期待される出力:**
```
Downloading Firefox 142.0.1 (playwright build v1496) from ...
Firefox 142.0.1 (playwright build v1496) downloaded to /home/user/.cache/ms-playwright/firefox-1496
```

### ステップ4: インストール確認

```bash
ls -la /home/user/.cache/ms-playwright/
```

**期待される出力:**
```
drwxr-xr-x 3 root root 4096 Nov 15 06:07 firefox-1495
drwxr-xr-x 3 root root 4096 Nov 15 06:07 firefox-1496
```

## 🔧 MCP設定

### .mcp/start_playwright_mcp_firefox.py の重要な設定

#### ポイント1: グローバルcli.jsを直接使用

```python
# ❌ これだと毎回npxがダウンロードして実行するためFirefoxが見つからない
cmd = ['npx', '@playwright/mcp@latest', '--config', temp_config, '--browser', 'firefox']

# ✅ グローバルインストール版を直接使用
cmd = [
    'node',
    '/opt/node22/lib/node_modules/@playwright/mcp/cli.js',
    '--config', temp_config,
    '--browser', 'firefox'
]
```

#### ポイント2: HOMEを明示的に設定

```python
# MCPサーバー起動時の環境変数
env = os.environ.copy()
# HOMEはデフォルトで継承されるが、必要に応じて明示的に設定
# env['HOME'] = '/home/user'  # 通常は不要
```

## 🧪 動作確認テスト

### テスト1: proxy.py方式でMCP接続

```bash
uv run python investigation/playwright/test_17_mcp_with_cli_direct.py
```

**期待される結果:**
- ✅ MCPサーバーに接続
- ✅ Firefoxが起動
- ⚠ 証明書エラーページが表示される（予期した動作）

### テスト2: 証明書エラーページで「Advanced」をクリック

```bash
uv run python investigation/playwright/test_20_click_advanced.py
```

**期待される結果:**
- ✅ 「Advanced」ボタンをクリック成功
- ✅ 「Accept the Risk and Continue」ボタンが表示される

## 📊 インストールバージョンの対応表

| Playwrightバージョン | Firefoxビルド | インストール先 |
|---------------------|--------------|-------------|
| v1.56.1 (通常) | v1495 | `/home/user/.cache/ms-playwright/firefox-1495` |
| v1.57.0-alpha (@playwright/mcp内蔵) | v1496 | `/home/user/.cache/ms-playwright/firefox-1496` |

**重要**: @playwright/mcp@0.0.47 はv1.57.0-alphaを使用するため、**Firefox build v1496が必要**です。

## ⚠️ トラブルシューティング

### 問題1: "Browser specified in your config is not installed"

**原因**: HOMEディレクトリが一致していない

**解決策**:
```bash
# 現在のHOMEを確認
echo $HOME

# HOME=/home/userでFirefoxを再インストール
HOME=/home/user node /opt/node22/lib/node_modules/@playwright/mcp/node_modules/playwright/cli.js install firefox
```

### 問題2: npx @playwright/mcp@latestでFirefoxが見つからない

**原因**: npxが毎回新しくパッケージをダウンロードして実行するため

**解決策**: グローバルインストール版のcli.jsを直接使用（上記参照）

### 問題3: 証明書エラーが表示される

**原因**: プロキシのCA証明書が信頼されていない

**CA証明書の場所**:
```bash
# プロキシのCA証明書
ls -la /usr/local/share/ca-certificates/swp-ca-staging.crt

# 発行者: Anthropic sandbox-egress-staging TLS Inspection CA
openssl x509 -in /usr/local/share/ca-certificates/swp-ca-staging.crt -text -noout
```

**現在の回避策**:
1. 手動で「Advanced」→「Accept the Risk and Continue」をクリック
2. または、test_10のようにPlaywrightを直接使用（MCPなし）

## 🔍 検証コマンド

### 完全な検証スクリプト

```bash
#!/bin/bash
set -e

echo "=== Firefox インストール検証 ==="

# 1. HOMEを確認
echo "Current HOME: $HOME"

# 2. @playwright/mcpのインストール確認
echo -e "\n@playwright/mcp version:"
npm list -g @playwright/mcp | grep @playwright/mcp

# 3. Firefox build v1496のインストール
echo -e "\nInstalling Firefox build v1496..."
HOME=/home/user node /opt/node22/lib/node_modules/@playwright/mcp/node_modules/playwright/cli.js install firefox

# 4. インストール確認
echo -e "\nInstalled Firefox browsers:"
ls -la /home/user/.cache/ms-playwright/

# 5. cli.jsの存在確認
echo -e "\ncli.js location:"
ls -la /opt/node22/lib/node_modules/@playwright/mcp/cli.js

echo -e "\n✅ Setup complete!"
echo -e "\nNext steps:"
echo "  1. Run test: uv run python investigation/playwright/test_17_mcp_with_cli_direct.py"
echo "  2. Expected: Firefox starts, certificate error page appears"
```

保存して実行:
```bash
chmod +x verify_firefox_setup.sh
./verify_firefox_setup.sh
```

## 📝 まとめ

### 重要なポイント

1. **HOME=/home/user を明示的に指定** してFirefoxをインストール
2. **@playwright/mcp内蔵のPlaywright用にFirefox build v1496をインストール**
3. **グローバルインストールのcli.jsを直接使用** (npxではなく)
4. **証明書エラーは既知の問題** （回避策あり）

### 成功の確認方法

```bash
# テスト実行
uv run python investigation/playwright/test_17_mcp_with_cli_direct.py

# 期待される出力:
# ✅ MCPサーバーに接続
# ✅ example.comにナビゲート中...
# ⚠ 証明書エラーページ表示（これは正常）
```

## 参考資料

- [test_17_mcp_with_cli_direct.py](./test_17_mcp_with_cli_direct.py) - proxy.py + cli.js直接使用
- [test_20_click_advanced.py](./test_20_click_advanced.py) - 証明書エラーページの操作
- [.mcp/start_playwright_mcp_firefox.py](../../.mcp/start_playwright_mcp_firefox.py) - MCPサーバー起動スクリプト
- [.mcp/playwright-firefox-config.json](../../.mcp/playwright-firefox-config.json) - Firefox設定ファイル
