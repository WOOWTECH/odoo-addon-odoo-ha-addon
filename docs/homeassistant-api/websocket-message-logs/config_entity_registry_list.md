# description

取回 entity 清單。

若一個 device 有多個 entities 就會展開。

# example

Send

```json
{
  "type": "config/entity_registry/list",
  "id": 34
}
```

Received

```json
{
  "id": 34,
  "type": "result",
  "success": true,
  "result": [
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "5775ca3dcdf4c1a964c80a487afa26e1",
      "config_subentry_id": null,
      "created_at": 0,
      "device_id": "c3e6c857fa2a9dc0d5f35a2808521fbf",
      "disabled_by": "integration",
      "entity_category": null,
      "entity_id": "sensor.file_editor_version",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "f75e9ef8c37924bd1ebc4aae2e468c83",
      "labels": [],
      "modified_at": 0,
      "name": null,
      "options": {
        "conversation": {
          "should_expose": false
        }
      },
      "original_name": "版本",
      "platform": "hassio",
      "translation_key": "version",
      "unique_id": "core_configurator_version"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "5775ca3dcdf4c1a964c80a487afa26e1",
      "config_subentry_id": null,
      "created_at": 0,
      "device_id": "c3e6c857fa2a9dc0d5f35a2808521fbf",
      "disabled_by": "integration",
      "entity_category": null,
      "entity_id": "sensor.file_editor_newest_version",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "79e219e3f7681ef4a0a3b804a90510cc",
      "labels": [],
      "modified_at": 0,
      "name": null,
      "options": {
        "conversation": {
          "should_expose": false
        }
      },
      "original_name": "最新版本",
      "platform": "hassio",
      "translation_key": "version_latest",
      "unique_id": "core_configurator_version_latest"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "5775ca3dcdf4c1a964c80a487afa26e1",
      "config_subentry_id": null,
      "created_at": 0,
      "device_id": "c3e6c857fa2a9dc0d5f35a2808521fbf",
      "disabled_by": "integration",
      "entity_category": null,
      "entity_id": "sensor.file_editor_cpu_percent",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "f9ea80072c00b9ace1af8914337a25c9",
      "labels": [],
      "modified_at": 0,
      "name": null,
      "options": {
        "conversation": {
          "should_expose": false
        }
      },
      "original_name": "CPU 百分比",
      "platform": "hassio",
      "translation_key": "cpu_percent",
      "unique_id": "core_configurator_cpu_percent"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "5775ca3dcdf4c1a964c80a487afa26e1",
      "config_subentry_id": null,
      "created_at": 0,
      "device_id": "c3e6c857fa2a9dc0d5f35a2808521fbf",
      "disabled_by": "integration",
      "entity_category": null,
      "entity_id": "sensor.file_editor_memory_percent",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "7051da8008c996ec8036e0b055488b50",
      "labels": [],
      "modified_at": 0,
      "name": null,
      "options": {
        "conversation": {
          "should_expose": false
        }
      },
      "original_name": "記憶體百分比",
      "platform": "hassio",
      "translation_key": "memory_percent",
      "unique_id": "core_configurator_memory_percent"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "5775ca3dcdf4c1a964c80a487afa26e1",
      "config_subentry_id": null,
      "created_at": 0,
      "device_id": "94c6f7f3f835bc28228905103bea66b5",
      "disabled_by": "integration",
      "entity_category": null,
      "entity_id": "sensor.mosquitto_broker_version",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "3b96fdf47bba917ba90710f972665346",
      "labels": [],
      "modified_at": 0,
      "name": null,
      "options": {
        "conversation": {
          "should_expose": false
        }
      },
      "original_name": "版本",
      "platform": "hassio",
      "translation_key": "version",
      "unique_id": "core_mosquitto_version"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "5775ca3dcdf4c1a964c80a487afa26e1",
      "config_subentry_id": null,
      "created_at": 0,
      "device_id": "94c6f7f3f835bc28228905103bea66b5",
      "disabled_by": "integration",
      "entity_category": null,
      "entity_id": "sensor.mosquitto_broker_newest_version",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "0c40d985cdbd5c5b163a1385a8fd675f",
      "labels": [],
      "modified_at": 0,
      "name": null,
      "options": {
        "conversation": {
          "should_expose": false
        }
      },
      "original_name": "最新版本",
      "platform": "hassio",
      "translation_key": "version_latest",
      "unique_id": "core_mosquitto_version_latest"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "5775ca3dcdf4c1a964c80a487afa26e1",
      "config_subentry_id": null,
      "created_at": 0,
      "device_id": "94c6f7f3f835bc28228905103bea66b5",
      "disabled_by": "integration",
      "entity_category": null,
      "entity_id": "sensor.mosquitto_broker_cpu_percent",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "186cf63e1ba2019b4de47673cfe17ed1",
      "labels": [],
      "modified_at": 0,
      "name": null,
      "options": {
        "conversation": {
          "should_expose": false
        }
      },
      "original_name": "CPU 百分比",
      "platform": "hassio",
      "translation_key": "cpu_percent",
      "unique_id": "core_mosquitto_cpu_percent"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "5775ca3dcdf4c1a964c80a487afa26e1",
      "config_subentry_id": null,
      "created_at": 0,
      "device_id": "94c6f7f3f835bc28228905103bea66b5",
      "disabled_by": "integration",
      "entity_category": null,
      "entity_id": "sensor.mosquitto_broker_memory_percent",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "cc189c2dc21ce3d6cb3a609601c0d253",
      "labels": [],
      "modified_at": 0,
      "name": null,
      "options": {
        "conversation": {
          "should_expose": false
        }
      },
      "original_name": "記憶體百分比",
      "platform": "hassio",
      "translation_key": "memory_percent",
      "unique_id": "core_mosquitto_memory_percent"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "5775ca3dcdf4c1a964c80a487afa26e1",
      "config_subentry_id": null,
      "created_at": 0,
      "device_id": "6542590bf680a5fe3173e0529b334a06",
      "disabled_by": "integration",
      "entity_category": null,
      "entity_id": "sensor.node_red_version",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "364713aabfbca577e34fd96de3fb7d00",
      "labels": [],
      "modified_at": 0,
      "name": null,
      "options": {
        "conversation": {
          "should_expose": false
        }
      },
      "original_name": "版本",
      "platform": "hassio",
      "translation_key": "version",
      "unique_id": "a0d7b954_nodered_version"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "5775ca3dcdf4c1a964c80a487afa26e1",
      "config_subentry_id": null,
      "created_at": 0,
      "device_id": "6542590bf680a5fe3173e0529b334a06",
      "disabled_by": "integration",
      "entity_category": null,
      "entity_id": "sensor.node_red_newest_version",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "d6e67414f8f2595dbf4fc8dd79bff8d9",
      "labels": [],
      "modified_at": 0,
      "name": null,
      "options": {
        "conversation": {
          "should_expose": false
        }
      },
      "original_name": "最新版本",
      "platform": "hassio",
      "translation_key": "version_latest",
      "unique_id": "a0d7b954_nodered_version_latest"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "5775ca3dcdf4c1a964c80a487afa26e1",
      "config_subentry_id": null,
      "created_at": 0,
      "device_id": "6542590bf680a5fe3173e0529b334a06",
      "disabled_by": "integration",
      "entity_category": null,
      "entity_id": "sensor.node_red_cpu_percent",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "3d680a4b9e67178391a8ed6a6133bd24",
      "labels": [],
      "modified_at": 0,
      "name": null,
      "options": {
        "conversation": {
          "should_expose": false
        }
      },
      "original_name": "CPU 百分比",
      "platform": "hassio",
      "translation_key": "cpu_percent",
      "unique_id": "a0d7b954_nodered_cpu_percent"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "5775ca3dcdf4c1a964c80a487afa26e1",
      "config_subentry_id": null,
      "created_at": 0,
      "device_id": "6542590bf680a5fe3173e0529b334a06",
      "disabled_by": "integration",
      "entity_category": null,
      "entity_id": "sensor.node_red_memory_percent",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "0a7975504cff8a1e3eb600fb68c4d263",
      "labels": [],
      "modified_at": 0,
      "name": null,
      "options": {
        "conversation": {
          "should_expose": false
        }
      },
      "original_name": "記憶體百分比",
      "platform": "hassio",
      "translation_key": "memory_percent",
      "unique_id": "a0d7b954_nodered_memory_percent"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "5775ca3dcdf4c1a964c80a487afa26e1",
      "config_subentry_id": null,
      "created_at": 0,
      "device_id": "1ef3ad0ead5262e5fbd9211c440dbef5",
      "disabled_by": "integration",
      "entity_category": null,
      "entity_id": "sensor.samba_share_version",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "0ce768635e6c1756eebfc4738b2fbd3f",
      "labels": [],
      "modified_at": 0,
      "name": null,
      "options": {
        "conversation": {
          "should_expose": false
        }
      },
      "original_name": "版本",
      "platform": "hassio",
      "translation_key": "version",
      "unique_id": "core_samba_version"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "5775ca3dcdf4c1a964c80a487afa26e1",
      "config_subentry_id": null,
      "created_at": 0,
      "device_id": "1ef3ad0ead5262e5fbd9211c440dbef5",
      "disabled_by": "integration",
      "entity_category": null,
      "entity_id": "sensor.samba_share_newest_version",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "7e43797951c899ef3b54edafc31deab4",
      "labels": [],
      "modified_at": 0,
      "name": null,
      "options": {
        "conversation": {
          "should_expose": false
        }
      },
      "original_name": "最新版本",
      "platform": "hassio",
      "translation_key": "version_latest",
      "unique_id": "core_samba_version_latest"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "5775ca3dcdf4c1a964c80a487afa26e1",
      "config_subentry_id": null,
      "created_at": 0,
      "device_id": "1ef3ad0ead5262e5fbd9211c440dbef5",
      "disabled_by": "integration",
      "entity_category": null,
      "entity_id": "sensor.samba_share_cpu_percent",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "50900321671479e319b528db06775e88",
      "labels": [],
      "modified_at": 0,
      "name": null,
      "options": {
        "conversation": {
          "should_expose": false
        }
      },
      "original_name": "CPU 百分比",
      "platform": "hassio",
      "translation_key": "cpu_percent",
      "unique_id": "core_samba_cpu_percent"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "5775ca3dcdf4c1a964c80a487afa26e1",
      "config_subentry_id": null,
      "created_at": 0,
      "device_id": "1ef3ad0ead5262e5fbd9211c440dbef5",
      "disabled_by": "integration",
      "entity_category": null,
      "entity_id": "sensor.samba_share_memory_percent",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "bc470448e31770bb72084df7c22f225b",
      "labels": [],
      "modified_at": 0,
      "name": null,
      "options": {
        "conversation": {
          "should_expose": false
        }
      },
      "original_name": "記憶體百分比",
      "platform": "hassio",
      "translation_key": "memory_percent",
      "unique_id": "core_samba_memory_percent"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "5775ca3dcdf4c1a964c80a487afa26e1",
      "config_subentry_id": null,
      "created_at": 0,
      "device_id": "f479abc2e1bf55db5781b477972dffe5",
      "disabled_by": "integration",
      "entity_category": null,
      "entity_id": "sensor.home_assistant_operating_system_version",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "0769e0a41d76f84aa11b9392afa1a1ff",
      "labels": [],
      "modified_at": 0,
      "name": null,
      "options": {
        "conversation": {
          "should_expose": false
        }
      },
      "original_name": "版本",
      "platform": "hassio",
      "translation_key": "version",
      "unique_id": "home_assistant_os_version"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "5775ca3dcdf4c1a964c80a487afa26e1",
      "config_subentry_id": null,
      "created_at": 0,
      "device_id": "f479abc2e1bf55db5781b477972dffe5",
      "disabled_by": "integration",
      "entity_category": null,
      "entity_id": "sensor.home_assistant_operating_system_newest_version",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "00c1dae23f20950f6bff00095662404d",
      "labels": [],
      "modified_at": 0,
      "name": null,
      "options": {
        "conversation": {
          "should_expose": false
        }
      },
      "original_name": "最新版本",
      "platform": "hassio",
      "translation_key": "version_latest",
      "unique_id": "home_assistant_os_version_latest"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "5775ca3dcdf4c1a964c80a487afa26e1",
      "config_subentry_id": null,
      "created_at": 0,
      "device_id": "c3e6c857fa2a9dc0d5f35a2808521fbf",
      "disabled_by": "integration",
      "entity_category": null,
      "entity_id": "binary_sensor.file_editor_running",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "47ace489020edd2624b4f8614a7e0f11",
      "labels": [],
      "modified_at": 0,
      "name": null,
      "options": {
        "conversation": {
          "should_expose": false
        }
      },
      "original_name": "執行中",
      "platform": "hassio",
      "translation_key": "state",
      "unique_id": "core_configurator_state"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "5775ca3dcdf4c1a964c80a487afa26e1",
      "config_subentry_id": null,
      "created_at": 0,
      "device_id": "94c6f7f3f835bc28228905103bea66b5",
      "disabled_by": "integration",
      "entity_category": null,
      "entity_id": "binary_sensor.mosquitto_broker_running",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "c52d7f5168bb9d90a18487182059754b",
      "labels": [],
      "modified_at": 0,
      "name": null,
      "options": {
        "conversation": {
          "should_expose": false
        }
      },
      "original_name": "執行中",
      "platform": "hassio",
      "translation_key": "state",
      "unique_id": "core_mosquitto_state"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "5775ca3dcdf4c1a964c80a487afa26e1",
      "config_subentry_id": null,
      "created_at": 0,
      "device_id": "6542590bf680a5fe3173e0529b334a06",
      "disabled_by": "integration",
      "entity_category": null,
      "entity_id": "binary_sensor.node_red_running",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "0e4972630ec95f869781a27617c5ee85",
      "labels": [],
      "modified_at": 0,
      "name": null,
      "options": {
        "conversation": {
          "should_expose": false
        }
      },
      "original_name": "執行中",
      "platform": "hassio",
      "translation_key": "state",
      "unique_id": "a0d7b954_nodered_state"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "5775ca3dcdf4c1a964c80a487afa26e1",
      "config_subentry_id": null,
      "created_at": 0,
      "device_id": "1ef3ad0ead5262e5fbd9211c440dbef5",
      "disabled_by": "integration",
      "entity_category": null,
      "entity_id": "binary_sensor.samba_share_running",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "bb805a2ca680008c366749d9b48d48cc",
      "labels": [],
      "modified_at": 0,
      "name": null,
      "options": {
        "conversation": {
          "should_expose": false
        }
      },
      "original_name": "執行中",
      "platform": "hassio",
      "translation_key": "state",
      "unique_id": "core_samba_state"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "5775ca3dcdf4c1a964c80a487afa26e1",
      "config_subentry_id": null,
      "created_at": 0,
      "device_id": "a379c433ec37d690c99e879186b29b25",
      "disabled_by": null,
      "entity_category": "config",
      "entity_id": "update.home_assistant_supervisor_update",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "729fbe5203cdb0efcfa4359111f5649d",
      "labels": [],
      "modified_at": 1750913679.829401,
      "name": null,
      "options": {
        "conversation": {
          "should_expose": false
        }
      },
      "original_name": "更新",
      "platform": "hassio",
      "translation_key": "update",
      "unique_id": "home_assistant_supervisor_version_latest"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "5775ca3dcdf4c1a964c80a487afa26e1",
      "config_subentry_id": null,
      "created_at": 0,
      "device_id": "4c5a78a8b7d9b7ab4840f38a183d19c7",
      "disabled_by": null,
      "entity_category": "config",
      "entity_id": "update.home_assistant_core_update",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "c5f81ff03232cce868c01d3172df798f",
      "labels": [],
      "modified_at": 1750913679.830059,
      "name": null,
      "options": {
        "conversation": {
          "should_expose": false
        }
      },
      "original_name": "更新",
      "platform": "hassio",
      "translation_key": "update",
      "unique_id": "home_assistant_core_version_latest"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "5775ca3dcdf4c1a964c80a487afa26e1",
      "config_subentry_id": null,
      "created_at": 0,
      "device_id": "c3e6c857fa2a9dc0d5f35a2808521fbf",
      "disabled_by": null,
      "entity_category": "config",
      "entity_id": "update.file_editor_update",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "13aeea8c8c95215e73b22405ba5315ac",
      "labels": [],
      "modified_at": 1750913679.830975,
      "name": null,
      "options": {
        "conversation": {
          "should_expose": false
        }
      },
      "original_name": "更新",
      "platform": "hassio",
      "translation_key": "update",
      "unique_id": "core_configurator_version_latest"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "5775ca3dcdf4c1a964c80a487afa26e1",
      "config_subentry_id": null,
      "created_at": 0,
      "device_id": "94c6f7f3f835bc28228905103bea66b5",
      "disabled_by": null,
      "entity_category": "config",
      "entity_id": "update.mosquitto_broker_update",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "4b35715f07e86272149240bc9306af41",
      "labels": [],
      "modified_at": 1750913679.831886,
      "name": null,
      "options": {
        "conversation": {
          "should_expose": false
        }
      },
      "original_name": "更新",
      "platform": "hassio",
      "translation_key": "update",
      "unique_id": "core_mosquitto_version_latest"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "5775ca3dcdf4c1a964c80a487afa26e1",
      "config_subentry_id": null,
      "created_at": 0,
      "device_id": "6542590bf680a5fe3173e0529b334a06",
      "disabled_by": null,
      "entity_category": "config",
      "entity_id": "update.node_red_update",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "27474a518e7d9d3d5f64bbf5c601bcd8",
      "labels": [],
      "modified_at": 1750913679.833567,
      "name": null,
      "options": {
        "conversation": {
          "should_expose": false
        }
      },
      "original_name": "更新",
      "platform": "hassio",
      "translation_key": "update",
      "unique_id": "a0d7b954_nodered_version_latest"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "5775ca3dcdf4c1a964c80a487afa26e1",
      "config_subentry_id": null,
      "created_at": 0,
      "device_id": "1ef3ad0ead5262e5fbd9211c440dbef5",
      "disabled_by": null,
      "entity_category": "config",
      "entity_id": "update.samba_share_update",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "a372643980aa91a7c9227fc22fc40eff",
      "labels": [],
      "modified_at": 1750913679.834666,
      "name": null,
      "options": {
        "conversation": {
          "should_expose": false
        }
      },
      "original_name": "更新",
      "platform": "hassio",
      "translation_key": "update",
      "unique_id": "core_samba_version_latest"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "5775ca3dcdf4c1a964c80a487afa26e1",
      "config_subentry_id": null,
      "created_at": 0,
      "device_id": "f479abc2e1bf55db5781b477972dffe5",
      "disabled_by": null,
      "entity_category": "config",
      "entity_id": "update.home_assistant_operating_system_update",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "5dddc23a598a95af7b41fc5eb9564b32",
      "labels": [],
      "modified_at": 1750913679.835832,
      "name": null,
      "options": {
        "conversation": {
          "should_expose": false
        }
      },
      "original_name": "更新",
      "platform": "hassio",
      "translation_key": "update",
      "unique_id": "home_assistant_os_version_latest"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": null,
      "config_subentry_id": null,
      "created_at": 0,
      "device_id": null,
      "disabled_by": null,
      "entity_category": null,
      "entity_id": "person.admin",
      "has_entity_name": false,
      "hidden_by": null,
      "icon": null,
      "id": "69db5769941a3b33d673bd9e269255d3",
      "labels": [],
      "modified_at": 0,
      "name": null,
      "options": {
        "conversation": {
          "should_expose": false
        }
      },
      "original_name": "admin",
      "platform": "person",
      "translation_key": null,
      "unique_id": "admin"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "5775ca3dcdf4c1a964c80a487afa26e1",
      "config_subentry_id": null,
      "created_at": 0,
      "device_id": "4c5a78a8b7d9b7ab4840f38a183d19c7",
      "disabled_by": "integration",
      "entity_category": null,
      "entity_id": "sensor.home_assistant_core_cpu_bai_fen_bi",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "ae3bfa7c5bcb4cde93aafc1537ab6381",
      "labels": [],
      "modified_at": 0,
      "name": null,
      "options": {
        "conversation": {
          "should_expose": false
        }
      },
      "original_name": "CPU 百分比",
      "platform": "hassio",
      "translation_key": "cpu_percent",
      "unique_id": "home_assistant_core_cpu_percent"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "5775ca3dcdf4c1a964c80a487afa26e1",
      "config_subentry_id": null,
      "created_at": 0,
      "device_id": "4c5a78a8b7d9b7ab4840f38a183d19c7",
      "disabled_by": "integration",
      "entity_category": null,
      "entity_id": "sensor.home_assistant_core_ji_yi_ti_bai_fen_bi",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "348a7f63c2b2bd7577d0ee3c002daf11",
      "labels": [],
      "modified_at": 0,
      "name": null,
      "options": {
        "conversation": {
          "should_expose": false
        }
      },
      "original_name": "記憶體百分比",
      "platform": "hassio",
      "translation_key": "memory_percent",
      "unique_id": "home_assistant_core_memory_percent"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "5775ca3dcdf4c1a964c80a487afa26e1",
      "config_subentry_id": null,
      "created_at": 0,
      "device_id": "a379c433ec37d690c99e879186b29b25",
      "disabled_by": "integration",
      "entity_category": null,
      "entity_id": "sensor.home_assistant_supervisor_cpu_bai_fen_bi",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "588fc3ed98c326d50e168dbb57dcef57",
      "labels": [],
      "modified_at": 0,
      "name": null,
      "options": {
        "conversation": {
          "should_expose": false
        }
      },
      "original_name": "CPU 百分比",
      "platform": "hassio",
      "translation_key": "cpu_percent",
      "unique_id": "home_assistant_supervisor_cpu_percent"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "5775ca3dcdf4c1a964c80a487afa26e1",
      "config_subentry_id": null,
      "created_at": 0,
      "device_id": "a379c433ec37d690c99e879186b29b25",
      "disabled_by": "integration",
      "entity_category": null,
      "entity_id": "sensor.home_assistant_supervisor_ji_yi_ti_bai_fen_bi",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "1e5e343ec2d4fa0685e38a33b414c4c1",
      "labels": [],
      "modified_at": 0,
      "name": null,
      "options": {
        "conversation": {
          "should_expose": false
        }
      },
      "original_name": "記憶體百分比",
      "platform": "hassio",
      "translation_key": "memory_percent",
      "unique_id": "home_assistant_supervisor_memory_percent"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "5775ca3dcdf4c1a964c80a487afa26e1",
      "config_subentry_id": null,
      "created_at": 0,
      "device_id": "e01e55a1ba4ab13e406bda839737cd4a",
      "disabled_by": "integration",
      "entity_category": "diagnostic",
      "entity_id": "sensor.home_assistant_host_os_agent_ban_ben",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "e14d7a39f9d559afb6f98a766374b6f6",
      "labels": [],
      "modified_at": 0,
      "name": null,
      "options": {
        "conversation": {
          "should_expose": false
        }
      },
      "original_name": "OS Agent 版本",
      "platform": "hassio",
      "translation_key": "agent_version",
      "unique_id": "home_assistant_host_agent_version"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "5775ca3dcdf4c1a964c80a487afa26e1",
      "config_subentry_id": null,
      "created_at": 0,
      "device_id": "e01e55a1ba4ab13e406bda839737cd4a",
      "disabled_by": "integration",
      "entity_category": "diagnostic",
      "entity_id": "sensor.home_assistant_host_apparmor_ban_ben",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "5de19424e6a636210abc23c80cc4e80e",
      "labels": [],
      "modified_at": 0,
      "name": null,
      "options": {
        "conversation": {
          "should_expose": false
        }
      },
      "original_name": "Apparmor 版本",
      "platform": "hassio",
      "translation_key": "apparmor_version",
      "unique_id": "home_assistant_host_apparmor_version"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "5775ca3dcdf4c1a964c80a487afa26e1",
      "config_subentry_id": null,
      "created_at": 0,
      "device_id": "e01e55a1ba4ab13e406bda839737cd4a",
      "disabled_by": "integration",
      "entity_category": "diagnostic",
      "entity_id": "sensor.home_assistant_host_zong_rong_liang",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "f505ebad81b75b1815a62f601251a9f7",
      "labels": [],
      "modified_at": 0,
      "name": null,
      "options": {
        "conversation": {
          "should_expose": false
        }
      },
      "original_name": "總容量",
      "platform": "hassio",
      "translation_key": "disk_total",
      "unique_id": "home_assistant_host_disk_total"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "5775ca3dcdf4c1a964c80a487afa26e1",
      "config_subentry_id": null,
      "created_at": 0,
      "device_id": "e01e55a1ba4ab13e406bda839737cd4a",
      "disabled_by": "integration",
      "entity_category": "diagnostic",
      "entity_id": "sensor.home_assistant_host_yi_shi_yong_kong_jian",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "c31a7a452a2edb611655c313d521b41a",
      "labels": [],
      "modified_at": 0,
      "name": null,
      "options": {
        "conversation": {
          "should_expose": false
        }
      },
      "original_name": "已使用空間",
      "platform": "hassio",
      "translation_key": "disk_used",
      "unique_id": "home_assistant_host_disk_used"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "5775ca3dcdf4c1a964c80a487afa26e1",
      "config_subentry_id": null,
      "created_at": 0,
      "device_id": "e01e55a1ba4ab13e406bda839737cd4a",
      "disabled_by": "integration",
      "entity_category": "diagnostic",
      "entity_id": "sensor.home_assistant_host_ke_yong_kong_jian",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "fbcf763e73b6dacccabfc77d0746ec4f",
      "labels": [],
      "modified_at": 0,
      "name": null,
      "options": {
        "conversation": {
          "should_expose": false
        }
      },
      "original_name": "可用空間",
      "platform": "hassio",
      "translation_key": "disk_free",
      "unique_id": "home_assistant_host_disk_free"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "58ce032d896ef65c6e99f2333da9174d",
      "config_subentry_id": null,
      "created_at": 0,
      "device_id": "64312199f691eb8d16885793c03f73fb",
      "disabled_by": null,
      "entity_category": "diagnostic",
      "entity_id": "sensor.sun_next_dawn",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "f8cb69a7fcaef6f728a3f6f0c135b548",
      "labels": [],
      "modified_at": 0,
      "name": null,
      "options": {
        "conversation": {
          "should_expose": false
        }
      },
      "original_name": "下次清晨",
      "platform": "sun",
      "translation_key": "next_dawn",
      "unique_id": "58ce032d896ef65c6e99f2333da9174d-next_dawn"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "58ce032d896ef65c6e99f2333da9174d",
      "config_subentry_id": null,
      "created_at": 0,
      "device_id": "64312199f691eb8d16885793c03f73fb",
      "disabled_by": null,
      "entity_category": "diagnostic",
      "entity_id": "sensor.sun_next_dusk",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "fb8d76eeb70f48b66f8736e8ebc514cc",
      "labels": [],
      "modified_at": 0,
      "name": null,
      "options": {
        "conversation": {
          "should_expose": false
        }
      },
      "original_name": "下次黃昏",
      "platform": "sun",
      "translation_key": "next_dusk",
      "unique_id": "58ce032d896ef65c6e99f2333da9174d-next_dusk"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "58ce032d896ef65c6e99f2333da9174d",
      "config_subentry_id": null,
      "created_at": 0,
      "device_id": "64312199f691eb8d16885793c03f73fb",
      "disabled_by": null,
      "entity_category": "diagnostic",
      "entity_id": "sensor.sun_next_midnight",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "66b58e218862255081a84839ae94334c",
      "labels": [],
      "modified_at": 0,
      "name": null,
      "options": {
        "conversation": {
          "should_expose": false
        }
      },
      "original_name": "下次午夜",
      "platform": "sun",
      "translation_key": "next_midnight",
      "unique_id": "58ce032d896ef65c6e99f2333da9174d-next_midnight"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "58ce032d896ef65c6e99f2333da9174d",
      "config_subentry_id": null,
      "created_at": 0,
      "device_id": "64312199f691eb8d16885793c03f73fb",
      "disabled_by": null,
      "entity_category": "diagnostic",
      "entity_id": "sensor.sun_next_noon",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "8a882a25210a694b6ccc66cdbeb1b3d0",
      "labels": [],
      "modified_at": 0,
      "name": null,
      "options": {
        "conversation": {
          "should_expose": false
        }
      },
      "original_name": "下次正午",
      "platform": "sun",
      "translation_key": "next_noon",
      "unique_id": "58ce032d896ef65c6e99f2333da9174d-next_noon"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "58ce032d896ef65c6e99f2333da9174d",
      "config_subentry_id": null,
      "created_at": 0,
      "device_id": "64312199f691eb8d16885793c03f73fb",
      "disabled_by": null,
      "entity_category": "diagnostic",
      "entity_id": "sensor.sun_next_rising",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "3dd8ada4766304177269a15be6810291",
      "labels": [],
      "modified_at": 0,
      "name": null,
      "options": {
        "conversation": {
          "should_expose": false
        }
      },
      "original_name": "下次日出",
      "platform": "sun",
      "translation_key": "next_rising",
      "unique_id": "58ce032d896ef65c6e99f2333da9174d-next_rising"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "58ce032d896ef65c6e99f2333da9174d",
      "config_subentry_id": null,
      "created_at": 0,
      "device_id": "64312199f691eb8d16885793c03f73fb",
      "disabled_by": null,
      "entity_category": "diagnostic",
      "entity_id": "sensor.sun_next_setting",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "9e3d2aca0e17c2cb158c91fd60caf5ea",
      "labels": [],
      "modified_at": 0,
      "name": null,
      "options": {
        "conversation": {
          "should_expose": false
        }
      },
      "original_name": "下次日落",
      "platform": "sun",
      "translation_key": "next_setting",
      "unique_id": "58ce032d896ef65c6e99f2333da9174d-next_setting"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "58ce032d896ef65c6e99f2333da9174d",
      "config_subentry_id": null,
      "created_at": 0,
      "device_id": "64312199f691eb8d16885793c03f73fb",
      "disabled_by": "integration",
      "entity_category": "diagnostic",
      "entity_id": "sensor.sun_solar_elevation",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "8cf4c10ef4e7d30a7b5c529ad4844a6f",
      "labels": [],
      "modified_at": 0,
      "name": null,
      "options": {
        "conversation": {
          "should_expose": false
        }
      },
      "original_name": "太陽高度",
      "platform": "sun",
      "translation_key": "solar_elevation",
      "unique_id": "58ce032d896ef65c6e99f2333da9174d-solar_elevation"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "58ce032d896ef65c6e99f2333da9174d",
      "config_subentry_id": null,
      "created_at": 0,
      "device_id": "64312199f691eb8d16885793c03f73fb",
      "disabled_by": "integration",
      "entity_category": "diagnostic",
      "entity_id": "sensor.sun_solar_azimuth",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "f22da79383576001807f788fcc9bbb98",
      "labels": [],
      "modified_at": 0,
      "name": null,
      "options": {
        "conversation": {
          "should_expose": false
        }
      },
      "original_name": "太陽方位",
      "platform": "sun",
      "translation_key": "solar_azimuth",
      "unique_id": "58ce032d896ef65c6e99f2333da9174d-solar_azimuth"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "5775ca3dcdf4c1a964c80a487afa26e1",
      "config_subentry_id": null,
      "created_at": 0,
      "device_id": "f7ac5c74c87afbf5d150c22ec3a0d586",
      "disabled_by": "integration",
      "entity_category": null,
      "entity_id": "binary_sensor.openthread_border_router_running",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "c9e2372bf377ad567450d719a8f1f18d",
      "labels": [],
      "modified_at": 0,
      "name": null,
      "options": {
        "conversation": {
          "should_expose": false
        }
      },
      "original_name": "執行中",
      "platform": "hassio",
      "translation_key": "state",
      "unique_id": "core_openthread_border_router_state"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "5775ca3dcdf4c1a964c80a487afa26e1",
      "config_subentry_id": null,
      "created_at": 0,
      "device_id": "9b9f8c35f6a41bfe78f10803adf3e04e",
      "disabled_by": "integration",
      "entity_category": null,
      "entity_id": "binary_sensor.terminal_ssh_running",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "2f6c6c093e1582e556a12cc9cdb9ac8b",
      "labels": [],
      "modified_at": 0,
      "name": null,
      "options": {
        "conversation": {
          "should_expose": false
        }
      },
      "original_name": "執行中",
      "platform": "hassio",
      "translation_key": "state",
      "unique_id": "core_ssh_state"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "5775ca3dcdf4c1a964c80a487afa26e1",
      "config_subentry_id": null,
      "created_at": 0,
      "device_id": "f6def5ef540e5658b96188d3883ae684",
      "disabled_by": "integration",
      "entity_category": null,
      "entity_id": "binary_sensor.rtsptoweb_webrtc_running",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "1f946dccb4659cff4f6c6ee618f0af4b",
      "labels": [],
      "modified_at": 0,
      "name": null,
      "options": {
        "conversation": {
          "should_expose": false
        }
      },
      "original_name": "執行中",
      "platform": "hassio",
      "translation_key": "state",
      "unique_id": "e19319ad_rtsp-to-web_state"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "5775ca3dcdf4c1a964c80a487afa26e1",
      "config_subentry_id": null,
      "created_at": 0,
      "device_id": "f7ac5c74c87afbf5d150c22ec3a0d586",
      "disabled_by": null,
      "entity_category": "config",
      "entity_id": "update.openthread_border_router_update",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "67da4ec1fa10a5e6b44651f283e3d4a2",
      "labels": [],
      "modified_at": 1750913679.834174,
      "name": null,
      "options": {
        "conversation": {
          "should_expose": false
        }
      },
      "original_name": "更新",
      "platform": "hassio",
      "translation_key": "update",
      "unique_id": "core_openthread_border_router_version_latest"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "5775ca3dcdf4c1a964c80a487afa26e1",
      "config_subentry_id": null,
      "created_at": 0,
      "device_id": "9b9f8c35f6a41bfe78f10803adf3e04e",
      "disabled_by": null,
      "entity_category": "config",
      "entity_id": "update.terminal_ssh_update",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "8200d9d1442abe62372cede7b8a30126",
      "labels": [],
      "modified_at": 1750913679.832917,
      "name": null,
      "options": {
        "conversation": {
          "should_expose": false
        }
      },
      "original_name": "更新",
      "platform": "hassio",
      "translation_key": "update",
      "unique_id": "core_ssh_version_latest"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "5775ca3dcdf4c1a964c80a487afa26e1",
      "config_subentry_id": null,
      "created_at": 0,
      "device_id": "f6def5ef540e5658b96188d3883ae684",
      "disabled_by": null,
      "entity_category": "config",
      "entity_id": "update.rtsptoweb_webrtc_update",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "e4ac025d20590bb28d2d914a714999ed",
      "labels": [],
      "modified_at": 1750913679.833298,
      "name": null,
      "options": {
        "conversation": {
          "should_expose": false
        }
      },
      "original_name": "更新",
      "platform": "hassio",
      "translation_key": "update",
      "unique_id": "e19319ad_rtsp-to-web_version_latest"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "5775ca3dcdf4c1a964c80a487afa26e1",
      "config_subentry_id": null,
      "created_at": 0,
      "device_id": "f7ac5c74c87afbf5d150c22ec3a0d586",
      "disabled_by": "integration",
      "entity_category": null,
      "entity_id": "sensor.openthread_border_router_version",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "9ccb344e36336672f31cb0ea625efaff",
      "labels": [],
      "modified_at": 0,
      "name": null,
      "options": {
        "conversation": {
          "should_expose": false
        }
      },
      "original_name": "版本",
      "platform": "hassio",
      "translation_key": "version",
      "unique_id": "core_openthread_border_router_version"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "5775ca3dcdf4c1a964c80a487afa26e1",
      "config_subentry_id": null,
      "created_at": 0,
      "device_id": "f7ac5c74c87afbf5d150c22ec3a0d586",
      "disabled_by": "integration",
      "entity_category": null,
      "entity_id": "sensor.openthread_border_router_newest_version",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "bb2e7ebd3939a8644a808b7b7d2e03b2",
      "labels": [],
      "modified_at": 0,
      "name": null,
      "options": {
        "conversation": {
          "should_expose": false
        }
      },
      "original_name": "最新版本",
      "platform": "hassio",
      "translation_key": "version_latest",
      "unique_id": "core_openthread_border_router_version_latest"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "5775ca3dcdf4c1a964c80a487afa26e1",
      "config_subentry_id": null,
      "created_at": 0,
      "device_id": "f7ac5c74c87afbf5d150c22ec3a0d586",
      "disabled_by": "integration",
      "entity_category": null,
      "entity_id": "sensor.openthread_border_router_cpu_percent",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "75929adbbeb5e399a6985f878c2b176d",
      "labels": [],
      "modified_at": 0,
      "name": null,
      "options": {
        "conversation": {
          "should_expose": false
        }
      },
      "original_name": "CPU 百分比",
      "platform": "hassio",
      "translation_key": "cpu_percent",
      "unique_id": "core_openthread_border_router_cpu_percent"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "5775ca3dcdf4c1a964c80a487afa26e1",
      "config_subentry_id": null,
      "created_at": 0,
      "device_id": "f7ac5c74c87afbf5d150c22ec3a0d586",
      "disabled_by": "integration",
      "entity_category": null,
      "entity_id": "sensor.openthread_border_router_memory_percent",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "9ba4db077da4efc1c4721cce6f0aefd1",
      "labels": [],
      "modified_at": 0,
      "name": null,
      "options": {
        "conversation": {
          "should_expose": false
        }
      },
      "original_name": "記憶體百分比",
      "platform": "hassio",
      "translation_key": "memory_percent",
      "unique_id": "core_openthread_border_router_memory_percent"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "5775ca3dcdf4c1a964c80a487afa26e1",
      "config_subentry_id": null,
      "created_at": 0,
      "device_id": "9b9f8c35f6a41bfe78f10803adf3e04e",
      "disabled_by": "integration",
      "entity_category": null,
      "entity_id": "sensor.terminal_ssh_version",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "e6e5022e0fb4882ce46a486de905d161",
      "labels": [],
      "modified_at": 0,
      "name": null,
      "options": {
        "conversation": {
          "should_expose": false
        }
      },
      "original_name": "版本",
      "platform": "hassio",
      "translation_key": "version",
      "unique_id": "core_ssh_version"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "5775ca3dcdf4c1a964c80a487afa26e1",
      "config_subentry_id": null,
      "created_at": 0,
      "device_id": "9b9f8c35f6a41bfe78f10803adf3e04e",
      "disabled_by": "integration",
      "entity_category": null,
      "entity_id": "sensor.terminal_ssh_newest_version",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "7cd17e18b9fd017d7cba4ad4048970ab",
      "labels": [],
      "modified_at": 0,
      "name": null,
      "options": {
        "conversation": {
          "should_expose": false
        }
      },
      "original_name": "最新版本",
      "platform": "hassio",
      "translation_key": "version_latest",
      "unique_id": "core_ssh_version_latest"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "5775ca3dcdf4c1a964c80a487afa26e1",
      "config_subentry_id": null,
      "created_at": 0,
      "device_id": "9b9f8c35f6a41bfe78f10803adf3e04e",
      "disabled_by": "integration",
      "entity_category": null,
      "entity_id": "sensor.terminal_ssh_cpu_percent",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "6c49d9942834c5603bea3a0c4d746ebf",
      "labels": [],
      "modified_at": 0,
      "name": null,
      "options": {
        "conversation": {
          "should_expose": false
        }
      },
      "original_name": "CPU 百分比",
      "platform": "hassio",
      "translation_key": "cpu_percent",
      "unique_id": "core_ssh_cpu_percent"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "5775ca3dcdf4c1a964c80a487afa26e1",
      "config_subentry_id": null,
      "created_at": 0,
      "device_id": "9b9f8c35f6a41bfe78f10803adf3e04e",
      "disabled_by": "integration",
      "entity_category": null,
      "entity_id": "sensor.terminal_ssh_memory_percent",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "1162366d3cb35b325930aff619da0388",
      "labels": [],
      "modified_at": 0,
      "name": null,
      "options": {
        "conversation": {
          "should_expose": false
        }
      },
      "original_name": "記憶體百分比",
      "platform": "hassio",
      "translation_key": "memory_percent",
      "unique_id": "core_ssh_memory_percent"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "5775ca3dcdf4c1a964c80a487afa26e1",
      "config_subentry_id": null,
      "created_at": 0,
      "device_id": "f6def5ef540e5658b96188d3883ae684",
      "disabled_by": "integration",
      "entity_category": null,
      "entity_id": "sensor.rtsptoweb_webrtc_version",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "23bdeec0094334c6d63e85b4be8b8221",
      "labels": [],
      "modified_at": 0,
      "name": null,
      "options": {
        "conversation": {
          "should_expose": false
        }
      },
      "original_name": "版本",
      "platform": "hassio",
      "translation_key": "version",
      "unique_id": "e19319ad_rtsp-to-web_version"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "5775ca3dcdf4c1a964c80a487afa26e1",
      "config_subentry_id": null,
      "created_at": 0,
      "device_id": "f6def5ef540e5658b96188d3883ae684",
      "disabled_by": "integration",
      "entity_category": null,
      "entity_id": "sensor.rtsptoweb_webrtc_newest_version",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "47fd581da0f6bbb0a10e3f001041f010",
      "labels": [],
      "modified_at": 0,
      "name": null,
      "options": {
        "conversation": {
          "should_expose": false
        }
      },
      "original_name": "最新版本",
      "platform": "hassio",
      "translation_key": "version_latest",
      "unique_id": "e19319ad_rtsp-to-web_version_latest"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "5775ca3dcdf4c1a964c80a487afa26e1",
      "config_subentry_id": null,
      "created_at": 0,
      "device_id": "f6def5ef540e5658b96188d3883ae684",
      "disabled_by": "integration",
      "entity_category": null,
      "entity_id": "sensor.rtsptoweb_webrtc_cpu_percent",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "1ca2bf50f9751f76b78348d648ec7eba",
      "labels": [],
      "modified_at": 0,
      "name": null,
      "options": {
        "conversation": {
          "should_expose": false
        }
      },
      "original_name": "CPU 百分比",
      "platform": "hassio",
      "translation_key": "cpu_percent",
      "unique_id": "e19319ad_rtsp-to-web_cpu_percent"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "5775ca3dcdf4c1a964c80a487afa26e1",
      "config_subentry_id": null,
      "created_at": 0,
      "device_id": "f6def5ef540e5658b96188d3883ae684",
      "disabled_by": "integration",
      "entity_category": null,
      "entity_id": "sensor.rtsptoweb_webrtc_memory_percent",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "c31fa68f9b6235e6c38bb3187d8f5a56",
      "labels": [],
      "modified_at": 0,
      "name": null,
      "options": {
        "conversation": {
          "should_expose": false
        }
      },
      "original_name": "記憶體百分比",
      "platform": "hassio",
      "translation_key": "memory_percent",
      "unique_id": "e19319ad_rtsp-to-web_memory_percent"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": null,
      "config_subentry_id": null,
      "created_at": 0,
      "device_id": null,
      "disabled_by": null,
      "entity_category": "diagnostic",
      "entity_id": "binary_sensor.remote_ui",
      "has_entity_name": false,
      "hidden_by": null,
      "icon": null,
      "id": "6f28f7e2cd65fa9286e3762fe7f11405",
      "labels": [],
      "modified_at": 0,
      "name": null,
      "options": {
        "conversation": {
          "should_expose": false
        }
      },
      "original_name": "Remote UI",
      "platform": "cloud",
      "translation_key": null,
      "unique_id": "cloud-remote-ui-connectivity"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "5775ca3dcdf4c1a964c80a487afa26e1",
      "config_subentry_id": null,
      "created_at": 0,
      "device_id": "7302c6e904d8f9657463738f8592366d",
      "disabled_by": "integration",
      "entity_category": null,
      "entity_id": "binary_sensor.matter_server_zhi_xing_zhong",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "2d715198792f770f62df81ace4265ef9",
      "labels": [],
      "modified_at": 0,
      "name": null,
      "options": {
        "cloud.google_assistant": {
          "should_expose": false
        },
        "cloud.alexa": {
          "should_expose": false
        },
        "conversation": {
          "should_expose": false
        }
      },
      "original_name": "執行中",
      "platform": "hassio",
      "translation_key": "state",
      "unique_id": "core_matter_server_state"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "5775ca3dcdf4c1a964c80a487afa26e1",
      "config_subentry_id": null,
      "created_at": 0,
      "device_id": "390f2305468bd777732658ad0ccba0d5",
      "disabled_by": "integration",
      "entity_category": null,
      "entity_id": "binary_sensor.esphome_zhi_xing_zhong",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "e3bde9b6abeca8998931bc093a315bc1",
      "labels": [],
      "modified_at": 0,
      "name": null,
      "options": {
        "cloud.google_assistant": {
          "should_expose": false
        },
        "cloud.alexa": {
          "should_expose": false
        },
        "conversation": {
          "should_expose": false
        }
      },
      "original_name": "執行中",
      "platform": "hassio",
      "translation_key": "state",
      "unique_id": "5c53de3b_esphome_state"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "5775ca3dcdf4c1a964c80a487afa26e1",
      "config_subentry_id": null,
      "created_at": 0,
      "device_id": "7302c6e904d8f9657463738f8592366d",
      "disabled_by": "integration",
      "entity_category": null,
      "entity_id": "sensor.matter_server_ban_ben",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "1e7844fd9e954a86c53cc2f45aa0aabc",
      "labels": [],
      "modified_at": 0,
      "name": null,
      "options": {
        "cloud.google_assistant": {
          "should_expose": false
        },
        "cloud.alexa": {
          "should_expose": false
        },
        "conversation": {
          "should_expose": false
        }
      },
      "original_name": "版本",
      "platform": "hassio",
      "translation_key": "version",
      "unique_id": "core_matter_server_version"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "5775ca3dcdf4c1a964c80a487afa26e1",
      "config_subentry_id": null,
      "created_at": 0,
      "device_id": "7302c6e904d8f9657463738f8592366d",
      "disabled_by": "integration",
      "entity_category": null,
      "entity_id": "sensor.matter_server_zui_xin_ban_ben",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "90371830fe5faca492ac52ae59c7c345",
      "labels": [],
      "modified_at": 0,
      "name": null,
      "options": {
        "cloud.google_assistant": {
          "should_expose": false
        },
        "cloud.alexa": {
          "should_expose": false
        },
        "conversation": {
          "should_expose": false
        }
      },
      "original_name": "最新版本",
      "platform": "hassio",
      "translation_key": "version_latest",
      "unique_id": "core_matter_server_version_latest"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "5775ca3dcdf4c1a964c80a487afa26e1",
      "config_subentry_id": null,
      "created_at": 0,
      "device_id": "7302c6e904d8f9657463738f8592366d",
      "disabled_by": "integration",
      "entity_category": null,
      "entity_id": "sensor.matter_server_cpu_bai_fen_bi",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "1c3c3fcdee2d4c8de25ffb5b4a8c33c5",
      "labels": [],
      "modified_at": 0,
      "name": null,
      "options": {
        "cloud.google_assistant": {
          "should_expose": false
        },
        "cloud.alexa": {
          "should_expose": false
        },
        "conversation": {
          "should_expose": false
        }
      },
      "original_name": "CPU 百分比",
      "platform": "hassio",
      "translation_key": "cpu_percent",
      "unique_id": "core_matter_server_cpu_percent"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "5775ca3dcdf4c1a964c80a487afa26e1",
      "config_subentry_id": null,
      "created_at": 0,
      "device_id": "7302c6e904d8f9657463738f8592366d",
      "disabled_by": "integration",
      "entity_category": null,
      "entity_id": "sensor.matter_server_ji_yi_ti_bai_fen_bi",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "089e26b4c160500cc25588d31e6866b3",
      "labels": [],
      "modified_at": 0,
      "name": null,
      "options": {
        "cloud.google_assistant": {
          "should_expose": false
        },
        "cloud.alexa": {
          "should_expose": false
        },
        "conversation": {
          "should_expose": false
        }
      },
      "original_name": "記憶體百分比",
      "platform": "hassio",
      "translation_key": "memory_percent",
      "unique_id": "core_matter_server_memory_percent"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "5775ca3dcdf4c1a964c80a487afa26e1",
      "config_subentry_id": null,
      "created_at": 0,
      "device_id": "390f2305468bd777732658ad0ccba0d5",
      "disabled_by": "integration",
      "entity_category": null,
      "entity_id": "sensor.esphome_ban_ben",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "e08ec078023291be0707460acc3ac085",
      "labels": [],
      "modified_at": 0,
      "name": null,
      "options": {
        "cloud.google_assistant": {
          "should_expose": false
        },
        "cloud.alexa": {
          "should_expose": false
        },
        "conversation": {
          "should_expose": false
        }
      },
      "original_name": "版本",
      "platform": "hassio",
      "translation_key": "version",
      "unique_id": "5c53de3b_esphome_version"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "5775ca3dcdf4c1a964c80a487afa26e1",
      "config_subentry_id": null,
      "created_at": 0,
      "device_id": "390f2305468bd777732658ad0ccba0d5",
      "disabled_by": "integration",
      "entity_category": null,
      "entity_id": "sensor.esphome_zui_xin_ban_ben",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "ecbdb9fbfd4f793a41c78a2b47431f69",
      "labels": [],
      "modified_at": 0,
      "name": null,
      "options": {
        "cloud.google_assistant": {
          "should_expose": false
        },
        "cloud.alexa": {
          "should_expose": false
        },
        "conversation": {
          "should_expose": false
        }
      },
      "original_name": "最新版本",
      "platform": "hassio",
      "translation_key": "version_latest",
      "unique_id": "5c53de3b_esphome_version_latest"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "5775ca3dcdf4c1a964c80a487afa26e1",
      "config_subentry_id": null,
      "created_at": 0,
      "device_id": "390f2305468bd777732658ad0ccba0d5",
      "disabled_by": "integration",
      "entity_category": null,
      "entity_id": "sensor.esphome_cpu_bai_fen_bi",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "9f74526c04e83940cf946c05925554f3",
      "labels": [],
      "modified_at": 0,
      "name": null,
      "options": {
        "cloud.google_assistant": {
          "should_expose": false
        },
        "cloud.alexa": {
          "should_expose": false
        },
        "conversation": {
          "should_expose": false
        }
      },
      "original_name": "CPU 百分比",
      "platform": "hassio",
      "translation_key": "cpu_percent",
      "unique_id": "5c53de3b_esphome_cpu_percent"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "5775ca3dcdf4c1a964c80a487afa26e1",
      "config_subentry_id": null,
      "created_at": 0,
      "device_id": "390f2305468bd777732658ad0ccba0d5",
      "disabled_by": "integration",
      "entity_category": null,
      "entity_id": "sensor.esphome_ji_yi_ti_bai_fen_bi",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "28aa175471e2f6260ee39d36edb6e97c",
      "labels": [],
      "modified_at": 0,
      "name": null,
      "options": {
        "cloud.google_assistant": {
          "should_expose": false
        },
        "cloud.alexa": {
          "should_expose": false
        },
        "conversation": {
          "should_expose": false
        }
      },
      "original_name": "記憶體百分比",
      "platform": "hassio",
      "translation_key": "memory_percent",
      "unique_id": "5c53de3b_esphome_memory_percent"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "5775ca3dcdf4c1a964c80a487afa26e1",
      "config_subentry_id": null,
      "created_at": 0,
      "device_id": "7302c6e904d8f9657463738f8592366d",
      "disabled_by": null,
      "entity_category": "config",
      "entity_id": "update.matter_server_update",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "c63e337eab503a189e7e8b9754019df1",
      "labels": [],
      "modified_at": 1750913679.830534,
      "name": null,
      "options": {
        "cloud.google_assistant": {
          "should_expose": false
        },
        "cloud.alexa": {
          "should_expose": false
        },
        "conversation": {
          "should_expose": false
        }
      },
      "original_name": "更新",
      "platform": "hassio",
      "translation_key": "update",
      "unique_id": "core_matter_server_version_latest"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "5775ca3dcdf4c1a964c80a487afa26e1",
      "config_subentry_id": null,
      "created_at": 0,
      "device_id": "390f2305468bd777732658ad0ccba0d5",
      "disabled_by": null,
      "entity_category": "config",
      "entity_id": "update.esphome_update",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "468e6e3488cbe02c5737788610b55d97",
      "labels": [],
      "modified_at": 1750913679.831256,
      "name": null,
      "options": {
        "cloud.google_assistant": {
          "should_expose": false
        },
        "cloud.alexa": {
          "should_expose": false
        },
        "conversation": {
          "should_expose": false
        }
      },
      "original_name": "更新",
      "platform": "hassio",
      "translation_key": "update",
      "unique_id": "5c53de3b_esphome_version_latest"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "58ce032d896ef65c6e99f2333da9174d",
      "config_subentry_id": null,
      "created_at": 0,
      "device_id": "64312199f691eb8d16885793c03f73fb",
      "disabled_by": "integration",
      "entity_category": "diagnostic",
      "entity_id": "sensor.sun_solar_rising",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "ec37a96ed511268a29e725c52db34cdb",
      "labels": [],
      "modified_at": 0,
      "name": null,
      "options": {
        "conversation": {
          "should_expose": false
        }
      },
      "original_name": "太陽升起",
      "platform": "sun",
      "translation_key": "solar_rising",
      "unique_id": "58ce032d896ef65c6e99f2333da9174d-solar_rising"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "5775ca3dcdf4c1a964c80a487afa26e1",
      "config_subentry_id": null,
      "created_at": 1729576660.638654,
      "device_id": "09d5d4132f621543d7e331375c5b3a70",
      "disabled_by": "integration",
      "entity_category": null,
      "entity_id": "binary_sensor.music_assistant_server_running",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "e616fdd293f6d60ea0fb3fadad53d8b3",
      "labels": [],
      "modified_at": 1729576660.638823,
      "name": null,
      "options": {},
      "original_name": "執行中",
      "platform": "hassio",
      "translation_key": "state",
      "unique_id": "d5369777_music_assistant_state"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "5775ca3dcdf4c1a964c80a487afa26e1",
      "config_subentry_id": null,
      "created_at": 1729576660.677459,
      "device_id": "09d5d4132f621543d7e331375c5b3a70",
      "disabled_by": "integration",
      "entity_category": null,
      "entity_id": "sensor.music_assistant_server_version",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "680e0c53fc5fdd32ea2a71e41d94d39c",
      "labels": [],
      "modified_at": 1729576660.677673,
      "name": null,
      "options": {},
      "original_name": "版本",
      "platform": "hassio",
      "translation_key": "version",
      "unique_id": "d5369777_music_assistant_version"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "5775ca3dcdf4c1a964c80a487afa26e1",
      "config_subentry_id": null,
      "created_at": 1729576660.678271,
      "device_id": "09d5d4132f621543d7e331375c5b3a70",
      "disabled_by": "integration",
      "entity_category": null,
      "entity_id": "sensor.music_assistant_server_newest_version",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "4f5ec4527b8f3fd74fc7910b0fb2cbb7",
      "labels": [],
      "modified_at": 1729576660.678436,
      "name": null,
      "options": {},
      "original_name": "最新版本",
      "platform": "hassio",
      "translation_key": "version_latest",
      "unique_id": "d5369777_music_assistant_version_latest"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "5775ca3dcdf4c1a964c80a487afa26e1",
      "config_subentry_id": null,
      "created_at": 1729576660.678985,
      "device_id": "09d5d4132f621543d7e331375c5b3a70",
      "disabled_by": "integration",
      "entity_category": null,
      "entity_id": "sensor.music_assistant_server_cpu_percent",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "217ae33a195d7b4c43bbfdf9aac0e601",
      "labels": [],
      "modified_at": 1729576660.679112,
      "name": null,
      "options": {},
      "original_name": "CPU 百分比",
      "platform": "hassio",
      "translation_key": "cpu_percent",
      "unique_id": "d5369777_music_assistant_cpu_percent"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "5775ca3dcdf4c1a964c80a487afa26e1",
      "config_subentry_id": null,
      "created_at": 1729576660.67958,
      "device_id": "09d5d4132f621543d7e331375c5b3a70",
      "disabled_by": "integration",
      "entity_category": null,
      "entity_id": "sensor.music_assistant_server_memory_percent",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "04c1bcaff44ab1558f55e364800af60d",
      "labels": [],
      "modified_at": 1729576660.679703,
      "name": null,
      "options": {},
      "original_name": "記憶體百分比",
      "platform": "hassio",
      "translation_key": "memory_percent",
      "unique_id": "d5369777_music_assistant_memory_percent"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "5775ca3dcdf4c1a964c80a487afa26e1",
      "config_subentry_id": null,
      "created_at": 1729576660.706372,
      "device_id": "09d5d4132f621543d7e331375c5b3a70",
      "disabled_by": null,
      "entity_category": "config",
      "entity_id": "update.music_assistant_server_update",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "4f181ba60957bd717b58a49e4e6c5299",
      "labels": [],
      "modified_at": 1750913679.832278,
      "name": null,
      "options": {
        "conversation": {
          "should_expose": false
        }
      },
      "original_name": "更新",
      "platform": "hassio",
      "translation_key": "update",
      "unique_id": "d5369777_music_assistant_version_latest"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "5775ca3dcdf4c1a964c80a487afa26e1",
      "config_subentry_id": null,
      "created_at": 1730696983.910044,
      "device_id": "649fd2d37f0384f5f872bee4f4054397",
      "disabled_by": "integration",
      "entity_category": null,
      "entity_id": "binary_sensor.get_hacs_running",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "cb4583ef4633b8ce88e4610b8947f0c9",
      "labels": [],
      "modified_at": 1730696983.910199,
      "name": null,
      "options": {},
      "original_name": "執行中",
      "platform": "hassio",
      "translation_key": "state",
      "unique_id": "cb646a50_get_state"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "5775ca3dcdf4c1a964c80a487afa26e1",
      "config_subentry_id": null,
      "created_at": 1730696983.923705,
      "device_id": "649fd2d37f0384f5f872bee4f4054397",
      "disabled_by": "integration",
      "entity_category": null,
      "entity_id": "sensor.get_hacs_version",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "0368d03a6e7bc48d433e2f466b616871",
      "labels": [],
      "modified_at": 1730696983.927856,
      "name": null,
      "options": {},
      "original_name": "版本",
      "platform": "hassio",
      "translation_key": "version",
      "unique_id": "cb646a50_get_version"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "5775ca3dcdf4c1a964c80a487afa26e1",
      "config_subentry_id": null,
      "created_at": 1730696983.928387,
      "device_id": "649fd2d37f0384f5f872bee4f4054397",
      "disabled_by": "integration",
      "entity_category": null,
      "entity_id": "sensor.get_hacs_newest_version",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "7f8361a8ee90faa52e25b50557121cdf",
      "labels": [],
      "modified_at": 1730696983.928529,
      "name": null,
      "options": {},
      "original_name": "最新版本",
      "platform": "hassio",
      "translation_key": "version_latest",
      "unique_id": "cb646a50_get_version_latest"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "5775ca3dcdf4c1a964c80a487afa26e1",
      "config_subentry_id": null,
      "created_at": 1730696983.928999,
      "device_id": "649fd2d37f0384f5f872bee4f4054397",
      "disabled_by": "integration",
      "entity_category": null,
      "entity_id": "sensor.get_hacs_cpu_percent",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "1ef4a4d5aa47b6ed685924dc77e07ea7",
      "labels": [],
      "modified_at": 1730696983.929121,
      "name": null,
      "options": {},
      "original_name": "CPU 百分比",
      "platform": "hassio",
      "translation_key": "cpu_percent",
      "unique_id": "cb646a50_get_cpu_percent"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "5775ca3dcdf4c1a964c80a487afa26e1",
      "config_subentry_id": null,
      "created_at": 1730696983.929507,
      "device_id": "649fd2d37f0384f5f872bee4f4054397",
      "disabled_by": "integration",
      "entity_category": null,
      "entity_id": "sensor.get_hacs_memory_percent",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "b0f164fab9636fed6a5214320dde8241",
      "labels": [],
      "modified_at": 1730696983.929676,
      "name": null,
      "options": {},
      "original_name": "記憶體百分比",
      "platform": "hassio",
      "translation_key": "memory_percent",
      "unique_id": "cb646a50_get_memory_percent"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "5775ca3dcdf4c1a964c80a487afa26e1",
      "config_subentry_id": null,
      "created_at": 1730696983.950027,
      "device_id": "649fd2d37f0384f5f872bee4f4054397",
      "disabled_by": null,
      "entity_category": "config",
      "entity_id": "update.get_hacs_update",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "13a943d3772bd2d4f2b601b18c37dce5",
      "labels": [],
      "modified_at": 1750913679.832662,
      "name": null,
      "options": {
        "conversation": {
          "should_expose": false
        }
      },
      "original_name": "更新",
      "platform": "hassio",
      "translation_key": "update",
      "unique_id": "cb646a50_get_version_latest"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "01JYN9DHD2RXAJMHEFC8KMCMZJ",
      "config_subentry_id": null,
      "created_at": 1750913698.0388,
      "device_id": "5cee94d4039563a67b132e01fef57bb2",
      "disabled_by": null,
      "entity_category": null,
      "entity_id": "event.backup_automatic_backup",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "a8a014542062fcc1a35402ebd9c89f6f",
      "labels": [],
      "modified_at": 1750913698.039295,
      "name": null,
      "options": {
        "conversation": {
          "should_expose": false
        }
      },
      "original_name": "自動備份",
      "platform": "backup",
      "translation_key": "automatic_backup_event",
      "unique_id": "automatic_backup_event"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "01JYN9DHD2RXAJMHEFC8KMCMZJ",
      "config_subentry_id": null,
      "created_at": 1750913698.04022,
      "device_id": "5cee94d4039563a67b132e01fef57bb2",
      "disabled_by": null,
      "entity_category": null,
      "entity_id": "sensor.backup_backup_manager_state",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "ea42483a63c4361c07ec657ccf75c4cd",
      "labels": [],
      "modified_at": 1750913698.040662,
      "name": null,
      "options": {
        "conversation": {
          "should_expose": false
        }
      },
      "original_name": "備份管理器狀態",
      "platform": "backup",
      "translation_key": "backup_manager_state",
      "unique_id": "backup_manager_state"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "01JYN9DHD2RXAJMHEFC8KMCMZJ",
      "config_subentry_id": null,
      "created_at": 1750913698.041088,
      "device_id": "5cee94d4039563a67b132e01fef57bb2",
      "disabled_by": null,
      "entity_category": null,
      "entity_id": "sensor.backup_next_scheduled_automatic_backup",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "ce29c0a6cc24bcf01fce5e9ce84eaa20",
      "labels": [],
      "modified_at": 1750913698.041424,
      "name": null,
      "options": {
        "conversation": {
          "should_expose": false
        }
      },
      "original_name": "下次排程的自動備份",
      "platform": "backup",
      "translation_key": "next_scheduled_automatic_backup",
      "unique_id": "next_scheduled_automatic_backup"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "01JYN9DHD2RXAJMHEFC8KMCMZJ",
      "config_subentry_id": null,
      "created_at": 1750913698.041806,
      "device_id": "5cee94d4039563a67b132e01fef57bb2",
      "disabled_by": null,
      "entity_category": null,
      "entity_id": "sensor.backup_last_successful_automatic_backup",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "199b75a96a40b3d8ffba8844e823ee4f",
      "labels": [],
      "modified_at": 1750913698.04213,
      "name": null,
      "options": {
        "conversation": {
          "should_expose": false
        }
      },
      "original_name": "上次成功的自動備份",
      "platform": "backup",
      "translation_key": "last_successful_automatic_backup",
      "unique_id": "last_successful_automatic_backup"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "01JYN9DHD2RXAJMHEFC8KMCMZJ",
      "config_subentry_id": null,
      "created_at": 1750913698.042531,
      "device_id": "5cee94d4039563a67b132e01fef57bb2",
      "disabled_by": null,
      "entity_category": null,
      "entity_id": "sensor.backup_last_attempted_automatic_backup",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "d0e54bd27b8580bb95fcb1cb3eb03903",
      "labels": [],
      "modified_at": 1750913698.044364,
      "name": null,
      "options": {
        "conversation": {
          "should_expose": false
        }
      },
      "original_name": "上次嘗試自動備份",
      "platform": "backup",
      "translation_key": "last_attempted_automatic_backup",
      "unique_id": "last_attempted_automatic_backup"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "5775ca3dcdf4c1a964c80a487afa26e1",
      "config_subentry_id": null,
      "created_at": 1757845096.245601,
      "device_id": "4b8062fc603d1dc70e9016a98376b951",
      "disabled_by": "integration",
      "entity_category": null,
      "entity_id": "binary_sensor.immich_running",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "e61b480dd630656080f6fa67af6db5f2",
      "labels": [],
      "modified_at": 1757845096.245759,
      "name": null,
      "options": {},
      "original_name": "執行中",
      "platform": "hassio",
      "translation_key": "state",
      "unique_id": "db21ed7f_immich_state"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "5775ca3dcdf4c1a964c80a487afa26e1",
      "config_subentry_id": null,
      "created_at": 1757845096.25181,
      "device_id": "4b8062fc603d1dc70e9016a98376b951",
      "disabled_by": "integration",
      "entity_category": null,
      "entity_id": "sensor.immich_version",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "5015ec1135bc8194c598abb7a5bbb253",
      "labels": [],
      "modified_at": 1757845096.251918,
      "name": null,
      "options": {},
      "original_name": "版本",
      "platform": "hassio",
      "translation_key": "version",
      "unique_id": "db21ed7f_immich_version"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "5775ca3dcdf4c1a964c80a487afa26e1",
      "config_subentry_id": null,
      "created_at": 1757845096.252162,
      "device_id": "4b8062fc603d1dc70e9016a98376b951",
      "disabled_by": "integration",
      "entity_category": null,
      "entity_id": "sensor.immich_newest_version",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "8242b0f3f23d8658cdd6693e1dc14c79",
      "labels": [],
      "modified_at": 1757845096.252225,
      "name": null,
      "options": {},
      "original_name": "最新版本",
      "platform": "hassio",
      "translation_key": "version_latest",
      "unique_id": "db21ed7f_immich_version_latest"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "5775ca3dcdf4c1a964c80a487afa26e1",
      "config_subentry_id": null,
      "created_at": 1757845096.252388,
      "device_id": "4b8062fc603d1dc70e9016a98376b951",
      "disabled_by": "integration",
      "entity_category": null,
      "entity_id": "sensor.immich_cpu_percent",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "89e6ec6a6bb6d5cb890e50a0b434fe0f",
      "labels": [],
      "modified_at": 1757845096.252442,
      "name": null,
      "options": {},
      "original_name": "CPU 百分比",
      "platform": "hassio",
      "translation_key": "cpu_percent",
      "unique_id": "db21ed7f_immich_cpu_percent"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "5775ca3dcdf4c1a964c80a487afa26e1",
      "config_subentry_id": null,
      "created_at": 1757845096.252599,
      "device_id": "4b8062fc603d1dc70e9016a98376b951",
      "disabled_by": "integration",
      "entity_category": null,
      "entity_id": "sensor.immich_memory_percent",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "3b8d7cdce838b26b16eecada32b68b94",
      "labels": [],
      "modified_at": 1757845096.252652,
      "name": null,
      "options": {},
      "original_name": "記憶體百分比",
      "platform": "hassio",
      "translation_key": "memory_percent",
      "unique_id": "db21ed7f_immich_memory_percent"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "5775ca3dcdf4c1a964c80a487afa26e1",
      "config_subentry_id": null,
      "created_at": 1757845096.259068,
      "device_id": "4b8062fc603d1dc70e9016a98376b951",
      "disabled_by": null,
      "entity_category": "config",
      "entity_id": "update.immich_update",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "af4e2641a42cce84dace46ca561f0dec",
      "labels": [],
      "modified_at": 1757845096.259414,
      "name": null,
      "options": {
        "conversation": {
          "should_expose": false
        }
      },
      "original_name": "更新",
      "platform": "hassio",
      "translation_key": "update",
      "unique_id": "db21ed7f_immich_version_latest"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "5775ca3dcdf4c1a964c80a487afa26e1",
      "config_subentry_id": null,
      "created_at": 1757867596.338881,
      "device_id": "fdc23e23cef71d4d157759c860fbb289",
      "disabled_by": "integration",
      "entity_category": null,
      "entity_id": "binary_sensor.hassos_ssh_port_22222_configurator_running",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "6710a65aec616cd18e0d6a319f3c4fd8",
      "labels": [],
      "modified_at": 1757867596.339005,
      "name": null,
      "options": {},
      "original_name": "執行中",
      "platform": "hassio",
      "translation_key": "state",
      "unique_id": "efd493c6_hassos_ssh_configurator_addon_state"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "5775ca3dcdf4c1a964c80a487afa26e1",
      "config_subentry_id": null,
      "created_at": 1757867596.344247,
      "device_id": "fdc23e23cef71d4d157759c860fbb289",
      "disabled_by": "integration",
      "entity_category": null,
      "entity_id": "sensor.hassos_ssh_port_22222_configurator_version",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "dcd256cfa6697fd122e616623c7020ea",
      "labels": [],
      "modified_at": 1757867596.344878,
      "name": null,
      "options": {},
      "original_name": "版本",
      "platform": "hassio",
      "translation_key": "version",
      "unique_id": "efd493c6_hassos_ssh_configurator_addon_version"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "5775ca3dcdf4c1a964c80a487afa26e1",
      "config_subentry_id": null,
      "created_at": 1757867596.345139,
      "device_id": "fdc23e23cef71d4d157759c860fbb289",
      "disabled_by": "integration",
      "entity_category": null,
      "entity_id": "sensor.hassos_ssh_port_22222_configurator_newest_version",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "10d64ae856faca5e6636868a7f859a32",
      "labels": [],
      "modified_at": 1757867596.345215,
      "name": null,
      "options": {},
      "original_name": "最新版本",
      "platform": "hassio",
      "translation_key": "version_latest",
      "unique_id": "efd493c6_hassos_ssh_configurator_addon_version_latest"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "5775ca3dcdf4c1a964c80a487afa26e1",
      "config_subentry_id": null,
      "created_at": 1757867596.345386,
      "device_id": "fdc23e23cef71d4d157759c860fbb289",
      "disabled_by": "integration",
      "entity_category": null,
      "entity_id": "sensor.hassos_ssh_port_22222_configurator_cpu_percent",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "15888a0d9037a0fed4af82757a0591f1",
      "labels": [],
      "modified_at": 1757867596.34545,
      "name": null,
      "options": {},
      "original_name": "CPU 百分比",
      "platform": "hassio",
      "translation_key": "cpu_percent",
      "unique_id": "efd493c6_hassos_ssh_configurator_addon_cpu_percent"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "5775ca3dcdf4c1a964c80a487afa26e1",
      "config_subentry_id": null,
      "created_at": 1757867596.345612,
      "device_id": "fdc23e23cef71d4d157759c860fbb289",
      "disabled_by": "integration",
      "entity_category": null,
      "entity_id": "sensor.hassos_ssh_port_22222_configurator_memory_percent",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "a8b3b7a36294a533b2f875d8b38901c6",
      "labels": [],
      "modified_at": 1757867596.345687,
      "name": null,
      "options": {},
      "original_name": "記憶體百分比",
      "platform": "hassio",
      "translation_key": "memory_percent",
      "unique_id": "efd493c6_hassos_ssh_configurator_addon_memory_percent"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "5775ca3dcdf4c1a964c80a487afa26e1",
      "config_subentry_id": null,
      "created_at": 1757867596.352341,
      "device_id": "fdc23e23cef71d4d157759c860fbb289",
      "disabled_by": null,
      "entity_category": "config",
      "entity_id": "update.hassos_ssh_port_22222_configurator_update",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "ca41c968b07b919675689abba8a1a34f",
      "labels": [],
      "modified_at": 1757867596.352694,
      "name": null,
      "options": {
        "conversation": {
          "should_expose": false
        }
      },
      "original_name": "更新",
      "platform": "hassio",
      "translation_key": "update",
      "unique_id": "efd493c6_hassos_ssh_configurator_addon_version_latest"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "5775ca3dcdf4c1a964c80a487afa26e1",
      "config_subentry_id": null,
      "created_at": 1757866396.29867,
      "device_id": "c84072114c6d78517313f70497aefc0c",
      "disabled_by": "integration",
      "entity_category": null,
      "entity_id": "binary_sensor.timescaledb_running",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "411f1140f404bf19af4f3a08ac6bfde9",
      "labels": [],
      "modified_at": 1758031346.101438,
      "name": null,
      "options": {},
      "original_name": "執行中",
      "platform": "hassio",
      "translation_key": "state",
      "unique_id": "80e8e4d2_timescaledb_state"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "5775ca3dcdf4c1a964c80a487afa26e1",
      "config_subentry_id": null,
      "created_at": 1757866396.303435,
      "device_id": "c84072114c6d78517313f70497aefc0c",
      "disabled_by": "integration",
      "entity_category": null,
      "entity_id": "sensor.timescaledb_version",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "c63c6a0e307ce7e404aa5a162a49ce34",
      "labels": [],
      "modified_at": 1758031346.106416,
      "name": null,
      "options": {},
      "original_name": "版本",
      "platform": "hassio",
      "translation_key": "version",
      "unique_id": "80e8e4d2_timescaledb_version"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "5775ca3dcdf4c1a964c80a487afa26e1",
      "config_subentry_id": null,
      "created_at": 1757866396.303786,
      "device_id": "c84072114c6d78517313f70497aefc0c",
      "disabled_by": "integration",
      "entity_category": null,
      "entity_id": "sensor.timescaledb_newest_version",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "c033f1cf7c50c4b19cf08cf5f7cf6e2e",
      "labels": [],
      "modified_at": 1758031346.107045,
      "name": null,
      "options": {},
      "original_name": "最新版本",
      "platform": "hassio",
      "translation_key": "version_latest",
      "unique_id": "80e8e4d2_timescaledb_version_latest"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "5775ca3dcdf4c1a964c80a487afa26e1",
      "config_subentry_id": null,
      "created_at": 1757866396.304028,
      "device_id": "c84072114c6d78517313f70497aefc0c",
      "disabled_by": "integration",
      "entity_category": null,
      "entity_id": "sensor.timescaledb_cpu_percent",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "7d5de24a3925ab4c26436335db2b64e6",
      "labels": [],
      "modified_at": 1758031346.107329,
      "name": null,
      "options": {},
      "original_name": "CPU 百分比",
      "platform": "hassio",
      "translation_key": "cpu_percent",
      "unique_id": "80e8e4d2_timescaledb_cpu_percent"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "5775ca3dcdf4c1a964c80a487afa26e1",
      "config_subentry_id": null,
      "created_at": 1757866396.304845,
      "device_id": "c84072114c6d78517313f70497aefc0c",
      "disabled_by": "integration",
      "entity_category": null,
      "entity_id": "sensor.timescaledb_memory_percent",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "ca7c2254d3aa83475f873354480f8508",
      "labels": [],
      "modified_at": 1758031346.107553,
      "name": null,
      "options": {},
      "original_name": "記憶體百分比",
      "platform": "hassio",
      "translation_key": "memory_percent",
      "unique_id": "80e8e4d2_timescaledb_memory_percent"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "5775ca3dcdf4c1a964c80a487afa26e1",
      "config_subentry_id": null,
      "created_at": 1757866396.311249,
      "device_id": "c84072114c6d78517313f70497aefc0c",
      "disabled_by": null,
      "entity_category": "config",
      "entity_id": "update.timescaledb_update",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "d2d8f02ca400fafee076b01c400eb21f",
      "labels": [],
      "modified_at": 1758031346.115985,
      "name": null,
      "options": {
        "conversation": {
          "should_expose": false
        }
      },
      "original_name": "更新",
      "platform": "hassio",
      "translation_key": "update",
      "unique_id": "80e8e4d2_timescaledb_version_latest"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "5775ca3dcdf4c1a964c80a487afa26e1",
      "config_subentry_id": null,
      "created_at": 1753413147.943076,
      "device_id": "ff04ee634979593a989e9ae0b26ea223",
      "disabled_by": "integration",
      "entity_category": null,
      "entity_id": "binary_sensor.timescaledb_running_2",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "91964d74e7444588da359c88c02c13a1",
      "labels": [],
      "modified_at": 1758188546.096632,
      "name": null,
      "options": {},
      "original_name": "執行中",
      "platform": "hassio",
      "translation_key": "state",
      "unique_id": "77b2833f_timescaledb_state"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "5775ca3dcdf4c1a964c80a487afa26e1",
      "config_subentry_id": null,
      "created_at": 1753413147.94978,
      "device_id": "ff04ee634979593a989e9ae0b26ea223",
      "disabled_by": "integration",
      "entity_category": null,
      "entity_id": "sensor.timescaledb_version_2",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "156e06300b0ad0f2491da6ffb5b87e09",
      "labels": [],
      "modified_at": 1758188546.10317,
      "name": null,
      "options": {},
      "original_name": "版本",
      "platform": "hassio",
      "translation_key": "version",
      "unique_id": "77b2833f_timescaledb_version"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "5775ca3dcdf4c1a964c80a487afa26e1",
      "config_subentry_id": null,
      "created_at": 1753413147.950312,
      "device_id": "ff04ee634979593a989e9ae0b26ea223",
      "disabled_by": "integration",
      "entity_category": null,
      "entity_id": "sensor.timescaledb_newest_version_2",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "39871c166f7d3f4ed69fa819a500a66b",
      "labels": [],
      "modified_at": 1758188546.103499,
      "name": null,
      "options": {},
      "original_name": "最新版本",
      "platform": "hassio",
      "translation_key": "version_latest",
      "unique_id": "77b2833f_timescaledb_version_latest"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "5775ca3dcdf4c1a964c80a487afa26e1",
      "config_subentry_id": null,
      "created_at": 1753413147.950641,
      "device_id": "ff04ee634979593a989e9ae0b26ea223",
      "disabled_by": "integration",
      "entity_category": null,
      "entity_id": "sensor.timescaledb_cpu_percent_2",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "e29090acaddd372843334abd9e938278",
      "labels": [],
      "modified_at": 1758188546.103746,
      "name": null,
      "options": {},
      "original_name": "CPU 百分比",
      "platform": "hassio",
      "translation_key": "cpu_percent",
      "unique_id": "77b2833f_timescaledb_cpu_percent"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "5775ca3dcdf4c1a964c80a487afa26e1",
      "config_subentry_id": null,
      "created_at": 1753413147.950872,
      "device_id": "ff04ee634979593a989e9ae0b26ea223",
      "disabled_by": "integration",
      "entity_category": null,
      "entity_id": "sensor.timescaledb_memory_percent_2",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "f614fcabcfb40b85c7d89592e9edda79",
      "labels": [],
      "modified_at": 1758188546.103998,
      "name": null,
      "options": {},
      "original_name": "記憶體百分比",
      "platform": "hassio",
      "translation_key": "memory_percent",
      "unique_id": "77b2833f_timescaledb_memory_percent"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "5775ca3dcdf4c1a964c80a487afa26e1",
      "config_subentry_id": null,
      "created_at": 1753413147.960291,
      "device_id": "ff04ee634979593a989e9ae0b26ea223",
      "disabled_by": null,
      "entity_category": "config",
      "entity_id": "update.timescaledb_update_2",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "863b9508631c09b244fd2f943081334c",
      "labels": [],
      "modified_at": 1758188546.111759,
      "name": null,
      "options": {
        "conversation": {
          "should_expose": false
        }
      },
      "original_name": "更新",
      "platform": "hassio",
      "translation_key": "update",
      "unique_id": "77b2833f_timescaledb_version_latest"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "5775ca3dcdf4c1a964c80a487afa26e1",
      "config_subentry_id": null,
      "created_at": 1753412847.884453,
      "device_id": "a6ce7f55bb2f17fc2cdf4da205828443",
      "disabled_by": "integration",
      "entity_category": null,
      "entity_id": "binary_sensor.pgadmin4_running",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "0b4490e6e466193f7e66bef0a172d62f",
      "labels": [],
      "modified_at": 1758188846.031394,
      "name": null,
      "options": {},
      "original_name": "執行中",
      "platform": "hassio",
      "translation_key": "state",
      "unique_id": "77b2833f_pgadmin4_state"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "5775ca3dcdf4c1a964c80a487afa26e1",
      "config_subentry_id": null,
      "created_at": 1753412847.892354,
      "device_id": "a6ce7f55bb2f17fc2cdf4da205828443",
      "disabled_by": "integration",
      "entity_category": null,
      "entity_id": "sensor.pgadmin4_version",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "5591dbfbf57ec2f86a567303a2972d34",
      "labels": [],
      "modified_at": 1758188846.03756,
      "name": null,
      "options": {},
      "original_name": "版本",
      "platform": "hassio",
      "translation_key": "version",
      "unique_id": "77b2833f_pgadmin4_version"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "5775ca3dcdf4c1a964c80a487afa26e1",
      "config_subentry_id": null,
      "created_at": 1753412847.892841,
      "device_id": "a6ce7f55bb2f17fc2cdf4da205828443",
      "disabled_by": "integration",
      "entity_category": null,
      "entity_id": "sensor.pgadmin4_newest_version",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "c476b374747ef5a69ac2b88d25561d29",
      "labels": [],
      "modified_at": 1758188846.037899,
      "name": null,
      "options": {},
      "original_name": "最新版本",
      "platform": "hassio",
      "translation_key": "version_latest",
      "unique_id": "77b2833f_pgadmin4_version_latest"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "5775ca3dcdf4c1a964c80a487afa26e1",
      "config_subentry_id": null,
      "created_at": 1753412847.893229,
      "device_id": "a6ce7f55bb2f17fc2cdf4da205828443",
      "disabled_by": "integration",
      "entity_category": null,
      "entity_id": "sensor.pgadmin4_cpu_percent",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "9e6e2b9438802c1cb022f271abba33a8",
      "labels": [],
      "modified_at": 1758188846.038123,
      "name": null,
      "options": {},
      "original_name": "CPU 百分比",
      "platform": "hassio",
      "translation_key": "cpu_percent",
      "unique_id": "77b2833f_pgadmin4_cpu_percent"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "5775ca3dcdf4c1a964c80a487afa26e1",
      "config_subentry_id": null,
      "created_at": 1753412847.893593,
      "device_id": "a6ce7f55bb2f17fc2cdf4da205828443",
      "disabled_by": "integration",
      "entity_category": null,
      "entity_id": "sensor.pgadmin4_memory_percent",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "110fc7b5d5a150b0689ea3781d82dd7e",
      "labels": [],
      "modified_at": 1758188846.038336,
      "name": null,
      "options": {},
      "original_name": "記憶體百分比",
      "platform": "hassio",
      "translation_key": "memory_percent",
      "unique_id": "77b2833f_pgadmin4_memory_percent"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "5775ca3dcdf4c1a964c80a487afa26e1",
      "config_subentry_id": null,
      "created_at": 1753412847.902281,
      "device_id": "a6ce7f55bb2f17fc2cdf4da205828443",
      "disabled_by": null,
      "entity_category": "config",
      "entity_id": "update.pgadmin4_update",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "26c1f8f6f9a5077e04e7318ee00f9036",
      "labels": [],
      "modified_at": 1758188846.045661,
      "name": null,
      "options": {
        "conversation": {
          "should_expose": false
        }
      },
      "original_name": "更新",
      "platform": "hassio",
      "translation_key": "update",
      "unique_id": "77b2833f_pgadmin4_version_latest"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "5775ca3dcdf4c1a964c80a487afa26e1",
      "config_subentry_id": null,
      "created_at": 1758383246.322155,
      "device_id": "ff799dda80040d874de8105fcd73c6b4",
      "disabled_by": "integration",
      "entity_category": null,
      "entity_id": "binary_sensor.cloudflared_running",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "dc706c793485b006886469410b9fe8b9",
      "labels": [],
      "modified_at": 1758383246.322269,
      "name": null,
      "options": {},
      "original_name": "執行中",
      "platform": "hassio",
      "translation_key": "state",
      "unique_id": "9074a9fa_cloudflared_state"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "5775ca3dcdf4c1a964c80a487afa26e1",
      "config_subentry_id": null,
      "created_at": 1758383246.328793,
      "device_id": "ff799dda80040d874de8105fcd73c6b4",
      "disabled_by": "integration",
      "entity_category": null,
      "entity_id": "sensor.cloudflared_version",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "fb9fd8acb1706d93ad5a446f923dee5d",
      "labels": [],
      "modified_at": 1758383246.328881,
      "name": null,
      "options": {},
      "original_name": "版本",
      "platform": "hassio",
      "translation_key": "version",
      "unique_id": "9074a9fa_cloudflared_version"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "5775ca3dcdf4c1a964c80a487afa26e1",
      "config_subentry_id": null,
      "created_at": 1758383246.329102,
      "device_id": "ff799dda80040d874de8105fcd73c6b4",
      "disabled_by": "integration",
      "entity_category": null,
      "entity_id": "sensor.cloudflared_newest_version",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "cc91de56bb5fde58fe35079c74e223ac",
      "labels": [],
      "modified_at": 1758383246.329168,
      "name": null,
      "options": {},
      "original_name": "最新版本",
      "platform": "hassio",
      "translation_key": "version_latest",
      "unique_id": "9074a9fa_cloudflared_version_latest"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "5775ca3dcdf4c1a964c80a487afa26e1",
      "config_subentry_id": null,
      "created_at": 1758383246.329329,
      "device_id": "ff799dda80040d874de8105fcd73c6b4",
      "disabled_by": "integration",
      "entity_category": null,
      "entity_id": "sensor.cloudflared_cpu_percent",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "cda1e3e8fa0348f974fe959ae59ac7df",
      "labels": [],
      "modified_at": 1758383246.329383,
      "name": null,
      "options": {},
      "original_name": "CPU 百分比",
      "platform": "hassio",
      "translation_key": "cpu_percent",
      "unique_id": "9074a9fa_cloudflared_cpu_percent"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "5775ca3dcdf4c1a964c80a487afa26e1",
      "config_subentry_id": null,
      "created_at": 1758383246.329539,
      "device_id": "ff799dda80040d874de8105fcd73c6b4",
      "disabled_by": "integration",
      "entity_category": null,
      "entity_id": "sensor.cloudflared_memory_percent",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "4b58b070f90f2fd6958a03e7915cb38d",
      "labels": [],
      "modified_at": 1758383246.329595,
      "name": null,
      "options": {},
      "original_name": "記憶體百分比",
      "platform": "hassio",
      "translation_key": "memory_percent",
      "unique_id": "9074a9fa_cloudflared_memory_percent"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "5775ca3dcdf4c1a964c80a487afa26e1",
      "config_subentry_id": null,
      "created_at": 1758383246.336797,
      "device_id": "ff799dda80040d874de8105fcd73c6b4",
      "disabled_by": null,
      "entity_category": "config",
      "entity_id": "update.cloudflared_update",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "642be010d224b453fa39a3363172d643",
      "labels": [],
      "modified_at": 1758383246.337123,
      "name": null,
      "options": {
        "conversation": {
          "should_expose": false
        }
      },
      "original_name": "更新",
      "platform": "hassio",
      "translation_key": "update",
      "unique_id": "9074a9fa_cloudflared_version_latest"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "01K5TQ0GNBV50K6G7V5F23K6M3",
      "config_subentry_id": null,
      "created_at": 1758611915.559237,
      "device_id": "5eaef03dd163151dcf3be4d5d411c793",
      "disabled_by": "integration",
      "entity_category": "diagnostic",
      "entity_id": "switch.hacs_pre_release",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "654c0f8738b201bea2e63d13fa46fc09",
      "labels": [],
      "modified_at": 1758611915.559339,
      "name": null,
      "options": {},
      "original_name": "Pre-release",
      "platform": "hacs",
      "translation_key": "pre-release",
      "unique_id": "172733314"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "01K5TQ0GNBV50K6G7V5F23K6M3",
      "config_subentry_id": null,
      "created_at": 1758611915.559872,
      "device_id": "aee354f93c5ce41fff255d6642bc3dc1",
      "disabled_by": "integration",
      "entity_category": "diagnostic",
      "entity_id": "switch.mushroom_pre_release",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "3618ba152cb2c67ba0390ac43cf9dc14",
      "labels": [],
      "modified_at": 1758611915.559936,
      "name": null,
      "options": {},
      "original_name": "Pre-release",
      "platform": "hacs",
      "translation_key": "pre-release",
      "unique_id": "444350375"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "01K5TQ0GNBV50K6G7V5F23K6M3",
      "config_subentry_id": null,
      "created_at": 1758611915.56029,
      "device_id": "94e9e2a8bc2a1eed9734e91c8ca1c2ce",
      "disabled_by": "integration",
      "entity_category": "diagnostic",
      "entity_id": "switch.art_net_led_lighting_for_dmx_pre_release",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "d360d34f7375c3f58180cd2190ea0ae6",
      "labels": [],
      "modified_at": 1758611915.560351,
      "name": null,
      "options": {},
      "original_name": "Pre-release",
      "platform": "hacs",
      "translation_key": "pre-release",
      "unique_id": "400558791"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "01K5TQ0GNBV50K6G7V5F23K6M3",
      "config_subentry_id": null,
      "created_at": 1758611915.5616,
      "device_id": "5eaef03dd163151dcf3be4d5d411c793",
      "disabled_by": null,
      "entity_category": "config",
      "entity_id": "update.hacs_update",
      "has_entity_name": false,
      "hidden_by": null,
      "icon": null,
      "id": "a7b82f3ebd8d5a6a9e2d55593f68e6d4",
      "labels": [],
      "modified_at": 1758611915.562266,
      "name": null,
      "options": {
        "conversation": {
          "should_expose": false
        }
      },
      "original_name": "HACS update",
      "platform": "hacs",
      "translation_key": null,
      "unique_id": "172733314"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "01K5TQ0GNBV50K6G7V5F23K6M3",
      "config_subentry_id": null,
      "created_at": 1758611915.562718,
      "device_id": "aee354f93c5ce41fff255d6642bc3dc1",
      "disabled_by": null,
      "entity_category": "config",
      "entity_id": "update.mushroom_update",
      "has_entity_name": false,
      "hidden_by": null,
      "icon": null,
      "id": "e7d04f8e14b354c0ff65616ec9f57126",
      "labels": [],
      "modified_at": 1758611915.563136,
      "name": null,
      "options": {
        "conversation": {
          "should_expose": false
        }
      },
      "original_name": "Mushroom update",
      "platform": "hacs",
      "translation_key": null,
      "unique_id": "444350375"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "01K5TQ0GNBV50K6G7V5F23K6M3",
      "config_subentry_id": null,
      "created_at": 1758611915.563516,
      "device_id": "94e9e2a8bc2a1eed9734e91c8ca1c2ce",
      "disabled_by": null,
      "entity_category": "config",
      "entity_id": "update.art_net_led_lighting_for_dmx_update",
      "has_entity_name": false,
      "hidden_by": null,
      "icon": null,
      "id": "8afaafc86aa2581077c8cea1402254ce",
      "labels": [],
      "modified_at": 1758611915.563808,
      "name": null,
      "options": {
        "conversation": {
          "should_expose": false
        }
      },
      "original_name": "Art-net LED Lighting for DMX update",
      "platform": "hacs",
      "translation_key": null,
      "unique_id": "400558791"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "01K5TQ0GNBV50K6G7V5F23K6M3",
      "config_subentry_id": null,
      "created_at": 1758611979.962844,
      "device_id": "ab66b5233688a0d77bb694c85915e48b",
      "disabled_by": null,
      "entity_category": "config",
      "entity_id": "update.virtual_components_update",
      "has_entity_name": false,
      "hidden_by": null,
      "icon": null,
      "id": "c800daa1850ff17964806cc2ea17b336",
      "labels": [],
      "modified_at": 1758611979.963274,
      "name": null,
      "options": {
        "conversation": {
          "should_expose": false
        }
      },
      "original_name": "Virtual Components update",
      "platform": "hacs",
      "translation_key": null,
      "unique_id": "245267534"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "01K5TQF9Q0CAPR3G1NA8V7REGR",
      "config_subentry_id": null,
      "created_at": 1758612508.333761,
      "device_id": "7fd3f673905464e78f3e4a9dc9b801e9",
      "disabled_by": null,
      "entity_category": null,
      "entity_id": "binary_sensor.living_room_motion",
      "has_entity_name": false,
      "hidden_by": null,
      "icon": null,
      "id": "6d750e48f3b00bf73af2cf466f05df49",
      "labels": [],
      "modified_at": 1758612508.334522,
      "name": null,
      "options": {
        "conversation": {
          "should_expose": true
        }
      },
      "original_name": "Living Room Motion",
      "platform": "virtual",
      "translation_key": null,
      "unique_id": "3e4ca030-1c64-4ad3-a4da-dbf802fabf07.virtual"
    },
    {
      "area_id": "wo_shi",
      "categories": {},
      "config_entry_id": "01K5TQF9Q0CAPR3G1NA8V7REGR",
      "config_subentry_id": null,
      "created_at": 1758612508.334914,
      "device_id": "1d9bec0c5140bcf348c3bbbe3640dc2d",
      "disabled_by": null,
      "entity_category": null,
      "entity_id": "binary_sensor.back_door",
      "has_entity_name": false,
      "hidden_by": null,
      "icon": null,
      "id": "f458925574823157d0a85f7ddaf9a21c",
      "labels": [],
      "modified_at": 1761625090.226993,
      "name": null,
      "options": {
        "conversation": {
          "should_expose": true
        }
      },
      "original_name": "Back Door",
      "platform": "virtual",
      "translation_key": null,
      "unique_id": "36fa4d1b-3345-403f-9448-afb99833a6f5.virtual"
    },
    {
      "area_id": "wo_shi",
      "categories": {},
      "config_entry_id": "01K5TQF9Q0CAPR3G1NA8V7REGR",
      "config_subentry_id": null,
      "created_at": 1758612508.336383,
      "device_id": "54a431a2d33152a6c8ad78c9077a60b3",
      "disabled_by": null,
      "entity_category": null,
      "entity_id": "cover.test_cover_cover",
      "has_entity_name": false,
      "hidden_by": null,
      "icon": null,
      "id": "ee8f068197acf237b7d54f3cf619e28a",
      "labels": [],
      "modified_at": 1761625133.160492,
      "name": null,
      "options": {
        "conversation": {
          "should_expose": true
        }
      },
      "original_name": "Test Cover cover",
      "platform": "virtual",
      "translation_key": null,
      "unique_id": "9866106e-0de0-4b98-b023-02317f717ab5.virtual"
    },
    {
      "area_id": "wo_shi",
      "categories": {},
      "config_entry_id": "01K5TQF9Q0CAPR3G1NA8V7REGR",
      "config_subentry_id": null,
      "created_at": 1758612508.337922,
      "device_id": "bd723712c021e12daef4dd55fd89eef3",
      "disabled_by": null,
      "entity_category": null,
      "entity_id": "fan.test_fan",
      "has_entity_name": false,
      "hidden_by": null,
      "icon": null,
      "id": "1047c5a6cb8ac53a8ef0677567271c4f",
      "labels": [],
      "modified_at": 1760460391.974523,
      "name": null,
      "options": {
        "conversation": {
          "should_expose": true
        }
      },
      "original_name": "Test Fan ",
      "platform": "virtual",
      "translation_key": null,
      "unique_id": "eb955155-cf1d-462b-8d01-c9cb01eb3541.virtual"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "01K5TQF9Q0CAPR3G1NA8V7REGR",
      "config_subentry_id": null,
      "created_at": 1758612508.339871,
      "device_id": "e26680b27526d484d9bbab230c6b50dd",
      "disabled_by": null,
      "entity_category": null,
      "entity_id": "light.test_lights",
      "has_entity_name": false,
      "hidden_by": null,
      "icon": null,
      "id": "ab3c0cc8ee2560d8382fb8531c5c4200",
      "labels": [],
      "modified_at": 1758612508.340538,
      "name": null,
      "options": {
        "conversation": {
          "should_expose": true
        }
      },
      "original_name": "Test Lights ",
      "platform": "virtual",
      "translation_key": null,
      "unique_id": "54aa3e4c-da74-4576-98ba-ee4603dfdff8.virtual"
    },
    {
      "area_id": "test3",
      "categories": {},
      "config_entry_id": "01K5TQF9Q0CAPR3G1NA8V7REGR",
      "config_subentry_id": null,
      "created_at": 1758612508.341985,
      "device_id": "4a913b08c70ae173a12cf738e341aea4",
      "disabled_by": null,
      "entity_category": null,
      "entity_id": "switch.test_switch",
      "has_entity_name": false,
      "hidden_by": null,
      "icon": null,
      "id": "4fe91b15627004bde587bf7abb207498",
      "labels": [],
      "modified_at": 1760542579.523299,
      "name": null,
      "options": {
        "conversation": {
          "should_expose": true
        }
      },
      "original_name": "Test Switch ",
      "platform": "virtual",
      "translation_key": null,
      "unique_id": "9489d718-127d-4e10-8f5e-8f6678f90ce2.virtual"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "5775ca3dcdf4c1a964c80a487afa26e1",
      "config_subentry_id": null,
      "created_at": 1753414048.08589,
      "device_id": "8c3adca61fd2f06ed569e0c442d1436e",
      "disabled_by": "integration",
      "entity_category": null,
      "entity_id": "binary_sensor.odoo_running",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "607b9760c1fed317561d7eaf5fc7ce48",
      "labels": [],
      "modified_at": 1758807704.005821,
      "name": null,
      "options": {},
      "original_name": "執行中",
      "platform": "hassio",
      "translation_key": "state",
      "unique_id": "local_odoo_state"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "5775ca3dcdf4c1a964c80a487afa26e1",
      "config_subentry_id": null,
      "created_at": 1753414048.093469,
      "device_id": "8c3adca61fd2f06ed569e0c442d1436e",
      "disabled_by": "integration",
      "entity_category": null,
      "entity_id": "sensor.odoo_version",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "a0616b1076065fc747cd8434313b58de",
      "labels": [],
      "modified_at": 1758807704.012834,
      "name": null,
      "options": {},
      "original_name": "版本",
      "platform": "hassio",
      "translation_key": "version",
      "unique_id": "local_odoo_version"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "5775ca3dcdf4c1a964c80a487afa26e1",
      "config_subentry_id": null,
      "created_at": 1753414048.093853,
      "device_id": "8c3adca61fd2f06ed569e0c442d1436e",
      "disabled_by": "integration",
      "entity_category": null,
      "entity_id": "sensor.odoo_newest_version",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "98c9c1aab6d4ab69f86a913c53708161",
      "labels": [],
      "modified_at": 1758807704.013108,
      "name": null,
      "options": {},
      "original_name": "最新版本",
      "platform": "hassio",
      "translation_key": "version_latest",
      "unique_id": "local_odoo_version_latest"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "5775ca3dcdf4c1a964c80a487afa26e1",
      "config_subentry_id": null,
      "created_at": 1753414048.094087,
      "device_id": "8c3adca61fd2f06ed569e0c442d1436e",
      "disabled_by": "integration",
      "entity_category": null,
      "entity_id": "sensor.odoo_cpu_percent",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "1e85cfce9cfa6a824d39275a35d76ef3",
      "labels": [],
      "modified_at": 1758807704.013321,
      "name": null,
      "options": {},
      "original_name": "CPU 百分比",
      "platform": "hassio",
      "translation_key": "cpu_percent",
      "unique_id": "local_odoo_cpu_percent"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "5775ca3dcdf4c1a964c80a487afa26e1",
      "config_subentry_id": null,
      "created_at": 1753414048.094478,
      "device_id": "8c3adca61fd2f06ed569e0c442d1436e",
      "disabled_by": "integration",
      "entity_category": null,
      "entity_id": "sensor.odoo_memory_percent",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "551da6de2e0e9f27b071b5769e4d5f3a",
      "labels": [],
      "modified_at": 1758807704.01353,
      "name": null,
      "options": {},
      "original_name": "記憶體百分比",
      "platform": "hassio",
      "translation_key": "memory_percent",
      "unique_id": "local_odoo_memory_percent"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "5775ca3dcdf4c1a964c80a487afa26e1",
      "config_subentry_id": null,
      "created_at": 1753414048.104582,
      "device_id": "8c3adca61fd2f06ed569e0c442d1436e",
      "disabled_by": null,
      "entity_category": "config",
      "entity_id": "update.odoo_update",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "11ab90ebc6ac4d925a7d9db8f2b24cee",
      "labels": [],
      "modified_at": 1758807704.026325,
      "name": null,
      "options": {
        "conversation": {
          "should_expose": false
        }
      },
      "original_name": "更新",
      "platform": "hassio",
      "translation_key": "update",
      "unique_id": "local_odoo_version_latest"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "01K5TQ0GNBV50K6G7V5F23K6M3",
      "config_subentry_id": null,
      "created_at": 1761128640.074864,
      "device_id": "ab66b5233688a0d77bb694c85915e48b",
      "disabled_by": "integration",
      "entity_category": "diagnostic",
      "entity_id": "switch.virtual_components_pre_release",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "2480400d972292c91e72d5388225cd0d",
      "labels": [],
      "modified_at": 1761128640.074982,
      "name": null,
      "options": {},
      "original_name": "Pre-release",
      "platform": "hacs",
      "translation_key": "pre-release",
      "unique_id": "245267534"
    },
    {
      "area_id": "wo_shi",
      "categories": {},
      "config_entry_id": null,
      "config_subentry_id": null,
      "created_at": 1761578566.872493,
      "device_id": null,
      "disabled_by": null,
      "entity_category": null,
      "entity_id": "automation.duo_qie_kai_guan_kong_zhi_deng_ju",
      "has_entity_name": false,
      "hidden_by": null,
      "icon": null,
      "id": "a6e05449a401d4412b59fdfd4e7c92c9",
      "labels": [],
      "modified_at": 1761582373.010024,
      "name": null,
      "options": {
        "conversation": {
          "should_expose": false
        }
      },
      "original_name": "多切開關控制燈具",
      "platform": "automation",
      "translation_key": null,
      "unique_id": "1761578561276"
    },
    {
      "area_id": "wo_shi",
      "categories": {},
      "config_entry_id": null,
      "config_subentry_id": null,
      "created_at": 1761578616.1371,
      "device_id": null,
      "disabled_by": null,
      "entity_category": null,
      "entity_id": "script.notify",
      "has_entity_name": false,
      "hidden_by": null,
      "icon": null,
      "id": "1fd649a2dbbe58257629b8efe6d9ac24",
      "labels": [],
      "modified_at": 1761582387.288124,
      "name": null,
      "options": {
        "conversation": {
          "should_expose": false
        }
      },
      "original_name": "notify",
      "platform": "script",
      "translation_key": null,
      "unique_id": "notify"
    },
    {
      "area_id": "wo_shi",
      "categories": {},
      "config_entry_id": null,
      "config_subentry_id": null,
      "created_at": 1761578729.429827,
      "device_id": null,
      "disabled_by": null,
      "entity_category": null,
      "entity_id": "scene.test2",
      "has_entity_name": false,
      "hidden_by": null,
      "icon": null,
      "id": "a38461df4ae91a043a4a2fdde457c448",
      "labels": [],
      "modified_at": 1761582380.89036,
      "name": null,
      "options": {
        "conversation": {
          "should_expose": true
        }
      },
      "original_name": "test2",
      "platform": "homeassistant",
      "translation_key": null,
      "unique_id": "1761578728359"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "5775ca3dcdf4c1a964c80a487afa26e1",
      "config_subentry_id": null,
      "created_at": 1764496136.431068,
      "device_id": "a4fb79c5af3ba322f6d74a26f0306f7b",
      "disabled_by": "integration",
      "entity_category": null,
      "entity_id": "binary_sensor.glances_running",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "c5c4a7929a561b5d15c4daaf449f3d65",
      "labels": [],
      "modified_at": 1764496136.43117,
      "name": null,
      "options": {},
      "original_name": "執行中",
      "platform": "hassio",
      "translation_key": "state",
      "unique_id": "a0d7b954_glances_state"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "5775ca3dcdf4c1a964c80a487afa26e1",
      "config_subentry_id": null,
      "created_at": 1764496136.437998,
      "device_id": "a4fb79c5af3ba322f6d74a26f0306f7b",
      "disabled_by": "integration",
      "entity_category": null,
      "entity_id": "sensor.glances_version",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "a7d2b6b11f96584fe61e04a375472548",
      "labels": [],
      "modified_at": 1764496136.438094,
      "name": null,
      "options": {},
      "original_name": "版本",
      "platform": "hassio",
      "translation_key": "version",
      "unique_id": "a0d7b954_glances_version"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "5775ca3dcdf4c1a964c80a487afa26e1",
      "config_subentry_id": null,
      "created_at": 1764496136.438318,
      "device_id": "a4fb79c5af3ba322f6d74a26f0306f7b",
      "disabled_by": "integration",
      "entity_category": null,
      "entity_id": "sensor.glances_newest_version",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "1e6f7a9e6bd14b1b4db52d2f882a5315",
      "labels": [],
      "modified_at": 1764496136.438379,
      "name": null,
      "options": {},
      "original_name": "最新版本",
      "platform": "hassio",
      "translation_key": "version_latest",
      "unique_id": "a0d7b954_glances_version_latest"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "5775ca3dcdf4c1a964c80a487afa26e1",
      "config_subentry_id": null,
      "created_at": 1764496136.438551,
      "device_id": "a4fb79c5af3ba322f6d74a26f0306f7b",
      "disabled_by": "integration",
      "entity_category": null,
      "entity_id": "sensor.glances_cpu_percent",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "71c26dd8bfeccd857a4f0b22686ee35e",
      "labels": [],
      "modified_at": 1764496136.438607,
      "name": null,
      "options": {},
      "original_name": "CPU 百分比",
      "platform": "hassio",
      "translation_key": "cpu_percent",
      "unique_id": "a0d7b954_glances_cpu_percent"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "5775ca3dcdf4c1a964c80a487afa26e1",
      "config_subentry_id": null,
      "created_at": 1764496136.43879,
      "device_id": "a4fb79c5af3ba322f6d74a26f0306f7b",
      "disabled_by": "integration",
      "entity_category": null,
      "entity_id": "sensor.glances_memory_percent",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "bb4f83e464e1121b5d557a99c262d527",
      "labels": [],
      "modified_at": 1764496136.438854,
      "name": null,
      "options": {},
      "original_name": "記憶體百分比",
      "platform": "hassio",
      "translation_key": "memory_percent",
      "unique_id": "a0d7b954_glances_memory_percent"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "5775ca3dcdf4c1a964c80a487afa26e1",
      "config_subentry_id": null,
      "created_at": 1764496136.450402,
      "device_id": "a4fb79c5af3ba322f6d74a26f0306f7b",
      "disabled_by": null,
      "entity_category": "config",
      "entity_id": "update.glances_update",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "7c18ec827ccf161c80c88baf409f60fe",
      "labels": [],
      "modified_at": 1764496136.450818,
      "name": null,
      "options": {
        "conversation": {
          "should_expose": false
        }
      },
      "original_name": "更新",
      "platform": "hassio",
      "translation_key": "update",
      "unique_id": "a0d7b954_glances_version_latest"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "01KBA31BNXAWX73PQ3W00QHXZG",
      "config_subentry_id": null,
      "created_at": 1764496551.693628,
      "device_id": "2ac79e2bf20b7e58eb2113d842ef6ef3",
      "disabled_by": null,
      "entity_category": null,
      "entity_id": "sensor.localhost_ssl_disk_used",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "c019dbbf543e21ab1d8907d3d41626d4",
      "labels": [],
      "modified_at": 1764496551.694711,
      "name": null,
      "options": {
        "sensor": {
          "suggested_display_precision": 2
        },
        "conversation": {
          "should_expose": false
        }
      },
      "original_name": "/ssl 使用空間",
      "platform": "glances",
      "translation_key": "disk_used",
      "unique_id": "01KBA31BNXAWX73PQ3W00QHXZG-/ssl-disk_use"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "01KBA31BNXAWX73PQ3W00QHXZG",
      "config_subentry_id": null,
      "created_at": 1764496551.695573,
      "device_id": "2ac79e2bf20b7e58eb2113d842ef6ef3",
      "disabled_by": null,
      "entity_category": null,
      "entity_id": "sensor.localhost_ssl_disk_usage",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "d7b8e383784fe11b8c4a0830ea3b30a1",
      "labels": [],
      "modified_at": 1764496551.696118,
      "name": null,
      "options": {
        "conversation": {
          "should_expose": false
        }
      },
      "original_name": "/ssl 磁碟使用量",
      "platform": "glances",
      "translation_key": "disk_usage",
      "unique_id": "01KBA31BNXAWX73PQ3W00QHXZG-/ssl-disk_use_percent"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "01KBA31BNXAWX73PQ3W00QHXZG",
      "config_subentry_id": null,
      "created_at": 1764496551.696688,
      "device_id": "2ac79e2bf20b7e58eb2113d842ef6ef3",
      "disabled_by": null,
      "entity_category": null,
      "entity_id": "sensor.localhost_ssl_disk_free",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "ef1c8a5b3bf6a9edf17c194b678d2759",
      "labels": [],
      "modified_at": 1764496551.697334,
      "name": null,
      "options": {
        "sensor": {
          "suggested_display_precision": 2
        },
        "conversation": {
          "should_expose": false
        }
      },
      "original_name": "/ssl 可用空間",
      "platform": "glances",
      "translation_key": "disk_free",
      "unique_id": "01KBA31BNXAWX73PQ3W00QHXZG-/ssl-disk_free"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "01KBA31BNXAWX73PQ3W00QHXZG",
      "config_subentry_id": null,
      "created_at": 1764496551.698058,
      "device_id": "2ac79e2bf20b7e58eb2113d842ef6ef3",
      "disabled_by": null,
      "entity_category": null,
      "entity_id": "sensor.localhost_share_disk_used",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "111f83f2ffceb0cdb33fbe9576e53d26",
      "labels": [],
      "modified_at": 1764496551.700311,
      "name": null,
      "options": {
        "sensor": {
          "suggested_display_precision": 2
        },
        "conversation": {
          "should_expose": false
        }
      },
      "original_name": "/share 使用空間",
      "platform": "glances",
      "translation_key": "disk_used",
      "unique_id": "01KBA31BNXAWX73PQ3W00QHXZG-/share-disk_use"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "01KBA31BNXAWX73PQ3W00QHXZG",
      "config_subentry_id": null,
      "created_at": 1764496551.701413,
      "device_id": "2ac79e2bf20b7e58eb2113d842ef6ef3",
      "disabled_by": null,
      "entity_category": null,
      "entity_id": "sensor.localhost_share_disk_usage",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "e228cb64fb367c4530d7efdb627753e5",
      "labels": [],
      "modified_at": 1764496551.702109,
      "name": null,
      "options": {
        "conversation": {
          "should_expose": false
        }
      },
      "original_name": "/share 磁碟使用量",
      "platform": "glances",
      "translation_key": "disk_usage",
      "unique_id": "01KBA31BNXAWX73PQ3W00QHXZG-/share-disk_use_percent"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "01KBA31BNXAWX73PQ3W00QHXZG",
      "config_subentry_id": null,
      "created_at": 1764496551.702805,
      "device_id": "2ac79e2bf20b7e58eb2113d842ef6ef3",
      "disabled_by": null,
      "entity_category": null,
      "entity_id": "sensor.localhost_share_disk_free",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "bec27d5766a8f61abb0d0b2c44209fdb",
      "labels": [],
      "modified_at": 1764496551.703534,
      "name": null,
      "options": {
        "sensor": {
          "suggested_display_precision": 2
        },
        "conversation": {
          "should_expose": false
        }
      },
      "original_name": "/share 可用空間",
      "platform": "glances",
      "translation_key": "disk_free",
      "unique_id": "01KBA31BNXAWX73PQ3W00QHXZG-/share-disk_free"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "01KBA31BNXAWX73PQ3W00QHXZG",
      "config_subentry_id": null,
      "created_at": 1764496551.704262,
      "device_id": "2ac79e2bf20b7e58eb2113d842ef6ef3",
      "disabled_by": null,
      "entity_category": null,
      "entity_id": "sensor.localhost_backup_disk_used",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "79999fef075eb5f840d7742e77c9b722",
      "labels": [],
      "modified_at": 1764496551.704934,
      "name": null,
      "options": {
        "sensor": {
          "suggested_display_precision": 2
        },
        "conversation": {
          "should_expose": false
        }
      },
      "original_name": "/backup 使用空間",
      "platform": "glances",
      "translation_key": "disk_used",
      "unique_id": "01KBA31BNXAWX73PQ3W00QHXZG-/backup-disk_use"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "01KBA31BNXAWX73PQ3W00QHXZG",
      "config_subentry_id": null,
      "created_at": 1764496551.706846,
      "device_id": "2ac79e2bf20b7e58eb2113d842ef6ef3",
      "disabled_by": null,
      "entity_category": null,
      "entity_id": "sensor.localhost_backup_disk_usage",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "2411dcb3b201f917004cecf9b708d7ee",
      "labels": [],
      "modified_at": 1764496551.707351,
      "name": null,
      "options": {
        "conversation": {
          "should_expose": false
        }
      },
      "original_name": "/backup 磁碟使用量",
      "platform": "glances",
      "translation_key": "disk_usage",
      "unique_id": "01KBA31BNXAWX73PQ3W00QHXZG-/backup-disk_use_percent"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "01KBA31BNXAWX73PQ3W00QHXZG",
      "config_subentry_id": null,
      "created_at": 1764496551.70793,
      "device_id": "2ac79e2bf20b7e58eb2113d842ef6ef3",
      "disabled_by": null,
      "entity_category": null,
      "entity_id": "sensor.localhost_backup_disk_free",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "79d86f996a583f986b68780204df3723",
      "labels": [],
      "modified_at": 1764496551.708478,
      "name": null,
      "options": {
        "sensor": {
          "suggested_display_precision": 2
        },
        "conversation": {
          "should_expose": false
        }
      },
      "original_name": "/backup 可用空間",
      "platform": "glances",
      "translation_key": "disk_free",
      "unique_id": "01KBA31BNXAWX73PQ3W00QHXZG-/backup-disk_free"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "01KBA31BNXAWX73PQ3W00QHXZG",
      "config_subentry_id": null,
      "created_at": 1764496551.708986,
      "device_id": "2ac79e2bf20b7e58eb2113d842ef6ef3",
      "disabled_by": null,
      "entity_category": null,
      "entity_id": "sensor.localhost_media_disk_used",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "4204698ccecfc78025eed43fd93b6437",
      "labels": [],
      "modified_at": 1764496551.709411,
      "name": null,
      "options": {
        "sensor": {
          "suggested_display_precision": 2
        },
        "conversation": {
          "should_expose": false
        }
      },
      "original_name": "/media 使用空間",
      "platform": "glances",
      "translation_key": "disk_used",
      "unique_id": "01KBA31BNXAWX73PQ3W00QHXZG-/media-disk_use"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "01KBA31BNXAWX73PQ3W00QHXZG",
      "config_subentry_id": null,
      "created_at": 1764496551.709872,
      "device_id": "2ac79e2bf20b7e58eb2113d842ef6ef3",
      "disabled_by": null,
      "entity_category": null,
      "entity_id": "sensor.localhost_media_disk_usage",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "275c126f57696536545cc5a14c4176a4",
      "labels": [],
      "modified_at": 1764496551.710168,
      "name": null,
      "options": {
        "conversation": {
          "should_expose": false
        }
      },
      "original_name": "/media 磁碟使用量",
      "platform": "glances",
      "translation_key": "disk_usage",
      "unique_id": "01KBA31BNXAWX73PQ3W00QHXZG-/media-disk_use_percent"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "01KBA31BNXAWX73PQ3W00QHXZG",
      "config_subentry_id": null,
      "created_at": 1764496551.710515,
      "device_id": "2ac79e2bf20b7e58eb2113d842ef6ef3",
      "disabled_by": null,
      "entity_category": null,
      "entity_id": "sensor.localhost_media_disk_free",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "5130588735e7e8f4f9c1b92cb44bab0e",
      "labels": [],
      "modified_at": 1764496551.710971,
      "name": null,
      "options": {
        "sensor": {
          "suggested_display_precision": 2
        },
        "conversation": {
          "should_expose": false
        }
      },
      "original_name": "/media 可用空間",
      "platform": "glances",
      "translation_key": "disk_free",
      "unique_id": "01KBA31BNXAWX73PQ3W00QHXZG-/media-disk_free"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "01KBA31BNXAWX73PQ3W00QHXZG",
      "config_subentry_id": null,
      "created_at": 1764496551.711547,
      "device_id": "2ac79e2bf20b7e58eb2113d842ef6ef3",
      "disabled_by": null,
      "entity_category": null,
      "entity_id": "sensor.localhost_config_disk_used",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "c2b39c0e55cce4f098bfd503b32f6622",
      "labels": [],
      "modified_at": 1764496551.71216,
      "name": null,
      "options": {
        "sensor": {
          "suggested_display_precision": 2
        },
        "conversation": {
          "should_expose": false
        }
      },
      "original_name": "/config 使用空間",
      "platform": "glances",
      "translation_key": "disk_used",
      "unique_id": "01KBA31BNXAWX73PQ3W00QHXZG-/config-disk_use"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "01KBA31BNXAWX73PQ3W00QHXZG",
      "config_subentry_id": null,
      "created_at": 1764496551.712805,
      "device_id": "2ac79e2bf20b7e58eb2113d842ef6ef3",
      "disabled_by": null,
      "entity_category": null,
      "entity_id": "sensor.localhost_config_disk_usage",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "af8a78366c9a7f89fa4b144c4e67366c",
      "labels": [],
      "modified_at": 1764496551.713207,
      "name": null,
      "options": {
        "conversation": {
          "should_expose": false
        }
      },
      "original_name": "/config 磁碟使用量",
      "platform": "glances",
      "translation_key": "disk_usage",
      "unique_id": "01KBA31BNXAWX73PQ3W00QHXZG-/config-disk_use_percent"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "01KBA31BNXAWX73PQ3W00QHXZG",
      "config_subentry_id": null,
      "created_at": 1764496551.713627,
      "device_id": "2ac79e2bf20b7e58eb2113d842ef6ef3",
      "disabled_by": null,
      "entity_category": null,
      "entity_id": "sensor.localhost_config_disk_free",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "969c0839b70bd983b0c7853bb5bef877",
      "labels": [],
      "modified_at": 1764496551.714229,
      "name": null,
      "options": {
        "sensor": {
          "suggested_display_precision": 2
        },
        "conversation": {
          "should_expose": false
        }
      },
      "original_name": "/config 可用空間",
      "platform": "glances",
      "translation_key": "disk_free",
      "unique_id": "01KBA31BNXAWX73PQ3W00QHXZG-/config-disk_free"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "01KBA31BNXAWX73PQ3W00QHXZG",
      "config_subentry_id": null,
      "created_at": 1764496551.714888,
      "device_id": "2ac79e2bf20b7e58eb2113d842ef6ef3",
      "disabled_by": null,
      "entity_category": null,
      "entity_id": "sensor.localhost_addons_disk_used",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "7bbcac81f72c0db88bb783b9d54cddc5",
      "labels": [],
      "modified_at": 1764496551.71542,
      "name": null,
      "options": {
        "sensor": {
          "suggested_display_precision": 2
        },
        "conversation": {
          "should_expose": false
        }
      },
      "original_name": "/addons 使用空間",
      "platform": "glances",
      "translation_key": "disk_used",
      "unique_id": "01KBA31BNXAWX73PQ3W00QHXZG-/addons-disk_use"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "01KBA31BNXAWX73PQ3W00QHXZG",
      "config_subentry_id": null,
      "created_at": 1764496551.716114,
      "device_id": "2ac79e2bf20b7e58eb2113d842ef6ef3",
      "disabled_by": null,
      "entity_category": null,
      "entity_id": "sensor.localhost_addons_disk_usage",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "11ebf4c6cceddd03243932730fd81fc8",
      "labels": [],
      "modified_at": 1764496551.717839,
      "name": null,
      "options": {
        "conversation": {
          "should_expose": false
        }
      },
      "original_name": "/addons 磁碟使用量",
      "platform": "glances",
      "translation_key": "disk_usage",
      "unique_id": "01KBA31BNXAWX73PQ3W00QHXZG-/addons-disk_use_percent"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "01KBA31BNXAWX73PQ3W00QHXZG",
      "config_subentry_id": null,
      "created_at": 1764496551.718508,
      "device_id": "2ac79e2bf20b7e58eb2113d842ef6ef3",
      "disabled_by": null,
      "entity_category": null,
      "entity_id": "sensor.localhost_addons_disk_free",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "671027a1efb91dc2f39124db2a478b88",
      "labels": [],
      "modified_at": 1764496551.719273,
      "name": null,
      "options": {
        "sensor": {
          "suggested_display_precision": 2
        },
        "conversation": {
          "should_expose": false
        }
      },
      "original_name": "/addons 可用空間",
      "platform": "glances",
      "translation_key": "disk_free",
      "unique_id": "01KBA31BNXAWX73PQ3W00QHXZG-/addons-disk_free"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "01KBA31BNXAWX73PQ3W00QHXZG",
      "config_subentry_id": null,
      "created_at": 1764496551.719994,
      "device_id": "2ac79e2bf20b7e58eb2113d842ef6ef3",
      "disabled_by": null,
      "entity_category": null,
      "entity_id": "sensor.localhost_data_disk_used",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "b1f5f61fecda5b6166fa19ee32458ba5",
      "labels": [],
      "modified_at": 1764496551.720794,
      "name": null,
      "options": {
        "sensor": {
          "suggested_display_precision": 2
        },
        "conversation": {
          "should_expose": false
        }
      },
      "original_name": "/data 使用空間",
      "platform": "glances",
      "translation_key": "disk_used",
      "unique_id": "01KBA31BNXAWX73PQ3W00QHXZG-/data-disk_use"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "01KBA31BNXAWX73PQ3W00QHXZG",
      "config_subentry_id": null,
      "created_at": 1764496551.723448,
      "device_id": "2ac79e2bf20b7e58eb2113d842ef6ef3",
      "disabled_by": null,
      "entity_category": null,
      "entity_id": "sensor.localhost_data_disk_usage",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "f6c66dd545c8fa95848c62895cdb8324",
      "labels": [],
      "modified_at": 1764496551.723963,
      "name": null,
      "options": {
        "conversation": {
          "should_expose": false
        }
      },
      "original_name": "/data 磁碟使用量",
      "platform": "glances",
      "translation_key": "disk_usage",
      "unique_id": "01KBA31BNXAWX73PQ3W00QHXZG-/data-disk_use_percent"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "01KBA31BNXAWX73PQ3W00QHXZG",
      "config_subentry_id": null,
      "created_at": 1764496551.724549,
      "device_id": "2ac79e2bf20b7e58eb2113d842ef6ef3",
      "disabled_by": null,
      "entity_category": null,
      "entity_id": "sensor.localhost_data_disk_free",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "664416cb5a65150101e72459d08fb992",
      "labels": [],
      "modified_at": 1764496551.725298,
      "name": null,
      "options": {
        "sensor": {
          "suggested_display_precision": 2
        },
        "conversation": {
          "should_expose": false
        }
      },
      "original_name": "/data 可用空間",
      "platform": "glances",
      "translation_key": "disk_free",
      "unique_id": "01KBA31BNXAWX73PQ3W00QHXZG-/data-disk_free"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "01KBA31BNXAWX73PQ3W00QHXZG",
      "config_subentry_id": null,
      "created_at": 1764496551.725982,
      "device_id": "2ac79e2bf20b7e58eb2113d842ef6ef3",
      "disabled_by": null,
      "entity_category": null,
      "entity_id": "sensor.localhost_run_cid_disk_used",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "6fdf6111a950a2bbcb17a3ba7abfcab0",
      "labels": [],
      "modified_at": 1764496551.726525,
      "name": null,
      "options": {
        "sensor": {
          "suggested_display_precision": 2
        },
        "conversation": {
          "should_expose": false
        }
      },
      "original_name": "/run/cid 使用空間",
      "platform": "glances",
      "translation_key": "disk_used",
      "unique_id": "01KBA31BNXAWX73PQ3W00QHXZG-/run/cid-disk_use"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "01KBA31BNXAWX73PQ3W00QHXZG",
      "config_subentry_id": null,
      "created_at": 1764496551.727214,
      "device_id": "2ac79e2bf20b7e58eb2113d842ef6ef3",
      "disabled_by": null,
      "entity_category": null,
      "entity_id": "sensor.localhost_run_cid_disk_usage",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "c4a7790fbb908ce03f6321d5a1fe67af",
      "labels": [],
      "modified_at": 1764496551.727638,
      "name": null,
      "options": {
        "conversation": {
          "should_expose": false
        }
      },
      "original_name": "/run/cid 磁碟使用量",
      "platform": "glances",
      "translation_key": "disk_usage",
      "unique_id": "01KBA31BNXAWX73PQ3W00QHXZG-/run/cid-disk_use_percent"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "01KBA31BNXAWX73PQ3W00QHXZG",
      "config_subentry_id": null,
      "created_at": 1764496551.729351,
      "device_id": "2ac79e2bf20b7e58eb2113d842ef6ef3",
      "disabled_by": null,
      "entity_category": null,
      "entity_id": "sensor.localhost_run_cid_disk_free",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "8323877c85a97f8242ae54bf9b7779c5",
      "labels": [],
      "modified_at": 1764496551.730102,
      "name": null,
      "options": {
        "sensor": {
          "suggested_display_precision": 2
        },
        "conversation": {
          "should_expose": false
        }
      },
      "original_name": "/run/cid 可用空間",
      "platform": "glances",
      "translation_key": "disk_free",
      "unique_id": "01KBA31BNXAWX73PQ3W00QHXZG-/run/cid-disk_free"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "01KBA31BNXAWX73PQ3W00QHXZG",
      "config_subentry_id": null,
      "created_at": 1764496551.73114,
      "device_id": "2ac79e2bf20b7e58eb2113d842ef6ef3",
      "disabled_by": null,
      "entity_category": null,
      "entity_id": "sensor.localhost_etc_resolv_conf_disk_used",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "1e32090e17dcaea9ad2cac8422fe974d",
      "labels": [],
      "modified_at": 1764496551.73175,
      "name": null,
      "options": {
        "sensor": {
          "suggested_display_precision": 2
        },
        "conversation": {
          "should_expose": false
        }
      },
      "original_name": "/etc/resolv.conf 使用空間",
      "platform": "glances",
      "translation_key": "disk_used",
      "unique_id": "01KBA31BNXAWX73PQ3W00QHXZG-/etc/resolv.conf-disk_use"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "01KBA31BNXAWX73PQ3W00QHXZG",
      "config_subentry_id": null,
      "created_at": 1764496551.732399,
      "device_id": "2ac79e2bf20b7e58eb2113d842ef6ef3",
      "disabled_by": null,
      "entity_category": null,
      "entity_id": "sensor.localhost_etc_resolv_conf_disk_usage",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "ff6c33ffbf7d99c3ed00ccc9e2639b46",
      "labels": [],
      "modified_at": 1764496551.732865,
      "name": null,
      "options": {
        "conversation": {
          "should_expose": false
        }
      },
      "original_name": "/etc/resolv.conf 磁碟使用量",
      "platform": "glances",
      "translation_key": "disk_usage",
      "unique_id": "01KBA31BNXAWX73PQ3W00QHXZG-/etc/resolv.conf-disk_use_percent"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "01KBA31BNXAWX73PQ3W00QHXZG",
      "config_subentry_id": null,
      "created_at": 1764496551.733308,
      "device_id": "2ac79e2bf20b7e58eb2113d842ef6ef3",
      "disabled_by": null,
      "entity_category": null,
      "entity_id": "sensor.localhost_etc_resolv_conf_disk_free",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "a1729b3f1c547a6d74ba85b342e82579",
      "labels": [],
      "modified_at": 1764496551.733905,
      "name": null,
      "options": {
        "sensor": {
          "suggested_display_precision": 2
        },
        "conversation": {
          "should_expose": false
        }
      },
      "original_name": "/etc/resolv.conf 可用空間",
      "platform": "glances",
      "translation_key": "disk_free",
      "unique_id": "01KBA31BNXAWX73PQ3W00QHXZG-/etc/resolv.conf-disk_free"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "01KBA31BNXAWX73PQ3W00QHXZG",
      "config_subentry_id": null,
      "created_at": 1764496551.735469,
      "device_id": "2ac79e2bf20b7e58eb2113d842ef6ef3",
      "disabled_by": null,
      "entity_category": null,
      "entity_id": "sensor.localhost_etc_hostname_disk_used",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "d4a6732fc00997ddb741df42cefd6daa",
      "labels": [],
      "modified_at": 1764496551.736225,
      "name": null,
      "options": {
        "sensor": {
          "suggested_display_precision": 2
        },
        "conversation": {
          "should_expose": false
        }
      },
      "original_name": "/etc/hostname 使用空間",
      "platform": "glances",
      "translation_key": "disk_used",
      "unique_id": "01KBA31BNXAWX73PQ3W00QHXZG-/etc/hostname-disk_use"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "01KBA31BNXAWX73PQ3W00QHXZG",
      "config_subentry_id": null,
      "created_at": 1764496551.736818,
      "device_id": "2ac79e2bf20b7e58eb2113d842ef6ef3",
      "disabled_by": null,
      "entity_category": null,
      "entity_id": "sensor.localhost_etc_hostname_disk_usage",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "0170b0f66cfe01feb6aefe258bc1ebb9",
      "labels": [],
      "modified_at": 1764496551.737532,
      "name": null,
      "options": {
        "conversation": {
          "should_expose": false
        }
      },
      "original_name": "/etc/hostname 磁碟使用量",
      "platform": "glances",
      "translation_key": "disk_usage",
      "unique_id": "01KBA31BNXAWX73PQ3W00QHXZG-/etc/hostname-disk_use_percent"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "01KBA31BNXAWX73PQ3W00QHXZG",
      "config_subentry_id": null,
      "created_at": 1764496551.738111,
      "device_id": "2ac79e2bf20b7e58eb2113d842ef6ef3",
      "disabled_by": null,
      "entity_category": null,
      "entity_id": "sensor.localhost_etc_hostname_disk_free",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "6722b6249a17e4c26a78be41266cd962",
      "labels": [],
      "modified_at": 1764496551.738651,
      "name": null,
      "options": {
        "sensor": {
          "suggested_display_precision": 2
        },
        "conversation": {
          "should_expose": false
        }
      },
      "original_name": "/etc/hostname 可用空間",
      "platform": "glances",
      "translation_key": "disk_free",
      "unique_id": "01KBA31BNXAWX73PQ3W00QHXZG-/etc/hostname-disk_free"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "01KBA31BNXAWX73PQ3W00QHXZG",
      "config_subentry_id": null,
      "created_at": 1764496551.739359,
      "device_id": "2ac79e2bf20b7e58eb2113d842ef6ef3",
      "disabled_by": null,
      "entity_category": null,
      "entity_id": "sensor.localhost_etc_hosts_disk_used",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "3f9a3d1c10edc2f773254c1422dff3a9",
      "labels": [],
      "modified_at": 1764496551.739942,
      "name": null,
      "options": {
        "sensor": {
          "suggested_display_precision": 2
        },
        "conversation": {
          "should_expose": false
        }
      },
      "original_name": "/etc/hosts 使用空間",
      "platform": "glances",
      "translation_key": "disk_used",
      "unique_id": "01KBA31BNXAWX73PQ3W00QHXZG-/etc/hosts-disk_use"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "01KBA31BNXAWX73PQ3W00QHXZG",
      "config_subentry_id": null,
      "created_at": 1764496551.740619,
      "device_id": "2ac79e2bf20b7e58eb2113d842ef6ef3",
      "disabled_by": null,
      "entity_category": null,
      "entity_id": "sensor.localhost_etc_hosts_disk_usage",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "e71ec016b745e758d6b179063ef772b0",
      "labels": [],
      "modified_at": 1764496551.741222,
      "name": null,
      "options": {
        "conversation": {
          "should_expose": false
        }
      },
      "original_name": "/etc/hosts 磁碟使用量",
      "platform": "glances",
      "translation_key": "disk_usage",
      "unique_id": "01KBA31BNXAWX73PQ3W00QHXZG-/etc/hosts-disk_use_percent"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "01KBA31BNXAWX73PQ3W00QHXZG",
      "config_subentry_id": null,
      "created_at": 1764496551.7417,
      "device_id": "2ac79e2bf20b7e58eb2113d842ef6ef3",
      "disabled_by": null,
      "entity_category": null,
      "entity_id": "sensor.localhost_etc_hosts_disk_free",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "628a6bac3b033d59e7fb0da0bf2d9dd2",
      "labels": [],
      "modified_at": 1764496551.742289,
      "name": null,
      "options": {
        "sensor": {
          "suggested_display_precision": 2
        },
        "conversation": {
          "should_expose": false
        }
      },
      "original_name": "/etc/hosts 可用空間",
      "platform": "glances",
      "translation_key": "disk_free",
      "unique_id": "01KBA31BNXAWX73PQ3W00QHXZG-/etc/hosts-disk_free"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "01KBA31BNXAWX73PQ3W00QHXZG",
      "config_subentry_id": null,
      "created_at": 1764496551.742811,
      "device_id": "2ac79e2bf20b7e58eb2113d842ef6ef3",
      "disabled_by": null,
      "entity_category": null,
      "entity_id": "sensor.localhost_acpitz_0_temperature",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "3e6a53a36ef5156f87e039ef1186a26b",
      "labels": [],
      "modified_at": 1764496551.743227,
      "name": null,
      "options": {
        "sensor": {
          "suggested_display_precision": 1
        },
        "conversation": {
          "should_expose": true
        }
      },
      "original_name": "acpitz 0 溫度",
      "platform": "glances",
      "translation_key": "temperature",
      "unique_id": "01KBA31BNXAWX73PQ3W00QHXZG-acpitz 0-temperature_core"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "01KBA31BNXAWX73PQ3W00QHXZG",
      "config_subentry_id": null,
      "created_at": 1764496551.743644,
      "device_id": "2ac79e2bf20b7e58eb2113d842ef6ef3",
      "disabled_by": null,
      "entity_category": null,
      "entity_id": "sensor.localhost_package_id_0_temperature",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "c1923a215f68baab2a848e76e4731960",
      "labels": [],
      "modified_at": 1764496551.744044,
      "name": null,
      "options": {
        "sensor": {
          "suggested_display_precision": 1
        },
        "conversation": {
          "should_expose": true
        }
      },
      "original_name": "Package id 0 溫度",
      "platform": "glances",
      "translation_key": "temperature",
      "unique_id": "01KBA31BNXAWX73PQ3W00QHXZG-Package id 0-temperature_core"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "01KBA31BNXAWX73PQ3W00QHXZG",
      "config_subentry_id": null,
      "created_at": 1764496551.744456,
      "device_id": "2ac79e2bf20b7e58eb2113d842ef6ef3",
      "disabled_by": null,
      "entity_category": null,
      "entity_id": "sensor.localhost_core_0_temperature",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "9dd727b70616c85249f308181df33d00",
      "labels": [],
      "modified_at": 1764496551.744834,
      "name": null,
      "options": {
        "sensor": {
          "suggested_display_precision": 1
        },
        "conversation": {
          "should_expose": true
        }
      },
      "original_name": "Core 0 溫度",
      "platform": "glances",
      "translation_key": "temperature",
      "unique_id": "01KBA31BNXAWX73PQ3W00QHXZG-Core 0-temperature_core"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "01KBA31BNXAWX73PQ3W00QHXZG",
      "config_subentry_id": null,
      "created_at": 1764496551.745244,
      "device_id": "2ac79e2bf20b7e58eb2113d842ef6ef3",
      "disabled_by": null,
      "entity_category": null,
      "entity_id": "sensor.localhost_core_1_temperature",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "72299e112116d8858ccf23b1576bc390",
      "labels": [],
      "modified_at": 1764496551.745616,
      "name": null,
      "options": {
        "sensor": {
          "suggested_display_precision": 1
        },
        "conversation": {
          "should_expose": true
        }
      },
      "original_name": "Core 1 溫度",
      "platform": "glances",
      "translation_key": "temperature",
      "unique_id": "01KBA31BNXAWX73PQ3W00QHXZG-Core 1-temperature_core"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "01KBA31BNXAWX73PQ3W00QHXZG",
      "config_subentry_id": null,
      "created_at": 1764496551.74603,
      "device_id": "2ac79e2bf20b7e58eb2113d842ef6ef3",
      "disabled_by": null,
      "entity_category": null,
      "entity_id": "sensor.localhost_core_2_temperature",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "8af769f9408927200af8a56d3a2b41a6",
      "labels": [],
      "modified_at": 1764496551.746391,
      "name": null,
      "options": {
        "sensor": {
          "suggested_display_precision": 1
        },
        "conversation": {
          "should_expose": true
        }
      },
      "original_name": "Core 2 溫度",
      "platform": "glances",
      "translation_key": "temperature",
      "unique_id": "01KBA31BNXAWX73PQ3W00QHXZG-Core 2-temperature_core"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "01KBA31BNXAWX73PQ3W00QHXZG",
      "config_subentry_id": null,
      "created_at": 1764496551.746799,
      "device_id": "2ac79e2bf20b7e58eb2113d842ef6ef3",
      "disabled_by": null,
      "entity_category": null,
      "entity_id": "sensor.localhost_core_3_temperature",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "c31e0ac9ef9c8ac41a99865cf80f65ec",
      "labels": [],
      "modified_at": 1764496551.747172,
      "name": null,
      "options": {
        "sensor": {
          "suggested_display_precision": 1
        },
        "conversation": {
          "should_expose": true
        }
      },
      "original_name": "Core 3 溫度",
      "platform": "glances",
      "translation_key": "temperature",
      "unique_id": "01KBA31BNXAWX73PQ3W00QHXZG-Core 3-temperature_core"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "01KBA31BNXAWX73PQ3W00QHXZG",
      "config_subentry_id": null,
      "created_at": 1764496551.747587,
      "device_id": "2ac79e2bf20b7e58eb2113d842ef6ef3",
      "disabled_by": null,
      "entity_category": null,
      "entity_id": "sensor.localhost_memory_usage",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "17e7e9e92d64910efaecacf5f9f3230e",
      "labels": [],
      "modified_at": 1764496551.747864,
      "name": null,
      "options": {
        "conversation": {
          "should_expose": false
        }
      },
      "original_name": "記憶體使用率",
      "platform": "glances",
      "translation_key": "memory_usage",
      "unique_id": "01KBA31BNXAWX73PQ3W00QHXZG--memory_use_percent"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "01KBA31BNXAWX73PQ3W00QHXZG",
      "config_subentry_id": null,
      "created_at": 1764496551.748188,
      "device_id": "2ac79e2bf20b7e58eb2113d842ef6ef3",
      "disabled_by": null,
      "entity_category": null,
      "entity_id": "sensor.localhost_memory_use",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "8bba12a4395d6513d17ca1d10fc93619",
      "labels": [],
      "modified_at": 1764496551.748553,
      "name": null,
      "options": {
        "sensor": {
          "suggested_display_precision": 2
        },
        "conversation": {
          "should_expose": false
        }
      },
      "original_name": "記憶體使用量",
      "platform": "glances",
      "translation_key": "memory_use",
      "unique_id": "01KBA31BNXAWX73PQ3W00QHXZG--memory_use"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "01KBA31BNXAWX73PQ3W00QHXZG",
      "config_subentry_id": null,
      "created_at": 1764496551.74898,
      "device_id": "2ac79e2bf20b7e58eb2113d842ef6ef3",
      "disabled_by": null,
      "entity_category": null,
      "entity_id": "sensor.localhost_memory_free",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "5ec53431092f0fec57f1ed94636fa7af",
      "labels": [],
      "modified_at": 1764496551.749341,
      "name": null,
      "options": {
        "sensor": {
          "suggested_display_precision": 2
        },
        "conversation": {
          "should_expose": false
        }
      },
      "original_name": "可用記憶體",
      "platform": "glances",
      "translation_key": "memory_free",
      "unique_id": "01KBA31BNXAWX73PQ3W00QHXZG--memory_free"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "01KBA31BNXAWX73PQ3W00QHXZG",
      "config_subentry_id": null,
      "created_at": 1764496551.749747,
      "device_id": "2ac79e2bf20b7e58eb2113d842ef6ef3",
      "disabled_by": null,
      "entity_category": null,
      "entity_id": "sensor.localhost_swap_usage",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "3fea38c1ac186396feea69fd9d8cf9cb",
      "labels": [],
      "modified_at": 1764496551.750044,
      "name": null,
      "options": {
        "conversation": {
          "should_expose": false
        }
      },
      "original_name": "暫存使用率",
      "platform": "glances",
      "translation_key": "swap_usage",
      "unique_id": "01KBA31BNXAWX73PQ3W00QHXZG--swap_use_percent"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "01KBA31BNXAWX73PQ3W00QHXZG",
      "config_subentry_id": null,
      "created_at": 1764496551.750383,
      "device_id": "2ac79e2bf20b7e58eb2113d842ef6ef3",
      "disabled_by": null,
      "entity_category": null,
      "entity_id": "sensor.localhost_swap_use",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "21590b738e0dd958d7801ebf2e4ea731",
      "labels": [],
      "modified_at": 1764496551.752331,
      "name": null,
      "options": {
        "sensor": {
          "suggested_display_precision": 2
        },
        "conversation": {
          "should_expose": false
        }
      },
      "original_name": "暫存使用量",
      "platform": "glances",
      "translation_key": "swap_use",
      "unique_id": "01KBA31BNXAWX73PQ3W00QHXZG--swap_use"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "01KBA31BNXAWX73PQ3W00QHXZG",
      "config_subentry_id": null,
      "created_at": 1764496551.752854,
      "device_id": "2ac79e2bf20b7e58eb2113d842ef6ef3",
      "disabled_by": null,
      "entity_category": null,
      "entity_id": "sensor.localhost_swap_free",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "005b3445c059821106eec1f51a5997d3",
      "labels": [],
      "modified_at": 1764496551.753267,
      "name": null,
      "options": {
        "sensor": {
          "suggested_display_precision": 2
        },
        "conversation": {
          "should_expose": false
        }
      },
      "original_name": "暫存可用量",
      "platform": "glances",
      "translation_key": "swap_free",
      "unique_id": "01KBA31BNXAWX73PQ3W00QHXZG--swap_free"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "01KBA31BNXAWX73PQ3W00QHXZG",
      "config_subentry_id": null,
      "created_at": 1764496551.753731,
      "device_id": "2ac79e2bf20b7e58eb2113d842ef6ef3",
      "disabled_by": null,
      "entity_category": null,
      "entity_id": "sensor.localhost_cpu_load",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "d43e6380f1d43e203b55fdd94025a12c",
      "labels": [],
      "modified_at": 1764496551.754026,
      "name": null,
      "options": {
        "conversation": {
          "should_expose": false
        }
      },
      "original_name": "CPU 負載",
      "platform": "glances",
      "translation_key": "processor_load",
      "unique_id": "01KBA31BNXAWX73PQ3W00QHXZG--processor_load"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "01KBA31BNXAWX73PQ3W00QHXZG",
      "config_subentry_id": null,
      "created_at": 1764496551.754356,
      "device_id": "2ac79e2bf20b7e58eb2113d842ef6ef3",
      "disabled_by": null,
      "entity_category": null,
      "entity_id": "sensor.localhost_running",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "8e6bc89670316eec275297d754cf84ba",
      "labels": [],
      "modified_at": 1764496551.754664,
      "name": null,
      "options": {
        "conversation": {
          "should_expose": false
        }
      },
      "original_name": "執行中",
      "platform": "glances",
      "translation_key": "process_running",
      "unique_id": "01KBA31BNXAWX73PQ3W00QHXZG--process_running"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "01KBA31BNXAWX73PQ3W00QHXZG",
      "config_subentry_id": null,
      "created_at": 1764496551.755132,
      "device_id": "2ac79e2bf20b7e58eb2113d842ef6ef3",
      "disabled_by": null,
      "entity_category": null,
      "entity_id": "sensor.localhost_total",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "ce269b178972f6c0fcf4c49146a89903",
      "labels": [],
      "modified_at": 1764496551.755447,
      "name": null,
      "options": {
        "conversation": {
          "should_expose": false
        }
      },
      "original_name": "總計",
      "platform": "glances",
      "translation_key": "process_total",
      "unique_id": "01KBA31BNXAWX73PQ3W00QHXZG--process_total"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "01KBA31BNXAWX73PQ3W00QHXZG",
      "config_subentry_id": null,
      "created_at": 1764496551.755797,
      "device_id": "2ac79e2bf20b7e58eb2113d842ef6ef3",
      "disabled_by": null,
      "entity_category": null,
      "entity_id": "sensor.localhost_threads",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "e52a5390c5a1aa3066fc9ec79556e3f0",
      "labels": [],
      "modified_at": 1764496551.756076,
      "name": null,
      "options": {
        "conversation": {
          "should_expose": false
        }
      },
      "original_name": "執行緒",
      "platform": "glances",
      "translation_key": "process_threads",
      "unique_id": "01KBA31BNXAWX73PQ3W00QHXZG--process_thread"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "01KBA31BNXAWX73PQ3W00QHXZG",
      "config_subentry_id": null,
      "created_at": 1764496551.756396,
      "device_id": "2ac79e2bf20b7e58eb2113d842ef6ef3",
      "disabled_by": null,
      "entity_category": null,
      "entity_id": "sensor.localhost_sleeping",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "cb6b49d53a206536a038e5bf8019cc73",
      "labels": [],
      "modified_at": 1764496551.756684,
      "name": null,
      "options": {
        "conversation": {
          "should_expose": false
        }
      },
      "original_name": "休眠中",
      "platform": "glances",
      "translation_key": "process_sleeping",
      "unique_id": "01KBA31BNXAWX73PQ3W00QHXZG--process_sleeping"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "01KBA31BNXAWX73PQ3W00QHXZG",
      "config_subentry_id": null,
      "created_at": 1764496551.757005,
      "device_id": "2ac79e2bf20b7e58eb2113d842ef6ef3",
      "disabled_by": null,
      "entity_category": null,
      "entity_id": "sensor.localhost_cpu_usage",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "f5454ae244e2e6327a10bd4c6490741c",
      "labels": [],
      "modified_at": 1764496551.757292,
      "name": null,
      "options": {
        "conversation": {
          "should_expose": false
        }
      },
      "original_name": "CPU 使用率",
      "platform": "glances",
      "translation_key": "cpu_usage",
      "unique_id": "01KBA31BNXAWX73PQ3W00QHXZG--cpu_use_percent"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "01KBA31BNXAWX73PQ3W00QHXZG",
      "config_subentry_id": null,
      "created_at": 1764496551.757634,
      "device_id": "2ac79e2bf20b7e58eb2113d842ef6ef3",
      "disabled_by": null,
      "entity_category": null,
      "entity_id": "sensor.localhost_lo_rx",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "efa4c53cd58e27c19b7bc67a71bdf66e",
      "labels": [],
      "modified_at": 1764496551.758064,
      "name": null,
      "options": {
        "sensor.private": {
          "suggested_unit_of_measurement": "Mbit/s"
        },
        "sensor": {
          "suggested_display_precision": 2
        },
        "conversation": {
          "should_expose": false
        }
      },
      "original_name": "lo RX",
      "platform": "glances",
      "translation_key": "network_rx",
      "unique_id": "01KBA31BNXAWX73PQ3W00QHXZG-lo-rx"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "01KBA31BNXAWX73PQ3W00QHXZG",
      "config_subentry_id": null,
      "created_at": 1764496551.758498,
      "device_id": "2ac79e2bf20b7e58eb2113d842ef6ef3",
      "disabled_by": null,
      "entity_category": null,
      "entity_id": "sensor.localhost_lo_tx",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "2f599f34a7e45ce5bfac7661e0b0996b",
      "labels": [],
      "modified_at": 1764496551.75892,
      "name": null,
      "options": {
        "sensor.private": {
          "suggested_unit_of_measurement": "Mbit/s"
        },
        "sensor": {
          "suggested_display_precision": 2
        },
        "conversation": {
          "should_expose": false
        }
      },
      "original_name": "lo TX",
      "platform": "glances",
      "translation_key": "network_tx",
      "unique_id": "01KBA31BNXAWX73PQ3W00QHXZG-lo-tx"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "01KBA31BNXAWX73PQ3W00QHXZG",
      "config_subentry_id": null,
      "created_at": 1764496551.759355,
      "device_id": "2ac79e2bf20b7e58eb2113d842ef6ef3",
      "disabled_by": null,
      "entity_category": null,
      "entity_id": "sensor.localhost_enp1s0_rx",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "0098c7b297977d2e9a97797bd795b7ed",
      "labels": [],
      "modified_at": 1764496551.759734,
      "name": null,
      "options": {
        "sensor.private": {
          "suggested_unit_of_measurement": "Mbit/s"
        },
        "sensor": {
          "suggested_display_precision": 2
        },
        "conversation": {
          "should_expose": false
        }
      },
      "original_name": "enp1s0 RX",
      "platform": "glances",
      "translation_key": "network_rx",
      "unique_id": "01KBA31BNXAWX73PQ3W00QHXZG-enp1s0-rx"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "01KBA31BNXAWX73PQ3W00QHXZG",
      "config_subentry_id": null,
      "created_at": 1764496551.76017,
      "device_id": "2ac79e2bf20b7e58eb2113d842ef6ef3",
      "disabled_by": null,
      "entity_category": null,
      "entity_id": "sensor.localhost_enp1s0_tx",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "8390eb8fecce081a7f87f9ca47d664f4",
      "labels": [],
      "modified_at": 1764496551.760563,
      "name": null,
      "options": {
        "sensor.private": {
          "suggested_unit_of_measurement": "Mbit/s"
        },
        "sensor": {
          "suggested_display_precision": 2
        },
        "conversation": {
          "should_expose": false
        }
      },
      "original_name": "enp1s0 TX",
      "platform": "glances",
      "translation_key": "network_tx",
      "unique_id": "01KBA31BNXAWX73PQ3W00QHXZG-enp1s0-tx"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "01KBA31BNXAWX73PQ3W00QHXZG",
      "config_subentry_id": null,
      "created_at": 1764496551.760996,
      "device_id": "2ac79e2bf20b7e58eb2113d842ef6ef3",
      "disabled_by": null,
      "entity_category": null,
      "entity_id": "sensor.localhost_enp2s0_rx",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "a91fa57014f5cdbb939cf769af6cdbf0",
      "labels": [],
      "modified_at": 1764496551.761354,
      "name": null,
      "options": {
        "sensor.private": {
          "suggested_unit_of_measurement": "Mbit/s"
        },
        "sensor": {
          "suggested_display_precision": 2
        },
        "conversation": {
          "should_expose": false
        }
      },
      "original_name": "enp2s0 RX",
      "platform": "glances",
      "translation_key": "network_rx",
      "unique_id": "01KBA31BNXAWX73PQ3W00QHXZG-enp2s0-rx"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "01KBA31BNXAWX73PQ3W00QHXZG",
      "config_subentry_id": null,
      "created_at": 1764496551.761788,
      "device_id": "2ac79e2bf20b7e58eb2113d842ef6ef3",
      "disabled_by": null,
      "entity_category": null,
      "entity_id": "sensor.localhost_enp2s0_tx",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "8fd82f092cfb6bfcf74e4889abae0540",
      "labels": [],
      "modified_at": 1764496551.763076,
      "name": null,
      "options": {
        "sensor.private": {
          "suggested_unit_of_measurement": "Mbit/s"
        },
        "sensor": {
          "suggested_display_precision": 2
        },
        "conversation": {
          "should_expose": false
        }
      },
      "original_name": "enp2s0 TX",
      "platform": "glances",
      "translation_key": "network_tx",
      "unique_id": "01KBA31BNXAWX73PQ3W00QHXZG-enp2s0-tx"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "01KBA31BNXAWX73PQ3W00QHXZG",
      "config_subentry_id": null,
      "created_at": 1764496551.763683,
      "device_id": "2ac79e2bf20b7e58eb2113d842ef6ef3",
      "disabled_by": null,
      "entity_category": null,
      "entity_id": "sensor.localhost_wlp3s0_rx",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "d2336d227a13a6fa1dc70554fd885f0f",
      "labels": [],
      "modified_at": 1764496551.764114,
      "name": null,
      "options": {
        "sensor.private": {
          "suggested_unit_of_measurement": "Mbit/s"
        },
        "sensor": {
          "suggested_display_precision": 2
        },
        "conversation": {
          "should_expose": false
        }
      },
      "original_name": "wlp3s0 RX",
      "platform": "glances",
      "translation_key": "network_rx",
      "unique_id": "01KBA31BNXAWX73PQ3W00QHXZG-wlp3s0-rx"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "01KBA31BNXAWX73PQ3W00QHXZG",
      "config_subentry_id": null,
      "created_at": 1764496551.764539,
      "device_id": "2ac79e2bf20b7e58eb2113d842ef6ef3",
      "disabled_by": null,
      "entity_category": null,
      "entity_id": "sensor.localhost_wlp3s0_tx",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "b186c8bc54e610f0733c62d491928515",
      "labels": [],
      "modified_at": 1764496551.764933,
      "name": null,
      "options": {
        "sensor.private": {
          "suggested_unit_of_measurement": "Mbit/s"
        },
        "sensor": {
          "suggested_display_precision": 2
        },
        "conversation": {
          "should_expose": false
        }
      },
      "original_name": "wlp3s0 TX",
      "platform": "glances",
      "translation_key": "network_tx",
      "unique_id": "01KBA31BNXAWX73PQ3W00QHXZG-wlp3s0-tx"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "01KBA31BNXAWX73PQ3W00QHXZG",
      "config_subentry_id": null,
      "created_at": 1764496551.765358,
      "device_id": "2ac79e2bf20b7e58eb2113d842ef6ef3",
      "disabled_by": null,
      "entity_category": null,
      "entity_id": "sensor.localhost_hassio_rx",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "f9053a289b189c24850ad23a60ff34a1",
      "labels": [],
      "modified_at": 1764496551.76574,
      "name": null,
      "options": {
        "sensor.private": {
          "suggested_unit_of_measurement": "Mbit/s"
        },
        "sensor": {
          "suggested_display_precision": 2
        },
        "conversation": {
          "should_expose": false
        }
      },
      "original_name": "hassio RX",
      "platform": "glances",
      "translation_key": "network_rx",
      "unique_id": "01KBA31BNXAWX73PQ3W00QHXZG-hassio-rx"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "01KBA31BNXAWX73PQ3W00QHXZG",
      "config_subentry_id": null,
      "created_at": 1764496551.766173,
      "device_id": "2ac79e2bf20b7e58eb2113d842ef6ef3",
      "disabled_by": null,
      "entity_category": null,
      "entity_id": "sensor.localhost_hassio_tx",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "486fd30f35e701265737cc23029d63c1",
      "labels": [],
      "modified_at": 1764496551.766546,
      "name": null,
      "options": {
        "sensor.private": {
          "suggested_unit_of_measurement": "Mbit/s"
        },
        "sensor": {
          "suggested_display_precision": 2
        },
        "conversation": {
          "should_expose": false
        }
      },
      "original_name": "hassio TX",
      "platform": "glances",
      "translation_key": "network_tx",
      "unique_id": "01KBA31BNXAWX73PQ3W00QHXZG-hassio-tx"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "01KBA31BNXAWX73PQ3W00QHXZG",
      "config_subentry_id": null,
      "created_at": 1764496551.766966,
      "device_id": "2ac79e2bf20b7e58eb2113d842ef6ef3",
      "disabled_by": null,
      "entity_category": null,
      "entity_id": "sensor.localhost_docker0_rx",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "ff6b69bf617bb5847ec4647c8109c118",
      "labels": [],
      "modified_at": 1764496551.767347,
      "name": null,
      "options": {
        "sensor.private": {
          "suggested_unit_of_measurement": "Mbit/s"
        },
        "sensor": {
          "suggested_display_precision": 2
        },
        "conversation": {
          "should_expose": false
        }
      },
      "original_name": "docker0 RX",
      "platform": "glances",
      "translation_key": "network_rx",
      "unique_id": "01KBA31BNXAWX73PQ3W00QHXZG-docker0-rx"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "01KBA31BNXAWX73PQ3W00QHXZG",
      "config_subentry_id": null,
      "created_at": 1764496551.767781,
      "device_id": "2ac79e2bf20b7e58eb2113d842ef6ef3",
      "disabled_by": null,
      "entity_category": null,
      "entity_id": "sensor.localhost_docker0_tx",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "81db7e9c87939ccc657dceaa0d1f5dd9",
      "labels": [],
      "modified_at": 1764496551.768189,
      "name": null,
      "options": {
        "sensor.private": {
          "suggested_unit_of_measurement": "Mbit/s"
        },
        "sensor": {
          "suggested_display_precision": 2
        },
        "conversation": {
          "should_expose": false
        }
      },
      "original_name": "docker0 TX",
      "platform": "glances",
      "translation_key": "network_tx",
      "unique_id": "01KBA31BNXAWX73PQ3W00QHXZG-docker0-tx"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "01KBA31BNXAWX73PQ3W00QHXZG",
      "config_subentry_id": null,
      "created_at": 1764496551.768625,
      "device_id": "2ac79e2bf20b7e58eb2113d842ef6ef3",
      "disabled_by": null,
      "entity_category": null,
      "entity_id": "sensor.localhost_vethb078a08_rx",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "df753a2917625bb8e0513b7d0ba4275c",
      "labels": [],
      "modified_at": 1764496551.769015,
      "name": null,
      "options": {
        "sensor.private": {
          "suggested_unit_of_measurement": "Mbit/s"
        },
        "sensor": {
          "suggested_display_precision": 2
        },
        "conversation": {
          "should_expose": false
        }
      },
      "original_name": "vethb078a08 RX",
      "platform": "glances",
      "translation_key": "network_rx",
      "unique_id": "01KBA31BNXAWX73PQ3W00QHXZG-vethb078a08-rx"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "01KBA31BNXAWX73PQ3W00QHXZG",
      "config_subentry_id": null,
      "created_at": 1764496551.769432,
      "device_id": "2ac79e2bf20b7e58eb2113d842ef6ef3",
      "disabled_by": null,
      "entity_category": null,
      "entity_id": "sensor.localhost_vethb078a08_tx",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "544605ae631a7354945ee5be08c9194f",
      "labels": [],
      "modified_at": 1764496551.76981,
      "name": null,
      "options": {
        "sensor.private": {
          "suggested_unit_of_measurement": "Mbit/s"
        },
        "sensor": {
          "suggested_display_precision": 2
        },
        "conversation": {
          "should_expose": false
        }
      },
      "original_name": "vethb078a08 TX",
      "platform": "glances",
      "translation_key": "network_tx",
      "unique_id": "01KBA31BNXAWX73PQ3W00QHXZG-vethb078a08-tx"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "01KBA31BNXAWX73PQ3W00QHXZG",
      "config_subentry_id": null,
      "created_at": 1764496551.770232,
      "device_id": "2ac79e2bf20b7e58eb2113d842ef6ef3",
      "disabled_by": null,
      "entity_category": null,
      "entity_id": "sensor.localhost_vethfc079cd_rx",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "68b97362257c48eaf44cf46c5b7d0c89",
      "labels": [],
      "modified_at": 1764496551.770594,
      "name": null,
      "options": {
        "sensor.private": {
          "suggested_unit_of_measurement": "Mbit/s"
        },
        "sensor": {
          "suggested_display_precision": 2
        },
        "conversation": {
          "should_expose": false
        }
      },
      "original_name": "vethfc079cd RX",
      "platform": "glances",
      "translation_key": "network_rx",
      "unique_id": "01KBA31BNXAWX73PQ3W00QHXZG-vethfc079cd-rx"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "01KBA31BNXAWX73PQ3W00QHXZG",
      "config_subentry_id": null,
      "created_at": 1764496551.771027,
      "device_id": "2ac79e2bf20b7e58eb2113d842ef6ef3",
      "disabled_by": null,
      "entity_category": null,
      "entity_id": "sensor.localhost_vethfc079cd_tx",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "ab9b6b648b6f4df56e172ef2905e3827",
      "labels": [],
      "modified_at": 1764496551.77142,
      "name": null,
      "options": {
        "sensor.private": {
          "suggested_unit_of_measurement": "Mbit/s"
        },
        "sensor": {
          "suggested_display_precision": 2
        },
        "conversation": {
          "should_expose": false
        }
      },
      "original_name": "vethfc079cd TX",
      "platform": "glances",
      "translation_key": "network_tx",
      "unique_id": "01KBA31BNXAWX73PQ3W00QHXZG-vethfc079cd-tx"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "01KBA31BNXAWX73PQ3W00QHXZG",
      "config_subentry_id": null,
      "created_at": 1764496551.771866,
      "device_id": "2ac79e2bf20b7e58eb2113d842ef6ef3",
      "disabled_by": null,
      "entity_category": null,
      "entity_id": "sensor.localhost_veth0fc7b01_rx",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "b4b69c91c58e5e42a59b980d71f478a6",
      "labels": [],
      "modified_at": 1764496551.772239,
      "name": null,
      "options": {
        "sensor.private": {
          "suggested_unit_of_measurement": "Mbit/s"
        },
        "sensor": {
          "suggested_display_precision": 2
        },
        "conversation": {
          "should_expose": false
        }
      },
      "original_name": "veth0fc7b01 RX",
      "platform": "glances",
      "translation_key": "network_rx",
      "unique_id": "01KBA31BNXAWX73PQ3W00QHXZG-veth0fc7b01-rx"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "01KBA31BNXAWX73PQ3W00QHXZG",
      "config_subentry_id": null,
      "created_at": 1764496551.77265,
      "device_id": "2ac79e2bf20b7e58eb2113d842ef6ef3",
      "disabled_by": null,
      "entity_category": null,
      "entity_id": "sensor.localhost_veth0fc7b01_tx",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "ee4ab7bb01d3f8a9bd79ee7dc5441c18",
      "labels": [],
      "modified_at": 1764496551.773038,
      "name": null,
      "options": {
        "sensor.private": {
          "suggested_unit_of_measurement": "Mbit/s"
        },
        "sensor": {
          "suggested_display_precision": 2
        },
        "conversation": {
          "should_expose": false
        }
      },
      "original_name": "veth0fc7b01 TX",
      "platform": "glances",
      "translation_key": "network_tx",
      "unique_id": "01KBA31BNXAWX73PQ3W00QHXZG-veth0fc7b01-tx"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "01KBA31BNXAWX73PQ3W00QHXZG",
      "config_subentry_id": null,
      "created_at": 1764496551.774965,
      "device_id": "2ac79e2bf20b7e58eb2113d842ef6ef3",
      "disabled_by": null,
      "entity_category": null,
      "entity_id": "sensor.localhost_vethc0fead1_rx",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "1cb2de03042e0b1f3dd41b84f78f18dc",
      "labels": [],
      "modified_at": 1764496551.775443,
      "name": null,
      "options": {
        "sensor.private": {
          "suggested_unit_of_measurement": "Mbit/s"
        },
        "sensor": {
          "suggested_display_precision": 2
        },
        "conversation": {
          "should_expose": false
        }
      },
      "original_name": "vethc0fead1 RX",
      "platform": "glances",
      "translation_key": "network_rx",
      "unique_id": "01KBA31BNXAWX73PQ3W00QHXZG-vethc0fead1-rx"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "01KBA31BNXAWX73PQ3W00QHXZG",
      "config_subentry_id": null,
      "created_at": 1764496551.775901,
      "device_id": "2ac79e2bf20b7e58eb2113d842ef6ef3",
      "disabled_by": null,
      "entity_category": null,
      "entity_id": "sensor.localhost_vethc0fead1_tx",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "609a4aa51437e7c8d22cb40f8eacb941",
      "labels": [],
      "modified_at": 1764496551.776291,
      "name": null,
      "options": {
        "sensor.private": {
          "suggested_unit_of_measurement": "Mbit/s"
        },
        "sensor": {
          "suggested_display_precision": 2
        },
        "conversation": {
          "should_expose": false
        }
      },
      "original_name": "vethc0fead1 TX",
      "platform": "glances",
      "translation_key": "network_tx",
      "unique_id": "01KBA31BNXAWX73PQ3W00QHXZG-vethc0fead1-tx"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "01KBA31BNXAWX73PQ3W00QHXZG",
      "config_subentry_id": null,
      "created_at": 1764496551.776728,
      "device_id": "2ac79e2bf20b7e58eb2113d842ef6ef3",
      "disabled_by": null,
      "entity_category": null,
      "entity_id": "sensor.localhost_veth9151383_rx",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "68bf68ff777998bf27a4eeec61296299",
      "labels": [],
      "modified_at": 1764496551.777102,
      "name": null,
      "options": {
        "sensor.private": {
          "suggested_unit_of_measurement": "Mbit/s"
        },
        "sensor": {
          "suggested_display_precision": 2
        },
        "conversation": {
          "should_expose": false
        }
      },
      "original_name": "veth9151383 RX",
      "platform": "glances",
      "translation_key": "network_rx",
      "unique_id": "01KBA31BNXAWX73PQ3W00QHXZG-veth9151383-rx"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "01KBA31BNXAWX73PQ3W00QHXZG",
      "config_subentry_id": null,
      "created_at": 1764496551.777512,
      "device_id": "2ac79e2bf20b7e58eb2113d842ef6ef3",
      "disabled_by": null,
      "entity_category": null,
      "entity_id": "sensor.localhost_veth9151383_tx",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "a9a45fbba37edf516507ddf87cedd968",
      "labels": [],
      "modified_at": 1764496551.777908,
      "name": null,
      "options": {
        "sensor.private": {
          "suggested_unit_of_measurement": "Mbit/s"
        },
        "sensor": {
          "suggested_display_precision": 2
        },
        "conversation": {
          "should_expose": false
        }
      },
      "original_name": "veth9151383 TX",
      "platform": "glances",
      "translation_key": "network_tx",
      "unique_id": "01KBA31BNXAWX73PQ3W00QHXZG-veth9151383-tx"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "01KBA31BNXAWX73PQ3W00QHXZG",
      "config_subentry_id": null,
      "created_at": 1764496551.778341,
      "device_id": "2ac79e2bf20b7e58eb2113d842ef6ef3",
      "disabled_by": null,
      "entity_category": null,
      "entity_id": "sensor.localhost_veth58593b6_rx",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "8a13bdd852ea4cd76e40161058cd6cf4",
      "labels": [],
      "modified_at": 1764496551.778713,
      "name": null,
      "options": {
        "sensor.private": {
          "suggested_unit_of_measurement": "Mbit/s"
        },
        "sensor": {
          "suggested_display_precision": 2
        },
        "conversation": {
          "should_expose": false
        }
      },
      "original_name": "veth58593b6 RX",
      "platform": "glances",
      "translation_key": "network_rx",
      "unique_id": "01KBA31BNXAWX73PQ3W00QHXZG-veth58593b6-rx"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "01KBA31BNXAWX73PQ3W00QHXZG",
      "config_subentry_id": null,
      "created_at": 1764496551.779133,
      "device_id": "2ac79e2bf20b7e58eb2113d842ef6ef3",
      "disabled_by": null,
      "entity_category": null,
      "entity_id": "sensor.localhost_veth58593b6_tx",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "03945b9e247fbf3570800976b49fa164",
      "labels": [],
      "modified_at": 1764496551.779505,
      "name": null,
      "options": {
        "sensor.private": {
          "suggested_unit_of_measurement": "Mbit/s"
        },
        "sensor": {
          "suggested_display_precision": 2
        },
        "conversation": {
          "should_expose": false
        }
      },
      "original_name": "veth58593b6 TX",
      "platform": "glances",
      "translation_key": "network_tx",
      "unique_id": "01KBA31BNXAWX73PQ3W00QHXZG-veth58593b6-tx"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "01KBA31BNXAWX73PQ3W00QHXZG",
      "config_subentry_id": null,
      "created_at": 1764496551.779948,
      "device_id": "2ac79e2bf20b7e58eb2113d842ef6ef3",
      "disabled_by": null,
      "entity_category": null,
      "entity_id": "sensor.localhost_veth5c8370f_rx",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "db386d37930e98ea4f0ec397df00a585",
      "labels": [],
      "modified_at": 1764496551.780325,
      "name": null,
      "options": {
        "sensor.private": {
          "suggested_unit_of_measurement": "Mbit/s"
        },
        "sensor": {
          "suggested_display_precision": 2
        },
        "conversation": {
          "should_expose": false
        }
      },
      "original_name": "veth5c8370f RX",
      "platform": "glances",
      "translation_key": "network_rx",
      "unique_id": "01KBA31BNXAWX73PQ3W00QHXZG-veth5c8370f-rx"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "01KBA31BNXAWX73PQ3W00QHXZG",
      "config_subentry_id": null,
      "created_at": 1764496551.78075,
      "device_id": "2ac79e2bf20b7e58eb2113d842ef6ef3",
      "disabled_by": null,
      "entity_category": null,
      "entity_id": "sensor.localhost_veth5c8370f_tx",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "3480d32836287551aa7dadc027fdd31c",
      "labels": [],
      "modified_at": 1764496551.781118,
      "name": null,
      "options": {
        "sensor.private": {
          "suggested_unit_of_measurement": "Mbit/s"
        },
        "sensor": {
          "suggested_display_precision": 2
        },
        "conversation": {
          "should_expose": false
        }
      },
      "original_name": "veth5c8370f TX",
      "platform": "glances",
      "translation_key": "network_tx",
      "unique_id": "01KBA31BNXAWX73PQ3W00QHXZG-veth5c8370f-tx"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "01KBA31BNXAWX73PQ3W00QHXZG",
      "config_subentry_id": null,
      "created_at": 1764496551.781523,
      "device_id": "2ac79e2bf20b7e58eb2113d842ef6ef3",
      "disabled_by": null,
      "entity_category": null,
      "entity_id": "sensor.localhost_veth97b1051_rx",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "6988d10db12e74041adfc4eb8cd2a22e",
      "labels": [],
      "modified_at": 1764496551.781915,
      "name": null,
      "options": {
        "sensor.private": {
          "suggested_unit_of_measurement": "Mbit/s"
        },
        "sensor": {
          "suggested_display_precision": 2
        },
        "conversation": {
          "should_expose": false
        }
      },
      "original_name": "veth97b1051 RX",
      "platform": "glances",
      "translation_key": "network_rx",
      "unique_id": "01KBA31BNXAWX73PQ3W00QHXZG-veth97b1051-rx"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "01KBA31BNXAWX73PQ3W00QHXZG",
      "config_subentry_id": null,
      "created_at": 1764496551.782324,
      "device_id": "2ac79e2bf20b7e58eb2113d842ef6ef3",
      "disabled_by": null,
      "entity_category": null,
      "entity_id": "sensor.localhost_veth97b1051_tx",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "f7f8d4917213acd3cb649d117ca99a73",
      "labels": [],
      "modified_at": 1764496551.782708,
      "name": null,
      "options": {
        "sensor.private": {
          "suggested_unit_of_measurement": "Mbit/s"
        },
        "sensor": {
          "suggested_display_precision": 2
        },
        "conversation": {
          "should_expose": false
        }
      },
      "original_name": "veth97b1051 TX",
      "platform": "glances",
      "translation_key": "network_tx",
      "unique_id": "01KBA31BNXAWX73PQ3W00QHXZG-veth97b1051-tx"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "01KBA31BNXAWX73PQ3W00QHXZG",
      "config_subentry_id": null,
      "created_at": 1764496551.783132,
      "device_id": "2ac79e2bf20b7e58eb2113d842ef6ef3",
      "disabled_by": null,
      "entity_category": null,
      "entity_id": "sensor.localhost_veth58c215a_rx",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "b53525588c888d7330475619b8a39c40",
      "labels": [],
      "modified_at": 1764496551.783505,
      "name": null,
      "options": {
        "sensor.private": {
          "suggested_unit_of_measurement": "Mbit/s"
        },
        "sensor": {
          "suggested_display_precision": 2
        },
        "conversation": {
          "should_expose": false
        }
      },
      "original_name": "veth58c215a RX",
      "platform": "glances",
      "translation_key": "network_rx",
      "unique_id": "01KBA31BNXAWX73PQ3W00QHXZG-veth58c215a-rx"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "01KBA31BNXAWX73PQ3W00QHXZG",
      "config_subentry_id": null,
      "created_at": 1764496551.783921,
      "device_id": "2ac79e2bf20b7e58eb2113d842ef6ef3",
      "disabled_by": null,
      "entity_category": null,
      "entity_id": "sensor.localhost_veth58c215a_tx",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "5a0b3faf0c2a61131908f6847f744c01",
      "labels": [],
      "modified_at": 1764496551.784281,
      "name": null,
      "options": {
        "sensor.private": {
          "suggested_unit_of_measurement": "Mbit/s"
        },
        "sensor": {
          "suggested_display_precision": 2
        },
        "conversation": {
          "should_expose": false
        }
      },
      "original_name": "veth58c215a TX",
      "platform": "glances",
      "translation_key": "network_tx",
      "unique_id": "01KBA31BNXAWX73PQ3W00QHXZG-veth58c215a-tx"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "01KBA31BNXAWX73PQ3W00QHXZG",
      "config_subentry_id": null,
      "created_at": 1764496551.784701,
      "device_id": "2ac79e2bf20b7e58eb2113d842ef6ef3",
      "disabled_by": null,
      "entity_category": null,
      "entity_id": "sensor.localhost_vethf4dcf75_rx",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "f63a5500ac8ff403f50f0e55d8272cff",
      "labels": [],
      "modified_at": 1764496551.787273,
      "name": null,
      "options": {
        "sensor.private": {
          "suggested_unit_of_measurement": "Mbit/s"
        },
        "sensor": {
          "suggested_display_precision": 2
        },
        "conversation": {
          "should_expose": false
        }
      },
      "original_name": "vethf4dcf75 RX",
      "platform": "glances",
      "translation_key": "network_rx",
      "unique_id": "01KBA31BNXAWX73PQ3W00QHXZG-vethf4dcf75-rx"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "01KBA31BNXAWX73PQ3W00QHXZG",
      "config_subentry_id": null,
      "created_at": 1764496551.78778,
      "device_id": "2ac79e2bf20b7e58eb2113d842ef6ef3",
      "disabled_by": null,
      "entity_category": null,
      "entity_id": "sensor.localhost_vethf4dcf75_tx",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "386f9fd9c8a78db52e47a11692aa3c47",
      "labels": [],
      "modified_at": 1764496551.788169,
      "name": null,
      "options": {
        "sensor.private": {
          "suggested_unit_of_measurement": "Mbit/s"
        },
        "sensor": {
          "suggested_display_precision": 2
        },
        "conversation": {
          "should_expose": false
        }
      },
      "original_name": "vethf4dcf75 TX",
      "platform": "glances",
      "translation_key": "network_tx",
      "unique_id": "01KBA31BNXAWX73PQ3W00QHXZG-vethf4dcf75-tx"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "01KBA31BNXAWX73PQ3W00QHXZG",
      "config_subentry_id": null,
      "created_at": 1764496551.788605,
      "device_id": "2ac79e2bf20b7e58eb2113d842ef6ef3",
      "disabled_by": null,
      "entity_category": null,
      "entity_id": "sensor.localhost_veth3befb79_rx",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "c3b0d1edce739c2a08bffd6acff82bf9",
      "labels": [],
      "modified_at": 1764496551.788984,
      "name": null,
      "options": {
        "sensor.private": {
          "suggested_unit_of_measurement": "Mbit/s"
        },
        "sensor": {
          "suggested_display_precision": 2
        },
        "conversation": {
          "should_expose": false
        }
      },
      "original_name": "veth3befb79 RX",
      "platform": "glances",
      "translation_key": "network_rx",
      "unique_id": "01KBA31BNXAWX73PQ3W00QHXZG-veth3befb79-rx"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "01KBA31BNXAWX73PQ3W00QHXZG",
      "config_subentry_id": null,
      "created_at": 1764496551.789401,
      "device_id": "2ac79e2bf20b7e58eb2113d842ef6ef3",
      "disabled_by": null,
      "entity_category": null,
      "entity_id": "sensor.localhost_veth3befb79_tx",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "8882bfd6370cf5823a0fc81262d90259",
      "labels": [],
      "modified_at": 1764496551.78978,
      "name": null,
      "options": {
        "sensor.private": {
          "suggested_unit_of_measurement": "Mbit/s"
        },
        "sensor": {
          "suggested_display_precision": 2
        },
        "conversation": {
          "should_expose": false
        }
      },
      "original_name": "veth3befb79 TX",
      "platform": "glances",
      "translation_key": "network_tx",
      "unique_id": "01KBA31BNXAWX73PQ3W00QHXZG-veth3befb79-tx"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "01KBA31BNXAWX73PQ3W00QHXZG",
      "config_subentry_id": null,
      "created_at": 1764496551.790207,
      "device_id": "2ac79e2bf20b7e58eb2113d842ef6ef3",
      "disabled_by": null,
      "entity_category": null,
      "entity_id": "sensor.localhost_veth5aea80c_rx",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "6bebb224a88370a547c981cc2e95e4bc",
      "labels": [],
      "modified_at": 1764496551.790589,
      "name": null,
      "options": {
        "sensor.private": {
          "suggested_unit_of_measurement": "Mbit/s"
        },
        "sensor": {
          "suggested_display_precision": 2
        },
        "conversation": {
          "should_expose": false
        }
      },
      "original_name": "veth5aea80c RX",
      "platform": "glances",
      "translation_key": "network_rx",
      "unique_id": "01KBA31BNXAWX73PQ3W00QHXZG-veth5aea80c-rx"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "01KBA31BNXAWX73PQ3W00QHXZG",
      "config_subentry_id": null,
      "created_at": 1764496551.791023,
      "device_id": "2ac79e2bf20b7e58eb2113d842ef6ef3",
      "disabled_by": null,
      "entity_category": null,
      "entity_id": "sensor.localhost_veth5aea80c_tx",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "d8fdddc7e426759771dbc672d1e6f01b",
      "labels": [],
      "modified_at": 1764496551.791404,
      "name": null,
      "options": {
        "sensor.private": {
          "suggested_unit_of_measurement": "Mbit/s"
        },
        "sensor": {
          "suggested_display_precision": 2
        },
        "conversation": {
          "should_expose": false
        }
      },
      "original_name": "veth5aea80c TX",
      "platform": "glances",
      "translation_key": "network_tx",
      "unique_id": "01KBA31BNXAWX73PQ3W00QHXZG-veth5aea80c-tx"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "01KBA31BNXAWX73PQ3W00QHXZG",
      "config_subentry_id": null,
      "created_at": 1764496551.79185,
      "device_id": "2ac79e2bf20b7e58eb2113d842ef6ef3",
      "disabled_by": null,
      "entity_category": null,
      "entity_id": "sensor.localhost_vethff12b05_rx",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "cf3840790121287a827a9854579b973b",
      "labels": [],
      "modified_at": 1764496551.79225,
      "name": null,
      "options": {
        "sensor.private": {
          "suggested_unit_of_measurement": "Mbit/s"
        },
        "sensor": {
          "suggested_display_precision": 2
        },
        "conversation": {
          "should_expose": false
        }
      },
      "original_name": "vethff12b05 RX",
      "platform": "glances",
      "translation_key": "network_rx",
      "unique_id": "01KBA31BNXAWX73PQ3W00QHXZG-vethff12b05-rx"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "01KBA31BNXAWX73PQ3W00QHXZG",
      "config_subentry_id": null,
      "created_at": 1764496551.792667,
      "device_id": "2ac79e2bf20b7e58eb2113d842ef6ef3",
      "disabled_by": null,
      "entity_category": null,
      "entity_id": "sensor.localhost_vethff12b05_tx",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "1bb5e1de34c1dca4c4e05ebe6de93bcc",
      "labels": [],
      "modified_at": 1764496551.793055,
      "name": null,
      "options": {
        "sensor.private": {
          "suggested_unit_of_measurement": "Mbit/s"
        },
        "sensor": {
          "suggested_display_precision": 2
        },
        "conversation": {
          "should_expose": false
        }
      },
      "original_name": "vethff12b05 TX",
      "platform": "glances",
      "translation_key": "network_tx",
      "unique_id": "01KBA31BNXAWX73PQ3W00QHXZG-vethff12b05-tx"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "01KBA31BNXAWX73PQ3W00QHXZG",
      "config_subentry_id": null,
      "created_at": 1764496551.793476,
      "device_id": "2ac79e2bf20b7e58eb2113d842ef6ef3",
      "disabled_by": null,
      "entity_category": null,
      "entity_id": "sensor.localhost_containers_active",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "25736ef27d708366bffd55229f1fa07b",
      "labels": [],
      "modified_at": 1764496551.793768,
      "name": null,
      "options": {
        "conversation": {
          "should_expose": false
        }
      },
      "original_name": "Container 活動",
      "platform": "glances",
      "translation_key": "container_active",
      "unique_id": "01KBA31BNXAWX73PQ3W00QHXZG--docker_active"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "01KBA31BNXAWX73PQ3W00QHXZG",
      "config_subentry_id": null,
      "created_at": 1764496551.794108,
      "device_id": "2ac79e2bf20b7e58eb2113d842ef6ef3",
      "disabled_by": null,
      "entity_category": null,
      "entity_id": "sensor.localhost_containers_cpu_usage",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "ae1a5edc8bdd9682335033ff7abfb6dd",
      "labels": [],
      "modified_at": 1764496551.794397,
      "name": null,
      "options": {
        "conversation": {
          "should_expose": false
        }
      },
      "original_name": "Container CPU 使用率",
      "platform": "glances",
      "translation_key": "container_cpu_usage",
      "unique_id": "01KBA31BNXAWX73PQ3W00QHXZG--docker_cpu_use"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "01KBA31BNXAWX73PQ3W00QHXZG",
      "config_subentry_id": null,
      "created_at": 1764496551.794787,
      "device_id": "2ac79e2bf20b7e58eb2113d842ef6ef3",
      "disabled_by": null,
      "entity_category": null,
      "entity_id": "sensor.localhost_containers_memory_used",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "884273af1ffa848669dc1e93273503af",
      "labels": [],
      "modified_at": 1764496551.795192,
      "name": null,
      "options": {
        "sensor": {
          "suggested_display_precision": 2
        },
        "conversation": {
          "should_expose": false
        }
      },
      "original_name": "Container 記憶體使用量",
      "platform": "glances",
      "translation_key": "container_memory_used",
      "unique_id": "01KBA31BNXAWX73PQ3W00QHXZG--docker_memory_use"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "01KBA31BNXAWX73PQ3W00QHXZG",
      "config_subentry_id": null,
      "created_at": 1764496551.795612,
      "device_id": "2ac79e2bf20b7e58eb2113d842ef6ef3",
      "disabled_by": null,
      "entity_category": null,
      "entity_id": "sensor.localhost_zram0_disk_read",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "a5f8cfa0ffefb65d072520fea3f0f19f",
      "labels": [],
      "modified_at": 1764496551.796469,
      "name": null,
      "options": {
        "sensor.private": {
          "suggested_unit_of_measurement": "MB/s"
        },
        "sensor": {
          "suggested_display_precision": 2
        },
        "conversation": {
          "should_expose": false
        }
      },
      "original_name": "zram0磁碟讀取",
      "platform": "glances",
      "translation_key": "diskio_read",
      "unique_id": "01KBA31BNXAWX73PQ3W00QHXZG-zram0-read"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "01KBA31BNXAWX73PQ3W00QHXZG",
      "config_subentry_id": null,
      "created_at": 1764496551.797834,
      "device_id": "2ac79e2bf20b7e58eb2113d842ef6ef3",
      "disabled_by": null,
      "entity_category": null,
      "entity_id": "sensor.localhost_zram0_disk_write",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "59b7f97fc40d47f52abf865795f8ab59",
      "labels": [],
      "modified_at": 1764496551.798319,
      "name": null,
      "options": {
        "sensor.private": {
          "suggested_unit_of_measurement": "MB/s"
        },
        "sensor": {
          "suggested_display_precision": 2
        },
        "conversation": {
          "should_expose": false
        }
      },
      "original_name": "zram0磁碟寫入",
      "platform": "glances",
      "translation_key": "diskio_write",
      "unique_id": "01KBA31BNXAWX73PQ3W00QHXZG-zram0-write"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "01KBA31BNXAWX73PQ3W00QHXZG",
      "config_subentry_id": null,
      "created_at": 1764496551.798759,
      "device_id": "2ac79e2bf20b7e58eb2113d842ef6ef3",
      "disabled_by": null,
      "entity_category": null,
      "entity_id": "sensor.localhost_zram1_disk_read",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "cadab3fc40eec00492da954caac31f01",
      "labels": [],
      "modified_at": 1764496551.799134,
      "name": null,
      "options": {
        "sensor.private": {
          "suggested_unit_of_measurement": "MB/s"
        },
        "sensor": {
          "suggested_display_precision": 2
        },
        "conversation": {
          "should_expose": false
        }
      },
      "original_name": "zram1磁碟讀取",
      "platform": "glances",
      "translation_key": "diskio_read",
      "unique_id": "01KBA31BNXAWX73PQ3W00QHXZG-zram1-read"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "01KBA31BNXAWX73PQ3W00QHXZG",
      "config_subentry_id": null,
      "created_at": 1764496551.799541,
      "device_id": "2ac79e2bf20b7e58eb2113d842ef6ef3",
      "disabled_by": null,
      "entity_category": null,
      "entity_id": "sensor.localhost_zram1_disk_write",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "653b66eaed3c8ce86ad88218e0cdddd7",
      "labels": [],
      "modified_at": 1764496551.799911,
      "name": null,
      "options": {
        "sensor.private": {
          "suggested_unit_of_measurement": "MB/s"
        },
        "sensor": {
          "suggested_display_precision": 2
        },
        "conversation": {
          "should_expose": false
        }
      },
      "original_name": "zram1磁碟寫入",
      "platform": "glances",
      "translation_key": "diskio_write",
      "unique_id": "01KBA31BNXAWX73PQ3W00QHXZG-zram1-write"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "01KBA31BNXAWX73PQ3W00QHXZG",
      "config_subentry_id": null,
      "created_at": 1764496551.800309,
      "device_id": "2ac79e2bf20b7e58eb2113d842ef6ef3",
      "disabled_by": null,
      "entity_category": null,
      "entity_id": "sensor.localhost_zram2_disk_read",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "da035d09baa4bae1fc3248af8712d603",
      "labels": [],
      "modified_at": 1764496551.800668,
      "name": null,
      "options": {
        "sensor.private": {
          "suggested_unit_of_measurement": "MB/s"
        },
        "sensor": {
          "suggested_display_precision": 2
        },
        "conversation": {
          "should_expose": false
        }
      },
      "original_name": "zram2磁碟讀取",
      "platform": "glances",
      "translation_key": "diskio_read",
      "unique_id": "01KBA31BNXAWX73PQ3W00QHXZG-zram2-read"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "01KBA31BNXAWX73PQ3W00QHXZG",
      "config_subentry_id": null,
      "created_at": 1764496551.801079,
      "device_id": "2ac79e2bf20b7e58eb2113d842ef6ef3",
      "disabled_by": null,
      "entity_category": null,
      "entity_id": "sensor.localhost_zram2_disk_write",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "f8e5bf4703fd56309fd6ebed0c498b33",
      "labels": [],
      "modified_at": 1764496551.801482,
      "name": null,
      "options": {
        "sensor.private": {
          "suggested_unit_of_measurement": "MB/s"
        },
        "sensor": {
          "suggested_display_precision": 2
        },
        "conversation": {
          "should_expose": false
        }
      },
      "original_name": "zram2磁碟寫入",
      "platform": "glances",
      "translation_key": "diskio_write",
      "unique_id": "01KBA31BNXAWX73PQ3W00QHXZG-zram2-write"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "01KBA31BNXAWX73PQ3W00QHXZG",
      "config_subentry_id": null,
      "created_at": 1764496551.801942,
      "device_id": "2ac79e2bf20b7e58eb2113d842ef6ef3",
      "disabled_by": null,
      "entity_category": null,
      "entity_id": "sensor.localhost_sda_disk_read",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "9aea27c8160a13ca93465fc48d5fe7da",
      "labels": [],
      "modified_at": 1764496551.802313,
      "name": null,
      "options": {
        "sensor.private": {
          "suggested_unit_of_measurement": "MB/s"
        },
        "sensor": {
          "suggested_display_precision": 2
        },
        "conversation": {
          "should_expose": false
        }
      },
      "original_name": "sda磁碟讀取",
      "platform": "glances",
      "translation_key": "diskio_read",
      "unique_id": "01KBA31BNXAWX73PQ3W00QHXZG-sda-read"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "01KBA31BNXAWX73PQ3W00QHXZG",
      "config_subentry_id": null,
      "created_at": 1764496551.802737,
      "device_id": "2ac79e2bf20b7e58eb2113d842ef6ef3",
      "disabled_by": null,
      "entity_category": null,
      "entity_id": "sensor.localhost_sda_disk_write",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "ecee6af483c5200f447b8b3b83222ac0",
      "labels": [],
      "modified_at": 1764496551.803125,
      "name": null,
      "options": {
        "sensor.private": {
          "suggested_unit_of_measurement": "MB/s"
        },
        "sensor": {
          "suggested_display_precision": 2
        },
        "conversation": {
          "should_expose": false
        }
      },
      "original_name": "sda磁碟寫入",
      "platform": "glances",
      "translation_key": "diskio_write",
      "unique_id": "01KBA31BNXAWX73PQ3W00QHXZG-sda-write"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "01KBA31BNXAWX73PQ3W00QHXZG",
      "config_subentry_id": null,
      "created_at": 1764496551.803528,
      "device_id": "2ac79e2bf20b7e58eb2113d842ef6ef3",
      "disabled_by": null,
      "entity_category": null,
      "entity_id": "sensor.localhost_sda1_disk_read",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "60c775066a362a3397a90a0abf7c14d7",
      "labels": [],
      "modified_at": 1764496551.803923,
      "name": null,
      "options": {
        "sensor.private": {
          "suggested_unit_of_measurement": "MB/s"
        },
        "sensor": {
          "suggested_display_precision": 2
        },
        "conversation": {
          "should_expose": false
        }
      },
      "original_name": "sda1磁碟讀取",
      "platform": "glances",
      "translation_key": "diskio_read",
      "unique_id": "01KBA31BNXAWX73PQ3W00QHXZG-sda1-read"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "01KBA31BNXAWX73PQ3W00QHXZG",
      "config_subentry_id": null,
      "created_at": 1764496551.804348,
      "device_id": "2ac79e2bf20b7e58eb2113d842ef6ef3",
      "disabled_by": null,
      "entity_category": null,
      "entity_id": "sensor.localhost_sda1_disk_write",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "ba7c342d374cabc524a7223bf3a56ed6",
      "labels": [],
      "modified_at": 1764496551.804725,
      "name": null,
      "options": {
        "sensor.private": {
          "suggested_unit_of_measurement": "MB/s"
        },
        "sensor": {
          "suggested_display_precision": 2
        },
        "conversation": {
          "should_expose": false
        }
      },
      "original_name": "sda1磁碟寫入",
      "platform": "glances",
      "translation_key": "diskio_write",
      "unique_id": "01KBA31BNXAWX73PQ3W00QHXZG-sda1-write"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "01KBA31BNXAWX73PQ3W00QHXZG",
      "config_subentry_id": null,
      "created_at": 1764496551.805131,
      "device_id": "2ac79e2bf20b7e58eb2113d842ef6ef3",
      "disabled_by": null,
      "entity_category": null,
      "entity_id": "sensor.localhost_sda2_disk_read",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "d6e83e7e1c3f5987720f3736519d8b4b",
      "labels": [],
      "modified_at": 1764496551.805487,
      "name": null,
      "options": {
        "sensor.private": {
          "suggested_unit_of_measurement": "MB/s"
        },
        "sensor": {
          "suggested_display_precision": 2
        },
        "conversation": {
          "should_expose": false
        }
      },
      "original_name": "sda2磁碟讀取",
      "platform": "glances",
      "translation_key": "diskio_read",
      "unique_id": "01KBA31BNXAWX73PQ3W00QHXZG-sda2-read"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "01KBA31BNXAWX73PQ3W00QHXZG",
      "config_subentry_id": null,
      "created_at": 1764496551.805908,
      "device_id": "2ac79e2bf20b7e58eb2113d842ef6ef3",
      "disabled_by": null,
      "entity_category": null,
      "entity_id": "sensor.localhost_sda2_disk_write",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "5e66cf26d39737dd1eb167614d4f5051",
      "labels": [],
      "modified_at": 1764496551.806269,
      "name": null,
      "options": {
        "sensor.private": {
          "suggested_unit_of_measurement": "MB/s"
        },
        "sensor": {
          "suggested_display_precision": 2
        },
        "conversation": {
          "should_expose": false
        }
      },
      "original_name": "sda2磁碟寫入",
      "platform": "glances",
      "translation_key": "diskio_write",
      "unique_id": "01KBA31BNXAWX73PQ3W00QHXZG-sda2-write"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "01KBA31BNXAWX73PQ3W00QHXZG",
      "config_subentry_id": null,
      "created_at": 1764496551.806669,
      "device_id": "2ac79e2bf20b7e58eb2113d842ef6ef3",
      "disabled_by": null,
      "entity_category": null,
      "entity_id": "sensor.localhost_sda3_disk_read",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "d5dc0968f8defbc3694ea28a61e6fa28",
      "labels": [],
      "modified_at": 1764496551.807038,
      "name": null,
      "options": {
        "sensor.private": {
          "suggested_unit_of_measurement": "MB/s"
        },
        "sensor": {
          "suggested_display_precision": 2
        },
        "conversation": {
          "should_expose": false
        }
      },
      "original_name": "sda3磁碟讀取",
      "platform": "glances",
      "translation_key": "diskio_read",
      "unique_id": "01KBA31BNXAWX73PQ3W00QHXZG-sda3-read"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "01KBA31BNXAWX73PQ3W00QHXZG",
      "config_subentry_id": null,
      "created_at": 1764496551.807453,
      "device_id": "2ac79e2bf20b7e58eb2113d842ef6ef3",
      "disabled_by": null,
      "entity_category": null,
      "entity_id": "sensor.localhost_sda3_disk_write",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "019264394ec5127c727615c797acd779",
      "labels": [],
      "modified_at": 1764496551.807864,
      "name": null,
      "options": {
        "sensor.private": {
          "suggested_unit_of_measurement": "MB/s"
        },
        "sensor": {
          "suggested_display_precision": 2
        },
        "conversation": {
          "should_expose": false
        }
      },
      "original_name": "sda3磁碟寫入",
      "platform": "glances",
      "translation_key": "diskio_write",
      "unique_id": "01KBA31BNXAWX73PQ3W00QHXZG-sda3-write"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "01KBA31BNXAWX73PQ3W00QHXZG",
      "config_subentry_id": null,
      "created_at": 1764496551.809436,
      "device_id": "2ac79e2bf20b7e58eb2113d842ef6ef3",
      "disabled_by": null,
      "entity_category": null,
      "entity_id": "sensor.localhost_sda4_disk_read",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "98f175b1ce2945199df1122fec4c45bc",
      "labels": [],
      "modified_at": 1764496551.80989,
      "name": null,
      "options": {
        "sensor.private": {
          "suggested_unit_of_measurement": "MB/s"
        },
        "sensor": {
          "suggested_display_precision": 2
        },
        "conversation": {
          "should_expose": false
        }
      },
      "original_name": "sda4磁碟讀取",
      "platform": "glances",
      "translation_key": "diskio_read",
      "unique_id": "01KBA31BNXAWX73PQ3W00QHXZG-sda4-read"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "01KBA31BNXAWX73PQ3W00QHXZG",
      "config_subentry_id": null,
      "created_at": 1764496551.810326,
      "device_id": "2ac79e2bf20b7e58eb2113d842ef6ef3",
      "disabled_by": null,
      "entity_category": null,
      "entity_id": "sensor.localhost_sda4_disk_write",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "16759fd16d14b014c204e32e0f67b9d8",
      "labels": [],
      "modified_at": 1764496551.810709,
      "name": null,
      "options": {
        "sensor.private": {
          "suggested_unit_of_measurement": "MB/s"
        },
        "sensor": {
          "suggested_display_precision": 2
        },
        "conversation": {
          "should_expose": false
        }
      },
      "original_name": "sda4磁碟寫入",
      "platform": "glances",
      "translation_key": "diskio_write",
      "unique_id": "01KBA31BNXAWX73PQ3W00QHXZG-sda4-write"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "01KBA31BNXAWX73PQ3W00QHXZG",
      "config_subentry_id": null,
      "created_at": 1764496551.811123,
      "device_id": "2ac79e2bf20b7e58eb2113d842ef6ef3",
      "disabled_by": null,
      "entity_category": null,
      "entity_id": "sensor.localhost_sda5_disk_read",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "a5ad8619e4195c52affbf71bee2df7ca",
      "labels": [],
      "modified_at": 1764496551.811487,
      "name": null,
      "options": {
        "sensor.private": {
          "suggested_unit_of_measurement": "MB/s"
        },
        "sensor": {
          "suggested_display_precision": 2
        },
        "conversation": {
          "should_expose": false
        }
      },
      "original_name": "sda5磁碟讀取",
      "platform": "glances",
      "translation_key": "diskio_read",
      "unique_id": "01KBA31BNXAWX73PQ3W00QHXZG-sda5-read"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "01KBA31BNXAWX73PQ3W00QHXZG",
      "config_subentry_id": null,
      "created_at": 1764496551.811912,
      "device_id": "2ac79e2bf20b7e58eb2113d842ef6ef3",
      "disabled_by": null,
      "entity_category": null,
      "entity_id": "sensor.localhost_sda5_disk_write",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "406f35ffb8a60d2e1541f6a92fb03d8e",
      "labels": [],
      "modified_at": 1764496551.812275,
      "name": null,
      "options": {
        "sensor.private": {
          "suggested_unit_of_measurement": "MB/s"
        },
        "sensor": {
          "suggested_display_precision": 2
        },
        "conversation": {
          "should_expose": false
        }
      },
      "original_name": "sda5磁碟寫入",
      "platform": "glances",
      "translation_key": "diskio_write",
      "unique_id": "01KBA31BNXAWX73PQ3W00QHXZG-sda5-write"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "01KBA31BNXAWX73PQ3W00QHXZG",
      "config_subentry_id": null,
      "created_at": 1764496551.812728,
      "device_id": "2ac79e2bf20b7e58eb2113d842ef6ef3",
      "disabled_by": null,
      "entity_category": null,
      "entity_id": "sensor.localhost_sda6_disk_read",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "b7d33728e7dca2a4b7e7f0584eeddfb3",
      "labels": [],
      "modified_at": 1764496551.813155,
      "name": null,
      "options": {
        "sensor.private": {
          "suggested_unit_of_measurement": "MB/s"
        },
        "sensor": {
          "suggested_display_precision": 2
        },
        "conversation": {
          "should_expose": false
        }
      },
      "original_name": "sda6磁碟讀取",
      "platform": "glances",
      "translation_key": "diskio_read",
      "unique_id": "01KBA31BNXAWX73PQ3W00QHXZG-sda6-read"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "01KBA31BNXAWX73PQ3W00QHXZG",
      "config_subentry_id": null,
      "created_at": 1764496551.813578,
      "device_id": "2ac79e2bf20b7e58eb2113d842ef6ef3",
      "disabled_by": null,
      "entity_category": null,
      "entity_id": "sensor.localhost_sda6_disk_write",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "ba1bc53aed71fafcca39ba61da0bd9b1",
      "labels": [],
      "modified_at": 1764496551.813967,
      "name": null,
      "options": {
        "sensor.private": {
          "suggested_unit_of_measurement": "MB/s"
        },
        "sensor": {
          "suggested_display_precision": 2
        },
        "conversation": {
          "should_expose": false
        }
      },
      "original_name": "sda6磁碟寫入",
      "platform": "glances",
      "translation_key": "diskio_write",
      "unique_id": "01KBA31BNXAWX73PQ3W00QHXZG-sda6-write"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "01KBA31BNXAWX73PQ3W00QHXZG",
      "config_subentry_id": null,
      "created_at": 1764496551.814382,
      "device_id": "2ac79e2bf20b7e58eb2113d842ef6ef3",
      "disabled_by": null,
      "entity_category": null,
      "entity_id": "sensor.localhost_sda7_disk_read",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "97b34d50dc3c00cfbed6709fbbb47409",
      "labels": [],
      "modified_at": 1764496551.814774,
      "name": null,
      "options": {
        "sensor.private": {
          "suggested_unit_of_measurement": "MB/s"
        },
        "sensor": {
          "suggested_display_precision": 2
        },
        "conversation": {
          "should_expose": false
        }
      },
      "original_name": "sda7磁碟讀取",
      "platform": "glances",
      "translation_key": "diskio_read",
      "unique_id": "01KBA31BNXAWX73PQ3W00QHXZG-sda7-read"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "01KBA31BNXAWX73PQ3W00QHXZG",
      "config_subentry_id": null,
      "created_at": 1764496551.815226,
      "device_id": "2ac79e2bf20b7e58eb2113d842ef6ef3",
      "disabled_by": null,
      "entity_category": null,
      "entity_id": "sensor.localhost_sda7_disk_write",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "f73a519aa25effb45f7915f3f910c500",
      "labels": [],
      "modified_at": 1764496551.815602,
      "name": null,
      "options": {
        "sensor.private": {
          "suggested_unit_of_measurement": "MB/s"
        },
        "sensor": {
          "suggested_display_precision": 2
        },
        "conversation": {
          "should_expose": false
        }
      },
      "original_name": "sda7磁碟寫入",
      "platform": "glances",
      "translation_key": "diskio_write",
      "unique_id": "01KBA31BNXAWX73PQ3W00QHXZG-sda7-write"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "01KBA31BNXAWX73PQ3W00QHXZG",
      "config_subentry_id": null,
      "created_at": 1764496551.816034,
      "device_id": "2ac79e2bf20b7e58eb2113d842ef6ef3",
      "disabled_by": null,
      "entity_category": null,
      "entity_id": "sensor.localhost_sda8_disk_read",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "cfc64a5e74a9ccced30a9b6f2f6906e8",
      "labels": [],
      "modified_at": 1764496551.816408,
      "name": null,
      "options": {
        "sensor.private": {
          "suggested_unit_of_measurement": "MB/s"
        },
        "sensor": {
          "suggested_display_precision": 2
        },
        "conversation": {
          "should_expose": false
        }
      },
      "original_name": "sda8磁碟讀取",
      "platform": "glances",
      "translation_key": "diskio_read",
      "unique_id": "01KBA31BNXAWX73PQ3W00QHXZG-sda8-read"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "01KBA31BNXAWX73PQ3W00QHXZG",
      "config_subentry_id": null,
      "created_at": 1764496551.816879,
      "device_id": "2ac79e2bf20b7e58eb2113d842ef6ef3",
      "disabled_by": null,
      "entity_category": null,
      "entity_id": "sensor.localhost_sda8_disk_write",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "06301d5967baefd1aa14c1be361060f1",
      "labels": [],
      "modified_at": 1764496551.81727,
      "name": null,
      "options": {
        "sensor.private": {
          "suggested_unit_of_measurement": "MB/s"
        },
        "sensor": {
          "suggested_display_precision": 2
        },
        "conversation": {
          "should_expose": false
        }
      },
      "original_name": "sda8磁碟寫入",
      "platform": "glances",
      "translation_key": "diskio_write",
      "unique_id": "01KBA31BNXAWX73PQ3W00QHXZG-sda8-write"
    },
    {
      "area_id": null,
      "categories": {},
      "config_entry_id": "01KBA31BNXAWX73PQ3W00QHXZG",
      "config_subentry_id": null,
      "created_at": 1764496551.817707,
      "device_id": "2ac79e2bf20b7e58eb2113d842ef6ef3",
      "disabled_by": null,
      "entity_category": null,
      "entity_id": "sensor.localhost_uptime",
      "has_entity_name": true,
      "hidden_by": null,
      "icon": null,
      "id": "4fe41a3b423572bf636f40e9ad59163b",
      "labels": [],
      "modified_at": 1764496551.818399,
      "name": null,
      "options": {
        "conversation": {
          "should_expose": false
        }
      },
      "original_name": "運作時間",
      "platform": "glances",
      "translation_key": "uptime",
      "unique_id": "01KBA31BNXAWX73PQ3W00QHXZG--uptime"
    }
  ]
}
```
