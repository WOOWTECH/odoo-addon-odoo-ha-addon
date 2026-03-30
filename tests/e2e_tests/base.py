"""
Base E2E Test Classes for Entity Controller Tests

Provides common functionality for all domain-specific E2E tests using Playwright.
"""

import os
import pytest
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, Generator
from playwright.sync_api import Page, Browser, BrowserContext, expect, Locator

from .config import E2EConfig, get_config


class BaseE2ETest:
    """Base class for all E2E tests"""

    config: E2EConfig = None
    page: Page = None
    browser: Browser = None
    context: BrowserContext = None

    @classmethod
    def setup_class(cls):
        """Class-level setup"""
        cls.config = get_config()

    def setup_method(self, method):
        """Method-level setup - called before each test"""
        pass

    def teardown_method(self, method):
        """Method-level teardown - called after each test"""
        if self.config.screenshot_on_failure:
            # Check if test failed
            if hasattr(method, "rep_call") and method.rep_call.failed:
                self._take_screenshot(f"failure_{method.__name__}")

    def _take_screenshot(self, name: str):
        """Take a screenshot"""
        if self.page:
            screenshot_dir = Path(self.config.screenshot_dir)
            screenshot_dir.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = screenshot_dir / f"{name}_{timestamp}.png"
            self.page.screenshot(path=str(filepath))
            print(f"Screenshot saved: {filepath}")

    def wait_for_api(self):
        """Wait for API response"""
        self.page.wait_for_timeout(self.config.get_wait_time("api_response"))

    def wait_for_animation(self):
        """Wait for animation to complete"""
        self.page.wait_for_timeout(self.config.get_wait_time("animation"))

    def wait_for_debounce(self):
        """Wait for debounce timeout"""
        self.page.wait_for_timeout(self.config.get_wait_time("debounce"))


class OdooE2ETest(BaseE2ETest):
    """Base class for Odoo-specific E2E tests"""

    logged_in: bool = False

    def login(self):
        """Login to Odoo"""
        if self.logged_in:
            return

        self.page.goto(self.config.login_url)
        self.page.wait_for_load_state("networkidle")

        # Fill login form
        self.page.fill("input[name='login']", self.config.odoo_username)
        self.page.fill("input[name='password']", self.config.odoo_password)

        # Select database if dropdown exists
        db_select = self.page.locator("select[name='db']")
        if db_select.count() > 0:
            db_select.select_option(self.config.odoo_database)

        # Click login button
        self.page.click("button[type='submit']")
        self.page.wait_for_load_state("networkidle")

        # Verify login success
        expect(self.page.locator(".o_main_navbar")).to_be_visible()
        self.logged_in = True

    def navigate_to_dashboard(self):
        """Navigate to the HA dashboard"""
        self.page.goto(self.config.dashboard_url)
        self.page.wait_for_load_state("networkidle")
        self.page.wait_for_timeout(self.config.get_wait_time("page_load"))

    def navigate_to_entity_list(self, domain: Optional[str] = None):
        """Navigate to the entity list view"""
        url = f"{self.config.base_url}/web#model=ha.entity&view_type=kanban"
        if domain:
            url += f"&domain=[('domain','=','{domain}')]"
        self.page.goto(url)
        self.page.wait_for_load_state("networkidle")
        self.page.wait_for_timeout(self.config.get_wait_time("page_load"))

    def find_entity_by_id(self, entity_id: str) -> Optional[Locator]:
        """Find an entity card by entity_id"""
        # Look for entity card containing the entity_id
        cards = self.page.locator(self.config.selectors.get("entity_card", ".o_kanban_record"))
        for i in range(cards.count()):
            card = cards.nth(i)
            if entity_id in card.inner_text():
                return card
        return None

    def find_entity_controller(self, domain: str) -> Optional[Locator]:
        """Find the entity controller for a domain"""
        selector = self.config.get_selector(domain, "controller")
        if selector:
            return self.page.locator(selector).first
        return None

    def get_element(self, domain: str, element: str) -> Locator:
        """Get a specific element for a domain"""
        selector = self.config.get_selector(domain, element)
        return self.page.locator(selector).first


