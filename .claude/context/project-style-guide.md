---
created: 2026-01-01T15:23:16Z
last_updated: 2026-01-01T15:23:16Z
version: 1.0
author: Claude Code PM System
---

# Project Style Guide

## Naming Conventions

### Python (Backend)

| Element | Convention | Example |
|---------|------------|---------|
| Module | snake_case | `ha_entity.py` |
| Class | PascalCase | `HAInstanceHelper` |
| Function | snake_case | `get_current_instance()` |
| Variable | snake_case | `entity_state` |
| Constant | UPPER_SNAKE | `DEFAULT_TIMEOUT` |
| Private | _prefix | `_internal_method()` |

### JavaScript (Frontend)

| Element | Convention | Example |
|---------|------------|---------|
| File | snake_case | `ha_data_service.js` |
| Class/Component | PascalCase | `EntityController` |
| Function | camelCase | `fetchEntities()` |
| Variable | camelCase | `entityState` |
| Constant | UPPER_SNAKE | `MAX_RETRIES` |
| Hook | usePrefixed | `useEntityControl()` |

### XML (Templates)

| Element | Convention | Example |
|---------|------------|---------|
| Template ID | PrefixedPascal | `HaEntityCard` |
| CSS Class | kebab-case | `ha-entity-card` |
| Component Name | PascalCase | `EntityController` |

## File Structure Patterns

### Model Files
```python
# models/ha_entity.py

from odoo import models, fields, api
from odoo.exceptions import UserError

class HAEntity(models.Model):
    _name = 'ha.entity'
    _description = 'Home Assistant Entity'

    # 1. Field definitions (grouped by type)
    name = fields.Char(string='Name', required=True)
    state = fields.Char(string='State')
    instance_id = fields.Many2one('ha.instance', string='Instance')

    # 2. Compute/inverse methods
    @api.depends('state')
    def _compute_state_display(self):
        ...

    # 3. Constraint methods
    @api.constrains('name')
    def _check_name(self):
        ...

    # 4. CRUD overrides
    def write(self, vals):
        ...

    # 5. Action methods
    def action_sync(self):
        ...

    # 6. Private methods
    def _internal_helper(self):
        ...
```

### Component Files
```javascript
// static/src/components/entity_card/entity_card.js

/** @odoo-module */

import { Component, useState, onWillUnmount } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

export class EntityCard extends Component {
    static template = "odoo_ha_addon.EntityCard";
    static props = {
        entity: Object,
        onUpdate: { type: Function, optional: true },
    };

    setup() {
        this.state = useState({ loading: false });
        this.haDataService = useService("ha_data");

        onWillUnmount(() => {
            this.cleanup();
        });
    }

    async onToggle() {
        // Implementation
    }
}
```

## Code Style Rules

### Python

```python
# Imports: Standard, third-party, Odoo, local
import logging
from datetime import datetime

from odoo import models, fields, api
from odoo.exceptions import UserError

from .common.utils import format_state

_logger = logging.getLogger(__name__)

# Class docstrings
class HAEntity(models.Model):
    """Home Assistant Entity Model.

    This model stores entity data synchronized from Home Assistant.
    """

# Method docstrings for complex methods
def sync_entities(self, instance_id):
    """Synchronize entities from Home Assistant.

    Args:
        instance_id: ID of the HA instance to sync from

    Returns:
        dict: Sync results with success count and errors

    Raises:
        UserError: If instance is not configured
    """
```

### JavaScript

```javascript
// Use JSDoc for complex functions
/**
 * Fetches entity data from the backend.
 * @param {number} instanceId - The instance ID
 * @param {Object} options - Fetch options
 * @param {boolean} options.includeHistory - Include history data
 * @returns {Promise<Array>} Entity list
 */
async fetchEntities(instanceId, options = {}) {
    // Implementation
}

// Prefer async/await over .then()
// Good
async loadData() {
    const data = await this.service.fetch();
    this.state.data = data;
}

// Avoid
loadData() {
    this.service.fetch().then(data => {
        this.state.data = data;
    });
}
```

## Comment Style

### When to Comment
- Complex business logic
- Non-obvious workarounds
- API contract documentation
- TODO items with context

### Comment Format
```python
# Single line for brief explanations
result = complex_calculation()  # Inline only for very short notes

# TODO: Add pagination support (Issue #123)
# FIXME: Workaround for HA WebSocket bug (see docs/issues/websocket.md)
```

```javascript
// Single line comments for brief notes

/*
 * Multi-line comments for longer explanations
 * that span multiple lines.
 */

// TODO: Migrate to new chart library when available
```

## XML Template Style

```xml
<?xml version="1.0" encoding="UTF-8"?>
<templates xml:space="preserve">
    <t t-name="odoo_ha_addon.EntityCard">
        <div class="ha-entity-card" t-att-class="{ 'is-active': props.entity.state === 'on' }">
            <h4 t-out="props.entity.name"/>
            <span class="state-badge" t-out="props.entity.state"/>

            <t t-if="props.entity.is_controllable">
                <button class="btn btn-primary" t-on-click="onToggle">
                    Toggle
                </button>
            </t>
        </div>
    </t>
</templates>
```

## Error Handling Patterns

### Backend
```python
from odoo.exceptions import UserError, AccessError

def action_connect(self):
    try:
        result = self._connect_to_ha()
    except ConnectionError as e:
        raise UserError(_("Failed to connect: %s") % str(e))
    except PermissionError as e:
        raise AccessError(_("Access denied: %s") % str(e))
```

### Frontend
```javascript
async fetchData() {
    try {
        this.state.loading = true;
        const data = await this.service.fetch();
        this.state.data = data;
    } catch (error) {
        this.notification.add(_t("Failed to load data"), { type: "danger" });
        debugWarn("Fetch error:", error);
    } finally {
        this.state.loading = false;
    }
}
```

## Commit Message Style

```
{type}: {description}

Types:
- feat: New feature
- fix: Bug fix
- docs: Documentation
- style: Formatting (no code change)
- refactor: Code restructuring
- perf: Performance improvement
- test: Test additions
- chore: Maintenance tasks

Examples:
feat: add multi-instance support for entity sync
fix: resolve WebSocket reconnection loop
refactor: extract chart constants to dedicated module
docs: update API documentation for v18.0.5.0
```

## Internationalization

### Python
```python
from odoo import _

# Translatable strings
raise UserError(_("Entity not found"))
message = _("Sync completed: %d entities") % count
```

### JavaScript
```javascript
import { _t } from "@web/core/l10n/translation";

this.notification.add(_t("Connection established"), { type: "success" });
```

## Testing Patterns

### Python Tests
```python
from odoo.tests.common import TransactionCase

class TestHAEntity(TransactionCase):

    def setUp(self):
        super().setUp()
        self.instance = self.env['ha.instance'].create({...})

    def test_entity_sync_creates_records(self):
        """Entity sync should create new entity records."""
        # Arrange
        # Act
        result = self.instance.action_sync_entities()
        # Assert
        self.assertEqual(result['success_count'], 5)
```
