---
name: device-related-entities-tabs
description: Show automations/scripts/scenes that REFERENCE a device's entities using HA search/related API
status: complete
created: 2026-02-04T11:10:43Z
updated: 2026-02-04T13:28:13Z
---

# Device Related Entities & Automation Tabs

## Problem Statement

Currently, the Device form view displays entities that **belong to** the device (via `device_id`), but:

1. **Automations/Scripts/Scenes tabs show wrong data** - They show entities where `device_id = device` AND `domain = automation|script|scene`, but this is incorrect
2. **HA behavior is different** - Home Assistant shows automations/scripts/scenes that **REFERENCE** the device's entities, not those that belong to the device

### Example of Correct Behavior (from HA screenshots)

For device "Hue原廠燈條":
- **Automations section** shows automation "建立" that references `light.hue_yuan_chang_deng_tiao` in its triggers/actions
- **Scenes section** shows scene "場景" that includes the device's light entity
- **Scripts section** shows script "新本" that controls the device

This is fundamentally different from showing automations/scripts/scenes where `device_id` equals the device.

## Requirements

### 1. Fix Automations Tab - Show Referenced Automations

**Current (Wrong):** Show `ha.entity` where `domain='automation'` AND `device_id=device`
**Expected (Correct):** Show `ha.entity` where `domain='automation'` AND the automation's config REFERENCES any of the device's entities

### 2. Fix Scripts Tab - Show Referenced Scripts

**Current (Wrong):** Show `ha.entity` where `domain='script'` AND `device_id=device`
**Expected (Correct):** Show `ha.entity` where `domain='script'` AND the script's config REFERENCES any of the device's entities

### 3. Fix Scenes Tab - Show Referenced Scenes

**Current (Wrong):** Show `ha.entity` where `domain='scene'` AND `device_id=device`
**Expected (Correct):** Show `ha.entity` where `domain='scene'` AND the scene INCLUDES any of the device's entities

## Technical Design

### Home Assistant API: `search/related`

HA provides a WebSocket API to find related items:

```json
// Request
{
  "type": "search/related",
  "item_type": "entity",
  "item_id": "light.hue_yuan_chang_deng_tiao",
  "id": 45
}

// Response
{
  "id": 45,
  "type": "result",
  "success": true,
  "result": {
    "area": ["wo_shi"],
    "device": ["4a913b08c70ae173a12cf738e341aea4"],
    "config_entry": ["01K5TQF9Q0CAPR3G1NA8V7REGR"],
    "integration": ["virtual"],
    "label": ["test9", "jj2"],
    "automation": ["automation.duo_qie_kai_guan_kong_zhi_deng_ju"],
    "scene": ["scene.test2"],
    "script": ["script.notify"]
  }
}
```

### Implementation Approach

#### Step 1: Create Device Related Items Sync Method

```python
# In ha_device.py
def _sync_related_items_from_ha(self, instance_id=None):
    """
    Sync related automations/scripts/scenes for all devices.

    For each device:
    1. Get all entity_ids belonging to the device
    2. For each entity, call search/related API
    3. Collect all automation/script/scene entity_ids
    4. Deduplicate and store in device fields
    """
    from odoo.addons.odoo_ha_addon.models.common.websocket_client import get_websocket_client

    devices = self.search([('ha_instance_id', '=', instance_id)])
    client = get_websocket_client(self.env, instance_id=instance_id)

    for device in devices:
        related_automations = set()
        related_scripts = set()
        related_scenes = set()

        # Query search/related for each entity in the device
        for entity in device.entity_ids:
            result = client.call_websocket_api_sync(
                'search/related',
                {'item_type': 'entity', 'item_id': entity.entity_id}
            )

            if result:
                related_automations.update(result.get('automation', []))
                related_scripts.update(result.get('script', []))
                related_scenes.update(result.get('scene', []))

        # Resolve entity_ids to ha.entity records
        automation_records = self.env['ha.entity'].search([
            ('entity_id', 'in', list(related_automations)),
            ('ha_instance_id', '=', instance_id)
        ])
        script_records = self.env['ha.entity'].search([
            ('entity_id', 'in', list(related_scripts)),
            ('ha_instance_id', '=', instance_id)
        ])
        scene_records = self.env['ha.entity'].search([
            ('entity_id', 'in', list(related_scenes)),
            ('ha_instance_id', '=', instance_id)
        ])

        # Update device with related items
        device.write({
            'related_automation_ids': [(6, 0, automation_records.ids)],
            'related_script_ids': [(6, 0, script_records.ids)],
            'related_scene_ids': [(6, 0, scene_records.ids)],
        })
```

#### Step 2: Add Stored Many2many Fields

Change from computed fields to stored fields (populated during sync):

```python
# In ha_device.py (replace computed fields)
related_automation_ids = fields.Many2many(
    'ha.entity',
    'ha_device_related_automation_rel',
    'device_id',
    'entity_id',
    string='Related Automations',
    help='Automations that reference this device\'s entities',
    domain="[('domain', '=', 'automation')]"
)

related_script_ids = fields.Many2many(
    'ha.entity',
    'ha_device_related_script_rel',
    'device_id',
    'entity_id',
    string='Related Scripts',
    help='Scripts that reference this device\'s entities',
    domain="[('domain', '=', 'script')]"
)

related_scene_ids = fields.Many2many(
    'ha.entity',
    'ha_device_related_scene_rel',
    'device_id',
    'entity_id',
    string='Related Scenes',
    help='Scenes that include this device\'s entities',
    domain="[('domain', '=', 'scene')]"
)
```

