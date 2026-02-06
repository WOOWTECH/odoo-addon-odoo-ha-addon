---
framework: odoo
test_command: odoo-bin --test-enable -i odoo_ha_addon
created: 2026-01-02T17:48:00Z
---

# Testing Configuration

## Framework
- Type: Odoo Test Framework (based on Python unittest)
- Version: Odoo 18.0
- Config File: __manifest__.py (module definition)
- Test Base Classes: TransactionCase, HttpCase

## Test Structure
- Test Directory: `tests/`
- Test Files: 4 files found
- Naming Pattern: `test_*.py`
- Test Classes: 12 classes total

## Test Files

| File | Classes | Type |
|------|---------|------|
| `test_controllers.py` | 3 | TransactionCase |
| `test_portal_mixin.py` | 3 | TransactionCase |
| `test_portal_controller.py` | 3 | HttpCase |
| `test_share_permissions.py` | 4 | TransactionCase |

## Test Tags
- `@tagged('post_install', '-at_install')` - Run after module install

## Commands

### Run All Tests (via Docker)
```bash
# From main project directory
MAIN_PROJECT="/Users/eugene/Documents/woow/AREA-odoo/odoo-server"
cd "$MAIN_PROJECT" && docker compose exec web \
  odoo-bin -d odoo -u odoo_ha_addon --test-enable --stop-after-init \
  --log-handler odoo.addons.odoo_ha_addon:DEBUG
```

### Run Specific Test Module
```bash
docker compose exec web \
  odoo-bin -d odoo -u odoo_ha_addon --test-enable --test-tags odoo_ha_addon \
  --stop-after-init
```

### Run with Debug Output
```bash
docker compose exec web \
  odoo-bin -d odoo -u odoo_ha_addon --test-enable --stop-after-init \
  --log-handler odoo.addons.odoo_ha_addon:DEBUG \
  --log-level=debug
```

## Environment
- Required: Docker with Odoo 18 container running
- Database: `odoo` (test uses transaction rollback)
- Test Isolation: Each TransactionCase uses savepoint rollback

## Test Runner Agent Configuration
- Use verbose output for debugging
- Run tests via Odoo test runner (not pytest)
- Tests run in isolated database transactions
- HttpCase tests require running HTTP server
- Wait for each test to complete

## Common Issues to Check
- Docker container must be running
- Module must be installed in database
- For HttpCase: Odoo web server must be accessible
- Test database permissions

## Test Categories

### Unit Tests (TransactionCase)
- `test_portal_mixin.py` - Portal mixin methods
- `test_share_permissions.py` - Permission and access tests
- `test_controllers.py` - Controller logic tests

### Integration Tests (HttpCase)
- `test_portal_controller.py` - HTTP route tests with browser simulation

## Notes
- Odoo tests are NOT run with pytest
- Tests are executed during module upgrade with `--test-enable`
- TransactionCase: Each test method runs in a rollback transaction
- HttpCase: Full HTTP requests, slower but more realistic
