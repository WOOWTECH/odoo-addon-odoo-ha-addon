# E2E Tests for Entity Controller Components

End-to-end UI tests for all Home Assistant domain entity controllers using Playwright.

## Features

- **Full Domain Coverage**: Tests for all 9 entity domains
- **Interactive Mode**: Manual testing with live browser
- **Setup Wizard**: Easy configuration via interactive setup
- **Test Data Generator**: Create mock entities for testing
- **Flexible Config**: YAML config, environment variables, CLI options
- **Reports**: HTML and JSON test reports
- **Screenshots**: Automatic failure screenshots

## Supported Domains

| Domain | Description | Test Count |
|--------|-------------|------------|
| **switch** | On/Off toggle controls | 11 tests |
| **light** | Toggle + brightness slider | 13 tests |
| **sensor** | Read-only value display | 8 tests |
| **climate** | Temperature controls + fan modes | 13 tests |
| **cover** | Open/Close/Stop + position slider | 15 tests |
| **fan** | Toggle + speed + oscillate + presets | 16 tests |
| **automation** | Toggle + trigger | 11 tests |
| **scene** | Activate button | 6 tests |
| **script** | Run + toggle | 12 tests |

## Quick Start

### Option 1: Setup Wizard (Recommended)

```bash
python e2e_tests/setup.py
```

The wizard will:
- Check and install dependencies
- Configure connection settings
- Test Odoo connection
- Create configuration file

### Option 2: Manual Setup

#### 1. Install Dependencies

```bash
# Python dependencies
pip install pytest playwright pyyaml pytest-html

# Install Playwright browser
playwright install chromium
```

#### 2. Configure Environment

Copy the example config and customize:

```bash
cp e2e_tests/e2e_config.yaml e2e_tests/e2e_config.local.yaml
```

Edit `e2e_config.local.yaml`:

```yaml
# Connection settings
odoo_base_url: "http://localhost"
odoo_port: 80
odoo_database: "odoo"
odoo_username: "admin"
odoo_password: "your_password"

# Browser settings
browser: "chromium"
headless: true
```

### 3. Run Tests

```bash
# Run all tests
python e2e_tests/run_tests.py

# Run specific domain
python e2e_tests/run_tests.py --domain switch
python e2e_tests/run_tests.py --domain light

# Run in debug mode (visible browser + slow motion)
python e2e_tests/run_tests.py --debug

# Generate HTML report
python e2e_tests/run_tests.py --html-report
```

## Test Structure

```
e2e_tests/
├── config.py                    # Configuration management
├── base.py                      # Base test classes
├── conftest.py                  # Pytest configuration
├── run_tests.py                 # Test runner script
├── e2e_config.yaml             # Default configuration
│
├── test_switch_controller.py    # Switch domain tests
├── test_light_controller.py     # Light domain tests
├── test_sensor_controller.py    # Sensor domain tests
├── test_climate_controller.py   # Climate domain tests
├── test_cover_controller.py     # Cover domain tests
├── test_fan_controller.py       # Fan domain tests
├── test_automation_controller.py # Automation domain tests
├── test_scene_controller.py     # Scene domain tests
└── test_script_controller.py    # Script domain tests
```

## Configuration Options

### Environment Variables

```bash
# Override config via environment
E2E_BASE_URL=http://localhost E2E_PORT=8069 pytest e2e_tests/

# Use custom config file
E2E_CONFIG_FILE=my_config.yaml pytest e2e_tests/

# Run headless
E2E_HEADLESS=true pytest e2e_tests/
```

### Command Line Options

```bash
# Domain filter
pytest e2e_tests/ --domain switch

# Browser options
pytest e2e_tests/ --headless=false --slow-mo=500

# Keyword filter
pytest e2e_tests/ -k "toggle"

# Verbose output
pytest e2e_tests/ -v

# Stop on first failure
pytest e2e_tests/ -x
```

### Config File Options

See `e2e_config.yaml` for all options:

```yaml
# Connection
odoo_base_url: "http://localhost"
odoo_port: 80
odoo_database: "odoo"
odoo_username: "admin"
odoo_password: "admin"

# Browser
browser: "chromium"  # chromium, firefox, webkit
headless: true
slow_mo: 0
timeout: 30000

# Screenshots
screenshot_on_failure: true
screenshot_dir: "e2e_tests/screenshots"

# Test entities (for mock testing)
test_entities:
  switch:
    entity_id: "switch.test_switch"
    name: "Test Switch"
    initial_state: "off"

# Domain test settings
domain_tests:
  switch:
    enabled: true
    test_toggle: true

# Wait times (ms)
wait_times:
  page_load: 5000
  api_response: 3000
  animation: 500
  debounce: 1000
```

