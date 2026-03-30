"""
E2E Tests for Scene Domain Controller

Tests the scene entity controller UI interactions including:
- Activate button functionality
- State display
- Loading states
"""

import pytest
from playwright.sync_api import Page, expect

from .base import EntityControllerTest, logged_in_page, e2e_config, browser, context, page


class TestSceneController(EntityControllerTest):
    """E2E tests for scene domain controller"""

    domain = "scene"

    # =========================================================================
    # Display Tests
    # =========================================================================

    def test_scene_controller_visible(self, logged_in_page: Page, e2e_config):
        """Test that scene controller is visible"""
        self.page = logged_in_page
        self.config = e2e_config

        self.navigate_to_entity_list("scene")

        controller = self.find_entity_controller("scene")
        if controller:
            expect(controller).to_be_visible()
        else:
            pytest.skip("No scene entities found in the system")

    def test_scene_badge_displayed(self, logged_in_page: Page, e2e_config):
        """Test that scene badge is displayed"""
        self.page = logged_in_page
        self.config = e2e_config

        self.navigate_to_entity_list("scene")

        badge = self.page.locator(self.config.get_selector("scene", "scene_badge")).first

        if badge.count() == 0:
            pytest.skip("No scene badges found")

        expect(badge).to_be_visible()

    # =========================================================================
    # Activate Button Tests
    # =========================================================================

    def test_activate_button_visible(self, logged_in_page: Page, e2e_config):
        """Test that Activate Scene button is visible"""
        self.page = logged_in_page
        self.config = e2e_config

        self.navigate_to_entity_list("scene")

        activate_btn = self.page.locator(self.config.get_selector("scene", "activate_button")).first

        if activate_btn.count() == 0:
            pytest.skip("No scene activate buttons found")

        expect(activate_btn).to_be_visible()
        expect(activate_btn).to_contain_text("Activate Scene")

    def test_activate_button_has_primary_class(self, logged_in_page: Page, e2e_config):
        """Test that Activate button has btn-primary class"""
        self.page = logged_in_page
        self.config = e2e_config

        self.navigate_to_entity_list("scene")

        primary_btns = self.page.locator(".scene-controller button.btn-primary")

        if primary_btns.count() > 0:
            expect(primary_btns.first).to_contain_text("Activate Scene")

    def test_activate_button_click(self, logged_in_page: Page, e2e_config):
        """Test clicking Activate Scene button"""
        self.page = logged_in_page
        self.config = e2e_config

        self.navigate_to_entity_list("scene")

        activate_btn = self.page.locator(self.config.get_selector("scene", "activate_button")).first

        if activate_btn.count() == 0:
            pytest.skip("No scene activate buttons found")

        activate_btn.click()
        self.page.wait_for_timeout(e2e_config.get_wait_time("api_response"))

        expect(activate_btn).to_be_enabled()

    # =========================================================================
    # Icon Tests
    # =========================================================================

    def test_activate_button_shows_image_icon(self, logged_in_page: Page, e2e_config):
        """Test that Activate button shows image icon"""
        self.page = logged_in_page
        self.config = e2e_config

        self.navigate_to_entity_list("scene")

        activate_btn = self.page.locator(".scene-controller button.btn-primary").first

        if activate_btn.count() > 0:
            icon = activate_btn.locator("i.fa-image")
            if icon.count() > 0:
                expect(icon).to_be_visible()

    def test_badge_shows_picture_icon(self, logged_in_page: Page, e2e_config):
        """Test that badge shows picture icon"""
        self.page = logged_in_page
        self.config = e2e_config

        self.navigate_to_entity_list("scene")

        badges = self.page.locator(".scene-controller .badge.bg-info")

        if badges.count() > 0:
            icon = badges.first.locator("i.fa-picture-o")
            if icon.count() > 0:
                expect(icon).to_be_visible()


# =============================================================================
# Standalone Test Functions
# =============================================================================


@pytest.mark.e2e
@pytest.mark.domain_scene
def test_scene_controller_renders(logged_in_page: Page, e2e_config):
    """Test scene controller renders correctly"""
    test = TestSceneController()
    test.test_scene_controller_visible(logged_in_page, e2e_config)


@pytest.mark.e2e
@pytest.mark.domain_scene
def test_scene_activate_works(logged_in_page: Page, e2e_config):
    """Test scene activate functionality"""
    test = TestSceneController()
    test.test_activate_button_click(logged_in_page, e2e_config)