class EntityControllerTest(OdooE2ETest):
    """Base class for entity controller E2E tests"""

    domain: str = None

    def setup_method(self, method):
        """Setup for each test method"""
        super().setup_method(method)

        # Check if domain tests are enabled
        if self.domain and not self.config.is_domain_enabled(self.domain):
            pytest.skip(f"{self.domain} tests are disabled in config")

    def get_test_entity(self) -> Dict:
        """Get the test entity configuration"""
        if not self.domain:
            raise ValueError("domain must be set in subclass")
        entity_config = self.config.get_entity_config(self.domain)
        if not entity_config:
            pytest.skip(f"No test entity configured for {self.domain}")
        return entity_config

    def get_domain_config(self) -> Dict:
        """Get the domain test configuration"""
        if not self.domain:
            raise ValueError("domain must be set in subclass")
        return self.config.get_domain_test_config(self.domain) or {}

    def navigate_to_test_entity(self):
        """Navigate to the test entity"""
        self.login()
        entity = self.get_test_entity()
        self.navigate_to_entity_list(self.domain)

        # Wait for entity controller to be visible
        controller = self.find_entity_controller(self.domain)
        if controller:
            expect(controller).to_be_visible(timeout=self.config.timeout)

    def get_state_badge(self) -> Locator:
        """Get the state badge element"""
        return self.get_element(self.domain, "state_badge")

    def expect_state(self, expected_state: str):
        """Assert the entity is in expected state"""
        badge = self.get_state_badge()
        expect(badge).to_contain_text(expected_state)

    def expect_loading(self):
        """Assert loading spinner is visible"""
        spinner = self.page.locator("i.fa-spinner.fa-spin").first
        expect(spinner).to_be_visible()

    def expect_not_loading(self):
        """Assert loading spinner is not visible"""
        spinner = self.page.locator("i.fa-spinner.fa-spin")
        expect(spinner).to_have_count(0)


# =============================================================================
# Pytest Fixtures
# =============================================================================


@pytest.fixture(scope="session")
def e2e_config() -> E2EConfig:
    """Provide E2E configuration"""
    config_file = os.environ.get("E2E_CONFIG_FILE")
    return get_config(config_file)


@pytest.fixture(scope="session")
def browser(e2e_config: E2EConfig) -> Generator[Browser, None, None]:
    """Provide browser instance"""
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser_type = getattr(p, e2e_config.browser)
        browser = browser_type.launch(
            headless=e2e_config.headless,
            slow_mo=e2e_config.slow_mo,
        )
        yield browser
        browser.close()


@pytest.fixture(scope="function")
def context(browser: Browser, e2e_config: E2EConfig) -> Generator[BrowserContext, None, None]:
    """Provide browser context for each test"""
    context = browser.new_context(
        viewport={"width": 1920, "height": 1080},
        ignore_https_errors=True,
    )
    context.set_default_timeout(e2e_config.timeout)
    yield context
    context.close()


@pytest.fixture(scope="function")
def page(context: BrowserContext) -> Generator[Page, None, None]:
    """Provide page for each test"""
    page = context.new_page()
    yield page
    page.close()


@pytest.fixture(scope="function")
def logged_in_page(page: Page, e2e_config: E2EConfig) -> Generator[Page, None, None]:
    """Provide a logged-in page"""
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

    yield page


# =============================================================================
# Test Markers
# =============================================================================

def requires_ha_instance(func):
    """Decorator to mark tests that require a Home Assistant instance"""
    return pytest.mark.requires_ha(func)


def domain_test(domain: str):
    """Decorator to mark tests for a specific domain"""
    def decorator(func):
        return pytest.mark.domain(domain)(func)
    return decorator
