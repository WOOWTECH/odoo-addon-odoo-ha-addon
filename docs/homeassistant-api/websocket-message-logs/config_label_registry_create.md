# description

建立 label。

# example

Send

```json
{
  "type": "config/label_registry/create",
  "name": "test1",
  "icon": null,
  "color": null,
  "description": null,
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
    "color": null,
    "created_at": 1765435391.21869,
    "description": null,
    "icon": null,
    "label_id": "test1",
    "name": "test1",
    "modified_at": 1765435391.218697
  }
}
```

若有訂閱

```json
{
  "type": "subscribe_events",
  "event_type": "label_registry_updated",
  "id": 37
}
```

會收到兩個 messages。

client 端通常收到 `label_registry_updated` 後，會再打 `"type": "config/label_registry/list"` 更新 label list。

```json
[
  {
    "type": "event",
    "event": {
      "event_type": "label_registry_updated",
      "data": {
        "action": "create",
        "label_id": "test1"
      },
      "origin": "LOCAL",
      "time_fired": "2025-12-11T06:43:11.218791+00:00",
      "context": {
        "id": "01KC62CF7JCM920P9EPK7TT846",
        "parent_id": null,
        "user_id": null
      }
    },
    "id": 37
  },
  {
    "id": 42,
    "type": "result",
    "success": true,
    "result": {
      "color": null,
      "created_at": 1765435391.21869,
      "description": null,
      "icon": null,
      "label_id": "test1",
      "name": "test1",
      "modified_at": 1765435391.218697
    }
  }
]
```
