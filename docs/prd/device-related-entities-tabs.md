---
name: device-related-entities-tabs
description: Add related entities list and automation/script/scene tabs to device form view
status: backlog
created: 2026-02-04T11:10:43Z
updated: 2026-02-04T11:10:43Z
---

# Device Related Entities & Automation Tabs

## Problem Statement

Currently, the Device form view has an "Entities" tab that should display all entities belonging to the device, but:

1. **Entities tab appears empty** - The entity list is not populating correctly
2. **No automation/script/scene visibility** - Users cannot see automations, scripts, or scenes related to the device from the device form

Users need to quickly see:
- All entities associated with a device (sensors, switches, lights, etc.)
- Related automations that use the device's entities
- Related scripts that control the device
- Related scenes that include the device

## Requirements

### 1. Fix Entities Tab Population

**Current State:** Entities tab shows empty list
**Expected:** Show all `ha.entity` records where `device_id` matches the current device

The existing field definition is correct:
```python
entity_ids = fields.One2many(
    'ha.entity',
    'device_id',
    string='Entities',
    help='Entities belonging to this device'
)
```

**Investigation needed:** Verify if entities have their `device_id` field properly populated during sync.

### 2. Add Automations Tab

Display all entities with `domain = 'automation'` that reference any of the device's entities.

**Tab Name:** "Automations"
**Columns:**
- Entity ID
- Name
- State (on/off)
- Last Triggered

**Logic:** An automation is "related" to a device if it references any of the device's entities in its triggers, conditions, or actions.

### 3. Add Scripts Tab

Display all entities with `domain = 'script'` that reference any of the device's entities.

**Tab Name:** "Scripts"
**Columns:**
- Entity ID
- Name
- State
- Last Triggered

### 4. Add Scenes Tab

Display all entities with `domain = 'scene'` that include any of the device's entities.

**Tab Name:** "Scenes"
**Columns:**
- Entity ID
- Name
- State

## Technical Design

### Option A: Computed Fields (Recommended)

Add computed Many2many fields to `ha.device` model:

```python
# In ha_device.py
automation_ids = fields.Many2many(
    'ha.entity',
    string='Related Automations',
    compute='_compute_related_automations',
    help='Automations that reference this device\'s entities'
)

script_ids = fields.Many2many(
    'ha.entity',
    string='Related Scripts',
    compute='_compute_related_scripts',
    help='Scripts that reference this device\'s entities'
)

scene_ids = fields.Many2many(
    'ha.entity',
    string='Related Scenes',
    compute='_compute_related_scenes',
    help='Scenes that include this device\'s entities'
)

def _compute_related_automations(self):
    for device in self:
        entity_ids = device.entity_ids.mapped('entity_id')
        # Find automations that reference any of these entity_ids
        # This requires parsing automation attributes/config
        automations = self.env['ha.entity'].search([
            ('domain', '=', 'automation'),
            ('ha_instance_id', '=', device.ha_instance_id.id),
            # Additional filtering based on entity references
        ])
        device.automation_ids = automations

def _compute_related_scripts(self):
    # Similar logic for scripts
    pass

def _compute_related_scenes(self):
    # Similar logic for scenes
    pass
```

### Option B: Simple Domain Filter

If determining "related" is complex, start with showing all automations/scripts/scenes from the same HA instance:

```python
automation_ids = fields.One2many(
    'ha.entity',
    compute='_compute_automations',
)

def _compute_automations(self):
    for device in self:
        device.automation_ids = self.env['ha.entity'].search([
            ('domain', '=', 'automation'),
            ('ha_instance_id', '=', device.ha_instance_id.id),
        ])
```

### View Changes

Update `ha_device_views.xml`:

```xml
<notebook>
    <page string="Entities" name="entities">
        <field name="entity_ids" readonly="1">
            <list>
                <field name="entity_id"/>
                <field name="name"/>
                <field name="domain"/>
                <field name="entity_state" string="State"/>
            </list>
        </field>
    </page>
    <page string="Automations" name="automations">
        <field name="automation_ids" readonly="1">
            <list>
                <field name="entity_id"/>
                <field name="name"/>
                <field name="entity_state" string="State"/>
                <field name="last_changed" string="Last Triggered"/>
            </list>
        </field>
    </page>
    <page string="Scripts" name="scripts">
        <field name="script_ids" readonly="1">
            <list>
                <field name="entity_id"/>
                <field name="name"/>
                <field name="entity_state" string="State"/>
                <field name="last_changed" string="Last Triggered"/>
            </list>
        </field>
    </page>
    <page string="Scenes" name="scenes">
        <field name="scene_ids" readonly="1">
            <list>
                <field name="entity_id"/>
                <field name="name"/>
                <field name="entity_state"/>
            </list>
        </field>
    </page>
    <page string="Technical" name="technical">
        <!-- existing technical content -->
    </page>
</notebook>
```

## Implementation Steps

1. **Phase 1: Fix Entity Population**
   - Investigate why `entity_ids` is empty
   - Verify `device_id` is being set on entities during HA sync
   - Fix sync logic if needed

2. **Phase 2: Add Computed Fields**
   - Add `automation_ids`, `script_ids`, `scene_ids` computed fields to `ha.device`
   - Implement compute methods with basic filtering

3. **Phase 3: Update Views**
   - Add new tabs to device form view
   - Test display of related entities

4. **Phase 4: Advanced Filtering (Optional)**
   - Parse automation/script/scene configurations
   - Filter to only truly related automations (those that reference device entities)

## Success Criteria

- [ ] Entities tab shows all entities belonging to the device
- [ ] Automations tab displays automation entities from same HA instance
- [ ] Scripts tab displays script entities from same HA instance
- [ ] Scenes tab displays scene entities from same HA instance
- [ ] All tabs are read-only (display only)
- [ ] i18n: Tab names translated to zh_TW

## Out of Scope

- Editing automations/scripts/scenes from Odoo
- Creating new automations from device view
- Deep parsing of automation YAML to find exact entity references (Phase 4 optional)

## References

- Current device form: `src/views/ha_device_views.xml`
- Device model: `src/models/ha_device.py`
- Entity model: `src/models/ha_entity.py`
- Entity sync logic: `src/models/ha_entity.py:sync_entity_from_ha_data()`
