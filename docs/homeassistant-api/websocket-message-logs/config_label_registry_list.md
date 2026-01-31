# description

取回 label 清單。

# example

Send

```json
{
  "type": "config/label_registry/list",
  "id": 18
}
```

Received

```json
{
  "id": 18,
  "type": "result",
  "success": true,
  "result": [
    {
      "color": null,
      "created_at": 1765033255.683357,
      "description": null,
      "icon": null,
      "label_id": "jj",
      "name": "jj",
      "modified_at": 1765033255.683372
    },
    {
      "color": null,
      "created_at": 1765432283.093184,
      "description": null,
      "icon": null,
      "label_id": "jj2",
      "name": "jj2",
      "modified_at": 1765432283.09319
    }
  ]
}
```
