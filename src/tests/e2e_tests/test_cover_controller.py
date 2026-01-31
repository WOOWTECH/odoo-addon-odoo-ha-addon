"""
E2E Tests for Cover Domain Controller

Tests the cover entity controller UI interactions including:
- Open/Close/Stop buttons
- Position slider control
- State display
- Loading states
"""

import pytest
from playwright.sync_api import Page, expect

from .base import EntityControllerTest, logged_in_page, e2e_config, browser, context, page


class TestCoverController(EntityControllerTest):
    """E2E tests for cover domain controller"""

    domain = "cover"

    # =========================================================================
    # Display Tests
    # =========================================================================

    def test_cover_controller_visible(self, logged_in_page: Page, e2e_config):
        """Test that cover controller is visible"""
        self.page = logged_in_page
        self.config = e2e_config

        self.navigate_to_entity_list("cover")

        controller = self.find_entity_controller("cover")
        if controller:
            expect(controller).to_be_visible()
        else:
            pytest.skip("No cover entities found in the system")

    def test_cover_state_badge_displayed(self, logged_in_page: Page, e2e_config):
        """Test that state badge is displayed"""
        self.page = logged_in_page
        self.config = e2e_config

        self.navigate_to_entity_list("cover")

        badge = self.page.locator(self.config.get_selector("cover", "state_badge")).first

        if badge.count() == 0:
            pytest.skip("No cover state badges found")

        expect(badge).to_be_visible()

    # =========================================================================
    # Button Tests
    # =========================================================================

    def test_open_button_visible(self, logged_in_page: Page, e2e_config):
        """Test that Open button is visible"""
        self.page = logged_in_page
        self.config = e2e_config

        self.navigate_to_entity_list("cover")

        open_btn = self.page.locator(self.config.get_selector("cover", "open_button")).first

        if open_btn.count() == 0:
            pytest.skip("No cover open buttons found")

        expect(open_btn).to_be_visible()
        expect(open_btn).to_contain_text("Open")

    def test_stop_button_visible(self, logged_in_page: Page, e2e_config):
        """Test that Stop button is visible"""
        self.page = logged_in_page
        self.config = e2e_config

        self.navigate_to_entity_list("cover")

        stop_btn = self.page.locator(self.config.get_selector("cover", "stop_button")).first

        if stop_btn.count() == 0:
            pytest.skip("No cover stop buttons found")

        expect(stop_btn).to_be_visible()
        expect(stop_btn).to_contain_text("Stop")

    def test_close_button_visible(self, logged_in_page: Page, e2e_config):
        """Test that Close button is visible"""
        self.page = logged_in_page
        self.config = e2e_config

        self.navigate_to_entity_list("cover")

        close_btn = self.page.locator(self.config.get_selector("cover", "close_button")).first

        if close_btn.count() == 0:
            pytest.skip("No cover close buttons found")

        expect(close_btn).to_be_visible()
        expect(close_btn).to_contain_text("Close")

    def test_open_button_click(self, logged_in_page: Page, e2e_config):
        """Test clicking Open button"""
        self.page = logged_in_page
        self.config = e2e_config

        self.navigate_to_entity_list("cover")

        open_btn = self.page.locator(self.config.get_selector("cover", "open_button")).first

        if open_btn.count() == 0:
            pytest.skip("No cover open buttons found")

        open_btn.click()
        self.page.wait_for_timeout(e2e_config.get_wait_time("api_response"))

        expect(open_btn).to_be_enabled()

    def test_stop_button_click(self, logged_in_page: Page, e2e_config):
        """Test clicking Stop button"""
        self.page = logged_in_page
        self.config = e2e_config

        self.navigate_to_entity_list("cover")

        stop_btn = self.page.locator(self.config.get_selector("cover", "stop_button")).first

        if stop_btn.count() == 0:
            pytest.skip("No cover stop buttons found")

        stop_btn.click()
        self.page.wait_for_timeout(e2e_config.get_wait_time("api_response"))

        expect(stop_btn).to_be_enabled()

    def test_close_button_click(self, logged_in_page: Page, e2e_config):
        """Test clicking Close button"""
        self.page = logged_in_page
        self.config = e2e_config

        self.navigate_to_entity_list("cover")

        close_btn = self.page.locator(self.config.get_selector("cover", "close_button")).first

        if close_btn.count() == 0:
            pytest.skip("No cover close buttons found")

        close_btn.click()
        self.page.wait_for_timeout(e2e_config.get_wait_time("api_response"))

        expect(close_btn).to_be_enabled()

    # =========================================================================
    # Button Style Tests
    # =========================================================================

    def test_open_button_has_success_class(self, logged_in_page: Page, e2e_config):
        """Test that Open button has btn-success class"""
        self.page = logged_in_page
        self.config = e2e_config

        self.navigate_to_entity_list("cover")

        open_btn = self.page.locator(".cover-controller button.btn-success").first

        if open_btn.count() > 0:
            expect(open_btn).to_contain_text("Open")

    def test_stop_button_has_warning_class(self, logged_in_page: Page, e2e_config):
        """Test that Stop button has btn-warning class"""
        self.page = logged_in_page
        self.config = e2e_config

        self.navigate_to_entity_list("cover")

        stop_btn = self.page.locator(".cover-controller button.btn-warning").first

        if stop_btn.count() > 0:
            expect(stop_btn).to_contain_text("Stop")

    def test_close_button_has_danger_class(self, logged_in_page: Page, e2e_config):
        """Test that Close button has btn-danger class"""
        self.page = logged_in_page
        self.config = e2e_config

        self.navigate_to_entity_list("cover")

        close_btn = self.page.locator(".cover-controller button.btn-danger").first

        if close_btn.count() > 0:
            expect(close_btn).to_contain_text("Close")

    # =========================================================================
    # Position Slider Tests
    # =========================================================================

    def test_position_slider_visible(self, logged_in_page: Page, e2e_config):
        """Test that position slider is visible when cover supports position"""
        self.page = logged_in_page
        self.config = e2e_config

        self.navigate_to_entity_list("cover")

        slider = self.page.locator(self.config.get_selector("cover", "position_slider")).first

        if slider.count() == 0:
            pytest.skip("No cover position sliders found")

        expect(slider).to_be_visible()

    def test_position_label_shows_percentage(self, logged_in_page: Page, e2e_config):
        """Test that position label shows percentage"""
        self.page = logged_in_page
        self.config = e2e_config

        self.navigate_to_entity_list("cover")

        label = self.page.locator(self.config.get_selector("cover", "position_label")).first

        if label.count() == 0:
            pytest.skip("No cover position labels found")

        text = label.inner_text()
        assert "Position" in text
        assert "%" in text

    def test_position_slider_drag(self, logged_in_page: Page, e2e_config):
        """Test dragging position slider"""
        self.page = logged_in_page
        self.config = e2e_config

        self.navigate_to_entity_list("cover")

        slider = self.page.locator(self.config.get_selector("cover", "position_slider")).first

        if slider.count() == 0:
            pytest.skip("No cover position sliders found")

        # Set position via fill
        slider.fill("50")
        slider.dispatch_event("change")

        self.page.wait_for_timeout(e2e_config.get_wait_time("debounce"))

    def test_position_slider_min_max(self, logged_in_page: Page, e2e_config):
        """Test position slider has correct min/max values"""
        self.page = logged_in_page
        self.config = e2e_config

        self.navigate_to_entity_list("cover")

        slider = self.page.locator(self.config.get_selector("cover", "position_slider")).first

        if slider.count() == 0:
            pytest.skip("No cover position sliders found")

        min_val = slider.get_attribute("min")
        max_val = slider.get_attribute("max")

        assert min_val == "0"
        assert max_val == "100"

    # =========================================================================
    # Icon Tests
    # =========================================================================

    def test_open_button_shows_arrow_up_icon(self, logged_in_page: Page, e2e_config):
        """Test that Open button shows arrow-up icon"""
        self.page = logged_in_page
        self.config = e2e_config

        self.navigate_to_entity_list("cover")

        open_btn = self.page.locator(".cover-controller button.btn-success").first

        if open_btn.count() > 0:
            icon = open_btn.locator("i.fa-arrow-up")
            if icon.count() > 0:
                expect(icon).to_be_visible()

    def test_stop_button_shows_stop_icon(self, logged_in_page: Page, e2e_config):
        """Test that Stop button shows stop icon"""
        self.page = logged_in_page
        self.config = e2e_config

        self.navigate_to_entity_list("cover")

        stop_btn = self.page.locator(".cover-controller button.btn-warning").first

        if stop_btn.count() > 0:
            icon = stop_btn.locator("i.fa-stop")
            if icon.count() > 0:
                expect(icon).to_be_visible()

    def test_close_button_shows_arrow_down_icon(self, logged_in_page: Page, e2e_config):
        """Test that Close button shows arrow-down icon"""
        self.page = logged_in_page
        self.config = e2e_config

        self.navigate_to_entity_list("cover")

        close_btn = self.page.locator(".cover-controller button.btn-danger").first

        if close_btn.count() > 0:
            icon = close_btn.locator("i.fa-arrow-down")
            if icon.count() > 0:
                expect(icon).to_be_visible()


# =============================================================================
# Standalone Test Functions
# =============================================================================


@pytest.mark.e2e
@pytest.mark.domain_cover
def test_cover_controller_renders(logged_in_page: Page, e2e_config):
    """Test cover controller renders correctly"""
    test = TestCoverController()
    test.test_cover_controller_visible(logged_in_page, e2e_config)


@pytest.mark.e2e
@pytest.mark.domain_cover
def test_cover_buttons(logged_in_page: Page, e2e_config):
    """Test cover control buttons"""
    test = TestCoverController()
    test.test_open_button_visible(logged_in_page, e2e_config)
    test.test_stop_button_visible(logged_in_page, e2e_config)
    test.test_close_button_visible(logged_in_page, e2e_config)


@pytest.mark.e2e
@pytest.mark.domain_cover
def test_cover_position_slider(logged_in_page: Page, e2e_config):
    """Test cover position slider"""
    test = TestCoverController()
    test.test_position_slider_visible(logged_in_page, e2e_config)
