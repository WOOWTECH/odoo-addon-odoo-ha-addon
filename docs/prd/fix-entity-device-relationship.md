---
name: fix-entity-device-relationship
description: Fix entity-device relationship sync so device form tabs show related entities
status: complete
created: 2026-02-04T11:22:50Z
updated: 2026-02-04T11:45:00Z
---

# Fix Entity-Device Relationship Sync

## Problem Statement

The device form view has tabs for Entities, Automations, Scripts, and Scenes, but all tabs show empty lists because:

1. **No entities have `device_id` populated** - Database shows 597 entities but 0 have `device_id` set
2. The `_sync_entity_registry_relations` method exists but devices weren't synced first

### Current State

```sql
SELECT COUNT(*) as total, COUNT(device_id) as with_device FROM ha_entity;
-- Result: total=597, with_device=0
```

## Root Cause Analysis

The entity sync process has two phases:
1. **Phase 1**: `sync_entity_states_from_ha()` - Syncs entity states (working)
2. **Phase 2**: `_sync_entity_registry_relations()` - Syncs area/label/device relationships

**The actual bug**: `_sync_entity_registry_relations` builds a `device_map` from `ha.device` records. If devices haven't been synced first, `device_map` is empty and no entity gets a `device_id`.

### Dependency Chain

1. Devices must be synced first (`sync_devices_from_ha`)
2. Then entity registry relations can be synced (`_sync_entity_registry_relations`)

## Solution Applied

Modified `sync_entity_states_from_ha()` in `src/models/ha_entity.py` to check for devices before syncing entity relations:

```python
# 同步完成後，更新 entity 與 area, labels 和 device 的關聯
if sync_area_relations:
    # 確保 devices 已同步（device_id 依賴 device 記錄存在）
    # Check if devices exist, if not sync them first
    device_count = self.env['ha.device'].sudo().search_count([
        ('ha_instance_id', '=', instance_id)
    ])
    if device_count == 0:
        _logger.info("No devices found, syncing devices first...")
        self.env['ha.device'].sudo().sync_devices_from_ha(instance_id=instance_id)

    self._sync_entity_registry_relations(instance_id)
```

## Implementation Steps

1. **Verify `_sync_entity_registry_relations` works** ✅
   - Method was already correct
   - Issue was missing devices in device_map

2. **Ensure devices synced before entity registry sync** ✅
   - Added device count check before `_sync_entity_registry_relations`
   - Auto-syncs devices if none exist

3. **Test the flow**
   - Trigger a full sync from Areas dashboard
   - Verify device form shows entities

## Technical Details

### Entity Registry Sync Method

Location: `src/models/ha_entity.py:_sync_entity_registry_relations()`

```python
def _sync_entity_registry_relations(self, instance_id):
    # Builds device_map from ha.device records
    devices = self.env['ha.device'].sudo().search([
        ('ha_instance_id', '=', instance_id)
    ])
    device_map = {device.device_id: device.id for device in devices}

    # For each entity, looks up device_id in registry
    ha_device_id = entry.get('device_id')
    if ha_device_id and ha_device_id in device_map:
        odoo_device_id = device_map[ha_device_id]
        update_vals['device_id'] = odoo_device_id
```

## Success Criteria

- [x] Devices synced before entity relations sync
- [ ] Entities have `device_id` populated after sync
- [ ] Device form "Entities" tab shows related entities
- [ ] Device form shows automation/script/scene entities if they belong to device
- [ ] Sync completes without errors

## Testing

```sql
-- Before fix
SELECT COUNT(*) as total, COUNT(device_id) as with_device FROM ha_entity;
-- Expected: total=597, with_device=0

-- After fix
SELECT COUNT(*) as total, COUNT(device_id) as with_device FROM ha_entity;
-- Expected: total=597, with_device>0 (many entities should have device_id)
```

## Files Modified

- `src/models/ha_entity.py:sync_entity_states_from_ha()` - Added device sync check before entity relations sync
