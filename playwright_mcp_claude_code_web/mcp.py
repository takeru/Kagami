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


def log(message: str, level: str = "INFO"):
    """Log output (outputs to stderr)"""
    prefix = {
        "INFO": "✓",
        "WARN": "⚠️",
        "ERROR": "❌",
        "DEBUG": "🔍"
    }.get(level, "ℹ️")
    print(f"{prefix} [MCP Wrapper] {message}", file=sys.stderr, flush=True)


def run_command(cmd: list[str], check: bool = True, capture_output: bool = False) -> Optional[subprocess.CompletedProcess]:
    """Execute command"""
    try:
        result = subprocess.run(
            cmd,
            check=check,
            capture_output=capture_output,
            text=True
        )
        return result
    except subprocess.CalledProcessError as e:
        if check:
            log(f"Command execution error: {' '.join(cmd)}", "ERROR")
            log(f"Error details: {e.stderr if capture_output else str(e)}", "ERROR")
            raise
        return None


def check_command_exists(command: str) -> bool:
    """Check if command exists"""
    result = run_command(["which", command], check=False, capture_output=True)
    return result and result.returncode == 0


def check_npm_package_installed(package: str) -> bool:
    """Check if npm package is globally installed"""
    result = run_command(
        ["npm", "list", "-g", package],
        check=False,
        capture_output=True
    )
    return result and package in result.stdout


def check_proxy_installed() -> bool:
    """Check if proxy.py is installed"""
    result = run_command(
        ["uv", "run", "proxy", "--version"],
        check=False,
        capture_output=True
    )
    return result and result.returncode == 0


def get_installed_firefox_version() -> Optional[Path]:
    """Dynamically detect installed Firefox version

    Returns:
        Path to installed Firefox directory. Returns None if not found.
        If multiple versions are installed, returns the latest version (highest number).
    """
    cache_dir = Path("/home/user/.cache/ms-playwright")

    if not cache_dir.exists():
        return None

    # Search for firefox-* pattern directories
    firefox_dirs = list(cache_dir.glob("firefox-*"))

    if not firefox_dirs:
        return None

    # Sort by version number (prefer latest version)
    # Extract numeric part like firefox-1496 -> 1496
    def extract_version(path: Path) -> int:
        try:
            return int(path.name.split('-')[1])
        except (IndexError, ValueError):
            return 0

    firefox_dirs.sort(key=extract_version, reverse=True)
    return firefox_dirs[0]


def setup_certutil():
    """Verify certutil installation"""
    log("Checking certutil installation status...")

    if check_command_exists("certutil"):
        log("certutil is already installed")
        return

    log("Installing certutil...", "WARN")
    run_command(["apt-get", "update", "-qq"])
    run_command(["apt-get", "install", "-y", "libnss3-tools"])
    log("certutil installed")


def setup_playwright_mcp():
    """Verify @playwright/mcp installation"""
    log("Checking @playwright/mcp installation status...")

    if check_npm_package_installed("@playwright/mcp"):
        log("@playwright/mcp is already installed")
        return

    log("Installing @playwright/mcp... (may take several minutes)", "WARN")
    run_command(["npm", "install", "-g", "@playwright/mcp"])
    log("@playwright/mcp installed")


def setup_proxy_py():
    """Verify proxy.py installation"""
    log("Checking proxy.py installation status...")

    # Check with uv run proxy --version
    result = run_command(
        ["uv", "run", "proxy", "--version"],
        check=False,
        capture_output=True
    )

    if result and result.returncode == 0:
        log("proxy.py is already installed")
        return

    log("Installing proxy.py...", "WARN")
    run_command(["uv", "pip", "install", "proxy.py"])
    log("proxy.py installed")


def setup_firefox():
    """Install Firefox"""
    log("Checking Firefox installation status...")

    firefox_build = get_installed_firefox_version()

    if firefox_build:
        version = firefox_build.name.split('-')[1] if '-' in firefox_build.name else 'unknown'
        log(f"Firefox is already installed: {firefox_build} (build v{version})")
        return

    log("Installing Firefox... (may take several minutes)", "WARN")

    env = os.environ.copy()
    env["HOME"] = "/home/user"

    run_command([
        "node",
        "/opt/node22/lib/node_modules/@playwright/mcp/node_modules/playwright/cli.js",
        "install",
        "firefox"
    ])

    # Check version after installation
    firefox_build = get_installed_firefox_version()
    if firefox_build:
        version = firefox_build.name.split('-')[1] if '-' in firefox_build.name else 'unknown'
        log(f"Firefox installed: {firefox_build} (build v{version})")
    else:
        log("Firefox installation completed but version could not be verified", "WARN")


def setup_firefox_profile():
    """Create Firefox profile"""
    log("Checking Firefox profile...")

    profile_dir = Path("/home/user/firefox-profile")
    cert_db = profile_dir / "cert9.db"

    if profile_dir.exists() and cert_db.exists():
        log(f"Firefox profile already exists: {profile_dir}")
        return

    log("Creating Firefox profile...")

    profile_dir.mkdir(parents=True, exist_ok=True)

    run_command([
        "certutil",
        "-N",
        "-d", f"sql:{profile_dir}",
        "--empty-password"
    ])

    log(f"Firefox profile created: {profile_dir}")


