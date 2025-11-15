#!/usr/bin/env python3
"""
PRを作成または更新するスクリプト
"""
import os
from github import Github

# GitHub認証
g = Github(os.getenv("GITHUB_TOKEN"))
repo = g.get_repo("takeru/Kagami")

# ブランチ名
branch_name = "claude/investigate-firefox-proxy-setup-01HAG3wWnzGa6W7vKm9eh943"

# 既存のPRを確認
existing_prs = list(repo.get_pulls(state="open", head=f"takeru:{branch_name}"))

# PRのタイトルと本文
pr_title = "重大な発見：FirefoxではProxy.pyなしでPreemptive Authが可能"

pr_body = """## 🎯 調査の目的

PR #16のコメントで「Firefoxでもproxy.pyが必須」と主張されていましたが、本当にそうなのか検証しました。

参照：https://github.com/takeru/Kagami/pull/16#issuecomment-3534991995

## 🔬 調査内容

以下の組み合わせでproxy.pyの必要性を検証：

1. **playwright + firefox（proxy.pyなし）**
2. **playwright + firefox（proxy.pyあり）**
3. **playwright-mcp + firefox + python mcp client**
4. **playwright-mcp + firefox + claude code mcp client**

さらに、proxy.pyなしでPreemptive Authenticationを実現する方法を追加調査：

5. **Playwright username/password設定**
6. **Firefox network prefs設定**
7. **page.route()でヘッダー注入**
8. **extraHTTPHeadersでヘッダー設定**

## 🎉 重大な発見

### ✅ Firefoxではproxy.pyは不要！

以下の2つの方法でproxy.pyなしでもPreemptive Authenticationが可能：

#### 方法1: `extraHTTPHeaders` を使う（推奨）⭐⭐

```python
context = browser.new_context(
    extra_http_headers={
        "Proxy-Authorization": f"Basic {base64_encoded_auth}"
    }
)
```

**利点**：
- 最もシンプル
- コンテキスト作成時に1回設定するだけ
- すべてのページに自動適用

#### 方法2: `page.route()` でヘッダー注入⭐

```python
def handle_route(route, request):
    headers = request.headers
    headers["Proxy-Authorization"] = f"Basic {auth_b64}"
    route.continue_(headers=headers)

page.route("**/*", handle_route)
```

**利点**：
- より柔軟な制御が可能

### ❌ Chromiumではproxy.pyが必須

- `Proxy-Authorization` が「Unsafe header」扱い
- セキュリティ上の理由でPlaywrightからの設定を拒否
- `extraHTTPHeaders` → `ERR_INVALID_ARGUMENT`
- `route()` → `Unsafe header` エラー

## 📊 全テスト結果

| テストケース | Firefox | Chromium |
|------------|---------|----------|
| **直接プロキシ接続** | ❌ | ❌ |
| **proxy.py経由** | ✅ | ✅ |
| **username/password設定** | ❌ | ❌ |
| **page.route()** | ✅ | ❌ |
| **extraHTTPHeaders** | ✅ | ❌ |

## 📝 作成したファイル

### テストスクリプト

- `investigation/playwright/test_01_firefox_direct_proxy.py` - proxy.pyなしのテスト（失敗を確認）
- `investigation/playwright/test_02_firefox_with_proxy_py.py` - proxy.pyありのテスト（成功を確認）
- `investigation/playwright/test_03_mcp_with_python_client.py` - MCPサーバーテスト
- `investigation/playwright/test_04_firefox_preemptive_auth.py` - 基本的なアプローチをテスト
- `investigation/playwright/test_05_route_header_injection.py` - route()方式（Firefox成功）
- `investigation/playwright/test_06_route_chromium.py` - route()方式（Chromium失敗）
- `investigation/playwright/test_07_extra_http_headers.py` - extraHTTPHeaders方式

### ドキュメント

- `investigation/playwright/FIREFOX_PROXY_INVESTIGATION_REPORT.md` - 詳細な調査レポート

### 設定更新

- `CLAUDE.md` - Gitコミットに関する注意事項を追加
- `.gitignore` - スクリーンショットとHTMLファイルを除外

## 🎯 結論

### PR #16コメントの主張について

**元の主張**：
> "ブラウザの種類に関わらず、JWT認証プロキシ使用時にはproxy.pyが技術的に必須"

**調査結果**：⚠️ **部分的に正しい**

- **Chromiumの場合**：✅ 正しい（proxy.pyが必須）
- **Firefoxの場合**：❌ 間違い（proxy.pyなしでも可能）

### より正確な結論

> "Chromiumでは proxy.py が必須。Firefoxでは proxy.py なしでも extraHTTPHeaders / route() で実現可能"

## 💡 推奨事項

### 現在の実装を維持する場合（推奨）

proxy.pyを使用する現在の実装は、Chromium/Firefox両方で動作するため、そのまま維持することを推奨します。

### Firefoxのみ使う場合は簡略化可能

- `extraHTTPHeaders` でproxy.py不要
- よりシンプルな構成
- レイテンシが若干改善

## 📖 詳細レポート

すべての詳細は以下のレポートを参照してください：

`investigation/playwright/FIREFOX_PROXY_INVESTIGATION_REPORT.md`
"""

if existing_prs:
    # PRが既に存在する場合は更新
    pr = existing_prs[0]
    pr.edit(title=pr_title, body=pr_body)
    print(f"✅ PRを更新しました: {pr.html_url}")
    print(f"PR番号: #{pr.number}")
else:
    # 新しいPRを作成
    # ベースブランチを取得（mainまたはmaster）
    try:
        base_branch = repo.default_branch
    except:
        base_branch = "main"

    pr = repo.create_pull(
        title=pr_title,
        body=pr_body,
        head=branch_name,
        base=base_branch
    )
    print(f"✅ 新しいPRを作成しました: {pr.html_url}")
    print(f"PR番号: #{pr.number}")
