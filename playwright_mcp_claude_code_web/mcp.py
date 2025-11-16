#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# ///
"""
Playwright MCP Server Launch Script for Claude Code (tools/list_changed workaround)

Communication flow:
  Claude Code → mcp.py (MCP Wrapper) → playwright-mcp (Firefox) → proxy.py → JWT Auth Proxy → Internet

This script:
  1. Returns full tool list immediately on first tools/list (avoiding Claude Code's tools/list_changed limitation)
  2. Returns temporary errors for tool calls until setup completes
  3. Runs full setup in a background thread
  4. Proxies requests to playwright-mcp after setup completes
  5. Stops proxy.py and playwright-mcp on exit

This avoids Claude Code's lack of support for tools/list_changed notifications.
"""
import os
import sys
import json
import subprocess
import threading
import time
import atexit
import signal
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List

# Global variables
proxy_process = None
playwright_mcp_process = None
setup_completed = False
setup_error = None
write_lock = threading.Lock()
playwright_tools: List[Dict[str, Any]] = []

# Playwright MCP tool definitions (静的に定義)
PLAYWRIGHT_TOOLS = [
    {
        "name": "playwright_navigate",
        "description": "Navigate to a URL",
        "inputSchema": {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "URL to navigate to"
                }
            },
            "required": ["url"]
        }
    },
    {
        "name": "playwright_screenshot",
        "description": "Take a screenshot of the current page or a specific element",
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Name for the screenshot"
                },
                "selector": {
                    "type": "string",
                    "description": "CSS selector for element to screenshot (optional)"
                },
                "width": {
                    "type": "number",
                    "description": "Screenshot width (optional)"
                },
                "height": {
                    "type": "number",
                    "description": "Screenshot height (optional)"
                }
            },
            "required": ["name"]
        }
    },
    {
        "name": "playwright_click",
        "description": "Click an element on the page",
        "inputSchema": {
            "type": "object",
            "properties": {
                "selector": {
                    "type": "string",
                    "description": "CSS selector for element to click"
                }
            },
            "required": ["selector"]
        }
    },
    {
        "name": "playwright_fill",
        "description": "Fill out an input field",
        "inputSchema": {
            "type": "object",
            "properties": {
                "selector": {
                    "type": "string",
                    "description": "CSS selector for input field"
                },
                "value": {
                    "type": "string",
                    "description": "Value to fill"
                }
            },
            "required": ["selector", "value"]
        }
    },
    {
        "name": "playwright_select",
        "description": "Select an option in a dropdown",
        "inputSchema": {
            "type": "object",
            "properties": {
                "selector": {
                    "type": "string",
                    "description": "CSS selector for select element"
                },
                "value": {
                    "type": "string",
                    "description": "Value to select"
                }
            },
            "required": ["selector", "value"]
        }
    },
    {
        "name": "playwright_hover",
        "description": "Hover over an element",
        "inputSchema": {
            "type": "object",
            "properties": {
                "selector": {
                    "type": "string",
                    "description": "CSS selector for element to hover"
                }
            },
            "required": ["selector"]
        }
    },
    {
        "name": "playwright_evaluate",
        "description": "Execute JavaScript in the browser console",
        "inputSchema": {
            "type": "object",
            "properties": {
                "script": {
                    "type": "string",
                    "description": "JavaScript code to execute"
                }
            },
            "required": ["script"]
        }
    }
]


