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

log "Generate Playwright Firefox config with proxy settings..."
uv run python - << 'PYTHON_SCRIPT'
import os
import json
from urllib.parse import urlparse

# プロキシURLをパース
proxy_url = os.getenv("HTTPS_PROXY")
if not proxy_url:
    print("Warning: HTTPS_PROXY not set, creating config without proxy")
    config = {
        "launchOptions": {
            "headless": True,
            "firefoxUserPrefs": {
                "privacy.trackingprotection.enabled": False,
                "network.proxy.allow_hijacking_localhost": True,
                "network.stricttransportsecurity.preloadlist": False,
                "security.cert_pinning.enforcement_level": 0,
                "security.enterprise_roots.enabled": True,
                "security.ssl.errorReporting.enabled": False,
                "browser.xul.error_pages.expert_bad_cert": True,
                "media.navigator.streams.fake": True
            }
        },
        "contextOptions": {
            "ignoreHttpsErrors": True
        }
    }
else:
    parsed = urlparse(proxy_url)
    config = {
        "launchOptions": {
            "headless": True,
            "proxy": {
                "server": f"{parsed.scheme}://{parsed.hostname}:{parsed.port}",
                "username": parsed.username,
                "password": parsed.password
            },
            "firefoxUserPrefs": {
                "privacy.trackingprotection.enabled": False,
                "network.proxy.allow_hijacking_localhost": True,
                "network.stricttransportsecurity.preloadlist": False,
                "security.cert_pinning.enforcement_level": 0,
                "security.enterprise_roots.enabled": True,
                "security.ssl.errorReporting.enabled": False,
                "browser.xul.error_pages.expert_bad_cert": True,
                "media.navigator.streams.fake": True
            }
        },
        "contextOptions": {
            "ignoreHttpsErrors": True
        }
    }

# ファイルに保存
os.makedirs('.mcp', exist_ok=True)
with open('.mcp/playwright-firefox-config.json', 'w') as f:
    json.dump(config, f, indent=2)
    f.write('\n')

print("✓ Generated .mcp/playwright-firefox-config.json")
PYTHON_SCRIPT

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
echo ""
echo "Important notes for Playwright:"
echo "  - Firefox is used for MCP (better proxy support)"
echo "  - External network access is restricted"
echo "  - See PLAYWRIGHT_INVESTIGATION.md for details"
