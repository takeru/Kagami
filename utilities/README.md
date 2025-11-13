# Utilities

このディレクトリには、GitHub操作などのユーティリティスクリプトが含まれています。

## スクリプト一覧

### create_pr.py
プルリクエストを作成するためのスクリプトです。

```bash
uv run python utilities/create_pr.py
```

### merge_pr.py
プルリクエストをマージするためのスクリプトです。

```bash
uv run python utilities/merge_pr.py
```

## 使用方法

これらのスクリプトはPyGitHubを使用してGitHub APIを操作します。
GITHUB_TOKEN環境変数が設定されている必要があります。

詳細は各スクリプトのコメントを参照してください。
