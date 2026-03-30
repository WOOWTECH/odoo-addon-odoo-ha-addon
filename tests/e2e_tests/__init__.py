"""
E2E Tests for Entity Controller Components

This package contains end-to-end UI tests for all Home Assistant
domain entity controllers using Playwright.

Supported Domains:
- switch: On/Off toggle controls
- light: Toggle + brightness slider
- sensor: Read-only value display
- climate: Temperature controls + fan modes
- cover: Open/Close/Stop + position slider
- fan: Toggle + speed slider + oscillate + preset modes
- automation: Toggle + trigger
- scene: Activate button
- script: Run + toggle

Usage:
    # Install dependencies
    pip install pytest playwright pyyaml
    playwright install chromium

    # Run all tests
    pytest e2e_tests/ -v

    # Run specific domain tests
    pytest e2e_tests/ -v -m domain_switch
    pytest e2e_tests/ -v -m domain_light

    # Run with custom config
    E2E_CONFIG_FILE=my_config.yaml pytest e2e_tests/ -v

    # Run in headed mode (for debugging)
    E2E_HEADLESS=false pytest e2e_tests/ -v

Configuration:
    See e2e_config.yaml for all configuration options.
    Copy to e2e_config.local.yaml and customize for your environment.
"""

from .config import E2EConfig, get_config, reset_config
from .base import (
    BaseE2ETest,
    OdooE2ETest,
    EntityControllerTest,
    e2e_config,
    browser,
    context,
    page,
    logged_in_page,
)

__all__ = [
    # Config
    "E2EConfig",
    "get_config",
    "reset_config",
    # Base classes
    "BaseE2ETest",
    "OdooE2ETest",
    "EntityControllerTest",
    # Fixtures
    "e2e_config",
    "browser",
    "context",
    "page",
    "logged_in_page",
]
