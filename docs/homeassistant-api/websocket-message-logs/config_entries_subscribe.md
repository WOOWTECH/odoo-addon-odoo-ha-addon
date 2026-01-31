# description

訂閱 entry 的狀態改變事件。

# example

Send

```
{"type":"config_entries/subscribe","type_filter":["device","hub","service","hardware"],"id":45}
```

Received the first message

```
{
  "id": 45,
  "type": "result",
  "success": true,
  "result": null
}
```

Received the second message

```
{
  "id": 45,
  "type": "event",
  "event": [
    {
      "type": null,
      "entry": {
        "created_at": 0,
        "entry_id": "5775ca3dcdf4c1a964c80a487afa26e1",
        "domain": "hassio",
        "modified_at": 0,
        "title": "Supervisor",
        "source": "system",
        "state": "loaded",
        "supports_options": false,
        "supports_remove_device": false,
        "supports_unload": true,
        "supports_reconfigure": false,
        "supported_subentry_types": {},
        "pref_disable_new_entities": false,
        "pref_disable_polling": false,
        "disabled_by": null,
        "reason": null,
        "error_reason_translation_key": null,
        "error_reason_translation_placeholders": null,
        "num_subentries": 0
      }
    },
    {
      "type": null,
      "entry": {
        "created_at": 0,
        "entry_id": "58ce032d896ef65c6e99f2333da9174d",
        "domain": "sun",
        "modified_at": 0,
        "title": "Sun",
        "source": "import",
        "state": "loaded",
        "supports_options": false,
        "supports_remove_device": false,
        "supports_unload": true,
        "supports_reconfigure": false,
        "supported_subentry_types": {},
        "pref_disable_new_entities": false,
        "pref_disable_polling": false,
        "disabled_by": null,
        "reason": null,
        "error_reason_translation_key": null,
        "error_reason_translation_placeholders": null,
        "num_subentries": 0
      }
    },
    {
      "type": null,
      "entry": {
        "created_at": 0,
        "entry_id": "dd342352e11a48c5766e4a88e2616a93",
        "domain": "radio_browser",
        "modified_at": 0,
        "title": "Radio Browser",
        "source": "onboarding",
        "state": "loaded",
        "supports_options": false,
        "supports_remove_device": false,
        "supports_unload": true,
        "supports_reconfigure": false,
        "supported_subentry_types": {},
        "pref_disable_new_entities": false,
        "pref_disable_polling": false,
        "disabled_by": null,
        "reason": null,
        "error_reason_translation_key": null,
        "error_reason_translation_placeholders": null,
        "num_subentries": 0
      }
    },
    {
      "type": null,
      "entry": {
        "created_at": 1731474425.371593,
        "entry_id": "01JCHYP1GV739VZA1NHZYA3CAB",
        "domain": "matter",
        "modified_at": 1731474425.371601,
        "title": "Matter",
        "source": "user",
        "state": "loaded",
        "supports_options": false,
        "supports_remove_device": true,
        "supports_unload": true,
        "supports_reconfigure": false,
        "supported_subentry_types": {},
        "pref_disable_new_entities": false,
        "pref_disable_polling": false,
        "disabled_by": null,
        "reason": null,
        "error_reason_translation_key": null,
        "error_reason_translation_placeholders": null,
        "num_subentries": 0
      }
    },
    {
      "type": null,
      "entry": {
        "created_at": 1750913697.186926,
        "entry_id": "01JYN9DHD2RXAJMHEFC8KMCMZJ",
        "domain": "backup",
        "modified_at": 1750913697.186933,
        "title": "Backup",
        "source": "system",
        "state": "loaded",
        "supports_options": false,
        "supports_remove_device": false,
        "supports_unload": true,
        "supports_reconfigure": false,
        "supported_subentry_types": {},
        "pref_disable_new_entities": false,
        "pref_disable_polling": false,
        "disabled_by": null,
        "reason": null,
        "error_reason_translation_key": null,
        "error_reason_translation_placeholders": null,
        "num_subentries": 0
      }
    },
    {
      "type": null,
      "entry": {
        "created_at": 1758611915.435253,
        "entry_id": "01K5TQ0GNBV50K6G7V5F23K6M3",
        "domain": "hacs",
        "modified_at": 1758611915.435261,
        "title": "",
        "source": "user",
        "state": "loaded",
        "supports_options": true,
        "supports_remove_device": false,
        "supports_unload": true,
        "supports_reconfigure": false,
        "supported_subentry_types": {},
        "pref_disable_new_entities": false,
        "pref_disable_polling": false,
        "disabled_by": null,
        "reason": null,
        "error_reason_translation_key": null,
        "error_reason_translation_placeholders": null,
        "num_subentries": 0
      }
    },
    {
      "type": null,
      "entry": {
        "created_at": 1758612399.840663,
        "entry_id": "01K5TQF9Q0CAPR3G1NA8V7REGR",
        "domain": "virtual",
        "modified_at": 1758612399.84067,
        "title": "imported - virtual",
        "source": "user",
        "state": "loaded",
        "supports_options": false,
        "supports_remove_device": false,
        "supports_unload": true,
        "supports_reconfigure": false,
        "supported_subentry_types": {},
        "pref_disable_new_entities": false,
        "pref_disable_polling": false,
        "disabled_by": null,
        "reason": null,
        "error_reason_translation_key": null,
        "error_reason_translation_placeholders": null,
        "num_subentries": 0
      }
    },
    {
      "type": null,
      "entry": {
        "created_at": 1764496551.613381,
        "entry_id": "01KBA31BNXAWX73PQ3W00QHXZG",
        "domain": "glances",
        "modified_at": 1764496551.613388,
        "title": "localhost:61209",
        "source": "user",
        "state": "loaded",
        "supports_options": false,
        "supports_remove_device": false,
        "supports_unload": true,
        "supports_reconfigure": false,
        "supported_subentry_types": {},
        "pref_disable_new_entities": false,
        "pref_disable_polling": false,
        "disabled_by": null,
        "reason": null,
        "error_reason_translation_key": null,
        "error_reason_translation_placeholders": null,
        "num_subentries": 0
      }
    }
  ]
}
```
