"""
E2E Test Configuration for Entity Controller Tests

This module provides flexible configuration for E2E UI testing of all
Home Assistant domain entity controllers.

Usage:
    # From command line
    python -m pytest e2e_tests/ --config-file=e2e_config.yaml

    # Or use environment variables
    E2E_BASE_URL=http://localhost:8069 python -m pytest e2e_tests/
"""

import os
import yaml
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, Dict, List, Any

# Default configuration
DEFAULT_CONFIG = {
    # Base URLs
    "odoo_base_url": "http://localhost",
    "odoo_port": 8069,

    # Authentication
    "odoo_database": "odoo",
    "odoo_username": "admin",
    "odoo_password": "admin",

    # Home Assistant Instance (for testing)
    "ha_instance_name": "Test HA Instance",

    # Browser settings
    "browser": "chromium",  # chromium, firefox, webkit
    "headless": True,
    "slow_mo": 0,  # Slow down actions by X ms (for debugging)
    "timeout": 30000,  # Default timeout in ms

    # Screenshot settings
    "screenshot_on_failure": True,
    "screenshot_dir": "e2e_tests/screenshots",

    # Test data
    "test_entities": {
        "switch": {
            "entity_id": "switch.test_switch",
            "name": "Test Switch",
            "initial_state": "off",
        },
        "light": {
            "entity_id": "light.test_light",
            "name": "Test Light",
            "initial_state": "off",
            "attributes": {
                "brightness": 255,
                "supported_color_modes": ["brightness"],
            },
        },
        "sensor": {
            "entity_id": "sensor.test_temperature",
            "name": "Test Temperature",
            "initial_state": "23.5",
            "attributes": {
                "unit_of_measurement": "°C",
                "device_class": "temperature",
            },
        },
        "climate": {
            "entity_id": "climate.test_thermostat",
            "name": "Test Thermostat",
            "initial_state": "heat",
            "attributes": {
                "temperature": 22,
                "current_temperature": 20.5,
                "hvac_modes": ["off", "heat", "cool", "auto"],
                "fan_modes": ["auto", "low", "medium", "high"],
            },
        },
        "cover": {
            "entity_id": "cover.test_blind",
            "name": "Test Blind",
            "initial_state": "open",
            "attributes": {
                "current_position": 100,
            },
        },
        "fan": {
            "entity_id": "fan.test_fan",
            "name": "Test Fan",
            "initial_state": "off",
            "attributes": {
                "percentage": 50,
                "oscillating": False,
                "preset_modes": ["normal", "sleep", "nature"],
            },
        },
        "automation": {
            "entity_id": "automation.test_automation",
            "name": "Test Automation",
            "initial_state": "on",
        },
        "scene": {
            "entity_id": "scene.test_scene",
            "name": "Test Scene",
            "initial_state": "scening",
        },
        "script": {
            "entity_id": "script.test_script",
            "name": "Test Script",
            "initial_state": "off",
        },
    },

    # Domain-specific test settings
    "domain_tests": {
        "switch": {
            "enabled": True,
            "test_toggle": True,
        },
        "light": {
            "enabled": True,
            "test_toggle": True,
            "test_brightness": True,
            "brightness_values": [0, 64, 128, 192, 255],
        },
        "sensor": {
            "enabled": True,
            # Sensors are read-only, only test display
        },
        "climate": {
            "enabled": True,
            "test_temperature": True,
            "temperature_values": [18, 20, 22, 24],
            "test_fan_mode": True,
        },
        "cover": {
            "enabled": True,
            "test_open_close": True,
            "test_position": True,
            "position_values": [0, 25, 50, 75, 100],
        },
        "fan": {
            "enabled": True,
            "test_toggle": True,
            "test_percentage": True,
            "percentage_values": [0, 25, 50, 75, 100],
            "test_oscillate": True,
            "test_preset_mode": True,
        },
        "automation": {
            "enabled": True,
            "test_toggle": True,
            "test_trigger": True,
        },
        "scene": {
            "enabled": True,
            "test_activate": True,
        },
        "script": {
            "enabled": True,
            "test_run": True,
            "test_toggle": True,
        },
    },

    # Selectors for UI elements
    "selectors": {
        # Common selectors
        "entity_card": ".o_kanban_record",
        "entity_controller": ".entity-controller",

        # Domain-specific selectors
        "switch": {
            "controller": ".switch-controller",
            "toggle_button": ".switch-controller button.btn",
            "form_switch": ".switch-controller .form-check-input",
            "state_badge": ".switch-controller .badge",
        },
        "light": {
            "controller": ".light-controller",
            "toggle_button": ".light-controller button.btn",
            "brightness_slider": ".light-controller input[type='range']",
            "brightness_label": ".light-controller .form-label",
            "state_badge": ".light-controller .badge",
        },
        "sensor": {
            "controller": ".sensor-controller",
            "value_badge": ".sensor-controller .badge",
            "device_class": ".sensor-controller .text-muted",
        },
        "climate": {
            "controller": ".climate-controller",
            "temp_badge": ".climate-controller .badge.bg-primary",
            "target_badge": ".climate-controller .badge.bg-success",
            "hvac_badge": ".climate-controller .badge.bg-info",
            "temp_input": ".climate-controller input[type='number']",
            "temp_minus": ".climate-controller button:first-child",
            "temp_plus": ".climate-controller button:last-child",
            "fan_mode_buttons": ".climate-controller .fan-mode-control .btn-group button",
        },
        "cover": {
            "controller": ".cover-controller",
            "open_button": ".cover-controller button.btn-success",
            "stop_button": ".cover-controller button.btn-warning",
            "close_button": ".cover-controller button.btn-danger",
            "position_slider": ".cover-controller input[type='range']",
            "position_label": ".cover-controller .form-label",
            "state_badge": ".cover-controller .badge.bg-info",
        },
        "fan": {
            "controller": ".fan-controller",
            "toggle_button": ".fan-controller button.btn:first-child",
            "speed_slider": ".fan-controller input[type='range']",
            "speed_label": ".fan-controller .speed-control .form-label",
            "oscillate_button": ".fan-controller button.btn-outline-info",
            "preset_select": ".fan-controller select.form-select",
            "state_badge": ".fan-controller .badge:last-child",
        },
        "automation": {
            "controller": ".automation-controller",
            "toggle_button": ".automation-controller button.btn:first-child",
            "trigger_button": ".automation-controller button.btn-warning",
            "state_badge": ".automation-controller .badge:last-child",
        },
        "scene": {
            "controller": ".scene-controller",
            "activate_button": ".scene-controller button.btn-primary",
            "scene_badge": ".scene-controller .badge",
        },
        "script": {
            "controller": ".script-controller",
            "run_button": ".script-controller button.btn-success",
            "toggle_button": ".script-controller button.btn:nth-child(2)",
            "state_badge": ".script-controller .badge:last-child",
        },
    },

    # Wait times
    "wait_times": {
        "page_load": 5000,
        "api_response": 3000,
        "animation": 500,
        "debounce": 1000,
    },

    # Reporting
    "reporting": {
        "generate_html": True,
        "generate_json": True,
        "output_dir": "e2e_tests/reports",
    },
}


