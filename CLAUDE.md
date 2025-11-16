**IMPORTANT**: All interactions with users must be conducted in Japanese

## Git Commit Notes

**Do NOT commit the following files:**

- Screenshots (*.png, *.jpg, *.jpeg, *.gif, etc.)
- HTML files fetched from browsers (*.html, etc.)
- Temporary test artifacts

These files are generated during testing and debugging, but are not needed in the repository.
Set appropriate patterns in .gitignore.

**Files that should be committed:**
- Source code (*.py, *.js, *.ts, etc.)
- Documentation (*.md)
- Configuration files (*.json, *.yaml, etc.)
- Test scripts

## Determining if Claude Code Web

```
if [ -n "$CLAUDE_CODE_REMOTE" ]; then echo "This is Claude Code Web"; else echo "This is not Claude Code Web"; fi
```

In Claude Code Web environment, please refer to @CLAUDE_CODE_WEB.md.

## About Playwright MCP Server

**This project is Claude Code Web exclusive.**

This repository contains a Playwright MCP server (`playwright_mcp_claude_code_web/mcp.py`) for Claude Code Web. It is designed to work only in Claude Code Web environment.

### Automatic Setup

The MCP server automatically sets up the following on first startup:

1. certutil installation
2. @playwright/mcp installation
3. proxy.py installation (uv pip install proxy.py)
4. Firefox (build v1496) installation
5. Firefox profile creation
6. CA certificate import
7. proxy.py startup

**Note:**
- First startup may take 30 seconds or more
- `HTTPS_PROXY` environment variable is required
- Setup is executed automatically, no manual operation required

### Dependencies

`mcp.py` uses only Python standard libraries (no external packages required).

The execution environment requires the following components, but **they are automatically installed on first startup**:
- `proxy.py` - Used for connecting to JWT proxy (automatically installed with `uv pip install proxy.py`)
- `@playwright/mcp` - Playwright MCP server (automatically installed with `npm install -g`)
- `node` - Node.js runtime (standard equipment in Claude Code Web environment)

### Using MCP Playwright Tools

In Claude Code Web environment, `mcp__playwright` should be installed.

**Available tools:**
- `mcp__playwright__browser_navigate` - Navigate to URL in browser
- Other Playwright MCP tools

**Note:**
- First startup takes time for setup, so it may not be immediately available
- Need to wait until setup completes (30+ seconds)
