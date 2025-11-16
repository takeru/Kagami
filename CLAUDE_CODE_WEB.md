# Notes for Claude Code Web Environment

Determine if this is Claude Code Web environment by checking if the CLAUDE_CODE_REMOTE environment variable is set.

```
if [ -n "$CLAUDE_CODE_REMOTE" ]; then echo "This is Claude Code Web"; else echo "This is not Claude Code Web"; fi
```

## Log Files

Detailed logs for Claude Code Web are saved in the following location:

```
/tmp/claude-code.log
```

If you need to check errors or MCP server startup status, please refer to this log file.

## Environment Setup

Before executing Python code, run .claude/claude_code_web_setup.sh to perform environment setup.

```bash
./.claude/claude_code_web_setup.sh
```

If "setup script completed" is output, it was successful.
If it fails, refer to the script and manually set up the submodule and .venv.


## Executing Python (after setup is completed)

```bash
uv run python src/package/path/to/script.py
```

**PEP 723 compliant scripts:**
```bash
uv run script.py  # if script.py has PEP 723 metadata
```

## GitHub Operations

**The `gh` command is NOT available in Claude Code Web environment.**

Use PyGithub instead for GitHub operations:

```python
import os
from github import Github, Auth

# Authenticate using GITHUB_TOKEN from environment
token = os.getenv('GITHUB_TOKEN')
auth = Auth.Token(token)
g = Github(auth=auth)

# Get repository
repo = g.get_repo("owner/repo")
```

### Issue Operations

```python
# Create Issue
issue = repo.create_issue(
    title="Issue title",
    body="Issue description\n\nDetails here..."
)
print(f"Created issue #{issue.number}: {issue.html_url}")

# Update Issue
issue.edit(
    title="Updated title",
    body="Updated description",
    state="open"  # or "closed"
)

# Add comment to Issue
comment = issue.create_comment("This is a comment on the issue.")
print(f"Added comment ID: {comment.id}")

# Get Issue comments
comments = issue.get_comments()
for c in comments:
    print(f"{c.user.login}: {c.body}")

# Close Issue
issue.edit(state="closed")
```

### Pull Request Operations

```python
# Create Pull Request
pr = repo.create_pull(
    title="PR title",
    body="PR description\n\n## Changes\n- Change 1\n- Change 2",
    head="feature-branch",  # source branch
    base="main"             # target branch
)
print(f"Created PR #{pr.number}: {pr.html_url}")

# Update Pull Request
pr.edit(
    title="Updated PR title",
    body="Updated PR description"
)

# Add comment to PR (issue comment)
comment = pr.create_issue_comment("This is a general comment on the PR.")
print(f"Added comment ID: {comment.id}")

# Get PR comments (issue comments)
comments = pr.get_issue_comments()
for c in comments:
    print(f"{c.user.login}: {c.body}")

# Get PR review comments (code-level comments)
review_comments = pr.get_review_comments()
for rc in review_comments:
    print(f"{rc.user.login} on {rc.path}:{rc.line}: {rc.body}")

# Close PR
pr.edit(state="closed")

# Merge PR
pr.merge(
    commit_message="Merge pull request",
    merge_method="squash"  # or "merge", "rebase"
)
```

### Getting Existing Issues/PRs

```python
# Get specific issue by number
issue = repo.get_issue(number=123)

# Get specific PR by number
pr = repo.get_pull(number=456)

# List all open issues
issues = repo.get_issues(state="open")
for issue in issues:
    print(f"#{issue.number}: {issue.title}")

# List all open PRs
prs = repo.get_pulls(state="open")
for pr in prs:
    print(f"#{pr.number}: {pr.title}")
```

PyGithub is already installed in this project's dependencies.
