# Claude Code Webの環境での注意事項

CLAUDE_CODE_REMOTE 環境変数が設定されているかどうかで、Claude Code Webの環境かどうかを判断します。

```
if [ -n "$CLAUDE_CODE_REMOTE" ]; then echo "Claude Code Webです"; else echo "Claude Code Webではありません"; fi
```

## 環境セットアップ

pythonの実行をするまえに、.claude/claude_code_web_setup.sh を実行することで、環境セットアップを行うようにしてください。

```bash
./.claude/claude_code_web_setup.sh
```

"setup script completed" が出力されていれば成功です。
失敗した場合は、スクリプトを参考に、submoduleと.venvを手動でセットアップしてください。


## pythonの実行（セットアップが完了している場合）

```bash
uv run python src/package/path/to/script.py
```

```bash
uv run pytest tests
```

# Github操作

PyGithubを使用してGithub APIを操作することができます。

https://pygithub.readthedocs.io/en/stable/examples/PullRequest.html
https://pygithub.readthedocs.io/en/stable/examples/Issue.html

```python
import os
from github import Github
from github.PullRequest import PullRequest
from github.Issue import Issue

g = Github(os.getenv("GITHUB_TOKEN"))
repo = g.get_repo("user/repo")

issues = repo.get_issues(state="open")
issue = issues.get(number=123)

pulls = repo.get_pulls(state="open")
pr = repo.get_pull(number=456)
```
