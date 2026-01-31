# description

取回 entity 資訊。

# example

Send

```json
{
  "type": "config/entity_registry/get",
  "entity_id": "fan.test_fan",
  "id": 54
}
```

Received

```json
{
  "id": 54,
  "type": "result",
  "success": true,
  "result": {
    "area_id": "wo_shi",
    "categories": {},
    "config_entry_id": "01K5TQF9Q0CAPR3G1NA8V7REGR",
    "config_subentry_id": null,
    "created_at": 1758612508.337922,
    "device_id": "bd723712c021e12daef4dd55fd89eef3",
    "disabled_by": null,
    "entity_category": null,
    "entity_id": "fan.test_fan",
    "has_entity_name": false,
    "hidden_by": null,
    "icon": null,
    "id": "1047c5a6cb8ac53a8ef0677567271c4f",
    "labels": [],
    "modified_at": 1765370010.263476,
    "name": "Test Fan 測試風扇",
    "options": {
      "conversation": {
        "should_expose": true
      }
    },
    "original_name": "Test Fan ",
    "platform": "virtual",
    "translation_key": null,
    "unique_id": "eb955155-cf1d-462b-8d01-c9cb01eb3541.virtual",
    "aliases": [],
    "capabilities": {
      "preset_modes": []
    },
    "device_class": null,
    "original_device_class": null,
    "original_icon": null
  }
}
```