## Writing Tests

### Basic Test Structure

```python
import pytest
from playwright.sync_api import Page, expect
from .base import EntityControllerTest, logged_in_page, e2e_config

class TestMyController(EntityControllerTest):
    domain = "my_domain"

    def test_something(self, logged_in_page: Page, e2e_config):
        self.page = logged_in_page
        self.config = e2e_config

        # Navigate to entities
        self.navigate_to_entity_list("my_domain")

        # Find and interact with elements
        button = self.page.locator(".my-button").first
        button.click()

        # Assert
        expect(button).to_be_enabled()
```

### Using Selectors from Config

```python
def test_with_config_selectors(self, logged_in_page: Page, e2e_config):
    self.page = logged_in_page
    self.config = e2e_config

    # Get selector from config
    selector = self.config.get_selector("switch", "toggle_button")
    button = self.page.locator(selector).first
```

### Pytest Markers

```python
@pytest.mark.e2e
@pytest.mark.domain_switch
def test_something():
    pass
```

## Reports

### HTML Report

```bash
python e2e_tests/run_tests.py --html-report
# Output: e2e_tests/reports/report.html
```

### JSON Report

```bash
python e2e_tests/run_tests.py --json-report
# Output: e2e_tests/reports/report.json
```

### Screenshots

Failed tests automatically capture screenshots:
- Location: `e2e_tests/screenshots/`
- Format: `failure_{test_name}.png`

## Troubleshooting

### Browser Not Found

```bash
playwright install chromium
```

### Connection Refused

Check Odoo is running:
```bash
curl http://localhost:8069/web/login
```

### Login Failed

Verify credentials in config file.

### Tests Timeout

Increase timeout in config:
```yaml
timeout: 60000  # 60 seconds
```

### No Entities Found

Tests will skip if no entities of that domain exist.
Create test entities in Home Assistant.

## CI/CD Integration

### GitHub Actions

```yaml
- name: Install dependencies
  run: |
    pip install pytest playwright pyyaml pytest-html
    playwright install chromium

- name: Run E2E tests
  run: python e2e_tests/run_tests.py --html-report

- name: Upload report
  uses: actions/upload-artifact@v3
  with:
    name: e2e-report
    path: e2e_tests/reports/
```

### Docker

```dockerfile
FROM mcr.microsoft.com/playwright/python:v1.40.0-jammy

WORKDIR /app
COPY . .
RUN pip install pytest pyyaml pytest-html

CMD ["python", "e2e_tests/run_tests.py"]
```

## Interactive Mode

For manual testing and debugging:

```bash
python e2e_tests/interactive.py
```

Features:
- Browse entities by domain
- Execute actions (toggle, set brightness, etc.)
- Take screenshots
- View entity states
- Live browser control

## Test Data

Create test entities for testing:

```bash
# Create test entities in Odoo
python e2e_tests/test_data.py create

# List existing test entities
python e2e_tests/test_data.py list

# Clean up test entities
python e2e_tests/test_data.py cleanup

# Generate mock data file
python e2e_tests/test_data.py generate-mock
```

## File Structure

```
e2e_tests/
├── README.md                    # This file
├── __init__.py                  # Package exports
│
├── setup.py                     # Setup wizard
├── run_tests.py                 # Test runner
├── interactive.py               # Interactive mode
├── test_data.py                 # Test data generator
│
├── config.py                    # Configuration management
├── base.py                      # Base test classes
├── conftest.py                  # Pytest configuration
├── e2e_config.yaml              # Default configuration
│
├── test_switch_controller.py    # Switch domain tests
├── test_light_controller.py     # Light domain tests
├── test_sensor_controller.py    # Sensor domain tests
├── test_climate_controller.py   # Climate domain tests
├── test_cover_controller.py     # Cover domain tests
├── test_fan_controller.py       # Fan domain tests
├── test_automation_controller.py # Automation domain tests
├── test_scene_controller.py     # Scene domain tests
└── test_script_controller.py    # Script domain tests
```
