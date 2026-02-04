# i18n Development Guide

This guide explains how to write translatable code in the Odoo HA Addon, covering both frontend (JavaScript/OWL) and backend (Python) patterns.

## Quick Reference

| Location | Method | Auto-translated? | Example |
|----------|--------|------------------|---------|
| Python code | `_()` | No | `_("Hello")` |
| JavaScript/OWL code | `_t()` | No | `_t("Hello")` |
| QWeb XML text | - | Yes | `<span>Hello</span>` |
| XML `string` attribute | - | Yes | `string="Hello"` |
| XML `placeholder` attribute | - | No | Use `t-att-placeholder` |

## Overview

Odoo 18 uses `.po` files for translations, which are loaded directly at runtime without database import. The translation workflow:

1. Write code with English strings
2. Mark strings for translation using `_()` or `_t()`
3. Add entries to `.po` files
4. Restart/update the module

## Frontend Translation (JavaScript/OWL)

### Import Statement

Always import `_t` from the translation module:

```javascript
import { _t } from "@web/core/l10n/translation";
```

### Basic Usage

```javascript
// In service methods
showError(message) {
    this.notification.add(_t("Failed to load data: ") + message, {
        type: "danger"
    });
}

// In component methods
onButtonClick() {
    this.notification.add(_t("Operation successful"));
}
```

### Real Examples from Codebase

From `static/src/services/ha_data_service.js`:

```javascript
// Error messages
this.showError(_t("Failed to load HA instance list: ") + result.error);
this.showError(_t("Error loading instance list: ") + error.message);

// Success messages
this.showSuccess(_t("Switched to instance: ") + result.data.instance_name);

// Dynamic text with concatenation
this.showSuccess(actionText + " " + entityName + " " + _t("succeeded"));
```

### String Concatenation vs Parameters

**Preferred: Concatenation** (simpler for translators)
```javascript
_t("Failed to load: ") + errorMessage
```

**Alternative: sprintf-style** (when position matters in translations)
```javascript
// Use for complex formatting where word order may change
_t("Found %s items in %s").replace("%s", count).replace("%s", location)
```

### OWL Component Template

QWeb templates in OWL components are auto-translated:

```xml
<!-- static/src/components/example/example.xml -->
<templates>
    <t t-name="odoo_ha_addon.ExampleComponent">
        <!-- Auto-translated: plain text -->
        <span>Loading...</span>

        <!-- Auto-translated: button text -->
        <button class="btn btn-primary">Save Changes</button>

        <!-- NOT auto-translated: attributes without special handling -->
        <input t-att-placeholder="_t('Enter name')" />
    </t>
</templates>
```

### Lazy Translation (`_lt`)

For strings that need to be evaluated later (e.g., in constants):

```javascript
import { _lt } from "@web/core/l10n/translation";

const MESSAGES = {
    success: _lt("Operation completed"),
    error: _lt("An error occurred"),
};

// Later in code
this.notification.add(MESSAGES.success.toString());
```

## Backend Translation (Python)

### Import Statement

Import `_` from odoo:

```python
from odoo import models, fields, api, _
```

### Basic Usage

```python
class HAInstance(models.Model):
    _name = 'ha.instance'

    def action_test_connection(self):
        # User-facing messages
        raise UserError(_("Invalid API URL format: %s") % self.api_url)

        # Notification messages
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'message': _("Connection successful!"),
                'type': 'success',
            }
        }
```

### Real Examples from Codebase

From `models/ha_instance.py`:

```python
# Error with parameter
raise ValidationError(
    _("Invalid API URL format: %s\n"
      "Expected format: http://homeassistant.local:8123 or https://my-ha.duckdns.org")
    % self.api_url
)

# Constraint message with multiple parameters
raise ValidationError(
    _("Cannot delete instance '%s' because it has %d associated entities.\n"
      "Please delete or reassign the entities first.")
    % (self.name, entity_count)
)

# Success notification with dynamic content
return {
    'params': {
        'message': _("Successfully synced from %s:\n"
                    "• %d areas\n"
                    "• %d devices\n"
                    "• %d entities")
                    % (self.name, areas_count, devices_count, entities_count),
    }
}
```

### Field Definitions (Auto-translated)

Field strings and help text are automatically translatable:

```python
class HAEntity(models.Model):
    _name = 'ha.entity'

    # string and help are auto-translated
    name = fields.Char(
        string="Name",  # Auto-translated
        help="The friendly name of the entity"  # Auto-translated
    )

    state = fields.Char(
        string="State",
        help="Current state value from Home Assistant"
    )
```

### Controller Responses

```python
from odoo import http, _

class HAController(http.Controller):

    @http.route('/ha/api/test', type='json', auth='user')
    def test_endpoint(self):
        if not self._validate_input():
            return {
                'success': False,
                'error': _("Invalid input parameters")
            }
        return {
            'success': True,
            'message': _("Test completed successfully")
        }
```

## XML Views (Auto-translated)

### View Definitions

Most XML attributes are auto-translated:

