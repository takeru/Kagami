#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# ///
"""
Playwright MCP Server Launch Script for Claude Code (Timeout Mitigation Version)

Communication flow:
  Claude Code → mcp.py (MCP Wrapper) → playwright-mcp (Firefox) → proxy.py → JWT Auth Proxy → Internet

This script:
  1. Responds immediately as an MCP server on startup (avoiding timeout)
  2. Runs setup in a background thread
  3. Proxies requests to playwright-mcp after setup completes
  4. Stops proxy.py and playwright-mcp on exit

This avoids the 30-second timeout in Claude Code Web.
"""
import os
import sys
import json
import subprocess
import threading
import time
import atexit
import signal
from pathlib import Path
from typing import Optional, Dict, Any

# Global variables
proxy_process = None
playwright_mcp_process = None
setup_completed = False
setup_error = None
write_lock = threading.Lock()


def log(message: str, level: str = "INFO"):
    """Log output (outputs to stderr)"""
    prefix = {
        "INFO": "✓",
        "WARN": "⚠️",
        "ERROR": "❌",
        "DEBUG": "🔍"
    }.get(level, "ℹ️")
    print(f"{prefix} [MCP Wrapper] {message}", file=sys.stderr, flush=True)


def run_setup_script():
    """Run setup script (background thread)"""
    global setup_completed, setup_error

    try:
        log("Starting background setup...")

        script_dir = Path(__file__).parent
        setup_script = script_dir / "setup_mcp.py"

        result = subprocess.run(
            ["uv", "run", "python", str(setup_script)],
            capture_output=True,
            text=True,
            env=os.environ.copy()
        )

        if result.returncode != 0:
            setup_error = f"Setup failed: {result.stderr}"
            log(setup_error, "ERROR")
            return

        log("Setup completed")
        setup_completed = True

        # Send notification to client
        notification = {
            "jsonrpc": "2.0",
            "method": "notifications/tools/list_changed"
        }
        write_jsonrpc_message(sys.stdout, notification)
        log("Sent tools/list_changed notification", "DEBUG")

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

    log(f"Starting proxy.py...")

    try:
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
        log("proxy.py started successfully (localhost:18915)")
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

    log(f"Starting playwright-mcp...")

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
        playwright_mcp_process = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            env=env,
            bufsize=0
        )

        log("playwright-mcp started successfully")
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
                "version": "1.0.0"
            }
        }
    }


def handle_tools_list(request: Dict[str, Any]) -> Dict[str, Any]:
    """Handle tools/list request"""
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
    elif not setup_completed:
        # During setup
        return {
            "jsonrpc": "2.0",
            "id": request.get("id"),
            "result": {
                "tools": [{
                    "name": "playwright_setup_in_progress",
                    "description": "Playwright MCP server setup is in progress. Please wait...",
                    "inputSchema": {
                        "type": "object",
                        "properties": {}
                    }
                }]
            }
        }
    else:
        # Setup completed - proxy to playwright-mcp
        return None  # Requires proxy


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
    log("Playwright MCP Wrapper Starting")
    log("=" * 70)

    # Start setup in background
    setup_thread = threading.Thread(target=run_setup_script, daemon=True)
    setup_thread.start()

    log("Starting to respond as MCP server")

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
                if response is None:
                    # After setup completes, start playwright-mcp and proxy
                    if not playwright_mcp_process:
                        if not start_proxy():
                            response = {
                                "jsonrpc": "2.0",
                                "id": request.get("id"),
                                "error": {
                                    "code": -32603,
                                    "message": "Failed to start proxy.py"
                                }
                            }
                        elif not start_playwright_mcp():
                            response = {
                                "jsonrpc": "2.0",
                                "id": request.get("id"),
                                "error": {
                                    "code": -32603,
                                    "message": "Failed to start playwright-mcp"
                                }
                            }

                    if response is None:
                        response = proxy_to_playwright_mcp(request)

            else:
                # Proxy other methods to playwright-mcp
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
