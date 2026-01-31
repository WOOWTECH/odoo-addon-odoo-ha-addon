"""
E2E Tests for Script Domain Controller

Tests the script entity controller UI interactions including:
- Run Script button functionality
- Toggle button functionality
- State display
- Loading states
"""

import pytest
from playwright.sync_api import Page, expect

from .base import EntityControllerTest, logged_in_page, e2e_config, browser, context, page


class TestScriptController(EntityControllerTest):
    """E2E tests for script domain controller"""

    domain = "script"

    # =========================================================================
    # Display Tests
    # =========================================================================

    def test_script_controller_visible(self, logged_in_page: Page, e2e_config):
        """Test that script controller is visible"""
        self.page = logged_in_page
        self.config = e2e_config

        self.navigate_to_entity_list("script")

        controller = self.find_entity_controller("script")
        if controller:
            expect(controller).to_be_visible()
        else:
            pytest.skip("No script entities found in the system")

    def test_script_shows_correct_state(self, logged_in_page: Page, e2e_config):
        """Test that script displays correct state"""
        self.page = logged_in_page
        self.config = e2e_config

        self.navigate_to_entity_list("script")

        badge = self.page.locator(self.config.get_selector("script", "state_badge")).first

        if badge.count() == 0:
            pytest.skip("No script state badges found")

        expect(badge).to_be_visible()
        badge_text = badge.inner_text().lower()
        assert badge_text in ["on", "off"]

    def test_script_badge_displayed(self, logged_in_page: Page, e2e_config):
        """Test that script badge is displayed"""
        self.page = logged_in_page
        self.config = e2e_config

        self.navigate_to_entity_list("script")

        badges = self.page.locator(".script-controller .badge.bg-success")

        if badges.count() > 0:
            expect(badges.first).to_contain_text("Script")

    # =========================================================================
    # Run Script Button Tests
    # =========================================================================

    def test_run_button_visible(self, logged_in_page: Page, e2e_config):
        """Test that Run Script button is visible"""
        self.page = logged_in_page
        self.config = e2e_config

        self.navigate_to_entity_list("script")

        run_btn = self.page.locator(self.config.get_selector("script", "run_button")).first

        if run_btn.count() == 0:
            pytest.skip("No script run buttons found")

        expect(run_btn).to_be_visible()
        expect(run_btn).to_contain_text("Run Script")

    def test_run_button_has_success_class(self, logged_in_page: Page, e2e_config):
        """Test that Run Script button has btn-success class"""
        self.page = logged_in_page
        self.config = e2e_config

        self.navigate_to_entity_list("script")

        success_btns = self.page.locator(".script-controller button.btn-success")

        if success_btns.count() > 0:
            expect(success_btns.first).to_contain_text("Run Script")

    def test_run_button_click(self, logged_in_page: Page, e2e_config):
        """Test clicking Run Script button"""
        self.page = logged_in_page
        self.config = e2e_config

        self.navigate_to_entity_list("script")

        run_btn = self.page.locator(self.config.get_selector("script", "run_button")).first

        if run_btn.count() == 0:
            pytest.skip("No script run buttons found")

        run_btn.click()
        self.page.wait_for_timeout(e2e_config.get_wait_time("api_response"))

        expect(run_btn).to_be_enabled()

    # =========================================================================
    # Toggle Button Tests
    # =========================================================================

    def test_toggle_button_visible(self, logged_in_page: Page, e2e_config):
        """Test that toggle button is visible"""
        self.page = logged_in_page
        self.config = e2e_config

        self.navigate_to_entity_list("script")

        toggle_btn = self.page.locator(self.config.get_selector("script", "toggle_button")).first

        if toggle_btn.count() == 0:
            pytest.skip("No script toggle buttons found")

        expect(toggle_btn).to_be_visible()

    def test_toggle_button_click(self, logged_in_page: Page, e2e_config):
        """Test clicking toggle button"""
        self.page = logged_in_page
        self.config = e2e_config

        self.navigate_to_entity_list("script")

        toggle_btn = self.page.locator(self.config.get_selector("script", "toggle_button")).first

        if toggle_btn.count() == 0:
            pytest.skip("No script toggle buttons found")

        toggle_btn.click()
        self.page.wait_for_timeout(e2e_config.get_wait_time("api_response"))

        expect(toggle_btn).to_be_enabled()

    def test_toggle_button_shows_on_off(self, logged_in_page: Page, e2e_config):
        """Test that toggle button shows ON or OFF"""
        self.page = logged_in_page
        self.config = e2e_config

        self.navigate_to_entity_list("script")

        toggle_btn = self.page.locator(self.config.get_selector("script", "toggle_button")).first

        if toggle_btn.count() == 0:
            pytest.skip("No script toggle buttons found")

        button_text = toggle_btn.inner_text()
        assert "ON" in button_text or "OFF" in button_text

    def test_on_toggle_has_primary_class(self, logged_in_page: Page, e2e_config):
        """Test that ON toggle button has btn-primary class"""
        self.page = logged_in_page
        self.config = e2e_config

        self.navigate_to_entity_list("script")

        # Toggle button is 2nd button (after run button)
        on_toggles = self.page.locator(".script-controller button:nth-child(2).btn-primary")

        if on_toggles.count() > 0:
            expect(on_toggles.first).to_contain_text("ON")

    # =========================================================================
    # Icon Tests
    # =========================================================================

    def test_run_button_shows_play_icon(self, logged_in_page: Page, e2e_config):
        """Test that Run Script button shows play icon"""
        self.page = logged_in_page
        self.config = e2e_config

        self.navigate_to_entity_list("script")

        run_btn = self.page.locator(".script-controller button.btn-success").first

        if run_btn.count() > 0:
            icon = run_btn.locator("i.fa-play")
            if icon.count() > 0:
                expect(icon).to_be_visible()

    def test_toggle_on_shows_toggle_on_icon(self, logged_in_page: Page, e2e_config):
        """Test that ON toggle shows toggle-on icon"""
        self.page = logged_in_page
        self.config = e2e_config

        self.navigate_to_entity_list("script")

        on_toggles = self.page.locator(".script-controller button:nth-child(2).btn-primary")

        if on_toggles.count() > 0:
            icon = on_toggles.first.locator("i.fa-toggle-on")
            if icon.count() > 0:
                expect(icon).to_be_visible()

    def test_script_badge_shows_file_icon(self, logged_in_page: Page, e2e_config):
        """Test that script badge shows file icon"""
        self.page = logged_in_page
        self.config = e2e_config

        self.navigate_to_entity_list("script")

        badges = self.page.locator(".script-controller .badge.bg-success")

        if badges.count() > 0:
            icon = badges.first.locator("i.fa-file-text-o")
            if icon.count() > 0:
                expect(icon).to_be_visible()


# =============================================================================
# Standalone Test Functions
# =============================================================================


@pytest.mark.e2e
@pytest.mark.domain_script
def test_script_controller_renders(logged_in_page: Page, e2e_config):
    """Test script controller renders correctly"""
    test = TestScriptController()
    test.test_script_controller_visible(logged_in_page, e2e_config)


@pytest.mark.e2e
@pytest.mark.domain_script
def test_script_run_works(logged_in_page: Page, e2e_config):
    """Test script run functionality"""
    test = TestScriptController()
    test.test_run_button_click(logged_in_page, e2e_config)


@pytest.mark.e2e
@pytest.mark.domain_script
def test_script_toggle_works(logged_in_page: Page, e2e_config):
    """Test script toggle functionality"""
    test = TestScriptController()
    test.test_toggle_button_click(logged_in_page, e2e_config)
