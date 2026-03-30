#!/usr/bin/env python3
"""
Interactive E2E Test Mode

Provides an interactive interface for running and debugging E2E tests.
Supports step-by-step execution, breakpoints, and live browser inspection.

Usage:
    python e2e_tests/interactive.py

Features:
    - Interactive domain/test selection
    - Step-by-step test execution
    - Live browser inspection mode
    - Quick entity state checking
    - Test result recording
"""

import os
import sys
import time
from pathlib import Path
from typing import Optional, List, Dict

try:
    from playwright.sync_api import sync_playwright, Page, Browser
except ImportError:
    print("Playwright not installed. Run: pip install playwright && playwright install chromium")
    sys.exit(1)

try:
    from .config import get_config, E2EConfig
except ImportError:
    # Direct execution
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from e2e_tests.config import get_config, E2EConfig


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
    """Apply color to text"""
    return f"{color_code}{text}{Colors.ENDC}"


DOMAINS = [
    "switch", "light", "sensor", "climate",
    "cover", "fan", "automation", "scene", "script"
]

DOMAIN_ACTIONS = {
    "switch": ["toggle", "view_state"],
    "light": ["toggle", "set_brightness", "view_state"],
    "sensor": ["view_state"],
    "climate": ["set_temperature", "set_fan_mode", "view_state"],
    "cover": ["open", "close", "stop", "set_position", "view_state"],
    "fan": ["toggle", "set_speed", "oscillate", "preset_mode", "view_state"],
    "automation": ["toggle", "trigger", "view_state"],
    "scene": ["activate", "view_state"],
    "script": ["run", "toggle", "view_state"],
}


