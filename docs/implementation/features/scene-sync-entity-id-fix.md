# Scene Area/Label Sync Entity ID Fix

**Created**: 2026-03-01T09:19:42Z
**Status**: Completed
**Affected Files**: `src/models/ha_entity.py`

## Problem Description

When creating a Scene in Odoo with an Area and/or Labels assigned, the sync to Home Assistant failed silently. The Area and Labels were not reflected in the HA entity registry.

### Root Cause

When a Scene is created via the HA Config API (`/api/config/scene/config/{id}`), Home Assistant auto-generates the `entity_id` based on the Scene name. For example:

- Scene Name: "Area Sync Test v2"
- HA Generated Entity ID: `scene.area_sync_test_v2`
- Odoo Stored Entity ID: `scene.area_sync_test_v2` (may differ in format)

The original sync code in `_update_entity_area_in_ha()` and `_update_entity_labels_in_ha()` used `self.entity_id` to send WebSocket `config/entity_registry/update` requests. However, when called from `_create_scene_in_ha()`, the HA-generated `entity_id` (returned in `ha_entity_id`) was different from what Odoo had stored, causing HA to fail finding the entity.

### Symptoms

- Scene created successfully in HA ✅
- Scene entities added correctly ✅
- Area NOT synced to HA ❌
- Labels NOT synced to HA ❌
- No error logs (silent failure)

## Solution

### Changes to `src/models/ha_entity.py`

#### 1. `_update_entity_area_in_ha()` (Lines 704-779)

Added `override_entity_id` parameter to allow callers to specify the actual HA entity_id:

```python
def _update_entity_area_in_ha(self, override_entity_id=None):
    """
    在 HA 中更新 Entity 的 area_id

    Args:
        override_entity_id: Optional entity_id to use instead of self.entity_id.
                           This is needed for scenes where HA generates a different
                           entity_id than what Odoo has stored.
    """
    self.ensure_one()
    # Use override_entity_id if provided (for scenes with HA-generated entity_id)
    effective_entity_id = override_entity_id or self.entity_id
    # ... rest of method uses effective_entity_id
```

#### 2. `_update_entity_labels_in_ha()` (Lines 834-878)

Same pattern - added `override_entity_id` parameter:

```python
def _update_entity_labels_in_ha(self, override_entity_id=None):
    self.ensure_one()
    # Use override_entity_id if provided (for scenes with HA-generated entity_id)
    effective_entity_id = override_entity_id or self.entity_id
    # ... rest of method uses effective_entity_id
```

#### 3. `_create_scene_in_ha()` (Lines 1895-1927)

Updated to pass the HA-returned entity_id to sync methods:

```python
# Get the actual entity_id from HA response (may differ from self.entity_id)
current_entity_id = ha_entity_id if ha_entity_id else self.entity_id

# Sync area if assigned
current_area = self.area_id
if current_area:
    self._update_entity_area_in_ha(override_entity_id=current_entity_id)
    _logger.info(
        "Scene %s: Area sync triggered for area '%s' with HA entity_id '%s'",
        self.name, current_area.name, current_entity_id
    )

# Sync labels if assigned
if self.label_ids:
    self._update_entity_labels_in_ha(override_entity_id=current_entity_id)
    _logger.info(
        "Scene %s: Label sync triggered for %d labels with HA entity_id '%s'",
        self.name, len(self.label_ids), current_entity_id
    )
```

## Testing

### Test Case: Create Scene with Area and Labels

1. Created Scene "Area Sync Test v2" with:
   - Scene ID: `scene.area_sync_test_v2`
   - Area: 辦公區 (ban_gong_qu)
   - Entity: sensor.athom_em_2_029d10_current_1

2. Verified via HA WebSocket API:
   ```
   entity_id: scene.area_sync_test_v2
   area_id: ban_gong_qu ✅
   labels: []
   ```

3. Added Label "重要設備" and saved

4. Verified via HA WebSocket API:
   ```
   entity_id: scene.area_sync_test_v2
   area_id: ban_gong_qu ✅
   labels: ['zhong_yao_she_bei'] ✅
   ```

### Result

Both Area and Label sync now work correctly for newly created Scenes.

## Backward Compatibility

- Existing code calling `_update_entity_area_in_ha()` or `_update_entity_labels_in_ha()` without parameters continues to work (uses `self.entity_id` as before)
- Only Scene creation flow passes the `override_entity_id` parameter
- No database migration required

## Related Files

- `src/models/ha_entity.py` - Main sync logic
- `src/models/common/ha_rest_api.py` - WebSocket API calls (`update_entity_registry()`)

## References

- HA WebSocket API: `config/entity_registry/update`
- HA Config API: `/api/config/scene/config/{id}`
