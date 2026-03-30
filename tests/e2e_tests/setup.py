#!/usr/bin/env python3
"""
E2E Test Setup Wizard

Interactive setup wizard for configuring E2E tests.
Helps users quickly set up their test environment.

Usage:
    python e2e_tests/setup.py
"""

import os
import sys
from pathlib import Path
from typing import Optional

try:
    import yaml
except ImportError:
    print("PyYAML not installed. Run: pip install pyyaml")
    sys.exit(1)


# ANSI colors
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


def color(text: str, color_code: str) -> str:
    return f"{color_code}{text}{Colors.ENDC}"


def get_input(prompt: str, default: str = "") -> str:
    """Get user input with default value"""
    if default:
        result = input(f"{prompt} [{default}]: ").strip()
        return result if result else default
    return input(f"{prompt}: ").strip()


def get_bool(prompt: str, default: bool = True) -> bool:
    """Get boolean input"""
    default_str = "yes" if default else "no"
    result = input(f"{prompt} (yes/no) [{default_str}]: ").strip().lower()
    if not result:
        return default
    return result in ["yes", "y", "true", "1"]


def check_dependencies():
    """Check and install required dependencies"""
    print(color("\n═══ Checking Dependencies ═══\n", Colors.HEADER))

    deps = {
        "pytest": "pytest",
        "playwright": "playwright",
        "yaml": "pyyaml",
    }

    missing = []
    for module, package in deps.items():
        try:
            __import__(module)
            print(color(f"  ✓ {package}", Colors.GREEN))
        except ImportError:
            print(color(f"  ✗ {package} (missing)", Colors.FAIL))
            missing.append(package)

    # Check pytest-html
    try:
        import pytest_html
        print(color("  ✓ pytest-html", Colors.GREEN))
    except ImportError:
        print(color("  ✗ pytest-html (optional, for HTML reports)", Colors.WARNING))

    if missing:
        print(color(f"\nMissing packages: {', '.join(missing)}", Colors.WARNING))
        install = get_bool("Install missing packages?", True)
        if install:
            import subprocess
            subprocess.run([sys.executable, "-m", "pip", "install"] + missing)
            print(color("✓ Packages installed", Colors.GREEN))

    # Check Playwright browser
    print(color("\nChecking Playwright browser...", Colors.BLUE))
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            p.chromium.launch(headless=True).close()
        print(color("  ✓ Chromium browser installed", Colors.GREEN))
    except Exception as e:
        print(color("  ✗ Chromium browser not installed", Colors.FAIL))
        install = get_bool("Install Playwright Chromium?", True)
        if install:
            import subprocess
            subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"])
            print(color("✓ Chromium installed", Colors.GREEN))


def configure_connection():
    """Configure Odoo connection settings"""
    print(color("\n═══ Odoo Connection Settings ═══\n", Colors.HEADER))

    config = {}

    config["odoo_base_url"] = get_input("Odoo base URL", "http://localhost")

    port = get_input("Odoo port (80 for nginx, 8069 for direct)", "80")
    config["odoo_port"] = int(port)

    config["odoo_database"] = get_input("Database name", "odoo")
    config["odoo_username"] = get_input("Username", "admin")
    config["odoo_password"] = get_input("Password", "admin")

    return config


def configure_browser():
    """Configure browser settings"""
    print(color("\n═══ Browser Settings ═══\n", Colors.HEADER))

    config = {}

    print("Available browsers: chromium, firefox, webkit")
    config["browser"] = get_input("Browser", "chromium")

    config["headless"] = get_bool("Run headless (no visible browser)?", True)

    slow_mo = get_input("Slow motion delay (ms, 0 for none)", "0")
    config["slow_mo"] = int(slow_mo)

    timeout = get_input("Default timeout (ms)", "30000")
    config["timeout"] = int(timeout)

    return config


def configure_testing():
    """Configure testing settings"""
    print(color("\n═══ Testing Settings ═══\n", Colors.HEADER))

    config = {}

    config["screenshot_on_failure"] = get_bool("Take screenshots on failure?", True)
    config["screenshot_dir"] = get_input("Screenshot directory", "e2e_tests/screenshots")

    # Domain settings
    config["domain_tests"] = {}
    print("\nEnable tests for domains:")
    domains = ["switch", "light", "sensor", "climate", "cover", "fan", "automation", "scene", "script"]
    for domain in domains:
        enabled = get_bool(f"  Test {domain}?", True)
        config["domain_tests"][domain] = {"enabled": enabled}

    return config


def test_connection(config: dict) -> bool:
    """Test connection to Odoo"""
    print(color("\n═══ Testing Connection ═══\n", Colors.HEADER))

    try:
        from playwright.sync_api import sync_playwright

        base_url = config["odoo_base_url"]
        port = config["odoo_port"]
        url = f"{base_url}:{port}" if port != 80 else base_url

        print(f"Connecting to {url}...")

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            # Try to load login page
            page.goto(f"{url}/web/login", timeout=10000)
            page.wait_for_load_state("networkidle")

            # Check for login form
            login_input = page.locator("input[name='login']")
            if login_input.count() > 0:
                print(color("✓ Login page accessible", Colors.GREEN))

                # Try to login
                page.fill("input[name='login']", config["odoo_username"])
                page.fill("input[name='password']", config["odoo_password"])

                db_select = page.locator("select[name='db']")
                if db_select.count() > 0:
                    try:
                        db_select.select_option(config["odoo_database"])
                    except Exception:
                        pass

                page.click("button[type='submit']")
                page.wait_for_load_state("networkidle")

                # Check if login succeeded
                navbar = page.locator(".o_main_navbar")
                if navbar.count() > 0:
                    print(color("✓ Login successful", Colors.GREEN))
                    browser.close()
                    return True
                else:
                    print(color("✗ Login failed (check credentials)", Colors.FAIL))
            else:
                print(color("✗ Login page not found", Colors.FAIL))

            browser.close()
            return False

    except Exception as e:
        print(color(f"✗ Connection failed: {e}", Colors.FAIL))
        return False