class InteractiveTestRunner:
    """Interactive test runner with live browser control"""

    def __init__(self):
        self.config: E2EConfig = get_config()
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self.logged_in = False

    def start(self):
        """Start the interactive session"""
        print(color("\n╔════════════════════════════════════════════════╗", Colors.CYAN))
        print(color("║     Entity Controller E2E Interactive Mode     ║", Colors.CYAN))
        print(color("╚════════════════════════════════════════════════╝\n", Colors.CYAN))

        self._launch_browser()
        self._main_menu()

    def _launch_browser(self):
        """Launch browser in headed mode"""
        print(color("Launching browser...", Colors.BLUE))
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(
            headless=False,
            slow_mo=100,
        )
        context = self.browser.new_context(
            viewport={"width": 1400, "height": 900},
        )
        self.page = context.new_page()
        print(color("✓ Browser ready\n", Colors.GREEN))

    def _login(self):
        """Login to Odoo"""
        if self.logged_in:
            return True

        print(color("Logging in to Odoo...", Colors.BLUE))
        try:
            self.page.goto(self.config.login_url)
            self.page.wait_for_load_state("networkidle")

            self.page.fill("input[name='login']", self.config.odoo_username)
            self.page.fill("input[name='password']", self.config.odoo_password)

            db_select = self.page.locator("select[name='db']")
            if db_select.count() > 0:
                db_select.select_option(self.config.odoo_database)

            self.page.click("button[type='submit']")
            self.page.wait_for_load_state("networkidle")

            # Verify login
            navbar = self.page.locator(".o_main_navbar")
            navbar.wait_for(timeout=10000)
            self.logged_in = True
            print(color("✓ Logged in successfully\n", Colors.GREEN))
            return True
        except Exception as e:
            print(color(f"✗ Login failed: {e}\n", Colors.FAIL))
            return False

    def _main_menu(self):
        """Main interactive menu"""
        while True:
            print(color("\n═══ Main Menu ═══", Colors.HEADER))
            print("1. Test by Domain")
            print("2. Browse All Entities")
            print("3. Quick Actions")
            print("4. Configuration")
            print("5. Run Automated Tests")
            print("0. Exit")

            choice = input(color("\nSelect option: ", Colors.CYAN)).strip()

            if choice == "1":
                self._domain_menu()
            elif choice == "2":
                self._browse_entities()
            elif choice == "3":
                self._quick_actions()
            elif choice == "4":
                self._config_menu()
            elif choice == "5":
                self._run_tests_menu()
            elif choice == "0":
                self._cleanup()
                break
            else:
                print(color("Invalid option", Colors.WARNING))

    def _domain_menu(self):
        """Domain selection menu"""
        print(color("\n═══ Select Domain ═══", Colors.HEADER))
        for i, domain in enumerate(DOMAINS, 1):
            print(f"{i}. {domain.capitalize()}")
        print("0. Back")

        choice = input(color("\nSelect domain: ", Colors.CYAN)).strip()

        if choice == "0":
            return

        try:
            idx = int(choice) - 1
            if 0 <= idx < len(DOMAINS):
                self._domain_actions(DOMAINS[idx])
        except ValueError:
            print(color("Invalid option", Colors.WARNING))

    def _domain_actions(self, domain: str):
        """Show actions for a domain"""
        if not self._login():
            return

        # Navigate to domain
        self._navigate_to_domain(domain)

        while True:
            actions = DOMAIN_ACTIONS.get(domain, ["view_state"])
            print(color(f"\n═══ {domain.upper()} Actions ═══", Colors.HEADER))
            for i, action in enumerate(actions, 1):
                print(f"{i}. {action.replace('_', ' ').title()}")
            print("r. Refresh page")
            print("s. Take screenshot")
            print("0. Back")

            choice = input(color("\nSelect action: ", Colors.CYAN)).strip().lower()

            if choice == "0":
                break
            elif choice == "r":
                self.page.reload()
                print(color("✓ Page refreshed", Colors.GREEN))
            elif choice == "s":
                self._take_screenshot(f"{domain}_screenshot")
            else:
                try:
                    idx = int(choice) - 1
                    if 0 <= idx < len(actions):
                        self._execute_action(domain, actions[idx])
                except ValueError:
                    print(color("Invalid option", Colors.WARNING))

    def _navigate_to_domain(self, domain: str):
        """Navigate to entity list filtered by domain"""
        print(color(f"Navigating to {domain} entities...", Colors.BLUE))
        url = f"{self.config.base_url}/web#model=ha.entity&view_type=kanban&domain=[('domain','=','{domain}')]"
        self.page.goto(url)
        self.page.wait_for_load_state("networkidle")
        time.sleep(1)  # Let UI settle
        print(color("✓ Navigation complete", Colors.GREEN))

    def _execute_action(self, domain: str, action: str):
        """Execute a domain action"""
        selector_map = {
            "toggle": self._find_toggle_button,
            "set_brightness": self._find_brightness_slider,
            "set_temperature": self._find_temperature_input,
            "set_fan_mode": self._find_fan_mode_buttons,
            "open": lambda: self.page.locator("button:has-text('Open')").first,
            "close": lambda: self.page.locator("button:has-text('Close')").first,
            "stop": lambda: self.page.locator("button:has-text('Stop')").first,
            "set_position": lambda: self.page.locator(".cover-controller input[type='range']").first,
            "set_speed": lambda: self.page.locator(".fan-controller input[type='range']").first,
            "oscillate": lambda: self.page.locator("button:has-text('Oscillate')").first,
            "preset_mode": lambda: self.page.locator(".fan-controller select").first,
            "trigger": lambda: self.page.locator("button:has-text('Trigger')").first,
            "activate": lambda: self.page.locator("button:has-text('Activate')").first,
            "run": lambda: self.page.locator("button:has-text('Run')").first,
            "view_state": self._view_state,
        }

        if action == "view_state":
            self._view_state(domain)
            return

        finder = selector_map.get(action)
        if not finder:
            print(color(f"Action not implemented: {action}", Colors.WARNING))
            return

        try:
            element = finder()
            if element and element.count() > 0:
                if "slider" in action or "input" in action or action in ["set_brightness", "set_position", "set_speed"]:
                    value = input(color("Enter value (0-100 or 0-255): ", Colors.CYAN)).strip()
                    element.fill(value)
                    element.dispatch_event("change")
                elif action == "set_temperature":
                    value = input(color("Enter temperature (10-35): ", Colors.CYAN)).strip()
                    element.fill(value)
                    element.dispatch_event("change")
                elif action == "preset_mode":
                    # Show options
                    options = element.locator("option").all_text_contents()
                    print("Available modes:", ", ".join(options))
                    mode = input(color("Enter mode: ", Colors.CYAN)).strip()
                    element.select_option(mode)
                else:
                    element.click()

                print(color(f"✓ Action '{action}' executed", Colors.GREEN))
                time.sleep(1)  # Let state update
            else:
                print(color(f"Element not found for action: {action}", Colors.WARNING))
        except Exception as e:
            print(color(f"✗ Action failed: {e}", Colors.FAIL))

    def _find_toggle_button(self):
        """Find toggle button"""
        selectors = [
            "button:has-text('ON')",
            "button:has-text('OFF')",
            ".form-check-input",
        ]
        for sel in selectors:
            el = self.page.locator(sel).first
            if el.count() > 0:
                return el
        return None

    def _find_brightness_slider(self):
        """Find brightness slider"""
        return self.page.locator(".light-controller input[type='range']").first

    def _find_temperature_input(self):
        """Find temperature input"""
        return self.page.locator(".climate-controller input[type='number']").first

    def _find_fan_mode_buttons(self):
        """Find fan mode buttons"""
        buttons = self.page.locator(".climate-controller .fan-mode-control button")
        if buttons.count() > 0:
            print("Available fan modes:")
            for i in range(buttons.count()):
                print(f"  {i+1}. {buttons.nth(i).inner_text()}")
            idx = int(input(color("Select mode number: ", Colors.CYAN)).strip()) - 1
            return buttons.nth(idx)
        return None

    def _view_state(self, domain: str = None):
        """View current entity states"""
        print(color("\n═══ Current States ═══", Colors.HEADER))

        badges = self.page.locator(".badge")
        for i in range(min(badges.count(), 10)):  # Limit to 10
            text = badges.nth(i).inner_text()
            print(f"  • {text}")

    def _browse_entities(self):
        """Browse all entities"""
        if not self._login():
            return

        print(color("\nNavigating to all entities...", Colors.BLUE))
        url = f"{self.config.base_url}/web#model=ha.entity&view_type=kanban"
        self.page.goto(url)
        self.page.wait_for_load_state("networkidle")

        print(color("✓ Browse mode - use browser to interact", Colors.GREEN))
        input(color("Press Enter to return to menu...", Colors.CYAN))

    def _quick_actions(self):
        """Quick actions menu"""
        print(color("\n═══ Quick Actions ═══", Colors.HEADER))
        print("1. Toggle first switch")
        print("2. Refresh all entities")
        print("3. Go to HA Dashboard")
        print("4. Take full page screenshot")
        print("0. Back")

        choice = input(color("\nSelect action: ", Colors.CYAN)).strip()

        if choice == "0":
            return

        if not self._login():
            return

        if choice == "1":
            self._navigate_to_domain("switch")
            toggle = self._find_toggle_button()
            if toggle:
                toggle.click()
                print(color("✓ Switch toggled", Colors.GREEN))
        elif choice == "2":
            self.page.reload()
            print(color("✓ Page refreshed", Colors.GREEN))
        elif choice == "3":
            self.page.goto(self.config.dashboard_url)
            print(color("✓ Navigated to dashboard", Colors.GREEN))
        elif choice == "4":
            self._take_screenshot("full_page", full_page=True)

    def _config_menu(self):
        """Configuration menu"""
        print(color("\n═══ Current Configuration ═══", Colors.HEADER))
        print(f"  Base URL: {self.config.base_url}")
        print(f"  Database: {self.config.odoo_database}")
        print(f"  Username: {self.config.odoo_username}")
        print(f"  Browser: {self.config.browser}")
        print(f"  Timeout: {self.config.timeout}ms")

        print(color("\n═══ Options ═══", Colors.HEADER))
        print("1. Edit base URL")
        print("2. Edit credentials")
        print("3. Reload config from file")
        print("0. Back")

        choice = input(color("\nSelect option: ", Colors.CYAN)).strip()

        if choice == "1":
            new_url = input(color("Enter new base URL: ", Colors.CYAN)).strip()
            if new_url:
                self.config.odoo_base_url = new_url
                self.logged_in = False
                print(color("✓ URL updated. Re-login required.", Colors.GREEN))
        elif choice == "2":
            self.config.odoo_username = input(color("Username: ", Colors.CYAN)).strip() or self.config.odoo_username
            self.config.odoo_password = input(color("Password: ", Colors.CYAN)).strip() or self.config.odoo_password
            self.logged_in = False
            print(color("✓ Credentials updated. Re-login required.", Colors.GREEN))
        elif choice == "3":
            from .config import reset_config
            reset_config()
            self.config = get_config()
            self.logged_in = False
            print(color("✓ Config reloaded", Colors.GREEN))

    def _run_tests_menu(self):
        """Run automated tests menu"""
        print(color("\n═══ Run Automated Tests ═══", Colors.HEADER))
        print("1. Run all tests")
        for i, domain in enumerate(DOMAINS, 2):
            print(f"{i}. Run {domain} tests")
        print("0. Back")

        choice = input(color("\nSelect option: ", Colors.CYAN)).strip()

        if choice == "0":
            return

        import subprocess

        if choice == "1":
            cmd = ["python", "-m", "pytest", "e2e_tests/", "-v", "--headless=false"]
        else:
            try:
                idx = int(choice) - 2
                if 0 <= idx < len(DOMAINS):
                    domain = DOMAINS[idx]
                    cmd = ["python", "-m", "pytest", "e2e_tests/", "-v", "-m", f"domain_{domain}", "--headless=false"]
                else:
                    return
            except ValueError:
                return

        print(color(f"\nRunning: {' '.join(cmd)}\n", Colors.BLUE))
        subprocess.run(cmd)

    def _take_screenshot(self, name: str, full_page: bool = False):
        """Take a screenshot"""
        screenshot_dir = Path(self.config.screenshot_dir)
        screenshot_dir.mkdir(parents=True, exist_ok=True)

        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filepath = screenshot_dir / f"{name}_{timestamp}.png"

        self.page.screenshot(path=str(filepath), full_page=full_page)
        print(color(f"✓ Screenshot saved: {filepath}", Colors.GREEN))

    def _cleanup(self):
        """Cleanup resources"""
        print(color("\nClosing browser...", Colors.BLUE))
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()
        print(color("✓ Goodbye!\n", Colors.GREEN))


def main():
    """Main entry point"""
    # Change to project directory
    os.chdir(Path(__file__).parent.parent)

    runner = InteractiveTestRunner()
    try:
        runner.start()
    except KeyboardInterrupt:
        print(color("\n\nInterrupted by user", Colors.WARNING))
        runner._cleanup()


if __name__ == "__main__":
    main()
