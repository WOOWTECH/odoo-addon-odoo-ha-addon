# description

Get area list

# example

Send

```json
{ "type": "config/area_registry/list", "id": 43 }
```

Received

```json
{
  "id": 43,
  "type": "result",
  "success": true,
  "result": [
    {
      "aliases": [],
      "area_id": "ke_ting",
      "floor_id": null,
      "humidity_entity_id": null,
      "icon": null,
      "labels": [],
      "name": "客廳",
      "picture": null,
      "temperature_entity_id": null,
      "created_at": 0,
      "modified_at": 0
    },
    {
      "aliases": [],
      "area_id": "chu_fang",
      "floor_id": null,
      "humidity_entity_id": null,
      "icon": null,
      "labels": [],
      "name": "廚房",
      "picture": null,
      "temperature_entity_id": null,
      "created_at": 0,
      "modified_at": 0
    },
    {
      "aliases": [],
      "area_id": "wo_shi",
      "floor_id": null,
      "humidity_entity_id": null,
      "icon": null,
      "labels": [],
      "name": "臥室",
      "picture": null,
      "temperature_entity_id": null,
      "created_at": 0,
      "modified_at": 0
    },
    {
      "aliases": [],
      "area_id": "test3",
      "floor_id": null,
      "humidity_entity_id": null,
      "icon": null,
      "labels": [],
      "name": "test3",
      "picture": null,
      "temperature_entity_id": null,
      "created_at": 1760542551.51415,
      "modified_at": 1760542551.514163
    },
    {
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
  ]
}
```
