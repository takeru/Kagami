# Playwright MCP for Claude Code Web

Complete setup for accessing HTTPS sites without certificate errors using Playwright MCP in Claude Code Web environment.

## 🎯 Overview

This directory contains:

- **mcp.py**: MCP server launch script with automatic setup
- **setup_minimal.py**: Minimal synchronous setup script
- **setup_mcp.py**: Full asynchronous setup script

## 📋 Communication Flow

```
MCP Client (Claude Code or other)
  ↓
playwright-mcp (Firefox + CA certificate)
  ↓
proxy.py (localhost:18915) ← JWT authentication
  ↓
JWT Auth Proxy ← TLS Inspection
  ↓
Internet ✅
```

## 🚀 Quick Start

### No Setup Required!

**mcp.py automatically runs setup on first startup.**

Simply using Playwright tools in Claude Code Web will automatically set up:
- ✅ certutil installation
- ✅ @playwright/mcp global installation
- ✅ Firefox installation
- ✅ Firefox profile creation
- ✅ JWT authentication proxy CA certificate import (staging/production)
- ✅ MCP configuration file creation

## 📁 File Structure

```
playwright_mcp_claude_code_web/
├── README.md                           # This file
├── mcp.py                              # MCP server launch script (with auto-setup)
├── setup_minimal.py                    # Minimal synchronous setup script
└── setup_mcp.py                        # Full asynchronous setup script
```

## 🔧 How It Works

### MCP Server Launch Script (mcp.py)

**Features:**
- Returns full tool list immediately on startup
- Returns clear error messages for tool calls during setup
- Runs automatic setup in background
- Auto-starts proxy.py
- Launches playwright-mcp in stdio mode
- Timestamped logging for better debugging

**.mcp.json configuration:**
```json
{
  "mcpServers": {
    "playwright": {
      "command": "python3",
      "args": ["playwright_mcp_claude_code_web/mcp.py"]
    }
  }
}
```

### Two-Phase Setup

**Phase 1: Synchronous Setup (runs on startup)**
1. Install @playwright/mcp globally if not installed
2. Create minimal configuration file
3. Start temporary playwright-mcp process
4. Fetch actual tools/list from playwright-mcp
5. Store tools in memory

**Phase 2: Asynchronous Setup (runs in background)**
1. Verify certutil installation
2. Install Firefox browser
3. Create Firefox profile (`/home/user/firefox-profile`)
4. Import CA certificates
5. Create full configuration file
6. Start proxy.py
7. Start playwright-mcp (full functionality)

**Behavior:**
- Startup: Synchronous setup fetches real tools from playwright-mcp
- Before async setup: Returns fetched tool list, tool calls return "setup in progress" error
- After async setup: Always proxies `tools/list` and tool calls to playwright-mcp
- No static tool definitions - always real tools from playwright-mcp

## 🔍 Troubleshooting

### Debugging Steps

When problems occur, follow these steps:

1. **Check Logs**
   ```bash
   # Check Claude Code main log
   tail -f /tmp/claude-code.log

   # Filter mcp.py related logs
   grep -i "mcp" /tmp/claude-code.log
   grep -i "playwright" /tmp/claude-code.log
   ```

2. **Restart Session**
   - Start a new Claude Code session to trigger fresh setup
   - Previous session state might be causing issues

3. **Verify MCP Tools**
   Use this debug prompt in Claude Code:
   ```
   mcp toolのリスト見せて。 mcp__playwrightある？ あるならyahooのトピックとってきて。
   ```

4. **Check Setup Timeline**
   Use this debug prompt to analyze logs:
   ```
   /tmp/claude-code.logやその他ログからmcp.py関連のセットアップログ、mcp tool呼び出しのタイミングを時系列で整理して。
   ```

5. **Test Browser Navigation**
   Simple test to verify everything works:
   ```
   mcp__playwright__browser_navigateでyahooのトピックスとってきて
   ```

### Common Issues

#### Certificate Error

**Symptom:**
```
❌ Certificate error occurred
SEC_ERROR_UNKNOWN_ISSUER
```

**Solution:**
mcp.py automatically handles setup. If certificates are missing, restart the MCP server.

Verify CA certificates:
```bash
certutil -L -d sql:/home/user/firefox-profile | grep Anthropic
```

Expected output:
```
Anthropic TLS Inspection CA                                  C,,
Anthropic TLS Inspection CA Production                       C,,
```

#### Firefox Not Found

**Symptom:**
```
Browser specified in your config is not installed
```

**Solution:**
Firefox is automatically installed by `setup_mcp.py`. If this error occurs, restart the MCP server to trigger setup.

#### proxy.py Won't Start

**Symptom:**
```
❌ HTTPS_PROXY environment variable not set
```

**Solution:**
- Verify this is Claude Code Web environment
- Check proxy settings with `echo $HTTPS_PROXY`

## 💡 Technical Background

### Why proxy.py is Required

**Reason:**
- To handle JWT authentication
- Firefox cannot directly handle complex JWT authentication

**HTTPS_PROXY format:**
```
http://user:jwt_eyJ0eXAi...@host:port
```

### Why CA Certificate Import is Required

**Reason:**
- Certificates are replaced by TLS Inspection
- Import to Firefox profile, not system certificate store

**Comparison:**
```
curl   → System certificate store → Access successful
Firefox → Its own certificate store → Fails without import
```

## 📝 Technical Notes

### Why Two-Phase Setup?

This project uses a complex two-phase setup approach (synchronous minimal setup + asynchronous full setup) because Claude Code does not support the `tools/list_changed` MCP notification.

If `tools/list_changed` were supported, the MCP server could simply notify the client when new tools become available after setup completes. However, without this notification support, the server must return the complete tool list immediately on first startup, which necessitates the current two-phase approach.

---

**Happy Coding with Playwright MCP! 🎉**
