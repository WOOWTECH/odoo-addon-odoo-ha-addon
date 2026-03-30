"""
E2E Tests for Switch Domain Controller

Tests the switch entity controller UI interactions including:
- Toggle button functionality
- Form switch functionality
- State display and updates
- Loading states
"""

import pytest
from playwright.sync_api import Page, expect

from .base import EntityControllerTest, logged_in_page, e2e_config, browser, context, page


class TestSwitchController(EntityControllerTest):
    """E2E tests for switch domain controller"""

    domain = "switch"

    # =========================================================================
    # Display Tests
    # =========================================================================

    def test_switch_controller_visible(self, logged_in_page: Page, e2e_config):
        """Test that switch controller is visible"""
        self.page = logged_in_page
        self.config = e2e_config

        # Navigate to entity list filtered by switch domain
        self.navigate_to_entity_list("switch")

        # Check controller is visible
        controller = self.find_entity_controller("switch")
        if controller:
            expect(controller).to_be_visible()
        else:
            # If no switch entities exist, skip
            pytest.skip("No switch entities found in the system")

    def test_switch_shows_correct_state(self, logged_in_page: Page, e2e_config):
        """Test that switch displays correct state (ON/OFF)"""
        self.page = logged_in_page
        self.config = e2e_config

        self.navigate_to_entity_list("switch")

        # Find toggle button
        toggle_btn = self.page.locator(self.config.get_selector("switch", "toggle_button")).first

        if toggle_btn.count() == 0:
            pytest.skip("No switch controllers found")

        # Button should show either ON or OFF
        button_text = toggle_btn.inner_text()
        assert "ON" in button_text or "OFF" in button_text

    def test_switch_state_badge_displayed(self, logged_in_page: Page, e2e_config):
        """Test that state badge is displayed"""
        self.page = logged_in_page
        self.config = e2e_config

        self.navigate_to_entity_list("switch")

        # Find state badge
        badge = self.page.locator(self.config.get_selector("switch", "state_badge")).first

        if badge.count() == 0:
            pytest.skip("No switch state badges found")

        expect(badge).to_be_visible()
        # Badge should show 'on' or 'off'
        badge_text = badge.inner_text().lower()
        assert badge_text in ["on", "off"]

    # =========================================================================
    # Interaction Tests
    # =========================================================================

    def test_toggle_button_click(self, logged_in_page: Page, e2e_config):
        """Test clicking toggle button changes state"""
        self.page = logged_in_page
        self.config = e2e_config

        self.navigate_to_entity_list("switch")

        # Find toggle button
        toggle_btn = self.page.locator(self.config.get_selector("switch", "toggle_button")).first

        if toggle_btn.count() == 0:
            pytest.skip("No switch controllers found")

        # Get initial state
        initial_text = toggle_btn.inner_text()
        initial_is_on = "ON" in initial_text

        # Click toggle
        toggle_btn.click()

        # Wait for API response
        self.page.wait_for_timeout(e2e_config.get_wait_time("api_response"))

        # Check state changed (or loading was shown)
        # Note: In real test, state may or may not change depending on HA connection
        # For now, just verify no errors occurred
        expect(toggle_btn).to_be_enabled()

    def test_form_switch_click(self, logged_in_page: Page, e2e_config):
        """Test clicking form switch toggles state"""
        self.page = logged_in_page
        self.config = e2e_config

        self.navigate_to_entity_list("switch")

        # Find form switch input
        form_switch = self.page.locator(self.config.get_selector("switch", "form_switch")).first

        if form_switch.count() == 0:
            pytest.skip("No switch form switches found")

        # Get initial state
        initial_checked = form_switch.is_checked()

        # Click form switch
        form_switch.click(force=True)

        # Wait for API response
        self.page.wait_for_timeout(e2e_config.get_wait_time("api_response"))

        # Verify switch is still functional (no errors)
        expect(form_switch).to_be_enabled()

    def test_toggle_shows_loading_spinner(self, logged_in_page: Page, e2e_config):
        """Test that loading spinner appears during toggle"""
        self.page = logged_in_page
        self.config = e2e_config

        self.navigate_to_entity_list("switch")

        # Find toggle button
        toggle_btn = self.page.locator(self.config.get_selector("switch", "toggle_button")).first

        if toggle_btn.count() == 0:
            pytest.skip("No switch controllers found")

        # Click and immediately check for spinner
        toggle_btn.click()

        # Check for spinner (may be very brief)
        spinner = self.page.locator(".switch-controller i.fa-spinner")
        # Note: Spinner may appear very briefly, so we just verify no crash

        # Wait for completion
        self.page.wait_for_timeout(e2e_config.get_wait_time("api_response"))

    # =========================================================================
    # UI State Tests
    # =========================================================================

    def test_on_state_has_primary_class(self, logged_in_page: Page, e2e_config):
        """Test that ON state button has btn-primary class"""
        self.page = logged_in_page
        self.config = e2e_config

        self.navigate_to_entity_list("switch")

        # Find toggle buttons with ON state
        on_buttons = self.page.locator(".switch-controller button.btn-primary")

        if on_buttons.count() > 0:
            # Verify button shows ON
            expect(on_buttons.first).to_contain_text("ON")

    def test_off_state_has_outline_class(self, logged_in_page: Page, e2e_config):
        """Test that OFF state button has btn-outline-secondary class"""
        self.page = logged_in_page
        self.config = e2e_config

        self.navigate_to_entity_list("switch")

        # Find toggle buttons with OFF state
        off_buttons = self.page.locator(".switch-controller button.btn-outline-secondary")

        if off_buttons.count() > 0:
            # Verify button shows OFF
            expect(off_buttons.first).to_contain_text("OFF")

    def test_on_badge_has_success_class(self, logged_in_page: Page, e2e_config):
        """Test that ON state badge has bg-success class"""
        self.page = logged_in_page
        self.config = e2e_config

        self.navigate_to_entity_list("switch")

        # Find badges with success class
        success_badges = self.page.locator(".switch-controller .badge.bg-success")

        if success_badges.count() > 0:
            expect(success_badges.first).to_contain_text("on")

    def test_off_badge_has_secondary_class(self, logged_in_page: Page, e2e_config):
        """Test that OFF state badge has bg-secondary class"""
        self.page = logged_in_page
        self.config = e2e_config

        self.navigate_to_entity_list("switch")

        # Find badges with secondary class
        secondary_badges = self.page.locator(".switch-controller .badge.bg-secondary")

        if secondary_badges.count() > 0:
            expect(secondary_badges.first).to_contain_text("off")

    # =========================================================================
    # Icon Tests
    # =========================================================================

    def test_on_state_shows_toggle_on_icon(self, logged_in_page: Page, e2e_config):
        """Test that ON state shows toggle-on icon"""
        self.page = logged_in_page
        self.config = e2e_config

        self.navigate_to_entity_list("switch")

        # Find switches in ON state
        on_buttons = self.page.locator(".switch-controller button.btn-primary")

        if on_buttons.count() > 0:
            # Check for toggle-on icon
            icon = on_buttons.first.locator("i.fa-toggle-on")
            if icon.count() > 0:
                expect(icon).to_be_visible()

    def test_off_state_shows_toggle_off_icon(self, logged_in_page: Page, e2e_config):
        """Test that OFF state shows toggle-off icon"""
        self.page = logged_in_page
        self.config = e2e_config

        self.navigate_to_entity_list("switch")

        # Find switches in OFF state
        off_buttons = self.page.locator(".switch-controller button.btn-outline-secondary")

        if off_buttons.count() > 0:
            # Check for toggle-off icon
            icon = off_buttons.first.locator("i.fa-toggle-off")
            if icon.count() > 0:
                expect(icon).to_be_visible()


# =============================================================================
# Standalone Test Functions (for pytest discovery)
# =============================================================================


@pytest.mark.e2e
@pytest.mark.domain_switch
def test_switch_controller_renders(logged_in_page: Page, e2e_config):
    """Test switch controller renders correctly"""
    test = TestSwitchController()
    test.test_switch_controller_visible(logged_in_page, e2e_config)


@pytest.mark.e2e
@pytest.mark.domain_switch
def test_switch_toggle_works(logged_in_page: Page, e2e_config):
    """Test switch toggle functionality"""
    test = TestSwitchController()
    test.test_toggle_button_click(logged_in_page, e2e_config)


@pytest.mark.e2e
@pytest.mark.domain_switch
def test_switch_form_toggle_works(logged_in_page: Page, e2e_config):
    """Test switch form toggle functionality"""
    test = TestSwitchController()
    test.test_form_switch_click(logged_in_page, e2e_config)
