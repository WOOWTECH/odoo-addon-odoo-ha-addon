# description

Subscribe `device_registry_updated` events.

若有訂閱 `device_registry_updated` events

```json
{
  "type": "subscribe_events",
  "event_type": "device_registry_updated",
  "id": 6
}
```

# event types

## `create` action

有 device 新增

```json
{
  "type": "event",
  "event": {
    "event_type": "device_registry_updated",
    "data": {
      "action": "create",
      "device_id": "d063db262bf217a94cf0b7e82ce3b700"
    },
    "origin": "LOCAL",
    "time_fired": "2025-12-10T10:46:56.541578+00:00",
    "context": {
      "id": "01KC3XY2RXPZ2NR3CWBD4AD0M4",
      "parent_id": null,
      "user_id": null
    }
  },
  "id": 6
}
```

## `update` action

有 device 更新資料

```json
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
}
```

## `remove` action

有 device 被刪除

```json
{
  "type": "event",
  "event": {
    "event_type": "device_registry_updated",
    "data": {
      "action": "remove",
      "device_id": "0bb7a4d76b62e78e4a6b352a4e9ffda9"
    },
    "origin": "LOCAL",
    "time_fired": "2025-12-10T10:45:27.214315+00:00",
    "context": {
      "id": "01KC3XVBHE8SHJX4JHWYE52448",
      "parent_id": null,
      "user_id": null
    }
  },
  "id": 6
}
```
