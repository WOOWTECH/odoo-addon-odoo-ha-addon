# Scene Entity Display Fix - PRD

**Created:** 2026-02-28T13:43:00Z
**Updated:** 2026-02-28T13:55:00Z
**Status:** Implemented
**Author:** Claude Code Assistant

---

## 1. Problem Statement

### Current Behavior
When creating a scene in Odoo and syncing to Home Assistant:
1. User selects individual **entities** in Odoo Scene Manager (e.g., `switch.onofflightswitch_2`, `light.two_way_color_light`)
2. Scene syncs to HA via REST API: `POST /api/config/scene/config/{id}`
3. In HA Scene Editor, entities are displayed **grouped by device** under "裝置" (Devices) section

### Expected Behavior
The user expects to see the individual **entities** they selected in Odoo, displayed as entities in HA's Scene Editor, not grouped by device.

### User's Screenshot Analysis
Scene "上次去問問我" shows:
- **裝置 (Devices) section:**
  - OnOffLightSwitch (with 5 OnOffLightSwitch sub-items)
  - Two Way Color Light (with 1 Two Way Color Light sub-item)
- **實體 (Entities) section:**
  - Message: "要將個別實體添加到場景中，請切換至即時編輯模式"

### HA Developer Tools Verification
The scene state `scene.shang_ci_qu_wen_wen_wo` shows:
- `entity_id: light.two_way_color_light, switch.onofflightswitch_2` (only 2 entities)
- `id: 1772255865322`

---

## 2. Root Cause Analysis

### HA Scene Editor Behavior
Home Assistant's Scene Editor UI has two display modes:
1. **Devices Section ("裝置")**: Shows entities grouped by their parent device
2. **Entities Section ("實體")**: Shows individual entities not belonging to any device

When an entity belongs to a device in HA's device registry, HA's Scene Editor automatically:
- Groups the entity under its parent device in the "裝置" section
- Shows all entities from that device together (even if only some were selected)

### Current Implementation Flow
```
Odoo → select entities → get_entity_states() → create_scene_config() → HA REST API
```

The API payload sent:
```json
{
  "id": "1772255865322",
  "name": "上次去問問我",
  "entities": {
    "light.two_way_color_light": {"state": "on", "brightness": 128},
    "switch.onofflightswitch_2": {"state": "on"}
  }
}
```

### Key Finding
**This is NOT a bug in Odoo's implementation.** The entities are correctly sent to HA. The "device grouping" display is HA's built-in Scene Editor behavior when entities belong to devices.

---

## 3. Solution

### Implemented: Add `metadata` with `entity_only: true`

HA's scene editor uses a `metadata` field to track how entities were added to a scene. By setting `entity_only: true` for each entity, we tell HA to display the entity in the "實體" (Entities) section instead of grouping it under "裝置" (Devices).

**Implementation in `hass_rest_api.py`:**
```python
# Build metadata to mark all entities as entity_only
metadata = {}
for entity_id in entities.keys():
    metadata[entity_id] = {"entity_only": True}

# Build scene config payload
payload = {
    "id": ha_scene_id,
    "name": name,
    "entities": entities,
    "metadata": metadata  # <-- Added this field
}
```

**Resulting YAML format in HA:**
```yaml
- id: "1772255865322"
  name: 上次去問問我
  entities:
    light.two_way_color_light:
      state: "off"
    switch.onofflightswitch_2:
      state: "off"
  metadata:
    light.two_way_color_light:
      entity_only: true
    switch.onofflightswitch_2:
      entity_only: true
```

### Alternative Options (Not Used)

#### Option B: Use Different HA API (scene.create service)
```yaml
service: scene.create
data:
  scene_id: my_scene
  snapshot_entities:
    - light.two_way_color_light
    - switch.onofflightswitch_2
```

**Drawbacks:**
- Creates dynamic/runtime scenes, NOT editable in HA GUI
- Scenes disappear on HA restart unless using `scene.apply` with persistence
- Original design document specifies editable scenes

#### Option C: Switch to YAML-based Scene Creation
Directly write to `scenes.yaml` file via HA File Editor addon.

**Drawbacks:**
- Requires additional addon dependency
- Complex file management
- Risk of YAML corruption

---

## 4. Verification Steps

### Test the Implementation
1. Create a new scene in Odoo with entities (e.g., `switch.xxx`, `light.yyy`)
2. Add entities to the scene via the scene entity selector
3. Save the scene (triggers sync to HA)
4. In HA Scene Editor, verify:
   - Entities appear in the "實體" (Entities) section
   - NOT grouped under "裝置" (Devices) section
5. Check scenes.yaml to confirm `metadata` with `entity_only: true` is present

### Expected Results
- Scene entities display in "實體" section in HA editor
- Each entity has `entity_only: true` in metadata
- Scene activation only affects selected entities

---

## 5. Conclusion

**Fix implemented by adding `metadata` field with `entity_only: true`.**

### Changes Made
- **File:** `src/models/common/hass_rest_api.py`
- **Method:** `create_scene_config()`
- **Change:** Added `metadata` dictionary with `entity_only: true` for each entity

### How It Works
The `metadata.entity_only` flag is used by HA's scene editor to determine how to display entities:
- `entity_only: true` → Display in "實體" (Entities) section
- `entity_only: false` or missing → Group under "裝置" (Devices) section

### Source References
- [HA Community: entity_only explanation](https://community.home-assistant.io/t/scenes-yaml-what-is-entity-only-true-for/704552)
- [GitHub Issue #109710](https://github.com/home-assistant/core/issues/109710)

---

## 6. Appendix: HA Scene Data Format

### HA Scene State (from Developer Tools)
```yaml
entity_id: scene.shang_ci_qu_wen_wen_wo
state: unknown
attributes:
  entity_id:
    - light.two_way_color_light
    - switch.onofflightswitch_2
  id: "1772255865322"
  friendly_name: 上次去問問我
```

### REST API Payload Format
```json
{
  "id": "1772255865322",
  "name": "上次去問問我",
  "entities": {
    "light.two_way_color_light": {
      "state": "on",
      "brightness": 128
    },
    "switch.onofflightswitch_2": {
      "state": "on"
    }
  }
}
```

### HA scenes.yaml Format (for reference)
```yaml
- id: "1772255865322"
  name: 上次去問問我
  entities:
    light.two_way_color_light:
      state: "on"
      brightness: 128
    switch.onofflightswitch_2:
      state: "on"
```