def log(message: str, level: str = "INFO"):
    """Log output with timestamp (outputs to stderr)"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    prefix = {
        "INFO": "✓",
        "WARN": "⚠️",
        "ERROR": "❌",
        "DEBUG": "🔍"
    }.get(level, "ℹ️")
    print(f"[{timestamp}] {prefix} [MCP Wrapper] {message}", file=sys.stderr, flush=True)


def get_playwright_tools_from_mcp() -> Optional[List[Dict[str, Any]]]:
    """
    Try to get actual tool list from @playwright/mcp
    If it fails, return None and use static tool definitions
    """
    try:
        log("Attempting to fetch tool list from @playwright/mcp...", "DEBUG")

        # Check if @playwright/mcp is installed
        result = subprocess.run(
            ["npm", "list", "-g", "@playwright/mcp"],
            capture_output=True,
            text=True,
            timeout=5
        )

        if result.returncode != 0:
            log("@playwright/mcp not installed, using static tool definitions", "WARN")
            return None

        log("@playwright/mcp is installed, using static tool definitions for now", "DEBUG")
        return None  # 静的定義を使用

    except Exception as e:
        log(f"Failed to check @playwright/mcp: {e}", "WARN")
        return None


def run_setup_script():
    """Run setup script (background thread)"""
    global setup_completed, setup_error, playwright_mcp_process

    try:
        log("Starting background setup...")

        script_dir = Path(__file__).parent
        setup_script = script_dir / "setup_mcp.py"

        start_time = time.time()
        result = subprocess.run(
            ["uv", "run", "python", str(setup_script)],
            capture_output=True,
            text=True,
            env=os.environ.copy()
        )
        elapsed = time.time() - start_time

        if result.returncode != 0:
            setup_error = f"Setup failed: {result.stderr}"
            log(f"Setup failed after {elapsed:.2f}s", "ERROR")
            log(setup_error, "ERROR")
            return

        log(f"Setup script completed in {elapsed:.2f}s")

        # Start proxy and playwright-mcp
        if not start_proxy():
            setup_error = "Failed to start proxy.py"
            return

        if not start_playwright_mcp():
            setup_error = "Failed to start playwright-mcp"
            return

        setup_completed = True
        log("Full setup completed successfully")

    except Exception as e:
        setup_error = f"Error during setup: {e}"
        log(setup_error, "ERROR")


def start_proxy():
    """Start proxy.py"""
    global proxy_process

    # Check HTTPS_PROXY environment variable
    https_proxy = os.environ.get('HTTPS_PROXY', '')
    if not https_proxy:
        log("HTTPS_PROXY environment variable not set", "ERROR")
        return False

    log("Starting proxy.py...")

    try:
        start_time = time.time()
        proxy_process = subprocess.Popen(
            [
                "uv", "run", "proxy",
                "--hostname", "127.0.0.1",
                "--port", "18915",
                "--plugins", "proxy.plugin.proxy_pool.ProxyPoolPlugin",
                "--proxy-pool", https_proxy
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

        # Wait for proxy.py to start
        time.sleep(2)
        elapsed = time.time() - start_time
        log(f"proxy.py started successfully in {elapsed:.2f}s (localhost:18915)")
        return True

    except Exception as e:
        log(f"proxy.py startup error: {e}", "ERROR")
        return False


def start_playwright_mcp():
    """Start playwright-mcp"""
    global playwright_mcp_process

    script_dir = Path(__file__).parent
    config_path = str(script_dir / "playwright-firefox-config.json")

    if not os.path.exists(config_path):
        log(f"Configuration file not found: {config_path}", "ERROR")
        return False

    log("Starting playwright-mcp...")

    cmd = [
        'node',
        '/opt/node22/lib/node_modules/@playwright/mcp/cli.js',
        '--config', config_path,
        '--browser', 'firefox',
        '--proxy-server', 'http://127.0.0.1:18915'
    ]

    env = os.environ.copy()
    env['HOME'] = '/home/user'

    try:
        start_time = time.time()
        playwright_mcp_process = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            env=env,
            bufsize=0
        )

        elapsed = time.time() - start_time
        log(f"playwright-mcp started successfully in {elapsed:.2f}s")
        return True

    except Exception as e:
        log(f"playwright-mcp startup error: {e}", "ERROR")
        return False


def stop_processes():
    """Stop proxy.py and playwright-mcp"""
    global proxy_process, playwright_mcp_process

    if playwright_mcp_process:
        log("Stopping playwright-mcp...")
        try:
            playwright_mcp_process.terminate()
            playwright_mcp_process.wait(timeout=5)
        except:
            playwright_mcp_process.kill()

    if proxy_process:
        log("Stopping proxy.py...")
        try:
            proxy_process.terminate()
            proxy_process.wait(timeout=5)
        except:
            proxy_process.kill()


def read_jsonrpc_message(stream) -> Optional[Dict[str, Any]]:
    """Read JSON-RPC message"""
    try:
        line = stream.readline()
        if not line:
            return None

        message = json.loads(line)
        return message
    except Exception as e:
        log(f"Message read error: {e}", "ERROR")
        return None


def write_jsonrpc_message(stream, message: Dict[str, Any]):
    """Write JSON-RPC message (thread-safe)"""
    try:
        with write_lock:
            json_str = json.dumps(message) + "\n"
            stream.write(json_str)
            stream.flush()
    except Exception as e:
        log(f"Message write error: {e}", "ERROR")


def handle_initialize(request: Dict[str, Any]) -> Dict[str, Any]:
    """Handle initialize request"""
    return {
        "jsonrpc": "2.0",
        "id": request.get("id"),
        "result": {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {}
            },
            "serverInfo": {
                "name": "playwright-mcp-wrapper",
                "version": "2.0.0"
            }
        }
    }


def handle_tools_list(request: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle tools/list request
    Always return full tool list immediately (workaround for Claude Code's lack of tools/list_changed support)
    """
    global playwright_tools

    if setup_error:
        # When setup error occurs
        return {
            "jsonrpc": "2.0",
            "id": request.get("id"),
            "error": {
                "code": -32603,
                "message": f"Setup error: {setup_error}"
            }
        }

    # Use static tool definitions or fetched tools
    if not playwright_tools:
        fetched_tools = get_playwright_tools_from_mcp()
        playwright_tools = fetched_tools if fetched_tools else PLAYWRIGHT_TOOLS
        log(f"Returning {len(playwright_tools)} tools in tools/list", "DEBUG")

    return {
        "jsonrpc": "2.0",
        "id": request.get("id"),
        "result": {
            "tools": playwright_tools
        }
    }


