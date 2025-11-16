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

## Troubleshooting

### CA Certificate Error

Verify CA certificate is properly imported:

```bash
certutil -L -d sql:/home/user/firefox-profile
```

The following certificates should be displayed:
- Anthropic TLS Inspection CA
- Anthropic TLS Inspection CA Production

## Technical Details

### Communication Flow

1. Claude Code sends request to `mcp.py` via MCP protocol (stdin/stdout)
2. `mcp.py` starts `proxy.py` (localhost:18915)
3. `mcp.py` starts `@playwright/mcp`
4. Playwright launches Firefox (proxy setting: localhost:18915)
5. `proxy.py` forwards to JWT authentication proxy
6. Access external sites

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
