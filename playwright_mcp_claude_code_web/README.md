# Playwright MCP for Claude Code Web

Complete setup for accessing HTTPS sites without certificate errors using Playwright MCP in Claude Code Web environment.

## 🎯 Overview

This directory contains:

- **mcp.py**: MCP server launch script v2.0 (**with automatic setup + tools/list_changed workaround**)
- **setup.sh**: Manual setup script (optional)
- **example.py**: Sample code for fetching Yahoo! JAPAN topics
- **test_mcp_setup.py**: Setup verification script
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
- ✅ Firefox build v1496 installation
- ✅ Firefox profile creation
- ✅ JWT authentication proxy CA certificate import (staging/production)
- ✅ MCP configuration file creation

### Optional: Manual Setup

If you want to verify setup beforehand:

```bash
# Run setup verification script
uv run python playwright_mcp_claude_code_web/test_mcp_setup.py

# Or run manual setup script
HOME=/home/user bash playwright_mcp_claude_code_web/setup.sh
```

### Run Sample Code

```bash
# Fetch Yahoo! JAPAN topics
HOME=/home/user uv run python playwright_mcp_claude_code_web/example.py
```

**Expected output:**
```
📰 Yahoo! JAPAN Topics
======================================================================
 1. Main Services
 2. For Business Use
 3. Prime Minister Takaichi: Behind the Scenes of Hard Work
 4. "Rice Vouchers" Under Government Consideration - When Will They Arrive?
 ...
✅ Fetched 30 topics
```

## 📁 File Structure

```
playwright_mcp_claude_code_web/
├── README.md                           # This file
├── mcp.py                              # MCP server launch script (with auto-setup)
├── setup.sh                            # Manual setup script (optional)
├── test_mcp_setup.py                   # Setup verification script
├── example.py                          # Sample code
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
      "command": "uv",
      "args": ["run", "python", "playwright_mcp_claude_code_web/mcp.py"],
      "env": {"HOME": "/home/user"},
      "timeout": 180000
    }
  }
}
```

**Automatic setup contents (background):**
1. Verify certutil installation
2. Install @playwright/mcp globally
3. Install Firefox build v1496
4. Create Firefox profile (`/home/user/firefox-profile`)
5. Import CA certificates
6. Create MCP configuration file

**v2.0 Behavior:**
- Tool list is returned immediately (7 tools: navigate, screenshot, click, fill, select, hover, evaluate)
- Tool calls return "setup in progress" error until background setup completes
- No `tools/list_changed` notification needed (Claude Code doesn't support it)

### Setup Verification Script (test_mcp_setup.py)

**Execution:**
```bash
uv run python playwright_mcp_claude_code_web/test_mcp_setup.py
```

**Functions:**
- Check setup status
- Auto-setup if not set up
- Display status of each component

### Manual Setup Script (setup.sh)

**Execution:**
```bash
HOME=/home/user bash playwright_mcp_claude_code_web/setup.sh
```

**Use cases:**
- When you want to complete setup in advance
- When you want to verify setup details

### Sample Code (example.py)

**Functions:**
- Access Yahoo! JAPAN via playwright-mcp
- Extract and display topics
- Detailed debug log output

**Execution:**
```bash
HOME=/home/user uv run python playwright_mcp_claude_code_web/example.py
```

**Code flow:**
1. Start proxy.py (JWT authentication)
2. Connect to playwright-mcp server
3. Navigate to Yahoo! JAPAN
4. Get snapshot
5. Extract topics
6. Display results
7. Close browser
8. Stop proxy.py

## 🔍 Troubleshooting

### Certificate Error Occurs

**Symptom:**
```
❌ Certificate error occurred
SEC_ERROR_UNKNOWN_ISSUER
```

**Solution:**
```bash
# Run setup verification script
uv run python playwright_mcp_claude_code_web/test_mcp_setup.py

# Or re-run manual setup
HOME=/home/user bash playwright_mcp_claude_code_web/setup.sh

# Verify CA certificates
certutil -L -d sql:/home/user/firefox-profile | grep Anthropic
```

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
```bash
# Install Firefox with HOME=/home/user
HOME=/home/user node /opt/node22/lib/node_modules/@playwright/mcp/node_modules/playwright/cli.js install firefox
```

### proxy.py Won't Start

**Symptom:**
```
❌ HTTPS_PROXY environment variable not set
```

**Solution:**
- Verify this is Claude Code Web environment
- Check proxy settings with `echo $HTTPS_PROXY`

## 💡 Important Points

### 1. HOME=/home/user is Required

```bash
# ❌ This will fail
bash playwright_mcp_claude_code_web/setup.sh

# ✅ This is correct
HOME=/home/user bash playwright_mcp_claude_code_web/setup.sh
```

**Reason:** Firefox requires profile owner and HOME directory owner to match.

### 2. proxy.py is Required

**Why needed?**
- To handle JWT authentication
- Firefox cannot directly handle complex JWT authentication

**Contents of HTTPS_PROXY environment variable:**
```
http://user:jwt_eyJ0eXAi...@host:port
```

### 3. CA Certificate Import is Required

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
# Run setup verification script
uv run python playwright_mcp_claude_code_web/test_mcp_setup.py
```

If the following are checked ✅, it's successful:
- [ ] certutil is installed
- [ ] @playwright/mcp is globally installed
- [ ] Firefox build v1496 is in `/home/user/.cache/ms-playwright/firefox-1496`
- [ ] Firefox profile is in `/home/user/firefox-profile`
- [ ] MCP configuration file exists

Manual verification:
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

1. Check setup status with `test_mcp_setup.py`
2. Re-run `setup.sh` if necessary
3. Check detailed documentation
4. Refer to test code
5. Verify CA certificate import status

---

**Happy Coding with Playwright MCP! 🎉**
