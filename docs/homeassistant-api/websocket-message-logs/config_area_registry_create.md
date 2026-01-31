# description

Create an area

# example

Send

```json
{
  "type": "config/area_registry/create",
  "name": "qoo",
  "labels": [],
  "aliases": [],
  "temperature_entity_id": null,
  "humidity_entity_id": null,
  "id": 42
}
```

Received

```json
{
  "id": 42,
  "type": "result",
  "success": true,
  "result": {
    "aliases": [],
    "area_id": "qoo",
    "floor_id": null,
    "humidity_entity_id": null,
    "icon": null,
    "labels": [],
    "name": "qoo",
    "picture": null,
    "temperature_entity_id": null,
    "created_at": 1764947153.56361,
    "modified_at": 1764947153.563622
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
        "action": "create",
        "area_id": "qoo"
      },
      "origin": "LOCAL",
      "time_fired": "2025-12-05T15:05:53.563833+00:00",
      "context": {
        "id": "01KBQGRMMVAS70WQKN6R9MBVJX",
        "parent_id": null,
        "user_id": null
      }
    },
    "id": 8
  },
  {
    "id": 42,
    "type": "result",
    "success": true,
    "result": {
      "aliases": [],
      "area_id": "qoo",
      "floor_id": null,
      "humidity_entity_id": null,
      "icon": null,
      "labels": [],
      "name": "qoo",
      "picture": null,
      "temperature_entity_id": null,
      "created_at": 1764947153.56361,
      "modified_at": 1764947153.563622
    }
  }
]
```
