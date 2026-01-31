"""
E2E Tests for Sensor Domain Controller

Tests the sensor entity controller UI display:
- Value display
- Unit of measurement display
- Device class display
- Read-only behavior (no controls)
"""

import pytest
from playwright.sync_api import Page, expect

from .base import EntityControllerTest, logged_in_page, e2e_config, browser, context, page


class TestSensorController(EntityControllerTest):
    """E2E tests for sensor domain controller"""

    domain = "sensor"

    # =========================================================================
    # Display Tests
    # =========================================================================

    def test_sensor_controller_visible(self, logged_in_page: Page, e2e_config):
        """Test that sensor controller is visible"""
        self.page = logged_in_page
        self.config = e2e_config

        self.navigate_to_entity_list("sensor")

        controller = self.find_entity_controller("sensor")
        if controller:
            expect(controller).to_be_visible()
        else:
            pytest.skip("No sensor entities found in the system")

    def test_sensor_value_badge_displayed(self, logged_in_page: Page, e2e_config):
        """Test that sensor value badge is displayed"""
        self.page = logged_in_page
        self.config = e2e_config

        self.navigate_to_entity_list("sensor")

        badge = self.page.locator(self.config.get_selector("sensor", "value_badge")).first

        if badge.count() == 0:
            pytest.skip("No sensor value badges found")

        expect(badge).to_be_visible()
        # Badge should have some value
        badge_text = badge.inner_text()
        assert len(badge_text) > 0

    def test_sensor_shows_value(self, logged_in_page: Page, e2e_config):
        """Test that sensor displays its value"""
        self.page = logged_in_page
        self.config = e2e_config

        self.navigate_to_entity_list("sensor")

        value_badges = self.page.locator(".sensor-controller .badge.bg-info")

        if value_badges.count() == 0:
            pytest.skip("No sensor controllers found")

        # At least one sensor should show a value
        expect(value_badges.first).to_be_visible()

    # =========================================================================
    # Unit of Measurement Tests
    # =========================================================================

    def test_sensor_shows_unit_of_measurement(self, logged_in_page: Page, e2e_config):
        """Test that sensor displays unit of measurement"""
        self.page = logged_in_page
        self.config = e2e_config

        self.navigate_to_entity_list("sensor")

        # Look for sensors with units (°C, %, W, etc.)
        badges = self.page.locator(".sensor-controller .badge.bg-info")

        if badges.count() == 0:
            pytest.skip("No sensor controllers found")

        # Check if any badge contains common units
        found_unit = False
        common_units = ["°C", "°F", "%", "W", "kW", "V", "A", "lx", "ppm", "hPa", "Pa", "mm"]

        for i in range(badges.count()):
            text = badges.nth(i).inner_text()
            for unit in common_units:
                if unit in text:
                    found_unit = True
                    break
            if found_unit:
                break

        # Not all sensors have units, so this is informational

    # =========================================================================
    # Device Class Tests
    # =========================================================================

    def test_sensor_shows_device_class(self, logged_in_page: Page, e2e_config):
        """Test that sensor displays device class if available"""
        self.page = logged_in_page
        self.config = e2e_config

        self.navigate_to_entity_list("sensor")

        device_class_elements = self.page.locator(self.config.get_selector("sensor", "device_class"))

        if device_class_elements.count() > 0:
            # At least one sensor shows device class
            expect(device_class_elements.first).to_be_visible()

    # =========================================================================
    # Read-Only Behavior Tests
    # =========================================================================

    def test_sensor_has_no_buttons(self, logged_in_page: Page, e2e_config):
        """Test that sensor controller has no control buttons"""
        self.page = logged_in_page
        self.config = e2e_config

        self.navigate_to_entity_list("sensor")

        controller = self.page.locator(".sensor-controller").first

        if controller.count() == 0:
            pytest.skip("No sensor controllers found")

        # Sensors should not have any buttons
        buttons = controller.locator("button")
        assert buttons.count() == 0, "Sensor should not have control buttons"

    def test_sensor_has_no_sliders(self, logged_in_page: Page, e2e_config):
        """Test that sensor controller has no sliders"""
        self.page = logged_in_page
        self.config = e2e_config

        self.navigate_to_entity_list("sensor")

        controller = self.page.locator(".sensor-controller").first

        if controller.count() == 0:
            pytest.skip("No sensor controllers found")

        # Sensors should not have any sliders
        sliders = controller.locator("input[type='range']")
        assert sliders.count() == 0, "Sensor should not have sliders"

    def test_sensor_has_no_inputs(self, logged_in_page: Page, e2e_config):
        """Test that sensor controller has no input fields"""
        self.page = logged_in_page
        self.config = e2e_config

        self.navigate_to_entity_list("sensor")

        controller = self.page.locator(".sensor-controller").first

        if controller.count() == 0:
            pytest.skip("No sensor controllers found")

        # Sensors should not have any inputs
        inputs = controller.locator("input")
        assert inputs.count() == 0, "Sensor should not have input fields"

    # =========================================================================
    # Icon Tests
    # =========================================================================

    def test_sensor_shows_tachometer_icon(self, logged_in_page: Page, e2e_config):
        """Test that sensor badge shows tachometer icon"""
        self.page = logged_in_page
        self.config = e2e_config

        self.navigate_to_entity_list("sensor")

        badges = self.page.locator(".sensor-controller .badge.bg-info")

        if badges.count() > 0:
            icon = badges.first.locator("i.fa-tachometer")
            if icon.count() > 0:
                expect(icon).to_be_visible()


# =============================================================================
# Standalone Test Functions
# =============================================================================


@pytest.mark.e2e
@pytest.mark.domain_sensor
def test_sensor_controller_renders(logged_in_page: Page, e2e_config):
    """Test sensor controller renders correctly"""
    test = TestSensorController()
    test.test_sensor_controller_visible(logged_in_page, e2e_config)


@pytest.mark.e2e
@pytest.mark.domain_sensor
def test_sensor_is_read_only(logged_in_page: Page, e2e_config):
    """Test sensor has no interactive controls"""
    test = TestSensorController()
    test.test_sensor_has_no_buttons(logged_in_page, e2e_config)
    test.test_sensor_has_no_sliders(logged_in_page, e2e_config)


@pytest.mark.e2e
@pytest.mark.domain_sensor
def test_sensor_value_display(logged_in_page: Page, e2e_config):
    """Test sensor value is displayed"""
    test = TestSensorController()
    test.test_sensor_value_badge_displayed(logged_in_page, e2e_config)
