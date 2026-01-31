# description

Subscribe `label_registry_updated` events.

若有訂閱 `label_registry_updated` events

```json
{
  "type": "subscribe_events",
  "event_type": "label_registry_updated",
  "id": 37
}
```

# event types

## `create` action

有 label 新增

```json
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
}
```
