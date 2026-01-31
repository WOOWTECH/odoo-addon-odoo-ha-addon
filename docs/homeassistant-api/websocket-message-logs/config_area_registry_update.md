# description

Update an area

# example

Send

```json
{
  "type": "config/area_registry/update",
  "area_id": "qoo",
  "name": "qoo2",
  "picture": null,
  "icon": null,
  "floor_id": null,
  "labels": [],
  "aliases": [],
  "temperature_entity_id": null,
  "humidity_entity_id": null,
  "id": 51
}
```

Received

```json
{
  "id": 51,
  "type": "result",
  "success": true,
  "result": {
    "aliases": [],
    "area_id": "qoo",
    "floor_id": null,
    "humidity_entity_id": null,
    "icon": null,
    "labels": [],
    "name": "qoo2",
    "picture": null,
    "temperature_entity_id": null,
    "created_at": 1764947153.56361,
    "modified_at": 1764947334.641665
  }
}
```

若有訂閱

```json
{
  "type": "subscribe_events",
  "event_type": "area_registry_updated",
  "id": 8
}
```

會收到兩個 messages。

client 端通常收到 `area_registry_updated` 後，會再打 `"type": "config/area_registry/list"` 更新 area list。

```json
[
  {
    "type": "event",
    "event": {
      "event_type": "area_registry_updated",
      "data": {
        "action": "update",
        "area_id": "qoo"
      },
      "origin": "LOCAL",
      "time_fired": "2025-12-05T15:08:54.641989+00:00",
      "context": {
        "id": "01KBQGY5FH3DGB0B252W6SCCJA",
        "parent_id": null,
        "user_id": null
      }
    },
    "id": 8
  },
  {
    "id": 51,
    "type": "result",
    "success": true,
    "result": {
      "aliases": [],
      "area_id": "qoo",
      "floor_id": null,
      "humidity_entity_id": null,
      "icon": null,
      "labels": [],
      "name": "qoo2",
      "picture": null,
      "temperature_entity_id": null,
      "created_at": 1764947153.56361,
      "modified_at": 1764947334.641665
    }
  }
]
```