```xml
<!-- views/ha_entity_views.xml -->
<record id="view_ha_entity_tree" model="ir.ui.view">
    <field name="name">ha.entity.tree</field>
    <field name="model">ha.entity</field>
    <field name="arch" type="xml">
        <tree string="HA Entities">  <!-- Auto-translated -->
            <field name="name" string="Entity Name"/>  <!-- Auto-translated -->
            <field name="state"/>
            <button name="action_refresh"
                    string="Refresh"  <!-- Auto-translated -->
                    type="object"/>
        </tree>
    </field>
</record>
```

### Form Views

```xml
<form string="HA Entity">  <!-- Auto-translated -->
    <sheet>
        <group string="Basic Information">  <!-- Auto-translated -->
            <field name="name"/>
            <field name="state"/>
        </group>
        <notebook>
            <page string="Details">  <!-- Auto-translated -->
                <field name="attributes"/>
            </page>
        </notebook>
    </sheet>
</form>
```

### Menu Items

```xml
<menuitem id="menu_ha_entity"
          name="Entities"  <!-- Auto-translated -->
          parent="menu_ha_root"
          action="action_ha_entity"/>
```

## What NOT to Translate

### Dynamic Data from External Sources

```python
# DON'T translate data from Home Assistant
entity_name = ha_response['friendly_name']  # Keep as-is
state_value = ha_response['state']  # Keep as-is

# DO translate UI labels around the data
message = _("Entity '%s' is now %s") % (entity_name, state_value)
```

### Technical Identifiers

```python
# DON'T translate
entity_id = "sensor.temperature"
domain = "switch"
model_name = "ha.entity"

# DO translate user-facing labels
label = _("Switch")  # User-facing domain name
```

### Log Messages (Developer-only)

```python
import logging
_logger = logging.getLogger(__name__)

# DON'T translate log messages (for developers)
_logger.info("WebSocket connected to %s", self.api_url)
_logger.error("Failed to parse response: %s", str(e))

# DO translate user-facing error messages
raise UserError(_("Connection failed. Please check your settings."))
```

### Database/API Field Names

```python
# DON'T translate
fields_to_fetch = ['name', 'state', 'attributes']
api_params = {'domain': 'switch', 'service': 'turn_on'}
```

## Adding Translations to .po Files

### Step 1: Identify the Source

Find where the string is defined:

```
#: models/ha_instance.py:551
#: static/src/services/ha_data_service.js:144
```

### Step 2: Add Entry to POT (Optional)

`i18n/odoo_ha_addon.pot`:
```po
#. module: odoo_ha_addon
#: model:ir.actions.act_window,name:odoo_ha_addon.action_ha_entity
msgid "HA Entities"
msgstr ""
```

### Step 3: Add Translation to .po File

`i18n/zh_TW.po`:
```po
#. module: odoo_ha_addon
#: model:ir.actions.act_window,name:odoo_ha_addon.action_ha_entity
msgid "HA Entities"
msgstr "HA 實體"
```

### Entry Format

```po
#. module: odoo_ha_addon              # Module name (comment)
#: models/ha_entity.py:25             # Source location (comment)
#, fuzzy                               # Optional: fuzzy flag
msgid "Original English text"         # Source string
msgstr "翻譯後的文字"                   # Translated string
```

### Important Format Rules

1. **Empty `msgstr`** = Uses original English
2. **Multi-line strings**: Use `\n` for newlines
3. **Parameters**: Keep `%s`, `%d`, etc. in same positions
4. **Special characters**: Escape quotes with `\"`

## Common Mistakes

### 1. Forgetting `_t()` in JavaScript

```javascript
// WRONG - won't be translated
this.notification.add("Operation failed");

// CORRECT
this.notification.add(_t("Operation failed"));
```

### 2. Translating Variable Content

```python
# WRONG - translating dynamic data
message = _("Entity %s is %s") % (_(entity_name), _(state))

# CORRECT - only translate the template
message = _("Entity %s is %s") % (entity_name, state)
```

### 3. Missing Import

```javascript
// WRONG - _t is undefined
showMessage() {
    return _t("Hello");  // ReferenceError!
}

// CORRECT - import first
import { _t } from "@web/core/l10n/translation";
```

### 4. Breaking String for Translation

```python
# WRONG - breaks translation context
msg = _("This is a ") + _("long message")

# CORRECT - keep as single string
msg = _("This is a long message")
```

## Testing Translations

### Switch Language

1. Go to **Settings > Users & Companies > Users**
2. Select your user
3. Change **Language** to Traditional Chinese
4. Save and refresh the page

### Verify in Browser

1. Open browser DevTools (F12)
2. Check for untranslated strings in the UI
3. Look for `msgid` text appearing instead of `msgstr`

### Module Update

After modifying `.po` files:

```bash
# Restart to reload translations
docker compose restart web

# Or full update if needed
docker compose exec web odoo -d odoo -u odoo_ha_addon --dev xml
```

## File Locations

| File | Purpose |
|------|---------|
| `i18n/odoo_ha_addon.pot` | Template with all English strings |
| `i18n/zh_TW.po` | Traditional Chinese translations |

## Related Documentation

- **[Internationalization Overview](../architecture/i18n.md)** - High-level i18n architecture
- **[i18n Implementation](../implementation/i18n/implementation.md)** - Implementation progress report
