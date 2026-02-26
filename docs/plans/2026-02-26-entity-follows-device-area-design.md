# Entity Follows Device Area - Design Document

**Created**: 2026-02-26T02:09:49Z
**Status**: Approved

## Problem Definition

When Home Assistant entities are configured to "follow device area", the HA entity registry API returns `area_id = null`. Currently, the Odoo HA integration stores this null value directly, causing entities to display as "no area" instead of showing their device's area.

## Solution Overview

1. Add `follows_device_area` boolean field to `ha.entity` model
2. Add `display_area_id` computed field to show the actual area (own or inherited from device)
3. Add "Follows Device Area" checkbox in UI next to the area field
4. When checked, area field becomes **readonly** and displays the device's area

## UI Design

```
┌─────────────────────────────────────────────────┐
│ Area: [  Living Room  ▼]  ☑ Follows Device Area │
└─────────────────────────────────────────────────┘
```

- Check "Follows Device Area" → Area dropdown becomes readonly, shows device's area
- Uncheck → Area dropdown becomes editable, user can select any area
- Checkbox only visible when entity has an associated device

## Core Behavior

| follows_device_area | device_id | Displayed Area | Area Field State |
|---------------------|-----------|----------------|------------------|
| ✅ True | Device A (Kitchen) | Kitchen | Readonly |
| ✅ True | null | None | Readonly |
| ❌ False | Any | area_id value | Editable |

## Sync Logic

### HA → Odoo Sync

When syncing entities from Home Assistant:

```
Receive entity registry entry
    ↓
Check area_id and device_id
    ↓
If area_id = null AND device_id != null:
    → follows_device_area = True
    → area_id = null (keep as-is)
Else:
    → follows_device_area = False
    → area_id = value from HA
```

### Odoo → HA Sync

When user changes the "Follows Device Area" checkbox:

| Action | Sync to HA |
|--------|------------|
| Check "Follows Device Area" | Send `area_id = null` to HA |
| Uncheck and select area | Send selected `area_id` to HA |

### Device Area Changes

When a device's area changes, all entities with `follows_device_area = True` automatically display the new area (computed field, no additional processing needed).

## File Changes

### Backend (Python)

**1. `models/ha_entity.py`**
- Add `follows_device_area` boolean field
- Add `display_area_id` computed field (depends on `area_id`, `follows_device_area`, `device_id.area_id`)
- Modify `_do_sync_entity_registry_relations()` sync logic
- Modify `_update_entity_area_in_ha()` to handle checkbox changes

**2. `views/ha_entity_views.xml`**
- Add "Follows Device Area" checkbox next to area field
- Set area field `readonly` attribute based on `follows_device_area`

### Frontend (JavaScript/OWL)
- Update custom components if needed to display `display_area_id`

### i18n
- Add Traditional Chinese translation: "跟隨裝置分區"

## Implementation Details

### New Field Definitions

```python
# ha_entity.py
follows_device_area = fields.Boolean(
    string='Follows Device Area',
    default=False,
    help='If checked, entity area follows its device area'
)

display_area_id = fields.Many2one(
    'ha.area',
    string='Display Area',
    compute='_compute_display_area_id',
    store=False,
)
```

### Computed Field Logic

```python
@api.depends('area_id', 'follows_device_area', 'device_id.area_id')
def _compute_display_area_id(self):
    for entity in self:
        if entity.follows_device_area and entity.device_id:
            entity.display_area_id = entity.device_id.area_id
        else:
            entity.display_area_id = entity.area_id
```

### View XML Changes

```xml
<field name="area_id"
       readonly="follows_device_area"/>
<field name="follows_device_area"
       string="Follows Device Area"
       invisible="not device_id"/>
```

(Checkbox only visible when entity has an associated device)

## Test Cases

1. Sync entity with `area_id = null` and `device_id` → `follows_device_area = True`
2. Sync entity with `area_id` set → `follows_device_area = False`
3. Check "Follows Device Area" → Sync `area_id = null` to HA
4. Uncheck and select area → Sync selected area to HA
5. Device area changes → Following entities' `display_area_id` auto-updates
6. Area field readonly when `follows_device_area = True`
7. Checkbox hidden when entity has no device