#### Step 3: Integrate into Sync Flow

Call `_sync_related_items_from_ha()` after entity sync:

```python
# In hooks.py or cron job
def sync_ha_data(instance_id):
    # 1. Sync entities (existing)
    env['ha.entity'].sync_entity_states_from_ha(instance_id)

    # 2. Sync entity registry relations (existing)
    env['ha.entity']._sync_entity_registry_relations(instance_id)

    # 3. NEW: Sync device related items
    env['ha.device']._sync_related_items_from_ha(instance_id)
```

#### Step 4: Update View Field Names

```xml
<!-- In ha_device_views.xml -->
<page string="Automations" name="automations">
    <!-- Change from automation_ids to related_automation_ids -->
    <field name="related_automation_ids" readonly="1">
        <list>
            <field name="entity_id"/>
            <field name="name"/>
            <field name="entity_state" string="State"/>
            <field name="last_changed" string="Last Triggered"/>
        </list>
    </field>
</page>
<page string="Scripts" name="scripts">
    <field name="related_script_ids" readonly="1">
        <list>
            <field name="entity_id"/>
            <field name="name"/>
            <field name="entity_state" string="State"/>
            <field name="last_changed" string="Last Triggered"/>
        </list>
    </field>
</page>
<page string="Scenes" name="scenes">
    <field name="related_scene_ids" readonly="1">
        <list>
            <field name="entity_id"/>
            <field name="name"/>
            <field name="entity_state"/>
        </list>
    </field>
</page>
```

### Optimization Considerations

#### API Call Reduction

For devices with many entities (e.g., 20 entities), this would make 20 API calls. Options:
1. **Batch processing** - Sync all devices in one cron job run
2. **Caching** - Store results and only re-sync periodically (hourly/daily)
3. **Lazy loading** - Only sync when user views the device form (not recommended for UX)

Recommended: Use cron job to sync every 15-30 minutes.

#### Performance

- Use `fields.Many2many` with explicit relation tables
- Add database index on relation tables
- Consider limiting entities queried per device (e.g., max 50)

## Implementation Steps

### Phase 1: Add New Fields (Model Changes)
- [x] Add `related_automation_ids`, `related_script_ids`, `related_scene_ids` fields
- [x] Create relation tables in database (auto-created by Odoo Many2many)
- [x] Update `__manifest__.py` with migration if needed (not needed)

### Phase 2: Implement Sync Method
- [x] Add `_sync_related_items_from_ha()` method to `ha.device`
- [x] Handle API errors gracefully
- [x] Add logging for debugging

### Phase 3: Integrate with Sync Flow
- [x] Add cron job for periodic sync (websocket_cron.xml)
- [x] Add controller endpoint for manual sync trigger

### Phase 4: Update Views
- [x] Update `ha_device_views.xml` to use new field names
- [ ] Update i18n translations (optional, fields already translated)

### Phase 5: Testing
- [x] Test with device that has related automations (天花三角燈條, 地面三角燈條)
- [x] Test with device that has related scenes (Hue原廠燈條 → scene.chang_jing)
- [x] Test with device that has no related items (empty tabs)
- [x] Test API error handling

## Success Criteria

- [x] Automations tab shows automations that **reference** the device's entities
- [x] Scripts tab shows scripts that **reference** the device's entities
- [x] Scenes tab shows scenes that **include** the device's entities
- [x] Data matches what Home Assistant shows on device page
- [x] Empty tabs display gracefully (no errors)
- [x] Sync runs periodically without performance issues (15-minute cron)
- [x] i18n: Tab names translated to zh_TW (existing translations)

## Out of Scope

- Editing automations/scripts/scenes from Odoo
- Creating new automations from device view
- Real-time updates via WebSocket subscription (can be future enhancement)

## References

### Files to Modify
- `src/models/ha_device.py` - Add fields and sync method
- `src/views/ha_device_views.xml` - Update tab field names
- `src/data/ir_cron.xml` - Add cron job (optional)
- `i18n/zh_TW.po` - Add translations

### API Documentation
- `docs/homeassistant-api/websocket-message-logs/search_related.md` - search/related API spec
- `docs/reference/home-assistant-api/` - General HA API docs

### Related Code
- `src/controllers/controllers.py:get_entity_relations()` - Existing search/related usage
- `src/models/common/websocket_client.py` - WebSocket client

## Appendix: Current vs Expected Behavior

| Aspect | Current (Wrong) | Expected (Correct) |
|--------|-----------------|-------------------|
| Data Source | `device_id` field on entity | HA `search/related` API |
| Automations | Automations where device_id=device | Automations that **use** device's entities |
| Scenes | Scenes where device_id=device | Scenes that **include** device's entities |
| Scripts | Scripts where device_id=device | Scripts that **control** device's entities |
| Hue原廠燈條 example | Empty (no automation has device_id=hue) | "建立" automation (references light.hue...) |
