# Kagami

**Claude Code Web exclusive** Playwright MCP server. Enables browser automation via JWT authentication proxy.

## Overview

This project is **designed exclusively for Claude Code Web environment** and provides an MCP (Model Context Protocol) server for using Playwright.

**Important:** This project is designed to work only in Claude Code Web environment. It will not work in local environments or other environments.

**Key Features:**

- Auto-setup functionality (automatically installs required components on first startup)
- External access via JWT authentication proxy
- Automation using Firefox browser
- Automatic CA certificate import
- MCP protocol compliant

## Architecture

```
Claude Code → mcp.py → playwright-mcp (Firefox) → proxy.py → JWT Auth Proxy → Internet
```

1. **mcp.py**: MCP server entry point. Responsible for initial setup and launching proxy.py
2. **@playwright/mcp**: Playwright MCP server implementation (Node.js)
3. **Firefox**: Browser engine
4. **proxy.py**: Local proxy server
5. **JWT Auth Proxy**: Authentication proxy for external access

## Setup

### Automatic Setup (Recommended)

The following will be automatically set up on first startup:

1. certutil installation
2. @playwright/mcp installation
3. Firefox installation
4. Firefox profile creation
5. CA certificate import
6. Configuration file generation

**Note:**
- First startup may take 30 seconds or more

## Usage

### Launch as MCP Server

Configure in `.mcp.json` and Claude Code will automatically launch it:

```json
{
  "mcpServers": {
    "playwright": {
      "command": "python3",
      "args": [
        "playwright_mcp_claude_code_web/mcp.py"
      ]
    }
  }
}
```

## File Structure

```
.
├── playwright_mcp_claude_code_web/
│   └── mcp.py                          # MCP server (uses only standard library)
├── .mcp.json                           # MCP server configuration
└── README.md                           # This file
```

## Technical Details

### Startup Flow

**mcp.py** uses a two-phase setup approach to avoid timeout issues:

#### Phase 1: Synchronous Setup (runs before responding)

1. **Minimal Setup** (`setup_minimal.py`)
   - Install `@playwright/mcp` via npm
   - Create minimal Firefox configuration file

2. **Fetch Tool List**
   - Start temporary `@playwright/mcp` process
   - Fetch available tool definitions
   - Store tool list for immediate response to `tools/list` requests
   - Terminate temporary process

3. **Start MCP Server**
   - Begin responding as MCP server
   - Return stored tool list for `tools/list` requests
   - Return "setup in progress" error for `tools/call` requests

#### Phase 2: Asynchronous Setup (runs in background)

4. **Full Setup** (`setup_mcp.py` - runs in background thread)
   - Install `certutil` (for certificate management)
   - Install `proxy.py` via uv
   - Install Firefox browser
   - Create Firefox profile (`/home/user/firefox-profile`)
   - Import CA certificates for TLS inspection
   - Generate final configuration file

5. **Start Services**
   - Start `proxy.py` (localhost:18915)
   - Start `@playwright/mcp` with full configuration
   - Begin proxying all requests to `@playwright/mcp`

### Communication Flow (After Setup)

1. Claude Code sends request to `mcp.py` via MCP protocol (stdin/stdout)
2. `mcp.py` proxies request to `@playwright/mcp`
3. `@playwright/mcp` launches Firefox (proxy setting: localhost:18915)
4. `proxy.py` forwards requests to JWT authentication proxy
5. Access external sites through authenticated proxy

### Security

- Import CA certificate for TLS inspection into Firefox profile
- All HTTPS traffic goes through JWT authentication proxy
- Firefox runs with dedicated profile (/home/user/firefox-profile)

## References

- [Playwright Documentation](https://playwright.dev/)
- [@playwright/mcp GitHub](https://github.com/microsoft/playwright)
- [MCP Protocol](https://modelcontextprotocol.io/)
- [proxy.py Documentation](https://github.com/abhinavsingh/proxy.py)

## License

MIT
