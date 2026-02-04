# PRD: Fix Device Related Items Sync

## Problem Statement

The device form tabs (Automations, Scripts, Scenes) are not showing all related items. Currently:
- **Hue原廠燈條** shows only Scene (場景) but should also show:
  - `automation.jian_li` (建立)
  - `script.unknown`

## Root Cause Analysis

### Current Implementation
The `_sync_related_items_from_ha` method only queries HA's `search/related` API for each **ENTITY** belonging to the device:

```python
for entity in device.entity_ids:
    result = client.call_websocket_api_sync(
        'search/related',
        {'item_type': 'entity', 'item_id': entity.entity_id}
    )
```

### The Bug
HA's `search/related` API returns **different results** when querying for a device vs querying for its entities:

**Entity Query** (`item_type: entity`, `item_id: light.hui_yi_qu_yuan_chang_deng_tiao`):
```json
{
  "scene": ["scene.chang_jing"]
}
```

**Device Query** (`item_type: device`, `item_id: f54e39854d82205ca1ec4e970df67469`):
```json
{
  "automation": ["automation.jian_li"],
  "script": ["script.unknown"],
  "scene": ["scene.chang_jing"]
}
```

The device-level query returns automations/scripts that reference the device directly (not through specific entities), which are missing from our current sync.

## Solution

Modify `_sync_related_items_from_ha` to:
1. Query `search/related` for the **DEVICE** itself
2. ALSO query `search/related` for each **ENTITY** in the device
3. Merge both results (union of all automation/script/scene IDs)

### Code Changes Required

**File:** `src/models/ha_device.py`

**Method:** `_sync_related_items_from_ha`

Add device-level query before entity queries:

```python
# 1. First, query search/related for the DEVICE itself
try:
    device_result = client.call_websocket_api_sync(
        'search/related',
        {'item_type': 'device', 'item_id': device.device_id}
    )
    if device_result and isinstance(device_result, dict):
        related_automations.update(device_result.get('automation', []))
        related_scripts.update(device_result.get('script', []))
        related_scenes.update(device_result.get('scene', []))
except Exception as e:
    _logger.warning(f"Failed to get related items for device {device.device_id}: {e}")

# 2. Then query for each entity (existing code)
for entity in device.entity_ids:
    ...
```

## Testing

### Manual Test
1. Run sync: `env['ha.device']._sync_related_items_from_ha()`
2. Check device 36 (Hue原廠燈條) has:
   - 1+ automation (automation.jian_li)
   - 1+ script (if script.unknown exists in Odoo)
   - 1 scene (scene.chang_jing)

### Database Verification
```sql
SELECT
  d.name,
  (SELECT COUNT(*) FROM ha_device_related_automation_rel WHERE device_id = d.id) as automations,
  (SELECT COUNT(*) FROM ha_device_related_script_rel WHERE device_id = d.id) as scripts,
  (SELECT COUNT(*) FROM ha_device_related_scene_rel WHERE device_id = d.id) as scenes
FROM ha_device d
WHERE d.id = 36;
```

Expected: `automations >= 1, scripts >= 0, scenes = 1`

## Acceptance Criteria

- [ ] Device 36 (Hue原廠燈條) Automations tab shows `automation.jian_li`
- [ ] Device 36 Scenes tab shows `scene.chang_jing` (already working)
- [ ] Sync correctly merges device-level and entity-level results
- [ ] No duplicate entries in relation tables
