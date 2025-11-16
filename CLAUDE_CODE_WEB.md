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

```bash
uv run pytest tests
```

**PEP 723 compliant scripts:**
```bash
uv run script.py  # if script.py has PEP 723 metadata
```

## GitHub Operations

**The `gh` command is NOT available in Claude Code Web environment.**

Use PyGithub instead for GitHub operations:

```python
from github import Github

# Authenticate using environment variable
g = Github()  # Uses GITHUB_TOKEN from environment

# Get repository
repo = g.get_repo("owner/repo")

# Create issue
issue = repo.create_issue(
    title="Issue title",
    body="Issue body"
)

# Create pull request
pr = repo.create_pull(
    title="PR title",
    body="PR body",
    head="feature-branch",
    base="main"
)
```

PyGithub is already installed in this project's dependencies.