def save_config(config: dict, path: Path):
    """Save configuration to file"""
    # Add default values
    full_config = {
        **config,
        "ha_instance_name": "Test HA Instance",
        "wait_times": {
            "page_load": 5000,
            "api_response": 3000,
            "animation": 500,
            "debounce": 1000,
        },
        "reporting": {
            "generate_html": True,
            "generate_json": True,
            "output_dir": "e2e_tests/reports",
        },
        "selectors": {
            "entity_card": ".o_kanban_record",
            "entity_controller": ".entity-controller",
            "switch": {
                "controller": ".switch-controller",
                "toggle_button": ".switch-controller button.btn",
                "form_switch": ".switch-controller .form-check-input",
                "state_badge": ".switch-controller .badge",
            },
            "light": {
                "controller": ".light-controller",
                "toggle_button": ".light-controller button.btn",
                "brightness_slider": ".light-controller input[type='range']",
                "brightness_label": ".light-controller .form-label",
                "state_badge": ".light-controller .badge",
            },
            "sensor": {
                "controller": ".sensor-controller",
                "value_badge": ".sensor-controller .badge",
                "device_class": ".sensor-controller .text-muted",
            },
            "climate": {
                "controller": ".climate-controller",
                "temp_badge": ".climate-controller .badge.bg-primary",
                "target_badge": ".climate-controller .badge.bg-success",
                "hvac_badge": ".climate-controller .badge.bg-info",
                "temp_input": ".climate-controller input[type='number']",
                "temp_minus": ".climate-controller button:first-child",
                "temp_plus": ".climate-controller button:last-child",
                "fan_mode_buttons": ".climate-controller .fan-mode-control .btn-group button",
            },
            "cover": {
                "controller": ".cover-controller",
                "open_button": ".cover-controller button.btn-success",
                "stop_button": ".cover-controller button.btn-warning",
                "close_button": ".cover-controller button.btn-danger",
                "position_slider": ".cover-controller input[type='range']",
                "position_label": ".cover-controller .form-label",
                "state_badge": ".cover-controller .badge.bg-info",
            },
            "fan": {
                "controller": ".fan-controller",
                "toggle_button": ".fan-controller button.btn:first-child",
                "speed_slider": ".fan-controller input[type='range']",
                "speed_label": ".fan-controller .speed-control .form-label",
                "oscillate_button": ".fan-controller button.btn-outline-info",
                "preset_select": ".fan-controller select.form-select",
                "state_badge": ".fan-controller .badge:last-child",
            },
            "automation": {
                "controller": ".automation-controller",
                "toggle_button": ".automation-controller button.btn:first-child",
                "trigger_button": ".automation-controller button.btn-warning",
                "state_badge": ".automation-controller .badge:last-child",
            },
            "scene": {
                "controller": ".scene-controller",
                "activate_button": ".scene-controller button.btn-primary",
                "scene_badge": ".scene-controller .badge",
            },
            "script": {
                "controller": ".script-controller",
                "run_button": ".script-controller button.btn-success",
                "toggle_button": ".script-controller button.btn:nth-child(2)",
                "state_badge": ".script-controller .badge:last-child",
            },
        },
    }

    with open(path, "w") as f:
        yaml.dump(full_config, f, default_flow_style=False, allow_unicode=True, sort_keys=False)


def main():
    """Main setup wizard"""
    print(color("\n╔════════════════════════════════════════════════╗", Colors.CYAN))
    print(color("║      E2E Test Setup Wizard                     ║", Colors.CYAN))
    print(color("╚════════════════════════════════════════════════╝\n", Colors.CYAN))

    # Change to project directory
    os.chdir(Path(__file__).parent.parent)

    # Check dependencies
    check_dependencies()

    # Configure connection
    connection_config = configure_connection()

    # Test connection first
    if test_connection(connection_config):
        print(color("\n✓ Connection test passed!", Colors.GREEN))
    else:
        retry = get_bool("\nConnection test failed. Continue anyway?", False)
        if not retry:
            print("Setup cancelled.")
            return

    # Configure browser
    browser_config = configure_browser()

    # Configure testing
    testing_config = configure_testing()

    # Merge configs
    full_config = {
        **connection_config,
        **browser_config,
        **testing_config,
    }

    # Save config
    config_path = Path("e2e_tests/e2e_config.local.yaml")
    print(color(f"\n═══ Saving Configuration ═══\n", Colors.HEADER))
    print(f"Config file: {config_path}")

    save_config(full_config, config_path)
    print(color("✓ Configuration saved!", Colors.GREEN))

    # Create directories
    Path("e2e_tests/screenshots").mkdir(parents=True, exist_ok=True)
    Path("e2e_tests/reports").mkdir(parents=True, exist_ok=True)
    print(color("✓ Directories created!", Colors.GREEN))

    # Summary
    print(color("\n═══ Setup Complete ═══\n", Colors.HEADER))
    print("To run tests:")
    print(color("  python e2e_tests/run_tests.py", Colors.CYAN))
    print("\nTo run interactive mode:")
    print(color("  python e2e_tests/interactive.py", Colors.CYAN))
    print("\nTo create test data:")
    print(color("  python e2e_tests/test_data.py create", Colors.CYAN))
    print()


if __name__ == "__main__":
    main()
