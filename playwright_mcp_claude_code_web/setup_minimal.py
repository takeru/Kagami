#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# ///
"""
Minimal synchronous setup for playwright-mcp
Only installs @playwright/mcp and creates minimal config to get tools/list
"""
import subprocess
import json
import sys
from pathlib import Path


def check_npm_package(package_name: str) -> bool:
    """Check if npm package is installed globally"""
    try:
        result = subprocess.run(
            ["npm", "list", "-g", package_name],
            capture_output=True,
            text=True,
            timeout=10
        )
        return result.returncode == 0
    except Exception:
        return False


def install_playwright_mcp() -> bool:
    """Install @playwright/mcp globally"""
    try:
        print("Installing @playwright/mcp...", file=sys.stderr, flush=True)
        result = subprocess.run(
            ["npm", "install", "-g", "@playwright/mcp"],
            capture_output=True,
            text=True,
            timeout=120
        )
        if result.returncode != 0:
            print(f"Failed to install @playwright/mcp: {result.stderr}", file=sys.stderr)
            return False
        print("@playwright/mcp installed successfully", file=sys.stderr, flush=True)
        return True
    except Exception as e:
        print(f"Error installing @playwright/mcp: {e}", file=sys.stderr)
        return False


def create_minimal_config() -> bool:
    """Create minimal playwright-mcp config file"""
    try:
        script_dir = Path(__file__).parent
        config_path = script_dir / "playwright-firefox-config.json"

        # Minimal config (will be deleted and replaced by setup_mcp.py)
        config = {
            "browser": "firefox",
            "headless": True
        }

        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)

        print(f"Created minimal config: {config_path}", file=sys.stderr, flush=True)
        return True
    except Exception as e:
        print(f"Error creating config: {e}", file=sys.stderr)
        return False


def main():
    """Run minimal synchronous setup"""
    print("=== Minimal Synchronous Setup ===", file=sys.stderr, flush=True)

    # Check and install @playwright/mcp
    if not check_npm_package("@playwright/mcp"):
        print("@playwright/mcp not found, installing...", file=sys.stderr, flush=True)
        if not install_playwright_mcp():
            print("ERROR: Failed to install @playwright/mcp", file=sys.stderr)
            return False
    else:
        print("@playwright/mcp already installed", file=sys.stderr, flush=True)

    # Create minimal config
    if not create_minimal_config():
        print("ERROR: Failed to create config", file=sys.stderr)
        return False

    print("=== Minimal setup completed ===", file=sys.stderr, flush=True)
    return True


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
