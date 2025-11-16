#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# ///
"""
Playwright MCP Server Launch Script for Claude Code

Communication flow:
  Claude Code → mcp.py → playwright-mcp (Firefox) → proxy.py → JWT Auth Proxy → Internet

This script:
  1. Automatically runs required setup on first startup
  2. Starts proxy.py in the background
  3. Launches playwright-mcp in stdio mode
  4. Stops proxy.py on exit
"""
import os
import sys
import subprocess
import time
import atexit
import signal
import json
from pathlib import Path
from typing import Optional

# Global variable to hold proxy.py process
proxy_process = None


def log(message: str, level: str = "INFO"):
    """Log output (outputs to stderr)"""
    prefix = {
        "INFO": "✓",
        "WARN": "⚠️",
        "ERROR": "❌",
        "DEBUG": "🔍"
    }.get(level, "ℹ️")
    print(f"{prefix} {message}", file=sys.stderr)


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
    """Install Firefox build v1496"""
    log("Checking Firefox build v1496 installation status...")

    firefox_build = Path("/home/user/.cache/ms-playwright/firefox-1496")

    if firefox_build.exists():
        log(f"Firefox build v1496 is already installed: {firefox_build}")
        return

    log("Installing Firefox build v1496... (may take several minutes)", "WARN")

    env = os.environ.copy()
    env["HOME"] = "/home/user"

    run_command([
        "node",
        "/opt/node22/lib/node_modules/@playwright/mcp/node_modules/playwright/cli.js",
        "install",
        "firefox"
    ])

    log("Firefox build v1496 installed")


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
        ("Firefox", lambda: Path("/home/user/.cache/ms-playwright/firefox-1496").exists()),
        ("Firefox profile", lambda: Path("/home/user/firefox-profile/cert9.db").exists()),
        ("MCP configuration file", lambda: (Path(__file__).parent / "playwright-firefox-config.json").exists()),
    ]

    all_ok = True
    for name, check_func in checks:
        if not check_func():
            log(f"{name} is not set up yet", "DEBUG")
            all_ok = False

    return all_ok


def start_proxy():
    """Start proxy.py"""
    global proxy_process

    # Check HTTPS_PROXY environment variable
    https_proxy = os.environ.get('HTTPS_PROXY', '')
    if not https_proxy:
        log("HTTPS_PROXY environment variable not set", "ERROR")
        sys.exit(1)

    log(f"Starting proxy.py... (proxy: {https_proxy[:50]}...)")

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


def stop_proxy():
    """Stop proxy.py"""
    global proxy_process

    if proxy_process is None:
        return

    log("Stopping proxy.py...")

    try:
        proxy_process.send_signal(signal.SIGTERM)
        proxy_process.wait(timeout=5)
        log("proxy.py stopped")
    except subprocess.TimeoutExpired:
        proxy_process.kill()
        log("proxy.py force terminated", "WARN")
    except Exception as e:
        log(f"Error stopping proxy.py: {e}", "WARN")


def main():
    """Main process"""
    # Set HOME environment variable
    os.environ['HOME'] = '/home/user'

    # Check setup status
    if not check_setup_completed():
        log("Running first-time setup...")
        run_setup()
    else:
        log("Setup already completed")

    # Register to stop proxy.py on exit
    atexit.register(stop_proxy)

    # Start proxy.py
    start_proxy()

    # playwright-mcp configuration file path
    script_dir = Path(__file__).parent
    config_path = str(script_dir / "playwright-firefox-config.json")

    if not os.path.exists(config_path):
        log(f"Configuration file not found: {config_path}", "ERROR")
        sys.exit(1)

    log(f"Configuration file: {config_path}")
    log("Starting playwright-mcp...")

    # Launch playwright-mcp (stdio mode)
    cmd = [
        'node',
        '/opt/node22/lib/node_modules/@playwright/mcp/cli.js',
        '--config', config_path,
        '--browser', 'firefox',
        '--proxy-server', 'http://127.0.0.1:18915'
    ]

    # Prepare environment variables
    env = os.environ.copy()
    env['HOME'] = '/home/user'

    # Run playwright-mcp (stdio mode)
    # Claude Code sends MCP protocol requests from stdin,
    # and receives responses via stdout
    try:
        subprocess.run(cmd, env=env)
    except KeyboardInterrupt:
        log("\nInterrupted")
    except Exception as e:
        log(f"\nError: {e}", "ERROR")
        sys.exit(1)


if __name__ == '__main__':
    main()
