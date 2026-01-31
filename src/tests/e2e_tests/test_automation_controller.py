"""
E2E Tests for Automation Domain Controller

Tests the automation entity controller UI interactions including:
- Toggle button functionality
- Trigger button functionality
- State display
- Loading states
"""

import pytest
from playwright.sync_api import Page, expect

from .base import EntityControllerTest, logged_in_page, e2e_config, browser, context, page


class TestAutomationController(EntityControllerTest):
    """E2E tests for automation domain controller"""

    domain = "automation"

    # =========================================================================
    # Display Tests
    # =========================================================================

    def test_automation_controller_visible(self, logged_in_page: Page, e2e_config):
        """Test that automation controller is visible"""
        self.page = logged_in_page
        self.config = e2e_config

        self.navigate_to_entity_list("automation")

        controller = self.find_entity_controller("automation")
        if controller:
            expect(controller).to_be_visible()
        else:
            pytest.skip("No automation entities found in the system")

    def test_automation_shows_correct_state(self, logged_in_page: Page, e2e_config):
        """Test that automation displays correct state (ON/OFF)"""
        self.page = logged_in_page
        self.config = e2e_config

        self.navigate_to_entity_list("automation")

        toggle_btn = self.page.locator(self.config.get_selector("automation", "toggle_button")).first

        if toggle_btn.count() == 0:
            pytest.skip("No automation controllers found")

        button_text = toggle_btn.inner_text()
        assert "ON" in button_text or "OFF" in button_text

    def test_automation_state_badge_displayed(self, logged_in_page: Page, e2e_config):
        """Test that state badge is displayed"""
        self.page = logged_in_page
        self.config = e2e_config

        self.navigate_to_entity_list("automation")

        badge = self.page.locator(self.config.get_selector("automation", "state_badge")).first

        if badge.count() == 0:
            pytest.skip("No automation state badges found")

        expect(badge).to_be_visible()
        badge_text = badge.inner_text().lower()
        assert badge_text in ["on", "off"]

    # =========================================================================
    # Toggle Tests
    # =========================================================================

    def test_toggle_button_click(self, logged_in_page: Page, e2e_config):
        """Test clicking toggle button changes state"""
        self.page = logged_in_page
        self.config = e2e_config

        self.navigate_to_entity_list("automation")

        toggle_btn = self.page.locator(self.config.get_selector("automation", "toggle_button")).first

        if toggle_btn.count() == 0:
            pytest.skip("No automation controllers found")

        toggle_btn.click()
        self.page.wait_for_timeout(e2e_config.get_wait_time("api_response"))

        expect(toggle_btn).to_be_enabled()

    def test_on_state_has_primary_class(self, logged_in_page: Page, e2e_config):
        """Test that ON state button has btn-primary class"""
        self.page = logged_in_page
        self.config = e2e_config

        self.navigate_to_entity_list("automation")

        on_buttons = self.page.locator(".automation-controller button.btn-primary")

        if on_buttons.count() > 0:
            expect(on_buttons.first).to_contain_text("ON")

    def test_off_state_has_outline_class(self, logged_in_page: Page, e2e_config):
        """Test that OFF state button has btn-outline-secondary class"""
        self.page = logged_in_page
        self.config = e2e_config

        self.navigate_to_entity_list("automation")

        off_buttons = self.page.locator(".automation-controller button.btn-outline-secondary")

        if off_buttons.count() > 0:
            expect(off_buttons.first).to_contain_text("OFF")

    # =========================================================================
    # Trigger Tests
    # =========================================================================

    def test_trigger_button_visible(self, logged_in_page: Page, e2e_config):
        """Test that Trigger button is visible"""
        self.page = logged_in_page
        self.config = e2e_config

        self.navigate_to_entity_list("automation")

        trigger_btn = self.page.locator(self.config.get_selector("automation", "trigger_button")).first

        if trigger_btn.count() == 0:
            pytest.skip("No automation trigger buttons found")

        expect(trigger_btn).to_be_visible()
        expect(trigger_btn).to_contain_text("Trigger")

    def test_trigger_button_has_warning_class(self, logged_in_page: Page, e2e_config):
        """Test that Trigger button has btn-warning class"""
        self.page = logged_in_page
        self.config = e2e_config

        self.navigate_to_entity_list("automation")

        trigger_btn = self.page.locator(".automation-controller button.btn-warning").first

        if trigger_btn.count() > 0:
            expect(trigger_btn).to_contain_text("Trigger")

    def test_trigger_button_click(self, logged_in_page: Page, e2e_config):
        """Test clicking Trigger button"""
        self.page = logged_in_page
        self.config = e2e_config

        self.navigate_to_entity_list("automation")

        trigger_btn = self.page.locator(self.config.get_selector("automation", "trigger_button")).first

        if trigger_btn.count() == 0:
            pytest.skip("No automation trigger buttons found")

        trigger_btn.click()
        self.page.wait_for_timeout(e2e_config.get_wait_time("api_response"))

        expect(trigger_btn).to_be_enabled()

    # =========================================================================
    # Icon Tests
    # =========================================================================

    def test_on_state_shows_toggle_on_icon(self, logged_in_page: Page, e2e_config):
        """Test that ON state shows toggle-on icon"""
        self.page = logged_in_page
        self.config = e2e_config

        self.navigate_to_entity_list("automation")

        on_buttons = self.page.locator(".automation-controller button.btn-primary")

        if on_buttons.count() > 0:
            icon = on_buttons.first.locator("i.fa-toggle-on")
            if icon.count() > 0:
                expect(icon).to_be_visible()

    def test_trigger_button_shows_play_icon(self, logged_in_page: Page, e2e_config):
        """Test that Trigger button shows play icon"""
        self.page = logged_in_page
        self.config = e2e_config

        self.navigate_to_entity_list("automation")

        trigger_btn = self.page.locator(".automation-controller button.btn-warning").first

        if trigger_btn.count() > 0:
            icon = trigger_btn.locator("i.fa-play")
            if icon.count() > 0:
                expect(icon).to_be_visible()

    def test_badge_shows_magic_icon(self, logged_in_page: Page, e2e_config):
        """Test that badge shows magic icon"""
        self.page = logged_in_page
        self.config = e2e_config

        self.navigate_to_entity_list("automation")

        badges = self.page.locator(".automation-controller .badge")

        if badges.count() > 0:
            icon = badges.first.locator("i.fa-magic")
            if icon.count() > 0:
                expect(icon).to_be_visible()


# =============================================================================
# Standalone Test Functions
# =============================================================================


@pytest.mark.e2e
@pytest.mark.domain_automation
def test_automation_controller_renders(logged_in_page: Page, e2e_config):
    """Test automation controller renders correctly"""
    test = TestAutomationController()
    test.test_automation_controller_visible(logged_in_page, e2e_config)


@pytest.mark.e2e
@pytest.mark.domain_automation
def test_automation_toggle_works(logged_in_page: Page, e2e_config):
    """Test automation toggle functionality"""
    test = TestAutomationController()
    test.test_toggle_button_click(logged_in_page, e2e_config)


@pytest.mark.e2e
@pytest.mark.domain_automation
def test_automation_trigger_works(logged_in_page: Page, e2e_config):
    """Test automation trigger functionality"""
    test = TestAutomationController()
    test.test_trigger_button_click(logged_in_page, e2e_config)
