# description

Delete an area

# example

Send

```json
{ "type": "config/area_registry/delete", "area_id": "qoo", "id": 56 }
```

Received

```json
{
  "id": 56,
  "type": "result",
  "success": true,
  "result": "success"
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
        "action": "remove",
        "area_id": "qoo"
      },
      "origin": "LOCAL",
      "time_fired": "2025-12-05T15:09:56.411969+00:00",
      "context": {
        "id": "01KBQH01SV4W7SE3VRA1YABDGG",
        "parent_id": null,
        "user_id": null
      }
    },
    "id": 8
  },
  {
    "id": 56,
    "type": "result",
    "success": true,
    "result": "success"
  }
]
```
