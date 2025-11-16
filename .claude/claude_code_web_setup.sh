#!/bin/bash
set -e

if [ -z "$CLAUDE_CODE_REMOTE" ]; then
    exit 0
fi
echo "This environment is Claude Code Web. Please read CLAUDE_CODE_WEB.md"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"
}

# Save original stdout
exec 3>&1

# redirect all command output and log to .claude/claude_code_web_setup.log
LOG_FILE=".claude/claude_code_web_setup_$(date '+%Y%m%d_%H%M%S').log"

log "Starting setup script. Please check if the script ran successfully until the end."
log "Success is indicated by the message 'SETUP COMPLETED SUCCESSFULLY' at the end of this script."
log "Detailed log is saved to $LOG_FILE"

exec > "$LOG_FILE" 2>&1

if false; then
log "submodule setup script for Claude Code Web"
log "initial submodule status:"
git submodule status || log "(no submodules)"

log "check environment variables..."
if [ -z "$GITHUB_TOKEN" ]; then
    log "warning: GITHUB_TOKEN environment variable is not set"
    log "private submodules cannot be accessed"
    log "please set the GITHUB_TOKEN environment variable"
    exit 1
else
    log "GITHUB_TOKEN environment variable is set"
fi

log "add Git URL rewrite setting..."
git config --global url."https://${GITHUB_TOKEN}@github.com/".insteadOf "https://github.com/" 2>/dev/null || true
log "Git configuration completed"

log "initialize submodule ./path/to/submodule"
if git submodule status ./path/to/submodule | grep -q "^-" ; then
    git submodule update --init --recursive --depth 1 ./path/to/submodule
else
    log "./path/to/submodule is already initialized"
fi
fi # if false

log "setup .venv..."
uv sync --dev

log "Verify PyGithub installation..."
uv run python -c "import github; print('✓ PyGithub installed')"

log "Setup Playwright MCP server..."
uv run python playwright_mcp_claude_code_web/setup_mcp.py
if [ $? -eq 0 ]; then
    log "✓ Playwright MCP server setup completed"
else
    log "⚠️  Playwright MCP server setup failed (non-critical)"
fi

# Restore stdout and print summary for Claude
exec 1>&3

echo "SETUP COMPLETED SUCCESSFULLY"
echo ""
echo "How to run python code:"
echo "  uv run python src/package/path/to/script.py"
echo "  uv run pytest tests/"
echo "  uv run pyright src/"
echo "  uv run ruff check src/"
echo "  uv run ruff format src/"
echo ""
echo "Installed components:"
echo "  ✓ PyGithub - GitHub API client"
echo "  ✓ Playwright MCP server - Browser automation for Claude Code Web"
