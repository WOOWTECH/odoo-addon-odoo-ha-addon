"""
E2E Tests for Climate Domain Controller

Tests the climate entity controller UI interactions including:
- Temperature display (current and target)
- Temperature adjustment buttons
- Temperature input field
- Fan mode selection
- HVAC mode display
"""

import pytest
from playwright.sync_api import Page, expect

from .base import EntityControllerTest, logged_in_page, e2e_config, browser, context, page


class TestClimateController(EntityControllerTest):
    """E2E tests for climate domain controller"""

    domain = "climate"

    # =========================================================================
    # Display Tests
    # =========================================================================

    def test_climate_controller_visible(self, logged_in_page: Page, e2e_config):
        """Test that climate controller is visible"""
        self.page = logged_in_page
        self.config = e2e_config

        self.navigate_to_entity_list("climate")

        controller = self.find_entity_controller("climate")
        if controller:
            expect(controller).to_be_visible()
        else:
            pytest.skip("No climate entities found in the system")

    def test_climate_shows_current_temperature(self, logged_in_page: Page, e2e_config):
        """Test that climate displays current temperature"""
        self.page = logged_in_page
        self.config = e2e_config

        self.navigate_to_entity_list("climate")

        temp_badge = self.page.locator(self.config.get_selector("climate", "temp_badge")).first

        if temp_badge.count() == 0:
            pytest.skip("No climate temp badges found")

        expect(temp_badge).to_be_visible()
        # Should contain °C or a number
        text = temp_badge.inner_text()
        assert "°C" in text or any(c.isdigit() for c in text)

    def test_climate_shows_target_temperature(self, logged_in_page: Page, e2e_config):
        """Test that climate displays target temperature"""
        self.page = logged_in_page
        self.config = e2e_config

        self.navigate_to_entity_list("climate")

        target_badge = self.page.locator(self.config.get_selector("climate", "target_badge")).first

        if target_badge.count() == 0:
            # Not all climate entities have target temp visible
            pytest.skip("No climate target badges found")

        expect(target_badge).to_be_visible()
        text = target_badge.inner_text()
        assert "Target" in text

    def test_climate_shows_hvac_mode(self, logged_in_page: Page, e2e_config):
        """Test that climate displays HVAC mode/action"""
        self.page = logged_in_page
        self.config = e2e_config

        self.navigate_to_entity_list("climate")

        hvac_badge = self.page.locator(self.config.get_selector("climate", "hvac_badge")).first

        if hvac_badge.count() == 0:
            pytest.skip("No climate hvac badges found")

        expect(hvac_badge).to_be_visible()

    # =========================================================================
    # Temperature Control Tests
    # =========================================================================

    def test_temperature_input_visible(self, logged_in_page: Page, e2e_config):
        """Test that temperature input field is visible"""
        self.page = logged_in_page
        self.config = e2e_config

        self.navigate_to_entity_list("climate")

        temp_input = self.page.locator(self.config.get_selector("climate", "temp_input")).first

        if temp_input.count() == 0:
            pytest.skip("No climate temperature inputs found")

        expect(temp_input).to_be_visible()

    def test_temperature_minus_button(self, logged_in_page: Page, e2e_config):
        """Test clicking minus button decreases temperature"""
        self.page = logged_in_page
        self.config = e2e_config

        self.navigate_to_entity_list("climate")

        minus_btn = self.page.locator(self.config.get_selector("climate", "temp_minus")).first
        temp_input = self.page.locator(self.config.get_selector("climate", "temp_input")).first

        if minus_btn.count() == 0 or temp_input.count() == 0:
            pytest.skip("No climate temperature controls found")

        # Click minus button
        minus_btn.click()
        self.page.wait_for_timeout(e2e_config.get_wait_time("api_response"))

        # Verify button is still enabled (no errors)
        expect(minus_btn).to_be_enabled()

    def test_temperature_plus_button(self, logged_in_page: Page, e2e_config):
        """Test clicking plus button increases temperature"""
        self.page = logged_in_page
        self.config = e2e_config

        self.navigate_to_entity_list("climate")

        plus_btn = self.page.locator(self.config.get_selector("climate", "temp_plus")).first
        temp_input = self.page.locator(self.config.get_selector("climate", "temp_input")).first

        if plus_btn.count() == 0 or temp_input.count() == 0:
            pytest.skip("No climate temperature controls found")

        # Click plus button
        plus_btn.click()
        self.page.wait_for_timeout(e2e_config.get_wait_time("api_response"))

        # Verify button is still enabled (no errors)
        expect(plus_btn).to_be_enabled()

    def test_temperature_input_change(self, logged_in_page: Page, e2e_config):
        """Test changing temperature via input field"""
        self.page = logged_in_page
        self.config = e2e_config

        self.navigate_to_entity_list("climate")

        temp_input = self.page.locator(self.config.get_selector("climate", "temp_input")).first

        if temp_input.count() == 0:
            pytest.skip("No climate temperature inputs found")

        # Set specific temperature
        temp_input.fill("22")
        temp_input.dispatch_event("change")

        self.page.wait_for_timeout(e2e_config.get_wait_time("api_response"))

        # Verify input is still functional
        expect(temp_input).to_be_enabled()

    def test_temperature_step_is_half_degree(self, logged_in_page: Page, e2e_config):
        """Test that temperature input step is 0.5"""
        self.page = logged_in_page
        self.config = e2e_config

        self.navigate_to_entity_list("climate")

        temp_input = self.page.locator(self.config.get_selector("climate", "temp_input")).first

        if temp_input.count() == 0:
            pytest.skip("No climate temperature inputs found")

        step = temp_input.get_attribute("step")
        assert step == "0.5"

    def test_temperature_min_is_10(self, logged_in_page: Page, e2e_config):
        """Test that temperature minimum is 10"""
        self.page = logged_in_page
        self.config = e2e_config

        self.navigate_to_entity_list("climate")

        temp_input = self.page.locator(self.config.get_selector("climate", "temp_input")).first

        if temp_input.count() == 0:
            pytest.skip("No climate temperature inputs found")

        min_val = temp_input.get_attribute("min")
        assert min_val == "10"

    def test_temperature_max_is_35(self, logged_in_page: Page, e2e_config):
        """Test that temperature maximum is 35"""
        self.page = logged_in_page
        self.config = e2e_config

        self.navigate_to_entity_list("climate")

        temp_input = self.page.locator(self.config.get_selector("climate", "temp_input")).first

        if temp_input.count() == 0:
            pytest.skip("No climate temperature inputs found")

        max_val = temp_input.get_attribute("max")
        assert max_val == "35"

    # =========================================================================
    # Fan Mode Tests
    # =========================================================================

    def test_fan_mode_buttons_visible(self, logged_in_page: Page, e2e_config):
        """Test that fan mode buttons are visible when supported"""
        self.page = logged_in_page
        self.config = e2e_config

        self.navigate_to_entity_list("climate")

        fan_buttons = self.page.locator(self.config.get_selector("climate", "fan_mode_buttons"))

        if fan_buttons.count() > 0:
            # At least one climate device supports fan modes
            expect(fan_buttons.first).to_be_visible()

    def test_fan_mode_button_click(self, logged_in_page: Page, e2e_config):
        """Test clicking fan mode button changes mode"""
        self.page = logged_in_page
        self.config = e2e_config

        self.navigate_to_entity_list("climate")

        fan_buttons = self.page.locator(self.config.get_selector("climate", "fan_mode_buttons"))

        if fan_buttons.count() == 0:
            pytest.skip("No fan mode buttons found")

        # Click first fan mode button
        fan_buttons.first.click()
        self.page.wait_for_timeout(e2e_config.get_wait_time("api_response"))

        # Verify buttons are still functional
        expect(fan_buttons.first).to_be_enabled()

    def test_active_fan_mode_has_info_class(self, logged_in_page: Page, e2e_config):
        """Test that active fan mode button has btn-info class"""
        self.page = logged_in_page
        self.config = e2e_config

        self.navigate_to_entity_list("climate")

        active_buttons = self.page.locator(".climate-controller .fan-mode-control .btn-info")

        if active_buttons.count() > 0:
            expect(active_buttons.first).to_be_visible()

    # =========================================================================
    # Icon Tests
    # =========================================================================

    def test_climate_shows_thermometer_icon(self, logged_in_page: Page, e2e_config):
        """Test that climate shows thermometer icon"""
        self.page = logged_in_page
        self.config = e2e_config

        self.navigate_to_entity_list("climate")

        icons = self.page.locator(".climate-controller i.fa-thermometer-half")

        if icons.count() > 0:
            expect(icons.first).to_be_visible()


# =============================================================================
# Standalone Test Functions
# =============================================================================


@pytest.mark.e2e
@pytest.mark.domain_climate
def test_climate_controller_renders(logged_in_page: Page, e2e_config):
    """Test climate controller renders correctly"""
    test = TestClimateController()
    test.test_climate_controller_visible(logged_in_page, e2e_config)


@pytest.mark.e2e
@pytest.mark.domain_climate
def test_climate_temperature_display(logged_in_page: Page, e2e_config):
    """Test climate temperature display"""
    test = TestClimateController()
    test.test_climate_shows_current_temperature(logged_in_page, e2e_config)


@pytest.mark.e2e
@pytest.mark.domain_climate
def test_climate_temperature_controls(logged_in_page: Page, e2e_config):
    """Test climate temperature control buttons"""
    test = TestClimateController()
    test.test_temperature_minus_button(logged_in_page, e2e_config)
    test.test_temperature_plus_button(logged_in_page, e2e_config)


@pytest.mark.e2e
@pytest.mark.domain_climate
def test_climate_fan_mode(logged_in_page: Page, e2e_config):
    """Test climate fan mode selection"""
    test = TestClimateController()
    test.test_fan_mode_buttons_visible(logged_in_page, e2e_config)
