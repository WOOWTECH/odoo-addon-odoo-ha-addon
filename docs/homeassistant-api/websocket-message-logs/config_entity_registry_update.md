# description

Update an entity

# example

Send

```json
{
  "type": "config/entity_registry/update",
  "entity_id": "switch.test_switch",
  "name": null,
  "icon": null,
  "area_id": "chu_fang",
  "labels": [],
  "new_entity_id": "switch.test_switch",
  "id": 48
}
```

Received

```json
{
  "id": 48,
  "type": "result",
  "success": true,
  "result": {
    "entity_entry": {
      "area_id": "chu_fang",
      "categories": {},
      "config_entry_id": "01K5TQF9Q0CAPR3G1NA8V7REGR",
      "config_subentry_id": null,
      "created_at": 1758612508.341985,
      "device_id": "4a913b08c70ae173a12cf738e341aea4",
      "disabled_by": null,
      "entity_category": null,
      "entity_id": "switch.test_switch",
      "has_entity_name": false,
      "hidden_by": null,
      "icon": null,
      "id": "4fe91b15627004bde587bf7abb207498",
      "labels": [],
      "modified_at": 1765359608.504572,
      "name": null,
      "options": {
        "conversation": {
          "should_expose": true
        }
      },
      "original_name": "Test Switch ",
      "platform": "virtual",
      "translation_key": null,
      "unique_id": "9489d718-127d-4e10-8f5e-8f6678f90ce2.virtual",
      "aliases": [],
      "capabilities": null,
      "device_class": null,
      "original_device_class": null,
      "original_icon": null
    }
  }
}
```

若有訂閱

```json
{
  "type": "subscribe_events",
  "event_type": "entity_registry_updated",
  "id": 4
}
```

會收到兩個 messages。

client 端通常收到 `entity_registry_updated`

```json
[
  {
    "type": "event",
    "event": {
      "event_type": "entity_registry_updated",
      "data": {
        "action": "update",
        "entity_id": "switch.test_switch",
        "changes": {
          "area_id": "test3"
        }
      },
      "origin": "LOCAL",
      "time_fired": "2025-12-10T09:40:08.504798+00:00",
      "context": {
        "id": "01KC3T3RNRD5F7GWF5NN373K39",
        "parent_id": null,
        "user_id": null
      }
    },
    "id": 4
  },
  {
    "id": 48,
    "type": "result",
    "success": true,
    "result": {
      "entity_entry": {
        "area_id": "chu_fang",
        "categories": {},
        "config_entry_id": "01K5TQF9Q0CAPR3G1NA8V7REGR",
        "config_subentry_id": null,
        "created_at": 1758612508.341985,
        "device_id": "4a913b08c70ae173a12cf738e341aea4",
        "disabled_by": null,
        "entity_category": null,
        "entity_id": "switch.test_switch",
        "has_entity_name": false,
        "hidden_by": null,
        "icon": null,
        "id": "4fe91b15627004bde587bf7abb207498",
        "labels": [],
        "modified_at": 1765359608.504572,
        "name": null,
        "options": {
          "conversation": {
            "should_expose": true
          }
        },
        "original_name": "Test Switch ",
        "platform": "virtual",
        "translation_key": null,
        "unique_id": "9489d718-127d-4e10-8f5e-8f6678f90ce2.virtual",
        "aliases": [],
        "capabilities": null,
        "device_class": null,
        "original_device_class": null,
        "original_icon": null
      }
    }
  }
]
```
