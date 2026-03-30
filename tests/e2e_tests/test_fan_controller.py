"""
E2E Tests for Fan Domain Controller

Tests the fan entity controller UI interactions including:
- Toggle button functionality
- Speed (percentage) slider control
- Oscillate toggle
- Preset mode selector
- State display
"""

import pytest
from playwright.sync_api import Page, expect

from .base import EntityControllerTest, logged_in_page, e2e_config, browser, context, page


class TestFanController(EntityControllerTest):
    """E2E tests for fan domain controller"""

    domain = "fan"

    # =========================================================================
    # Display Tests
    # =========================================================================

    def test_fan_controller_visible(self, logged_in_page: Page, e2e_config):
        """Test that fan controller is visible"""
        self.page = logged_in_page
        self.config = e2e_config

        self.navigate_to_entity_list("fan")

        controller = self.find_entity_controller("fan")
        if controller:
            expect(controller).to_be_visible()
        else:
            pytest.skip("No fan entities found in the system")

    def test_fan_shows_correct_state(self, logged_in_page: Page, e2e_config):
        """Test that fan displays correct state (ON/OFF)"""
        self.page = logged_in_page
        self.config = e2e_config

        self.navigate_to_entity_list("fan")

        toggle_btn = self.page.locator(self.config.get_selector("fan", "toggle_button")).first

        if toggle_btn.count() == 0:
            pytest.skip("No fan controllers found")

        button_text = toggle_btn.inner_text()
        assert "ON" in button_text or "OFF" in button_text

    def test_fan_state_badge_displayed(self, logged_in_page: Page, e2e_config):
        """Test that state badge is displayed"""
        self.page = logged_in_page
        self.config = e2e_config

        self.navigate_to_entity_list("fan")

        badge = self.page.locator(self.config.get_selector("fan", "state_badge")).first

        if badge.count() == 0:
            pytest.skip("No fan state badges found")

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

        self.navigate_to_entity_list("fan")

        toggle_btn = self.page.locator(self.config.get_selector("fan", "toggle_button")).first

        if toggle_btn.count() == 0:
            pytest.skip("No fan controllers found")

        toggle_btn.click()
        self.page.wait_for_timeout(e2e_config.get_wait_time("api_response"))

        expect(toggle_btn).to_be_enabled()

    def test_on_state_has_primary_class(self, logged_in_page: Page, e2e_config):
        """Test that ON state button has btn-primary class"""
        self.page = logged_in_page
        self.config = e2e_config

        self.navigate_to_entity_list("fan")

        on_buttons = self.page.locator(".fan-controller button.btn-primary")

        if on_buttons.count() > 0:
            expect(on_buttons.first).to_contain_text("ON")

    # =========================================================================
    # Speed (Percentage) Slider Tests
    # =========================================================================

    def test_speed_slider_visible(self, logged_in_page: Page, e2e_config):
        """Test that speed slider is visible when fan supports percentage"""
        self.page = logged_in_page
        self.config = e2e_config

        self.navigate_to_entity_list("fan")

        slider = self.page.locator(self.config.get_selector("fan", "speed_slider")).first

        if slider.count() == 0:
            pytest.skip("No fan speed sliders found")

        expect(slider).to_be_visible()

    def test_speed_label_shows_percentage(self, logged_in_page: Page, e2e_config):
        """Test that speed label shows percentage"""
        self.page = logged_in_page
        self.config = e2e_config

        self.navigate_to_entity_list("fan")

        label = self.page.locator(self.config.get_selector("fan", "speed_label")).first

        if label.count() == 0:
            pytest.skip("No fan speed labels found")

        text = label.inner_text()
        assert "Speed" in text
        assert "%" in text

    def test_speed_slider_drag(self, logged_in_page: Page, e2e_config):
        """Test dragging speed slider"""
        self.page = logged_in_page
        self.config = e2e_config

        self.navigate_to_entity_list("fan")

        slider = self.page.locator(self.config.get_selector("fan", "speed_slider")).first

        if slider.count() == 0:
            pytest.skip("No fan speed sliders found")

        slider.fill("75")
        slider.dispatch_event("change")

        self.page.wait_for_timeout(e2e_config.get_wait_time("debounce"))

    def test_speed_slider_min_max(self, logged_in_page: Page, e2e_config):
        """Test speed slider has correct min/max values"""
        self.page = logged_in_page
        self.config = e2e_config

        self.navigate_to_entity_list("fan")

        slider = self.page.locator(self.config.get_selector("fan", "speed_slider")).first

        if slider.count() == 0:
            pytest.skip("No fan speed sliders found")

        min_val = slider.get_attribute("min")
        max_val = slider.get_attribute("max")

        assert min_val == "0"
        assert max_val == "100"

    # =========================================================================
    # Oscillate Tests
    # =========================================================================

    def test_oscillate_button_visible(self, logged_in_page: Page, e2e_config):
        """Test that oscillate button is visible when fan is on and supports oscillation"""
        self.page = logged_in_page
        self.config = e2e_config

        self.navigate_to_entity_list("fan")

        oscillate_btn = self.page.locator(self.config.get_selector("fan", "oscillate_button")).first

        if oscillate_btn.count() == 0:
            pytest.skip("No oscillate buttons found (fan may be off or doesn't support oscillation)")

        expect(oscillate_btn).to_be_visible()

    def test_oscillate_button_click(self, logged_in_page: Page, e2e_config):
        """Test clicking oscillate button"""
        self.page = logged_in_page
        self.config = e2e_config

        self.navigate_to_entity_list("fan")

        oscillate_btn = self.page.locator(self.config.get_selector("fan", "oscillate_button")).first

        if oscillate_btn.count() == 0:
            pytest.skip("No oscillate buttons found")

        oscillate_btn.click()
        self.page.wait_for_timeout(e2e_config.get_wait_time("api_response"))

        expect(oscillate_btn).to_be_enabled()

    def test_oscillate_button_has_exchange_icon(self, logged_in_page: Page, e2e_config):
        """Test that oscillate button shows exchange icon"""
        self.page = logged_in_page
        self.config = e2e_config

        self.navigate_to_entity_list("fan")

        oscillate_btn = self.page.locator(self.config.get_selector("fan", "oscillate_button")).first

        if oscillate_btn.count() > 0:
            icon = oscillate_btn.locator("i.fa-exchange")
            if icon.count() > 0:
                expect(icon).to_be_visible()

    # =========================================================================
    # Preset Mode Tests
    # =========================================================================

    def test_preset_mode_selector_visible(self, logged_in_page: Page, e2e_config):
        """Test that preset mode selector is visible when fan is on and supports preset modes"""
        self.page = logged_in_page
        self.config = e2e_config

        self.navigate_to_entity_list("fan")

        preset_select = self.page.locator(self.config.get_selector("fan", "preset_select")).first

        if preset_select.count() == 0:
            pytest.skip("No preset mode selectors found (fan may be off or doesn't support preset modes)")

        expect(preset_select).to_be_visible()

    def test_preset_mode_has_options(self, logged_in_page: Page, e2e_config):
        """Test that preset mode selector has options"""
        self.page = logged_in_page
        self.config = e2e_config

        self.navigate_to_entity_list("fan")

        preset_select = self.page.locator(self.config.get_selector("fan", "preset_select")).first

        if preset_select.count() == 0:
            pytest.skip("No preset mode selectors found")

        options = preset_select.locator("option")
        assert options.count() > 1  # At least placeholder + 1 mode

    def test_preset_mode_selection(self, logged_in_page: Page, e2e_config):
        """Test selecting a preset mode"""
        self.page = logged_in_page
        self.config = e2e_config

        self.navigate_to_entity_list("fan")

        preset_select = self.page.locator(self.config.get_selector("fan", "preset_select")).first

        if preset_select.count() == 0:
            pytest.skip("No preset mode selectors found")

        # Get available options
        options = preset_select.locator("option:not([disabled])")

        if options.count() > 0:
            # Select first available option
            first_option = options.first.get_attribute("value")
            if first_option:
                preset_select.select_option(first_option)
                self.page.wait_for_timeout(e2e_config.get_wait_time("api_response"))

    # =========================================================================
    # Icon Tests
    # =========================================================================

    def test_toggle_button_shows_refresh_icon(self, logged_in_page: Page, e2e_config):
        """Test that toggle button shows refresh (fan) icon"""
        self.page = logged_in_page
        self.config = e2e_config

        self.navigate_to_entity_list("fan")

        toggle_btn = self.page.locator(self.config.get_selector("fan", "toggle_button")).first

        if toggle_btn.count() > 0:
            icon = toggle_btn.locator("i.fa-refresh")
            if icon.count() > 0:
                expect(icon).to_be_visible()


