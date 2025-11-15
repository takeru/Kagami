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

log "Verify Playwright installation..."
uv run python -c "import playwright; print('✓ Playwright installed')"

# Chromiumは使用しないため無効化
# log "Install Playwright Chromium browser..."
# uv run playwright install chromium

log "Install Playwright Firefox browser..."
uv run playwright install firefox

log "Install Playwright system dependencies..."
# エラーが出ても続行（権限の問題など）
# uv run playwright install-deps chromium || log "Warning: Some system dependencies could not be installed, but continuing"
uv run playwright install-deps firefox || log "Warning: Some Firefox dependencies could not be installed, but continuing"

log "Setup Playwright MCP for Claude Code..."

# certutilのインストール確認
log "Check certutil installation..."
if ! command -v certutil &> /dev/null; then
    log "Installing certutil (libnss3-tools)..."
    apt-get update -qq || log "Warning: apt-get update failed"
    apt-get install -y libnss3-tools > /dev/null 2>&1 || log "Warning: certutil installation failed"
fi

# @playwright/mcpのグローバルインストール
log "Install @playwright/mcp globally..."
if npm list -g @playwright/mcp 2>&1 | grep -q @playwright/mcp; then
    log "@playwright/mcp is already installed"
else
    npm install -g @playwright/mcp || log "Warning: @playwright/mcp installation failed"
fi

# Firefoxプロファイルの作成
PROFILE_DIR="/home/user/firefox-profile"
log "Create Firefox profile at $PROFILE_DIR..."
if [ -d "$PROFILE_DIR" ] && [ -f "$PROFILE_DIR/cert9.db" ]; then
    log "Firefox profile already exists"
else
    mkdir -p "$PROFILE_DIR"
    certutil -N -d sql:"$PROFILE_DIR" --empty-password || log "Warning: Firefox profile creation failed"
fi

# CA証明書のインポート
STAGING_CERT="/usr/local/share/ca-certificates/swp-ca-staging.crt"
PRODUCTION_CERT="/usr/local/share/ca-certificates/swp-ca-production.crt"

log "Import CA certificates..."
if [ -f "$STAGING_CERT" ]; then
    if certutil -L -d sql:"$PROFILE_DIR" -n "Anthropic TLS Inspection CA" &> /dev/null; then
        log "Staging CA certificate already imported"
    else
        certutil -A -n "Anthropic TLS Inspection CA" -t "C,," -i "$STAGING_CERT" -d sql:"$PROFILE_DIR" || log "Warning: Staging CA import failed"
    fi
else
    log "Warning: Staging CA certificate not found at $STAGING_CERT"
fi

if [ -f "$PRODUCTION_CERT" ]; then
    if certutil -L -d sql:"$PROFILE_DIR" -n "Anthropic TLS Inspection CA Production" &> /dev/null; then
        log "Production CA certificate already imported"
    else
        certutil -A -n "Anthropic TLS Inspection CA Production" -t "C,," -i "$PRODUCTION_CERT" -d sql:"$PROFILE_DIR" || log "Warning: Production CA import failed"
    fi
else
    log "Warning: Production CA certificate not found at $PRODUCTION_CERT"
fi

log "Playwright MCP setup completed"

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
echo "  ✓ Playwright - Browser automation"
echo "  ✓ Firefox browser"
echo "  ✓ @playwright/mcp - Playwright MCP server"
echo "  ✓ Firefox profile with CA certificates"
echo ""
echo "Playwright MCP is ready to use:"
echo "  - Use mcp__playwright__* tools in Claude Code"
echo "  - Firefox with proxy support enabled"
echo "  - CA certificates imported for TLS inspection"
echo ""
echo "Example Python usage:"
echo "  uv run python playwright_mcp_claude_code_web/get_yahoo_news.py"