def import_ca_certificates():
    """Import JWT authentication proxy CA certificates"""
    log("Checking CA certificate import status...")

    profile_dir = Path("/home/user/firefox-profile")
    staging_cert = Path("/usr/local/share/ca-certificates/swp-ca-staging.crt")
    production_cert = Path("/usr/local/share/ca-certificates/swp-ca-production.crt")

    # Verify certificate files exist
    if not staging_cert.exists():
        log(f"Staging CA certificate not found: {staging_cert}", "ERROR")
        sys.exit(1)

    if not production_cert.exists():
        log(f"Production CA certificate not found: {production_cert}", "ERROR")
        sys.exit(1)

    # Import staging CA certificate
    result = run_command([
        "certutil",
        "-L",
        "-d", f"sql:{profile_dir}",
        "-n", "Anthropic TLS Inspection CA"
    ], check=False, capture_output=True)

    if result and result.returncode == 0:
        log("Staging CA certificate is already imported")
    else:
        log("Importing staging CA certificate...")
        run_command([
            "certutil",
            "-A",
            "-n", "Anthropic TLS Inspection CA",
            "-t", "C,,",
            "-i", str(staging_cert),
            "-d", f"sql:{profile_dir}"
        ])
        log("Staging CA certificate imported")

    # Import production CA certificate
    result = run_command([
        "certutil",
        "-L",
        "-d", f"sql:{profile_dir}",
        "-n", "Anthropic TLS Inspection CA Production"
    ], check=False, capture_output=True)

    if result and result.returncode == 0:
        log("Production CA certificate is already imported")
    else:
        log("Importing production CA certificate...")
        run_command([
            "certutil",
            "-A",
            "-n", "Anthropic TLS Inspection CA Production",
            "-t", "C,,",
            "-i", str(production_cert),
            "-d", f"sql:{profile_dir}"
        ])
        log("Production CA certificate imported")


def setup_config_file():
    """Create MCP configuration file"""
    log("Checking MCP configuration file...")

    script_dir = Path(__file__).parent
    config_file = script_dir / "playwright-firefox-config.json"

    if config_file.exists():
        log(f"MCP configuration file already exists: {config_file}")
        return

    log("Creating MCP configuration file...")

    config = {
        "browser": {
            "browserName": "firefox",
            "userDataDir": "/home/user/firefox-profile",
            "launchOptions": {
                "headless": True,
                "firefoxUserPrefs": {
                    "privacy.trackingprotection.enabled": False,
                    "network.proxy.allow_hijacking_localhost": True,
                    "network.stricttransportsecurity.preloadlist": False,
                    "security.cert_pinning.enforcement_level": 0,
                    "security.enterprise_roots.enabled": False,
                    "security.ssl.errorReporting.enabled": False,
                    "browser.xul.error_pages.expert_bad_cert": True,
                    "media.navigator.streams.fake": True,
                    "security.insecure_connection_text.enabled": False,
                    "security.insecure_connection_text.pbmode.enabled": False,
                    "security.mixed_content.block_active_content": False,
                    "security.mixed_content.block_display_content": False,
                    "security.OCSP.enabled": 0
                },
                "acceptDownloads": False
            },
            "contextOptions": {
                "ignoreHTTPSErrors": True,
                "bypassCSP": True
            }
        }
    }

    with open(config_file, "w") as f:
        json.dump(config, f, indent=2)

    log(f"MCP configuration file created: {config_file}")


def run_setup():
    """Execute first-time setup"""
    log("=" * 70)
    log("Playwright MCP - Starting first-time setup")
    log("=" * 70)

    try:
        setup_certutil()
        setup_playwright_mcp()
        setup_proxy_py()
        setup_firefox()
        setup_firefox_profile()
        import_ca_certificates()
        setup_config_file()

        log("=" * 70)
        log("Setup completed successfully!")
        log("=" * 70)

    except Exception as e:
        log(f"Error occurred during setup: {e}", "ERROR")
        import traceback
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)


def check_setup_completed() -> bool:
    """Check if setup is completed"""
    checks = [
        ("certutil", lambda: check_command_exists("certutil")),
        ("@playwright/mcp", lambda: check_npm_package_installed("@playwright/mcp")),
        ("proxy.py", lambda: check_proxy_installed()),
        ("Firefox", lambda: get_installed_firefox_version() is not None),
        ("Firefox profile", lambda: Path("/home/user/firefox-profile/cert9.db").exists()),
        ("MCP configuration file", lambda: (Path(__file__).parent / "playwright-firefox-config.json").exists()),
    ]

    all_ok = True
    for name, check_func in checks:
        if not check_func():
            log(f"{name} is not set up yet", "DEBUG")
            all_ok = False

    return all_ok


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
    """Write JSON-RPC message"""
    try:
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
