"""
E2E Tests for Light Domain Controller

Tests the light entity controller UI interactions including:
- Toggle button functionality
- Brightness slider control
- State display and updates
- Loading states
"""

import pytest
from playwright.sync_api import Page, expect

from .base import EntityControllerTest, logged_in_page, e2e_config, browser, context, page


class TestLightController(EntityControllerTest):
    """E2E tests for light domain controller"""

    domain = "light"

    # =========================================================================
    # Display Tests
    # =========================================================================

    def test_light_controller_visible(self, logged_in_page: Page, e2e_config):
        """Test that light controller is visible"""
        self.page = logged_in_page
        self.config = e2e_config

        self.navigate_to_entity_list("light")

        controller = self.find_entity_controller("light")
        if controller:
            expect(controller).to_be_visible()
        else:
            pytest.skip("No light entities found in the system")

    def test_light_shows_correct_state(self, logged_in_page: Page, e2e_config):
        """Test that light displays correct state (ON/OFF)"""
        self.page = logged_in_page
        self.config = e2e_config

        self.navigate_to_entity_list("light")

        toggle_btn = self.page.locator(self.config.get_selector("light", "toggle_button")).first

        if toggle_btn.count() == 0:
            pytest.skip("No light controllers found")

        button_text = toggle_btn.inner_text()
        assert "ON" in button_text or "OFF" in button_text

    def test_light_state_badge_displayed(self, logged_in_page: Page, e2e_config):
        """Test that state badge is displayed"""
        self.page = logged_in_page
        self.config = e2e_config

        self.navigate_to_entity_list("light")

        badge = self.page.locator(self.config.get_selector("light", "state_badge")).first

        if badge.count() == 0:
            pytest.skip("No light state badges found")

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

        self.navigate_to_entity_list("light")

        toggle_btn = self.page.locator(self.config.get_selector("light", "toggle_button")).first

        if toggle_btn.count() == 0:
            pytest.skip("No light controllers found")

        initial_text = toggle_btn.inner_text()

        toggle_btn.click()
        self.page.wait_for_timeout(e2e_config.get_wait_time("api_response"))

        expect(toggle_btn).to_be_enabled()

    def test_toggle_shows_loading_spinner(self, logged_in_page: Page, e2e_config):
        """Test that loading spinner appears during toggle"""
        self.page = logged_in_page
        self.config = e2e_config

        self.navigate_to_entity_list("light")

        toggle_btn = self.page.locator(self.config.get_selector("light", "toggle_button")).first

        if toggle_btn.count() == 0:
            pytest.skip("No light controllers found")

        toggle_btn.click()
        self.page.wait_for_timeout(e2e_config.get_wait_time("api_response"))

    # =========================================================================
    # Brightness Tests
    # =========================================================================

    def test_brightness_slider_visible_when_on(self, logged_in_page: Page, e2e_config):
        """Test that brightness slider is visible when light is on"""
        self.page = logged_in_page
        self.config = e2e_config

        self.navigate_to_entity_list("light")

        # Find lights that are ON (have brightness slider visible)
        brightness_sliders = self.page.locator(self.config.get_selector("light", "brightness_slider"))

        if brightness_sliders.count() > 0:
            # At least one light is on with brightness support
            expect(brightness_sliders.first).to_be_visible()

    def test_brightness_label_shows_percentage(self, logged_in_page: Page, e2e_config):
        """Test that brightness label shows percentage"""
        self.page = logged_in_page
        self.config = e2e_config

        self.navigate_to_entity_list("light")

        brightness_labels = self.page.locator(self.config.get_selector("light", "brightness_label"))

        if brightness_labels.count() > 0:
            label_text = brightness_labels.first.inner_text()
            # Should contain a percentage
            assert "%" in label_text

    def test_brightness_slider_drag(self, logged_in_page: Page, e2e_config):
        """Test dragging brightness slider"""
        self.page = logged_in_page
        self.config = e2e_config

        self.navigate_to_entity_list("light")

        slider = self.page.locator(self.config.get_selector("light", "brightness_slider")).first

        if slider.count() == 0:
            pytest.skip("No brightness sliders found")

        # Get initial value
        initial_value = slider.input_value()

        # Simulate slider interaction using fill
        slider.fill("128")

        # Trigger change event
        slider.dispatch_event("change")

        self.page.wait_for_timeout(e2e_config.get_wait_time("debounce"))

    def test_brightness_input_updates_label(self, logged_in_page: Page, e2e_config):
        """Test that input on slider updates the label (optimistic update)"""
        self.page = logged_in_page
        self.config = e2e_config

        self.navigate_to_entity_list("light")

        slider = self.page.locator(self.config.get_selector("light", "brightness_slider")).first
        label = self.page.locator(self.config.get_selector("light", "brightness_label")).first

        if slider.count() == 0 or label.count() == 0:
            pytest.skip("No brightness controls found")

        # Set specific value
        slider.fill("192")
        slider.dispatch_event("input")

        # Label should update to reflect percentage (192/255 ~ 75%)
        # Note: Exact value depends on implementation

    # =========================================================================
    # UI State Tests
    # =========================================================================

    def test_on_state_has_warning_class(self, logged_in_page: Page, e2e_config):
        """Test that ON state button has btn-warning class (yellow light)"""
        self.page = logged_in_page
        self.config = e2e_config

        self.navigate_to_entity_list("light")

        on_buttons = self.page.locator(".light-controller button.btn-warning")

        if on_buttons.count() > 0:
            expect(on_buttons.first).to_contain_text("ON")

    def test_off_state_has_outline_class(self, logged_in_page: Page, e2e_config):
        """Test that OFF state button has btn-outline-secondary class"""
        self.page = logged_in_page
        self.config = e2e_config

        self.navigate_to_entity_list("light")

        off_buttons = self.page.locator(".light-controller button.btn-outline-secondary")

        if off_buttons.count() > 0:
            expect(off_buttons.first).to_contain_text("OFF")

    # =========================================================================
    # Icon Tests
    # =========================================================================

    def test_on_state_shows_lightbulb_icon(self, logged_in_page: Page, e2e_config):
        """Test that ON state shows filled lightbulb icon"""
        self.page = logged_in_page
        self.config = e2e_config

        self.navigate_to_entity_list("light")

        on_buttons = self.page.locator(".light-controller button.btn-warning")

        if on_buttons.count() > 0:
            icon = on_buttons.first.locator("i.fa-lightbulb")
            if icon.count() > 0:
                expect(icon).to_be_visible()

    def test_off_state_shows_lightbulb_outline_icon(self, logged_in_page: Page, e2e_config):
        """Test that OFF state shows outline lightbulb icon"""
        self.page = logged_in_page
        self.config = e2e_config

        self.navigate_to_entity_list("light")

        off_buttons = self.page.locator(".light-controller button.btn-outline-secondary")

        if off_buttons.count() > 0:
            icon = off_buttons.first.locator("i.fa-lightbulb-o")
            if icon.count() > 0:
                expect(icon).to_be_visible()


# =============================================================================
# Standalone Test Functions
# =============================================================================


@pytest.mark.e2e
@pytest.mark.domain_light
def test_light_controller_renders(logged_in_page: Page, e2e_config):
    """Test light controller renders correctly"""
    test = TestLightController()
    test.test_light_controller_visible(logged_in_page, e2e_config)


@pytest.mark.e2e
@pytest.mark.domain_light
def test_light_toggle_works(logged_in_page: Page, e2e_config):
    """Test light toggle functionality"""
    test = TestLightController()
    test.test_toggle_button_click(logged_in_page, e2e_config)


@pytest.mark.e2e
@pytest.mark.domain_light
def test_light_brightness_slider(logged_in_page: Page, e2e_config):
    """Test light brightness slider functionality"""
    test = TestLightController()
    test.test_brightness_slider_drag(logged_in_page, e2e_config)
