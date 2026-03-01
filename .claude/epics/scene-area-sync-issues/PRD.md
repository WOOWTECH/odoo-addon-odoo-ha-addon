# PRD: Scene & Area Sync Issues Fix

## Issue Summary

Two related issues with scene and area synchronization between Odoo and Home Assistant:

1. **Area Bidirectional Sync**: When setting area_id on an entity in Odoo, the change is not reflected in HA
2. **Scene Visibility**: Some scenes exist in Odoo but don't appear in HA's Scenes panel

## Root Cause Analysis

### Problem 1: Area Sync (Odoo → HA)

**Current Behavior:**
- User sets `area_id` on a scene entity in Odoo
- `write()` triggers `_update_entity_area_in_ha()`
- WebSocket API `config/entity_registry/update` is called
- Area change may not reflect in HA

**Root Causes Identified:**

1. **Device-based scenes (Hue Bridge)**: 63 out of 67 scenes in Odoo are from Hue Bridge integration. These are device-created scenes with `ha_scene_id = NULL`. The `entity_registry/update` API may have limitations for device-owned entities.

2. **Potential API timing issue**: The WebSocket call might succeed but HA's UI doesn't refresh immediately.

3. **Error swallowing**: Exceptions in `_update_entity_area_in_ha()` are logged but not surfaced to the user.

### Problem 2: Scenes Exist in Odoo but Not in HA

**Database Analysis:**
```
Total scenes in Odoo: 67
Scenes with ha_scene_id (created via Odoo): 4
Scenes without ha_scene_id (from HA/Hue): 63
```

**Root Causes:**

1. **Different scene types in HA:**
   - **Editable scenes** (scenes.yaml): Created via HA UI or API with numeric timestamp ID
   - **Device scenes** (Hue Bridge, etc.): Managed by integration, appear in states but not in HA Settings > Scenes

2. **User expectation mismatch**: The HA "Scenes" settings panel only shows editable scenes. Device scenes are visible in HA states but not in the configuration panel.

## Proposed Fixes

### Fix 1: Improve Area Sync Error Handling & Feedback

**Changes Required:**

1. **Add user notification on area sync failure** (`ha_entity.py`):
   - Show warning notification when `_update_entity_area_in_ha()` fails
   - Log detailed error for debugging

2. **Verify API response** (`_update_entity_area_in_ha`):
   - Check if the returned `area_id` matches what was sent
   - Log discrepancy if HA rejects the change

3. **Handle device-owned entity limitation**:
   - Detect if entity is device-owned (has `device_id` but no `ha_scene_id`)
   - Show appropriate message: "This scene is managed by its device (e.g., Hue Bridge). Area changes may not be reflected in Home Assistant."

### Fix 2: Clarify Scene Types in UI

**Changes Required:**

1. **Add computed field to show scene source** (`ha_entity.py`):
   ```python
   scene_source = fields.Selection([
       ('odoo', 'Created in Odoo'),
       ('ha_editable', 'HA Editable Scene'),
       ('device', 'Device Scene (Hue/etc.)'),
   ], compute='_compute_scene_source')
   ```

2. **Update list view** to show scene source column

3. **Add help text** explaining why some scenes don't appear in HA Settings

### Fix 3: Batch Sync Action Enhancement

**Changes Required:**

1. **Add "Sync Area to HA" button** for scenes with `ha_scene_id`
2. **Skip device scenes** with clear message in batch operations
3. **Log sync results** with counts per category

## Implementation Plan

### Phase 1: Diagnostic & Logging (Quick Win)
- Add detailed logging in `_update_entity_area_in_ha()`
- Log API response to verify if HA accepts the area change
- Estimated: 1 hour

### Phase 2: User Feedback
- Add notification on sync failure
- Show scene source in list view
- Estimated: 2 hours

### Phase 3: Device Scene Handling
- Detect device-owned scenes
- Show appropriate warnings
- Update documentation
- Estimated: 2 hours

## Technical Details

### Affected Files

1. `src/models/ha_entity.py`:
   - `_update_entity_area_in_ha()`: Add response validation
   - `write()`: Add user notification on failure
   - Add `scene_source` computed field

2. `src/views/ha_entity_views.xml`:
   - Add scene_source column to list view
   - Add help tooltip for scene types

3. `src/static/src/services/ha_data_service.js`:
   - Handle area sync notifications

### Database Query Findings

```sql
-- Scenes with ha_scene_id (Odoo-created, can sync area)
SELECT COUNT(*) FROM ha_entity WHERE domain='scene' AND ha_scene_id IS NOT NULL;
-- Result: 4

-- Scenes without ha_scene_id (device scenes, limited sync)
SELECT COUNT(*) FROM ha_entity WHERE domain='scene' AND ha_scene_id IS NULL;
-- Result: 63
```

## Success Criteria

1. When user changes area_id on an Odoo-created scene, it reflects in HA within 5 seconds
2. User receives clear feedback when area sync fails or is not applicable
3. User can distinguish between Odoo-created and device scenes in the UI
4. Documentation explains the different scene types and their limitations

## Out of Scope

- Creating device scenes in HA (not possible via API)
- Forcing area assignment on device-owned entities
- Modifying Hue Bridge scene configurations
