#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# ///
"""
Setup Script for Playwright MCP Server

This script sets up the following:
  1. certutil installation
  2. @playwright/mcp installation
  3. proxy.py installation
  4. Firefox installation
  5. Firefox profile creation
  6. CA certificate import
  7. MCP configuration file creation

Automatically called from SessionStart hook.
"""
import os
import sys
import subprocess
import json
from pathlib import Path
from typing import Optional


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


def check_setup_completed() -> bool:
    """Check if setup is completed"""
    script_dir = Path(__file__).parent

    checks = [
        ("certutil", lambda: check_command_exists("certutil")),
        ("@playwright/mcp", lambda: check_npm_package_installed("@playwright/mcp")),
        ("proxy.py", lambda: check_proxy_installed()),
        ("Firefox", lambda: get_installed_firefox_version() is not None),
        ("Firefox profile", lambda: Path("/home/user/firefox-profile/cert9.db").exists()),
        ("MCP configuration file", lambda: (script_dir / "playwright-firefox-config.json").exists()),
    ]

    all_ok = True
    for name, check_func in checks:
        if not check_func():
            log(f"{name} is not set up yet", "DEBUG")
            all_ok = False

    return all_ok


def main():
    """Main process"""
    # Set HOME environment variable
    os.environ['HOME'] = '/home/user'

    log("=" * 70)
    log("Playwright MCP - Starting setup")
    log("=" * 70)

    try:
        # Check setup status
        if check_setup_completed():
            log("Setup is already completed")
            log("=" * 70)
            return 0

        # Run setup
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
        return 0

    except Exception as e:
        log(f"Error occurred during setup: {e}", "ERROR")
        import traceback
        traceback.print_exc(file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
