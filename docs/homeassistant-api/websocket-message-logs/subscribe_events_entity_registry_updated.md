# description

Subscribe `entity_registry_updated` events.

若有訂閱 `entity_registry_updated` events

```json
{
  "type": "subscribe_events",
  "event_type": "entity_registry_updated",
  "id": 4
}
```

# event types

## `create` action

有 entity 新增

```json
{
  "type": "event",
  "event": {
    "event_type": "entity_registry_updated",
    "data": {
      "action": "create",
      "entity_id": "sensor.localhost_ssl_disk_used"
    },
    "origin": "LOCAL",
    "time_fired": "2025-12-10T09:56:57.467483+00:00",
    "context": {
      "id": "01KC3V2HZVV12HZ2BKBBF2JH5D",
      "parent_id": null,
      "user_id": null
    }
  },
  "id": 4
}
```

## `update` action

有 entity 更新資料

```json
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
}
```

這裡的 "changes" 中是舊值， 可以用 `config/entity_registry/get` 取回單一 entity 新值或是使用 `config/entity_registry/list` 重拿 entity list

## `remove` action

有 entity 被刪除

```json
{
  "type": "event",
  "event": {
    "event_type": "entity_registry_updated",
    "data": {
      "action": "remove",
      "entity_id": "sensor.localhost_zram2_disk_write"
    },
    "origin": "LOCAL",
    "time_fired": "2025-12-10T09:49:53.635790+00:00",
    "context": {
      "id": "01KC3TNM3362PA8FA0G43K6NPH",
      "parent_id": null,
      "user_id": null
    }
  },
  "id": 4
}
```