def handle_tool_call(request: Dict[str, Any]) -> Dict[str, Any]:
    """Handle tools/call request"""
    if setup_error:
        return {
            "jsonrpc": "2.0",
            "id": request.get("id"),
            "error": {
                "code": -32603,
                "message": f"Setup error: {setup_error}"
            }
        }

    if not setup_completed:
        # Setup still in progress - return temporary error
        tool_name = request.get("params", {}).get("name", "unknown")
        return {
            "jsonrpc": "2.0",
            "id": request.get("id"),
            "error": {
                "code": -32603,
                "message": "Playwright MCP setup is still in progress. Please wait a moment and try again..."
            }
        }

    # Setup completed - proxy to playwright-mcp
    return None  # Signal to proxy


def proxy_to_playwright_mcp(request: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Proxy request to playwright-mcp"""
    global playwright_mcp_process

    if not playwright_mcp_process:
        return {
            "jsonrpc": "2.0",
            "id": request.get("id"),
            "error": {
                "code": -32603,
                "message": "playwright-mcp is not running"
            }
        }

    try:
        # Send request
        write_jsonrpc_message(playwright_mcp_process.stdin, request)

        # Receive response
        response = read_jsonrpc_message(playwright_mcp_process.stdout)
        return response

    except Exception as e:
        log(f"Proxy error: {e}", "ERROR")
        return {
            "jsonrpc": "2.0",
            "id": request.get("id"),
            "error": {
                "code": -32603,
                "message": f"Proxy error: {e}"
            }
        }


def main():
    """Main process"""
    global setup_completed

    # Set HOME environment variable
    os.environ['HOME'] = '/home/user'

    # Register cleanup on exit
    atexit.register(stop_processes)

    log("=" * 70)
    log("Playwright MCP Wrapper Starting (v2.0 - tools/list_changed workaround)")
    log("=" * 70)

    # Start setup in background
    setup_thread = threading.Thread(target=run_setup_script, daemon=True)
    setup_thread.start()

    log("Starting to respond as MCP server")
    log("Tool list will be returned immediately, but calls will fail until setup completes")

    # Main loop: Process JSON-RPC messages
    try:
        while True:
            # Read request
            request = read_jsonrpc_message(sys.stdin)
            if not request:
                break

            method = request.get("method")
            log(f"Received request: {method}", "DEBUG")

            # Process by method
            response = None

            # Skip notifications (no response needed)
            if method and method.startswith("notifications/"):
                log(f"Skipping notification: {method}", "DEBUG")
                continue

            if method == "initialize":
                response = handle_initialize(request)

            elif method == "tools/list":
                response = handle_tools_list(request)

            elif method == "tools/call":
                response = handle_tool_call(request)
                if response is None:
                    # Proxy to playwright-mcp
                    response = proxy_to_playwright_mcp(request)

            else:
                # Proxy other methods to playwright-mcp (only if setup completed)
                if setup_completed and playwright_mcp_process:
                    response = proxy_to_playwright_mcp(request)
                else:
                    response = {
                        "jsonrpc": "2.0",
                        "id": request.get("id"),
                        "error": {
                            "code": -32603,
                            "message": "Setup is in progress. Please wait..."
                        }
                    }

            # Send response
            if response:
                write_jsonrpc_message(sys.stdout, response)

    except KeyboardInterrupt:
        log("Interrupted")
    except Exception as e:
        log(f"Error: {e}", "ERROR")
        import traceback
        traceback.print_exc(file=sys.stderr)


if __name__ == '__main__':
    main()
