# description

查出 entity id 的 domain 是誰？

# example

Send

```
{"type":"entity/source","id":50}
```

Received

```
{
  "id": 50,
  "type": "result",
  "success": true,
  "result": {
    "conversation.home_assistant": {
      "domain": "conversation"
    },
    "sensor.backup_backup_manager_state": {
      "domain": "backup"
    },
    "sensor.backup_next_scheduled_automatic_backup": {
      "domain": "backup"
    },
    "sensor.backup_last_successful_automatic_backup": {
      "domain": "backup"
    },
    "sensor.backup_last_attempted_automatic_backup": {
      "domain": "backup"
    },
    "event.backup_automatic_backup": {
      "domain": "backup"
    },
    "zone.home": {
      "domain": "zone"
    },
    "person.admin": {
      "domain": "person"
    },
    "sun.sun": {
      "domain": "sun"
    },
    "sensor.sun_next_dawn": {
      "domain": "sun"
    },
    "sensor.sun_next_dusk": {
      "domain": "sun"
    },
    "sensor.sun_next_midnight": {
      "domain": "sun"
    },
    "sensor.sun_next_noon": {
      "domain": "sun"
    },
    "sensor.sun_next_rising": {
      "domain": "sun"
    },
    "sensor.sun_next_setting": {
      "domain": "sun"
    },
    "update.virtual_components_update": {
      "domain": "hacs"
    },
    "update.hacs_update": {
      "domain": "hacs"
    },
    "update.mushroom_update": {
      "domain": "hacs"
    },
    "update.art_net_led_lighting_for_dmx_update": {
      "domain": "hacs"
    },
    "binary_sensor.living_room_motion": {
      "domain": "virtual"
    },
    "binary_sensor.back_door": {
      "domain": "virtual"
    },
    "cover.test_cover_cover": {
      "domain": "virtual"
    },
    "fan.test_fan": {
      "domain": "virtual"
    },
    "light.test_lights": {
      "domain": "virtual"
    },
    "switch.test_switch": {
      "domain": "virtual"
    },
    "automation.duo_qie_kai_guan_kong_zhi_deng_ju": {
      "domain": "automation"
    },
    "script.notify": {
      "domain": "script"
    },
    "scene.test2": {
      "domain": "homeassistant"
    },
    "update.home_assistant_supervisor_update": {
      "domain": "hassio"
    },
    "update.home_assistant_core_update": {
      "domain": "hassio"
    },
    "update.matter_server_update": {
      "domain": "hassio"
    },
    "update.file_editor_update": {
      "domain": "hassio"
    },
    "update.esphome_update": {
      "domain": "hassio"
    },
    "update.mosquitto_broker_update": {
      "domain": "hassio"
    },
    "update.music_assistant_server_update": {
      "domain": "hassio"
    },
    "update.get_hacs_update": {
      "domain": "hassio"
    },
    "update.terminal_ssh_update": {
      "domain": "hassio"
    },
    "update.rtsptoweb_webrtc_update": {
      "domain": "hassio"
    },
    "update.node_red_update": {
      "domain": "hassio"
    },
    "update.openthread_border_router_update": {
      "domain": "hassio"
    },
    "update.samba_share_update": {
      "domain": "hassio"
    },
    "update.immich_update": {
      "domain": "hassio"
    },
    "update.hassos_ssh_port_22222_configurator_update": {
      "domain": "hassio"
    },
    "update.timescaledb_update": {
      "domain": "hassio"
    },
    "update.timescaledb_update_2": {
      "domain": "hassio"
    },
    "update.pgadmin4_update": {
      "domain": "hassio"
    },
    "update.cloudflared_update": {
      "domain": "hassio"
    },
    "update.odoo_update": {
      "domain": "hassio"
    },
    "update.glances_update": {
      "domain": "hassio"
    },
    "update.home_assistant_operating_system_update": {
      "domain": "hassio"
    },
    "sensor.localhost_ssl_disk_used": {
      "domain": "glances"
    },
    "sensor.localhost_ssl_disk_usage": {
      "domain": "glances"
    },
    "sensor.localhost_ssl_disk_free": {
      "domain": "glances"
    },
    "sensor.localhost_share_disk_used": {
      "domain": "glances"
    },
    "sensor.localhost_share_disk_usage": {
      "domain": "glances"
    },
    "sensor.localhost_share_disk_free": {
      "domain": "glances"
    },
    "sensor.localhost_backup_disk_used": {
      "domain": "glances"
    },
    "sensor.localhost_backup_disk_usage": {
      "domain": "glances"
    },
    "sensor.localhost_backup_disk_free": {
      "domain": "glances"
    },
    "sensor.localhost_media_disk_used": {
      "domain": "glances"
    },
    "sensor.localhost_media_disk_usage": {
      "domain": "glances"
    },
    "sensor.localhost_media_disk_free": {
      "domain": "glances"
    },
    "sensor.localhost_config_disk_used": {
      "domain": "glances"
    },
    "sensor.localhost_config_disk_usage": {
      "domain": "glances"
    },
    "sensor.localhost_config_disk_free": {
      "domain": "glances"
    },
    "sensor.localhost_addons_disk_used": {
      "domain": "glances"
    },
    "sensor.localhost_addons_disk_usage": {
      "domain": "glances"
    },
    "sensor.localhost_addons_disk_free": {
      "domain": "glances"
    },
    "sensor.localhost_data_disk_used": {
      "domain": "glances"
    },
    "sensor.localhost_data_disk_usage": {
      "domain": "glances"
    },
    "sensor.localhost_data_disk_free": {
      "domain": "glances"
    },
    "sensor.localhost_run_cid_disk_used": {
      "domain": "glances"
    },
    "sensor.localhost_run_cid_disk_usage": {
      "domain": "glances"
    },
    "sensor.localhost_run_cid_disk_free": {
      "domain": "glances"
    },
    "sensor.localhost_etc_resolv_conf_disk_used": {
      "domain": "glances"
    },
    "sensor.localhost_etc_resolv_conf_disk_usage": {
      "domain": "glances"
    },
    "sensor.localhost_etc_resolv_conf_disk_free": {
      "domain": "glances"
    },
    "sensor.localhost_etc_hostname_disk_used": {
      "domain": "glances"
    },
    "sensor.localhost_etc_hostname_disk_usage": {
      "domain": "glances"
    },
    "sensor.localhost_etc_hostname_disk_free": {
      "domain": "glances"
    },
    "sensor.localhost_etc_hosts_disk_used": {
      "domain": "glances"
    },
    "sensor.localhost_etc_hosts_disk_usage": {
      "domain": "glances"
    },
    "sensor.localhost_etc_hosts_disk_free": {
      "domain": "glances"
    },
    "sensor.localhost_acpitz_0_temperature": {
      "domain": "glances"
    },
    "sensor.localhost_package_id_0_temperature": {
      "domain": "glances"
    },
    "sensor.localhost_core_0_temperature": {
      "domain": "glances"
    },
    "sensor.localhost_core_1_temperature": {
      "domain": "glances"
    },
    "sensor.localhost_core_2_temperature": {
      "domain": "glances"
    },
    "sensor.localhost_core_3_temperature": {
      "domain": "glances"
    },
    "sensor.localhost_memory_usage": {
      "domain": "glances"
    },
    "sensor.localhost_memory_use": {
      "domain": "glances"
    },
    "sensor.localhost_memory_free": {
      "domain": "glances"
    },
    "sensor.localhost_swap_usage": {
      "domain": "glances"
    },
    "sensor.localhost_swap_use": {
      "domain": "glances"
    },
    "sensor.localhost_swap_free": {
      "domain": "glances"
    },
    "sensor.localhost_cpu_load": {
      "domain": "glances"
    },
    "sensor.localhost_running": {
      "domain": "glances"
    },
    "sensor.localhost_total": {
      "domain": "glances"
    },
    "sensor.localhost_threads": {
      "domain": "glances"
    },
    "sensor.localhost_sleeping": {
      "domain": "glances"
    },
    "sensor.localhost_cpu_usage": {
      "domain": "glances"
    },
    "sensor.localhost_lo_rx": {
      "domain": "glances"
    },
    "sensor.localhost_lo_tx": {
      "domain": "glances"
    },
    "sensor.localhost_enp1s0_rx": {
      "domain": "glances"
    },
    "sensor.localhost_enp1s0_tx": {
      "domain": "glances"
    },
    "sensor.localhost_enp2s0_rx": {
      "domain": "glances"
    },
    "sensor.localhost_enp2s0_tx": {
      "domain": "glances"
    },
    "sensor.localhost_wlp3s0_rx": {
      "domain": "glances"
    },
    "sensor.localhost_wlp3s0_tx": {
      "domain": "glances"
    },
    "sensor.localhost_hassio_rx": {
      "domain": "glances"
    },
    "sensor.localhost_hassio_tx": {
      "domain": "glances"
    },
    "sensor.localhost_docker0_rx": {
      "domain": "glances"
    },
    "sensor.localhost_docker0_tx": {
      "domain": "glances"
    },
    "sensor.localhost_vethb078a08_rx": {
      "domain": "glances"
    },
    "sensor.localhost_vethb078a08_tx": {
      "domain": "glances"
    },
    "sensor.localhost_vethfc079cd_rx": {
      "domain": "glances"
    },
    "sensor.localhost_vethfc079cd_tx": {
      "domain": "glances"
    },
    "sensor.localhost_veth0fc7b01_rx": {
      "domain": "glances"
    },
    "sensor.localhost_veth0fc7b01_tx": {
      "domain": "glances"
    },
    "sensor.localhost_vethc0fead1_rx": {
      "domain": "glances"
    },
    "sensor.localhost_vethc0fead1_tx": {
      "domain": "glances"
    },
    "sensor.localhost_veth9151383_rx": {
      "domain": "glances"
    },
    "sensor.localhost_veth9151383_tx": {
      "domain": "glances"
    },
    "sensor.localhost_veth58593b6_rx": {
      "domain": "glances"
    },
    "sensor.localhost_veth58593b6_tx": {
      "domain": "glances"
    },
    "sensor.localhost_veth5c8370f_rx": {
      "domain": "glances"
    },
    "sensor.localhost_veth5c8370f_tx": {
      "domain": "glances"
    },
    "sensor.localhost_veth97b1051_rx": {
      "domain": "glances"
    },
    "sensor.localhost_veth97b1051_tx": {
      "domain": "glances"
    },
    "sensor.localhost_veth58c215a_rx": {
      "domain": "glances"
    },
    "sensor.localhost_veth58c215a_tx": {
      "domain": "glances"
    },
    "sensor.localhost_vethf4dcf75_rx": {
      "domain": "glances"
    },
    "sensor.localhost_vethf4dcf75_tx": {
      "domain": "glances"
    },
    "sensor.localhost_veth3befb79_rx": {
      "domain": "glances"
    },
    "sensor.localhost_veth3befb79_tx": {
      "domain": "glances"
    },
    "sensor.localhost_veth5aea80c_rx": {
      "domain": "glances"
    },
    "sensor.localhost_veth5aea80c_tx": {
      "domain": "glances"
    },
    "sensor.localhost_vethff12b05_rx": {
      "domain": "glances"
    },
    "sensor.localhost_vethff12b05_tx": {
      "domain": "glances"
    },
    "sensor.localhost_containers_active": {
      "domain": "glances"
    },
    "sensor.localhost_containers_cpu_usage": {
      "domain": "glances"
    },
    "sensor.localhost_containers_memory_used": {
      "domain": "glances"
    },
    "sensor.localhost_zram0_disk_read": {
      "domain": "glances"
    },
    "sensor.localhost_zram0_disk_write": {
      "domain": "glances"
    },
    "sensor.localhost_zram1_disk_read": {
      "domain": "glances"
    },
    "sensor.localhost_zram1_disk_write": {
      "domain": "glances"
    },
    "sensor.localhost_zram2_disk_read": {
      "domain": "glances"
    },
    "sensor.localhost_zram2_disk_write": {
      "domain": "glances"
    },
    "sensor.localhost_sda_disk_read": {
      "domain": "glances"
    },
    "sensor.localhost_sda_disk_write": {
      "domain": "glances"
    },
    "sensor.localhost_sda1_disk_read": {
      "domain": "glances"
    },
    "sensor.localhost_sda1_disk_write": {
      "domain": "glances"
    },
    "sensor.localhost_sda2_disk_read": {
      "domain": "glances"
    },
    "sensor.localhost_sda2_disk_write": {
      "domain": "glances"
    },
    "sensor.localhost_sda3_disk_read": {
      "domain": "glances"
    },
    "sensor.localhost_sda3_disk_write": {
      "domain": "glances"
    },
    "sensor.localhost_sda4_disk_read": {
      "domain": "glances"
    },
    "sensor.localhost_sda4_disk_write": {
      "domain": "glances"
    },
    "sensor.localhost_sda5_disk_read": {
      "domain": "glances"
    },
    "sensor.localhost_sda5_disk_write": {
      "domain": "glances"
    },
    "sensor.localhost_sda6_disk_read": {
      "domain": "glances"
    },
    "sensor.localhost_sda6_disk_write": {
      "domain": "glances"
    },
    "sensor.localhost_sda7_disk_read": {
      "domain": "glances"
    },
    "sensor.localhost_sda7_disk_write": {
      "domain": "glances"
    },
    "sensor.localhost_sda8_disk_read": {
      "domain": "glances"
    },
    "sensor.localhost_sda8_disk_write": {
      "domain": "glances"
    },
    "sensor.localhost_uptime": {
      "domain": "glances"
    }
  }
}
```
