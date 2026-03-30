"""
Pytest Configuration for E2E Tests

This module configures pytest fixtures and markers for E2E testing
of entity controller components.
"""

import os
import pytest
from pathlib import Path


def pytest_configure(config):
    """Configure custom pytest markers"""
    config.addinivalue_line("markers", "e2e: mark test as end-to-end test")
    config.addinivalue_line("markers", "domain_switch: mark test for switch domain")
    config.addinivalue_line("markers", "domain_light: mark test for light domain")
    config.addinivalue_line("markers", "domain_sensor: mark test for sensor domain")
    config.addinivalue_line("markers", "domain_climate: mark test for climate domain")
    config.addinivalue_line("markers", "domain_cover: mark test for cover domain")
    config.addinivalue_line("markers", "domain_fan: mark test for fan domain")
    config.addinivalue_line("markers", "domain_automation: mark test for automation domain")
    config.addinivalue_line("markers", "domain_scene: mark test for scene domain")
    config.addinivalue_line("markers", "domain_script: mark test for script domain")
    config.addinivalue_line("markers", "requires_ha: mark test as requiring Home Assistant connection")


def pytest_addoption(parser):
    """Add custom command line options"""
    parser.addoption(
        "--config-file",
        action="store",
        default=None,
        help="Path to E2E config YAML file",
    )
    parser.addoption(
        "--domain",
        action="store",
        default=None,
        help="Run tests only for specific domain (switch, light, sensor, etc.)",
    )
    parser.addoption(
        "--headless",
        action="store",
        default=None,
        help="Run browser in headless mode (true/false)",
    )
    parser.addoption(
        "--slow-mo",
        action="store",
        type=int,
        default=None,
        help="Slow down browser actions by X milliseconds",
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection based on command line options"""
    domain_filter = config.getoption("--domain")

    if domain_filter:
        skip_marker = pytest.mark.skip(reason=f"Skipping: only running {domain_filter} domain tests")
        for item in items:
            # Check if test has the matching domain marker
            domain_markers = [m for m in item.iter_markers() if m.name.startswith("domain_")]
            if domain_markers:
                has_matching_domain = any(m.name == f"domain_{domain_filter}" for m in domain_markers)
                if not has_matching_domain:
                    item.add_marker(skip_marker)


@pytest.fixture(scope="session")
def e2e_config():
    """Provide E2E configuration"""
    from .config import get_config

    config_file = os.environ.get("E2E_CONFIG_FILE")
    return get_config(config_file)


@pytest.fixture(scope="session")
def browser(e2e_config, request):
    """Provide browser instance"""
    from playwright.sync_api import sync_playwright

    # Check for command line overrides
    headless_opt = request.config.getoption("--headless")
    slow_mo_opt = request.config.getoption("--slow-mo")

    headless = e2e_config.headless
    slow_mo = e2e_config.slow_mo

    if headless_opt is not None:
        headless = headless_opt.lower() == "true"
    if slow_mo_opt is not None:
        slow_mo = slow_mo_opt

    with sync_playwright() as p:
        browser_type = getattr(p, e2e_config.browser)
        browser = browser_type.launch(
            headless=headless,
            slow_mo=slow_mo,
        )
        yield browser
        browser.close()


@pytest.fixture(scope="function")
def context(browser, e2e_config):
    """Provide browser context for each test"""
    context = browser.new_context(
        viewport={"width": 1920, "height": 1080},
        ignore_https_errors=True,
    )
    context.set_default_timeout(e2e_config.timeout)
    yield context
    context.close()


@pytest.fixture(scope="function")
def page(context):
    """Provide page for each test"""
    page = context.new_page()
    yield page
    page.close()


@pytest.fixture(scope="function")
def logged_in_page(page, e2e_config):
    """Provide a logged-in page"""
    from playwright.sync_api import expect

    # Navigate to login
    page.goto(e2e_config.login_url)
    page.wait_for_load_state("networkidle")

    # Fill login form
    page.fill("input[name='login']", e2e_config.odoo_username)
    page.fill("input[name='password']", e2e_config.odoo_password)

    # Select database if needed
    db_select = page.locator("select[name='db']")
    if db_select.count() > 0:
        db_select.select_option(e2e_config.odoo_database)

    # Submit login
    page.click("button[type='submit']")
    page.wait_for_load_state("networkidle")

    # Verify login success
    try:
        expect(page.locator(".o_main_navbar")).to_be_visible(timeout=10000)
    except Exception:
        # Handle login failure
        pass

    yield page


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Take screenshot on test failure"""
    outcome = yield
    rep = outcome.get_result()

    if rep.when == "call" and rep.failed:
        # Get page fixture if available
        page = item.funcargs.get("page") or item.funcargs.get("logged_in_page")
        if page:
            try:
                # Get config for screenshot directory
                e2e_config = item.funcargs.get("e2e_config")
                screenshot_dir = Path(e2e_config.screenshot_dir if e2e_config else "e2e_tests/screenshots")
                screenshot_dir.mkdir(parents=True, exist_ok=True)

                # Take screenshot
                screenshot_path = screenshot_dir / f"failure_{item.name}.png"
                page.screenshot(path=str(screenshot_path))
                print(f"\nScreenshot saved: {screenshot_path}")
            except Exception as e:
                print(f"\nFailed to take screenshot: {e}")


def pytest_html_report_title(report):
    """Set HTML report title"""
    report.title = "Entity Controller E2E Test Report"
