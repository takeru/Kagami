#!/usr/bin/env python3
"""PR #21の調査結果から2つのissueを作成"""
import os
from github import Github, Auth

def create_issue_1(repo):
    """playwright-mcp + Firefoxのブラウザインストール問題"""
    title = "playwright-mcp + Firefox: ブラウザが見つからない問題の解決"

    body = """## 🐛 問題の概要

PR #21の調査中に発見された、`npx @playwright/mcp` でFirefoxが認識されない問題を解決する。

参照: https://github.com/takeru/Kagami/pull/21

## 📋 現状

### テスト結果

以下のテストでブラウザインストールエラーが発生：

- **テスト3**: playwright-mcp + firefox + python mcp client
- **テスト4**: playwright-mcp + firefox + claude code mcp client

```
Error: Browser specified in your config is not installed.
Either install it (likely) or change the config.
```

### 試したこと

- `npx playwright install firefox` を実行 → 失敗
- `playwright install-deps firefox` を実行 → 権限の問題で失敗

### 推測される原因

- `npx @playwright/mcp` は独立したNode.jsパッケージ
- `uv run playwright install firefox` でインストールしたFirefoxとは別管理
- パスや環境変数の問題でブラウザが見つからない可能性

## 🎯 目標

playwright-mcpサーバーでFirefoxを正常に起動できるようにする。

## 📝 調査すべき項目

1. **Node.js版Playwrightのブラウザインストール状況**
   ```bash
   npx playwright install firefox
   npx playwright install-deps firefox
   ```

2. **ブラウザパスの確認**
   - Python Playwright: `playwright._impl._driver.compute_driver_executable()`
   - Node.js Playwright: `npx playwright --version`

3. **環境変数の確認**
   - `PLAYWRIGHT_BROWSERS_PATH`
   - ブラウザの実際のインストールパス

4. **MCP設定の確認**
   - `.mcp/playwright-firefox-config.json`
   - 正しいブラウザパスが指定されているか

## 📊 期待される結果

この問題が解決できれば：

✅ Python MCPクライアント経由でFirefoxが起動できる
✅ Claude Code MCP経由でFirefoxが起動できる
✅ PR #21のテスト3・4を完全に実行できる
✅ proxy.pyの必要性を実際のMCP環境で検証できる

## 🔗 関連ファイル

- `investigation/playwright/test_03_mcp_with_python_client.py`
- `investigation/playwright/FIREFOX_PROXY_INVESTIGATION_REPORT.md`
- `.mcp/playwright-firefox-config.json`
- `.mcp.json`

## 💡 参考情報

- [Playwright installation docs](https://playwright.dev/docs/browsers)
- [playwright-mcp GitHub](https://github.com/microsoft/playwright-mcp)
"""

    issue = repo.create_issue(
        title=title,
        body=body,
        labels=["bug", "investigation", "mcp", "firefox"]
    )

    return issue