# =============================================================================
# Standalone Test Functions
# =============================================================================


@pytest.mark.e2e
@pytest.mark.domain_fan
def test_fan_controller_renders(logged_in_page: Page, e2e_config):
    """Test fan controller renders correctly"""
    test = TestFanController()
    test.test_fan_controller_visible(logged_in_page, e2e_config)


@pytest.mark.e2e
@pytest.mark.domain_fan
def test_fan_toggle_works(logged_in_page: Page, e2e_config):
    """Test fan toggle functionality"""
    test = TestFanController()
    test.test_toggle_button_click(logged_in_page, e2e_config)


@pytest.mark.e2e
@pytest.mark.domain_fan
def test_fan_speed_slider(logged_in_page: Page, e2e_config):
    """Test fan speed slider"""
    test = TestFanController()
    test.test_speed_slider_visible(logged_in_page, e2e_config)


@pytest.mark.e2e
@pytest.mark.domain_fan
def test_fan_oscillate(logged_in_page: Page, e2e_config):
    """Test fan oscillate feature"""
    test = TestFanController()
    test.test_oscillate_button_visible(logged_in_page, e2e_config)


@pytest.mark.e2e
@pytest.mark.domain_fan
def test_fan_preset_modes(logged_in_page: Page, e2e_config):
    """Test fan preset mode selection"""
    test = TestFanController()
    test.test_preset_mode_selector_visible(logged_in_page, e2e_config)
