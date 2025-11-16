# Playwright MCP for Claude Code Web

Complete setup for accessing HTTPS sites without certificate errors using Playwright MCP in Claude Code Web environment.

## 🎯 Overview

This directory contains:

- **mcp.py**: MCP server launch script v2.0 (**with automatic setup + tools/list_changed workaround**)
- **setup_minimal.py**: Minimal synchronous setup script
- **setup_mcp.py**: Full asynchronous setup script
- **playwright-firefox-config.json**: Firefox configuration file (auto-generated)

**v2.0 Update:** Works around Claude Code's lack of `tools/list_changed` notification support by returning the full tool list immediately on first startup.

## 📋 Communication Flow

```
Python MCP Client
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
├── setup_mcp.py                        # Full asynchronous setup script
└── playwright-firefox-config.json      # Firefox configuration (auto-generated)
```

## 🔧 Detailed Usage

### MCP Server Launch Script (mcp.py)

**Features (v2.0):**
- Returns full tool list immediately on startup (bypasses Claude Code's tools/list_changed limitation)
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

**Synchronous setup (runs on startup, blocks until complete):**
1. Install @playwright/mcp globally if not installed
2. Create minimal configuration file
3. Start temporary playwright-mcp process
4. Fetch actual tools/list from playwright-mcp
5. Store tools in memory

**Asynchronous setup (runs in background):**
1. Verify certutil installation
2. Install Firefox browser
3. Create Firefox profile (`/home/user/firefox-profile`)
4. Import CA certificates
5. Create full configuration file
6. Start proxy.py
7. Start playwright-mcp (full functionality)

**v2.0 Behavior:**
- Startup: Synchronous setup fetches real tools from playwright-mcp
- Before async setup: Returns fetched tool list, tool calls return "setup in progress" error
- After async setup: Always proxies `tools/list` and tool calls to playwright-mcp
- No `tools/list_changed` notification needed (Claude Code doesn't support it)
- No static tool definitions - always real tools from playwright-mcp

### Setup Scripts

**setup_minimal.py:**
- Runs synchronously during mcp.py startup
- Installs @playwright/mcp via npm
- Creates minimal Firefox configuration
- Used to fetch initial tool list

**setup_mcp.py:**
- Runs asynchronously in background
- Installs certutil and Firefox
- Creates Firefox profile and imports CA certificates
- Starts proxy.py and playwright-mcp for full functionality

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

### Certificate Error Occurs

**Symptom:**
```
❌ Certificate error occurred
SEC_ERROR_UNKNOWN_ISSUER
```

**Solution:**
```bash
# Verify CA certificates
certutil -L -d sql:/home/user/firefox-profile | grep Anthropic
```

**Note:** mcp.py automatically handles setup. If certificates are missing, restart the MCP server.

**Expected output:**
```
Anthropic TLS Inspection CA                                  C,,
Anthropic TLS Inspection CA Production                       C,,
```

### Firefox Not Found

**Symptom:**
```
Browser specified in your config is not installed
```

**Solution:**
Firefox is automatically installed by `setup_mcp.py`. If this error occurs, restart the MCP server to trigger setup.

### proxy.py Won't Start

**Symptom:**
```
❌ HTTPS_PROXY environment variable not set
```

**Solution:**
- Verify this is Claude Code Web environment
- Check proxy settings with `echo $HTTPS_PROXY`

## 💡 Important Points

### 1. proxy.py is Required

**Why needed?**
- To handle JWT authentication
- Firefox cannot directly handle complex JWT authentication

**Contents of HTTPS_PROXY environment variable:**
```
http://user:jwt_eyJ0eXAi...@host:port
```

### 2. CA Certificate Import is Required

**Why needed?**
- Certificates are replaced by TLS Inspection
- Import to Firefox profile, not system certificate store

**Comparison:**
```
curl   → System certificate store → Access successful
Firefox → Its own certificate store → Fails without import
```

## 📚 Related Documentation

- [CA Certificate Import Guide](../investigation/playwright/CA_CERTIFICATE_IMPORT_GUIDE.md)
- [Firefox Setup in HOME=/home/user Environment](../investigation/playwright/HOME_USER_FIREFOX_SETUP.md)
- [Playwright Investigation Summary](../PLAYWRIGHT_INVESTIGATION.md)

## 🧪 Test Code

Verified test code:
- `test_24_firefox_profile_with_proxy_py.py` - Complete success version ✅
- `test_25_verify_system_cert_not_needed.py` - Verification that system certificate store is not needed

## ✅ Checklist

Verify setup completed correctly:
```bash
# Verify CA certificates
certutil -L -d sql:/home/user/firefox-profile | grep Anthropic
```

Expected output:
```
Anthropic TLS Inspection CA                                  C,,
Anthropic TLS Inspection CA Production                       C,,
```

If all checks pass, you can access HTTPS sites without certificate errors!

## 🎓 What You'll Learn

Through this setup you can learn:

1. **How TLS Inspection Works**
   - All HTTPS traffic is intercepted
   - Certificates are replaced
   - Mechanism for security checks

2. **Firefox Certificate Management**
   - Uses its own certificate store
   - Separate from system certificate store
   - Direct import to profile is required

3. **JWT Authentication Handling**
   - proxy.py is essential
   - Firefox cannot handle directly
   - Provided as simple HTTP proxy

4. **Both Are Needed**
   - CA certificate import ✅
   - Using proxy.py ✅
   - → Success for the first time!

## 🤝 Support

If problems occur:

1. Restart MCP server to trigger automatic setup
2. Check detailed documentation
3. Refer to test code
4. Verify CA certificate import status with `certutil -L -d sql:/home/user/firefox-profile | grep Anthropic`

---

**Happy Coding with Playwright MCP! 🎉**
