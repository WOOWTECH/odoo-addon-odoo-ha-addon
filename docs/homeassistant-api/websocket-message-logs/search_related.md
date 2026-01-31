# description

查一個物件的關聯資訊。

可以用來查詢一個 device 有什麼 entities。

# example

Send

```json
{
  "type": "search/related",
  "item_type": "device",
  "item_id": "2ac79e2bf20b7e58eb2113d842ef6ef3",
  "id": 49
}
```

```json
{
  "type": "search/related",
  "item_type": "entity",
  "item_id": "switch.test_switch",
  "id": 45
}
```

Received

```json
{
  "id": 49,
  "type": "result",
  "success": true,
  "result": {
    "config_entry": ["01KBA31BNXAWX73PQ3W00QHXZG"],
    "integration": ["glances"],
    "entity": [
      "sensor.localhost_zram2_disk_write",
      "sensor.localhost_lo_rx",
      "sensor.localhost_config_disk_free",
      "sensor.localhost_vethb078a08_rx",
      "sensor.localhost_config_disk_used",
      "sensor.localhost_sda3_disk_read",
      "sensor.localhost_veth5c8370f_tx",
      "sensor.localhost_sda4_disk_write",
      "sensor.localhost_share_disk_used",
      "sensor.localhost_running",
      "sensor.localhost_docker0_tx",
      "sensor.localhost_veth5c8370f_rx",
      "sensor.localhost_veth58c215a_rx",
      "sensor.localhost_lo_tx",
      "sensor.localhost_veth58593b6_rx",
      "sensor.localhost_total",
      "sensor.localhost_vethff12b05_tx",
      "sensor.localhost_hassio_rx",
      "sensor.localhost_enp1s0_tx",
      "sensor.localhost_veth0fc7b01_tx",
      "sensor.localhost_addons_disk_usage",
      "sensor.localhost_vethfc079cd_rx",
      "sensor.localhost_ssl_disk_usage",
      "sensor.localhost_swap_usage",
      "sensor.localhost_zram0_disk_write",
      "sensor.localhost_sda7_disk_read",
      "sensor.localhost_ssl_disk_used",
      "sensor.localhost_sda5_disk_write",
      "sensor.localhost_veth9151383_rx",
      "sensor.localhost_cpu_load",
      "sensor.localhost_vethf4dcf75_rx",
      "sensor.localhost_etc_hostname_disk_free",
      "sensor.localhost_threads",
      "sensor.localhost_enp2s0_rx",
      "sensor.localhost_veth58c215a_tx",
      "sensor.localhost_veth5aea80c_tx",
      "sensor.localhost_backup_disk_free",
      "sensor.localhost_sda_disk_read",
      "sensor.localhost_sda1_disk_write",
      "sensor.localhost_veth9151383_tx",
      "sensor.localhost_run_cid_disk_usage",
      "sensor.localhost_docker0_rx",
      "sensor.localhost_sda8_disk_write",
      "sensor.localhost_media_disk_used",
      "sensor.localhost_zram0_disk_read",
      "sensor.localhost_data_disk_usage",
      "sensor.localhost_containers_cpu_usage",
      "sensor.localhost_run_cid_disk_free",
      "sensor.localhost_core_3_temperature",
      "sensor.localhost_share_disk_usage",
      "sensor.localhost_share_disk_free",
      "sensor.localhost_containers_active",
      "sensor.localhost_zram1_disk_write",
      "sensor.localhost_wlp3s0_rx",
      "sensor.localhost_data_disk_free",
      "sensor.localhost_sda5_disk_read",
      "sensor.localhost_memory_use",
      "sensor.localhost_sda6_disk_read",
      "sensor.localhost_backup_disk_usage",
      "sensor.localhost_etc_resolv_conf_disk_used",
      "sensor.localhost_memory_usage",
      "sensor.localhost_media_disk_free",
      "sensor.localhost_sda2_disk_read",
      "sensor.localhost_veth58593b6_tx",
      "sensor.localhost_sda7_disk_write",
      "sensor.localhost_vethff12b05_rx",
      "sensor.localhost_core_1_temperature",
      "sensor.localhost_ssl_disk_free",
      "sensor.localhost_etc_hosts_disk_usage",
      "sensor.localhost_backup_disk_used",
      "sensor.localhost_acpitz_0_temperature",
      "sensor.localhost_etc_hosts_disk_used",
      "sensor.localhost_addons_disk_used",
      "sensor.localhost_sda8_disk_read",
      "sensor.localhost_sda2_disk_write",
      "sensor.localhost_veth3befb79_tx",
      "sensor.localhost_sda1_disk_read",
      "sensor.localhost_addons_disk_free",
      "sensor.localhost_sda4_disk_read",
      "sensor.localhost_vethc0fead1_rx",
      "sensor.localhost_uptime",
      "sensor.localhost_veth97b1051_rx",
      "sensor.localhost_etc_hostname_disk_usage",
      "sensor.localhost_veth0fc7b01_rx",
      "sensor.localhost_etc_resolv_conf_disk_usage",
      "sensor.localhost_etc_hosts_disk_free",
      "sensor.localhost_run_cid_disk_used",
      "sensor.localhost_veth3befb79_rx",
      "sensor.localhost_sleeping",
      "sensor.localhost_data_disk_used",
      "sensor.localhost_core_0_temperature",
      "sensor.localhost_swap_use",
      "sensor.localhost_swap_free",
      "sensor.localhost_package_id_0_temperature",
      "sensor.localhost_memory_free",
      "sensor.localhost_vethc0fead1_tx",
      "sensor.localhost_config_disk_usage",
      "sensor.localhost_enp2s0_tx",
      "sensor.localhost_enp1s0_rx",
      "sensor.localhost_vethf4dcf75_tx",
      "sensor.localhost_zram1_disk_read",
      "sensor.localhost_wlp3s0_tx",
      "sensor.localhost_etc_hostname_disk_used",
      "sensor.localhost_sda_disk_write",
      "sensor.localhost_vethb078a08_tx",
      "sensor.localhost_sda6_disk_write",
      "sensor.localhost_cpu_usage",
      "sensor.localhost_sda3_disk_write",
      "sensor.localhost_containers_memory_used",
      "sensor.localhost_core_2_temperature",
      "sensor.localhost_zram2_disk_read",
      "sensor.localhost_vethfc079cd_tx",
      "sensor.localhost_veth5aea80c_rx",
      "sensor.localhost_veth97b1051_tx",
      "sensor.localhost_etc_resolv_conf_disk_free",
      "sensor.localhost_media_disk_usage",
      "sensor.localhost_hassio_tx"
    ]
  }
}
```

```json
{
  "id": 45,
  "type": "result",
  "success": true,
  "result": {
    "area": ["wo_shi"],
    "device": ["4a913b08c70ae173a12cf738e341aea4"],
    "config_entry": ["01K5TQF9Q0CAPR3G1NA8V7REGR"],
    "integration": ["virtual"],
    "label": ["test9", "jj2", "test_space", "test8"],
    "automation": ["automation.duo_qie_kai_guan_kong_zhi_deng_ju"],
    "scene": ["scene.test2"],
    "script": ["script.notify"]
  }
}
```