def create_issue_2(repo):
    """extraHTTPHeaders方式のMCP実装"""
    title = "Firefox + MCP: extraHTTPHeaders方式でproxy.py不要の実装を調査"

    body = """## 🎯 目的

PR #21で発見された重要な知見を活用し、Firefox使用時にproxy.pyなしでMCPを動作させる方法を調査・実装する。

参照: https://github.com/takeru/Kagami/pull/21

## 💡 背景

### PR #21の重要な発見

Firefoxでは、Playwrightの `extraHTTPHeaders` 機能を使えば、proxy.pyなしでPreemptive Authenticationが可能：

```python
context = browser.new_context(
    extra_http_headers={
        "Proxy-Authorization": f"Basic {base64_encoded_auth}"
    }
)
```

**利点**:
- ✅ proxy.py不要
- ✅ シンプルな構成
- ✅ 追加のプロセス管理不要
- ✅ 直接プロキシに接続（レイテンシ削減）

**制限**:
- ❌ Firefoxのみ対応（Chromiumは「Unsafe header」制限あり）

## 📋 調査項目

### 1. playwright-mcpサーバーの現在の実装確認

- [ ] extraHTTPHeadersの設定がサポートされているか
- [ ] 設定ファイルでextraHTTPHeadersを指定できるか
- [ ] ソースコードを確認（実装状況を把握）

### 2. 実装方法の検討

**Option A**: 既存のMCPサーバーが対応済み

設定ファイルに追加するだけで動作：
```json
{
  "browser": "firefox",
  "extraHTTPHeaders": {
    "Proxy-Authorization": "Basic ..."
  }
}
```

**Option B**: MCPサーバーの改造が必要

- フォークして機能追加
- プルリクエストを上流に送る
- または独自ビルド版を維持

**Option C**: カスタムMCPサーバーを実装

- Playwrightを直接使用
- 必要最小限の機能のみ実装
- よりシンプルな構成

### 3. 認証情報の取り扱い

環境変数 `HTTPS_PROXY` から認証情報を抽出して設定：

```python
import os
import base64
from urllib.parse import urlparse

proxy_url = os.getenv("HTTPS_PROXY")
parsed = urlparse(proxy_url)
username = parsed.username
password = parsed.password

auth_b64 = base64.b64encode(f"{username}:{password}".encode()).decode()
```

セキュリティ考慮事項：
- 認証情報をログに出力しない
- 設定ファイルに平文で保存しない
- 環境変数経由で安全に渡す

## 🔬 検証計画

### Phase 1: 既存実装の調査

1. playwright-mcpのソースコードを確認
2. ドキュメントで設定オプションを調査
3. 実際に設定ファイルで試してみる

### Phase 2: 実装（必要な場合）

1. 最適なアプローチを選択（Option A/B/C）
2. 実装またはフォーク
3. テストスクリプトで動作確認

### Phase 3: 統合テスト

1. Python MCPクライアントでテスト
2. Claude Code MCPでテスト
3. proxy.py版と性能比較

## 📊 成功基準

以下が全て達成できたら成功：

- ✅ Firefoxでproxy.pyなしでMCPが動作
- ✅ JWT認証プロキシ経由で外部サイトにアクセス可能
- ✅ 設定が簡潔（proxy.py起動コマンドが不要）
- ✅ ドキュメント化（他の開発者が使える）

## 🔗 関連ファイル

- `investigation/playwright/test_07_extra_http_headers.py` - 動作確認済みの実装例
- `investigation/playwright/FIREFOX_PROXY_INVESTIGATION_REPORT.md` - 詳細レポート
- `.mcp/playwright-firefox-config.json` - 現在の設定
- `.mcp.json` - MCP設定

## 💡 参考情報

### Playwright APIドキュメント

- [Browser.new_context()](https://playwright.dev/python/docs/api/class-browser#browser-new-context)
- [extraHTTPHeaders option](https://playwright.dev/python/docs/api/class-browser#browser-new-context-option-extra-http-headers)

### 既存の動作確認済み実装

`investigation/playwright/test_07_extra_http_headers.py` に完全な動作例あり。

## 🚀 期待される効果

### ユーザー体験の向上

**現在**:
```json
{
  "command": "bash",
  "args": [
    "-c",
    "uv run proxy --hostname 127.0.0.1 --port 18911 ... & PROXY_PID=$!; trap \"kill $PROXY_PID\" EXIT; sleep 2; npx @playwright/mcp ..."
  ]
}
```
複雑なコマンド、プロセス管理が必要

**改善後（期待）**:
```json
{
  "command": "npx",
  "args": ["@playwright/mcp", "--config", ".mcp/playwright-firefox-config.json"]
}
```
シンプルで理解しやすい

### 技術的なメリット

1. **依存関係の削減**: proxy.py（Pythonパッケージ）が不要
2. **レイテンシの改善**: 中間プロキシを経由しない
3. **デバッグの簡易化**: プロセスが1つ減る
4. **メンテナンス性**: 設定がシンプル

## ⚠️ 注意事項

- この実装はFirefoxのみ対応
- Chromiumでは引き続きproxy.pyが必須
- Chromium/Firefox両対応が必要な場合は、現在のproxy.py方式を維持すべき
"""

    issue = repo.create_issue(
        title=title,
        body=body,
        labels=["enhancement", "investigation", "mcp", "firefox"]
    )

    return issue


def main():
    auth = Auth.Token(os.getenv("GITHUB_TOKEN"))
    g = Github(auth=auth)
    repo = g.get_repo("takeru/Kagami")

    print("Issue 1を作成中...")
    issue1 = create_issue_1(repo)
    print(f"✅ Issue #{issue1.number} 作成完了: {issue1.html_url}")
    print(f"   タイトル: {issue1.title}")

    print("\nIssue 2を作成中...")
    issue2 = create_issue_2(repo)
    print(f"✅ Issue #{issue2.number} 作成完了: {issue2.html_url}")
    print(f"   タイトル: {issue2.title}")

    print("\n" + "="*60)
    print("2つのissueを作成しました！")
    print("="*60)


if __name__ == "__main__":
    main()
