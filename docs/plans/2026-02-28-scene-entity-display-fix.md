# Scene Entity Display Fix - PRD

**Created:** 2026-02-28T13:43:00Z
**Status:** Draft
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

## 3. Solution Options

### Option A: No Code Change (Documentation Only)
**Recommendation: ✅ Preferred**

The current behavior is correct according to HA's design:
- Entities are correctly stored in the scene
- HA Scene Editor displays them grouped by device (standard HA UX)
- When scene is activated, only the specified entities are affected

**Action:** Document this behavior for users to understand.

### Option B: Use Different HA API (scene.create service)
Use the `scene.create` service instead of REST Config API:

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

### Option C: Switch to YAML-based Scene Creation
Directly write to `scenes.yaml` file via HA File Editor addon.

**Drawbacks:**
- Requires additional addon dependency
- Complex file management
- Risk of YAML corruption

---

## 4. Verification Steps

### Verify Current Implementation is Correct
1. Create scene in Odoo with 2 entities: `sensor.xxx`, `switch.yyy`
2. Sync to HA
3. In HA, check scene state via Developer Tools → States
4. Confirm `entity_id` attribute shows exactly the 2 selected entities
5. Activate the scene and verify only those 2 entities are affected

### Expected Results
- Scene state shows only selected entities
- Scene activation only affects selected entities
- Device grouping in UI is purely cosmetic

---

## 5. Conclusion

**The current implementation is working correctly.**

The "裝置" (Devices) grouping in HA's Scene Editor is standard Home Assistant behavior when entities belong to devices in HA's device registry. This is not a bug but a UX design choice by Home Assistant.

### Recommendations
1. **No code changes needed** - The implementation correctly sends entities to HA
2. **Add user documentation** explaining HA's device grouping display behavior
3. **Verify with test** - Create a scene with entities that don't belong to any device (e.g., sensors) and confirm they appear in the "實體" section

### User Communication
Explain to the user:
- HA Scene Editor groups entities by their parent device for display purposes
- The actual scene data only contains the entities they selected
- When the scene is activated, only the selected entities are affected
- This is standard HA behavior, not an Odoo issue

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
