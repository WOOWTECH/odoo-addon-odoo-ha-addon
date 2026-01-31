# description

Update an device

# example

Send

```json
{
  "type": "config/device_registry/update",
  "device_id": "d063db262bf217a94cf0b7e82ce3b700",
  "name_by_user": null,
  "area_id": "chu_fang",
  "labels": [],
  "disabled_by": null,
  "id": 65
}
```

Received

```json
{
  "id": 65,
  "type": "result",
  "success": true,
  "result": {
    "area_id": "chu_fang",
    "configuration_url": null,
    "config_entries": ["01KC3XY2PW9KPQ0S39QN4RS677"],
    "config_entries_subentries": {
      "01KC3XY2PW9KPQ0S39QN4RS677": [null]
    },
    "connections": [],
    "created_at": 1765363616.541419,
    "disabled_by": null,
    "entry_type": null,
    "hw_version": null,
    "id": "d063db262bf217a94cf0b7e82ce3b700",
    "identifiers": [["glances", "01KC3XY2PW9KPQ0S39QN4RS677"]],
    "labels": [],
    "manufacturer": "Glances",
    "model": null,
    "model_id": null,
    "modified_at": 1765363711.693941,
    "name_by_user": null,
    "name": "localhost",
    "primary_config_entry": "01KC3XY2PW9KPQ0S39QN4RS677",
    "serial_number": null,
    "sw_version": null,
    "via_device_id": null
  }
}
```

若有訂閱

```json
{
  "type": "subscribe_events",
  "event_type": "device_registry_updated",
  "id": 6
}
```

會收到兩個 messages。

client 端通常收到 `device_registry_updated`

```json
[
  {
    "type": "event",
    "event": {
      "event_type": "device_registry_updated",
      "data": {
        "action": "update",
        "device_id": "d063db262bf217a94cf0b7e82ce3b700",
        "changes": {
          "area_id": null
        }
      },
      "origin": "LOCAL",
      "time_fired": "2025-12-10T10:48:31.694230+00:00",
      "context": {
        "id": "01KC3Y0ZPEY2GA5P8YHB5TY8QQ",
        "parent_id": null,
        "user_id": null
      }
    },
    "id": 6
  },
  {
    "id": 65,
    "type": "result",
    "success": true,
    "result": {
      "area_id": "chu_fang",
      "configuration_url": null,
      "config_entries": ["01KC3XY2PW9KPQ0S39QN4RS677"],
      "config_entries_subentries": {
        "01KC3XY2PW9KPQ0S39QN4RS677": [null]
      },
      "connections": [],
      "created_at": 1765363616.541419,
      "disabled_by": null,
      "entry_type": null,
      "hw_version": null,
      "id": "d063db262bf217a94cf0b7e82ce3b700",
      "identifiers": [["glances", "01KC3XY2PW9KPQ0S39QN4RS677"]],
      "labels": [],
      "manufacturer": "Glances",
      "model": null,
      "model_id": null,
      "modified_at": 1765363711.693941,
      "name_by_user": null,
      "name": "localhost",
      "primary_config_entry": "01KC3XY2PW9KPQ0S39QN4RS677",
      "serial_number": null,
      "sw_version": null,
      "via_device_id": null
    }
  }
]
```
