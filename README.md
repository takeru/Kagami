# Kagami

PyGithub を使用して GitHub API を操作するプロジェクトです。

## 機能

- Issue に自動的にコメントを追加
- Issue コメントのリアルタイム監視（新しいコメントを検出して表示）
- ETag ベースの効率的な polling でrate limit を節約
- GitHub API との統合
- Claude Code と組み合わせて適切な返信を生成

## セットアップ

1. 依存関係のインストール:
```bash
pip install -r requirements.txt
```

2. GitHub トークンの設定:
```bash
export GITHUB_TOKEN="your_github_token_here"
```

GitHub トークンは [GitHub Settings > Developer settings > Personal access tokens](https://github.com/settings/tokens) から作成できます。
必要な権限: `repo` (プライベートリポジトリの場合) または `public_repo` (パブリックリポジトリの場合)

## 使用方法

### Issue にコメントを追加

```bash
# 現在の git リポジトリの最初のオープン issue にコメントを追加
python add_issue_comment.py

# 特定のリポジトリの最初のオープン issue にコメントを追加
python add_issue_comment.py owner/repo

# 特定の issue にコメントを追加
python add_issue_comment.py owner/repo 123
```

### 例

```bash
# takeru/Kagami の issue #1 にコメントを追加
python add_issue_comment.py takeru/Kagami 1

# takeru/finmlz の最初のオープン issue にコメントを追加
python add_issue_comment.py takeru/finmlz
```

### Issue コメントを監視

新しいコメントを検出して内容を表示します。ETag ベースの polling でrate limit を節約します。

```bash
# 基本的な使用方法（30秒間隔でチェック）
python monitor_issues.py owner/repo issue_number

# チェック間隔を指定（10秒）
python monitor_issues.py owner/repo issue_number --interval 10

# 詳細情報を表示
python monitor_issues.py owner/repo issue_number --verbose
```

#### 監視の例

```bash
# takeru/Kagami の issue #3 を監視
python monitor_issues.py takeru/Kagami 3

# 10秒間隔で監視
python monitor_issues.py takeru/Kagami 3 --interval 10
```

#### 監視の仕組み

- **ETag ベースの polling**: 変更がない場合はrate limit を消費しない
- **コメント検出**: 新しいコメントを検出すると内容を標準出力に表示
- **自分のコメントは無視**: 自分のコメントには反応しない
- **Rate limit 監視**: 定期的にrate limit の状態を表示
- **Ctrl+C で停止**: 安全に監視を停止できる

#### ワークフロー

1. `monitor_issues.py` を起動してissueを監視
2. 新しいコメントが投稿されると、その内容が標準出力に表示される
3. Claude Code（あなた）がコメント内容を確認
4. 適切な返信を考えて `add_issue_comment.py` で投稿

この仕組みにより、Claude が文脈を理解して適切に返信できます。

## PyGithub の基本的な使い方

```python
import os
from github import Github, Auth

# 認証（新しい Auth API を使用）
auth = Auth.Token(os.getenv("GITHUB_TOKEN"))
g = Github(auth=auth)

# リポジトリの取得
repo = g.get_repo("owner/repo")

# Issue の取得
issues = repo.get_issues(state="open")
issue = repo.get_issue(number=123)

# Pull Request の取得
pulls = repo.get_pulls(state="open")
pr = repo.get_pull(number=456)

# コメントの追加
issue.create_comment("これは自動コメントです！")
```

## 参考資料

- [PyGithub Documentation](https://pygithub.readthedocs.io/)
- [PyGithub Pull Request Examples](https://pygithub.readthedocs.io/en/stable/examples/PullRequest.html)
- [PyGithub Issue Examples](https://pygithub.readthedocs.io/en/stable/examples/Issue.html)