@dataclass
class E2EConfig:
    """E2E Test Configuration Class"""

    odoo_base_url: str = "http://localhost"
    odoo_port: int = 8069
    odoo_database: str = "odoo"
    odoo_username: str = "admin"
    odoo_password: str = "admin"
    ha_instance_name: str = "Test HA Instance"

    browser: str = "chromium"
    headless: bool = True
    slow_mo: int = 0
    timeout: int = 30000

    screenshot_on_failure: bool = True
    screenshot_dir: str = "e2e_tests/screenshots"

    test_entities: Dict[str, Dict] = field(default_factory=dict)
    domain_tests: Dict[str, Dict] = field(default_factory=dict)
    selectors: Dict[str, Any] = field(default_factory=dict)
    wait_times: Dict[str, int] = field(default_factory=dict)
    reporting: Dict[str, Any] = field(default_factory=dict)

    @property
    def base_url(self) -> str:
        """Get the full base URL"""
        if self.odoo_port == 80:
            return self.odoo_base_url
        return f"{self.odoo_base_url}:{self.odoo_port}"

    @property
    def login_url(self) -> str:
        """Get the login URL"""
        return f"{self.base_url}/web/login"

    @property
    def dashboard_url(self) -> str:
        """Get the HA dashboard URL"""
        return f"{self.base_url}/web#action=odoo_ha_addon.action_ha_instance_dashboard"

    def get_entity_config(self, domain: str) -> Optional[Dict]:
        """Get test entity configuration for a domain"""
        return self.test_entities.get(domain)

    def get_domain_test_config(self, domain: str) -> Optional[Dict]:
        """Get test configuration for a domain"""
        return self.domain_tests.get(domain)

    def is_domain_enabled(self, domain: str) -> bool:
        """Check if domain tests are enabled"""
        config = self.domain_tests.get(domain, {})
        return config.get("enabled", True)

    def get_selector(self, domain: str, element: str) -> Optional[str]:
        """Get a selector for a domain element"""
        domain_selectors = self.selectors.get(domain, {})
        return domain_selectors.get(element)

    def get_wait_time(self, wait_type: str) -> int:
        """Get wait time in milliseconds"""
        return self.wait_times.get(wait_type, 1000)

    @classmethod
    def from_dict(cls, data: Dict) -> "E2EConfig":
        """Create config from dictionary"""
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})

    @classmethod
    def from_yaml(cls, filepath: str) -> "E2EConfig":
        """Load config from YAML file"""
        with open(filepath, "r") as f:
            data = yaml.safe_load(f)
        return cls.from_dict(data)

    @classmethod
    def from_env(cls) -> "E2EConfig":
        """Load config from environment variables"""
        config = DEFAULT_CONFIG.copy()

        # Override with environment variables
        env_mappings = {
            "E2E_BASE_URL": "odoo_base_url",
            "E2E_PORT": ("odoo_port", int),
            "E2E_DATABASE": "odoo_database",
            "E2E_USERNAME": "odoo_username",
            "E2E_PASSWORD": "odoo_password",
            "E2E_BROWSER": "browser",
            "E2E_HEADLESS": ("headless", lambda x: x.lower() == "true"),
            "E2E_SLOW_MO": ("slow_mo", int),
            "E2E_TIMEOUT": ("timeout", int),
        }

        for env_key, config_key in env_mappings.items():
            value = os.environ.get(env_key)
            if value:
                if isinstance(config_key, tuple):
                    key, converter = config_key
                    config[key] = converter(value)
                else:
                    config[config_key] = value

        return cls.from_dict(config)

    @classmethod
    def load(cls, config_file: Optional[str] = None) -> "E2EConfig":
        """
        Load configuration with priority:
        1. Specified config file
        2. Default config file (e2e_config.yaml)
        3. Environment variables
        4. Default values
        """
        # Start with defaults
        config_data = DEFAULT_CONFIG.copy()

        # Try to load from file
        config_paths = [
            config_file,
            "e2e_config.yaml",
            "e2e_tests/e2e_config.yaml",
            Path(__file__).parent / "e2e_config.yaml",
        ]

        for path in config_paths:
            if path and Path(path).exists():
                with open(path, "r") as f:
                    file_config = yaml.safe_load(f)
                    if file_config:
                        # Deep merge
                        _deep_merge(config_data, file_config)
                break

        # Override with environment variables
        env_overrides = cls.from_env().__dict__
        for key, value in env_overrides.items():
            if os.environ.get(f"E2E_{key.upper()}"):
                config_data[key] = value

        return cls.from_dict(config_data)

    def to_yaml(self, filepath: str):
        """Save config to YAML file"""
        with open(filepath, "w") as f:
            yaml.dump(self.__dict__, f, default_flow_style=False)


def _deep_merge(base: Dict, override: Dict) -> Dict:
    """Deep merge two dictionaries"""
    for key, value in override.items():
        if key in base and isinstance(base[key], dict) and isinstance(value, dict):
            _deep_merge(base[key], value)
        else:
            base[key] = value
    return base


# Global config instance
_config: Optional[E2EConfig] = None


def get_config(config_file: Optional[str] = None) -> E2EConfig:
    """Get or create the global configuration"""
    global _config
    if _config is None or config_file:
        _config = E2EConfig.load(config_file)
    return _config


def reset_config():
    """Reset the global configuration"""
    global _config
    _config = None
