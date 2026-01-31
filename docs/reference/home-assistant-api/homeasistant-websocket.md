## websocket payload

### general payload

```
{
  "id": "流水號"
  "type": "xxx",
}
```

- "id" 流水號，會一直慢慢增加。當連線成功後，即 client 收到 `{"type":"auth_ok","ha_version":"2025.6.3"}` 訊息表示連線成功， client 之後發送的訊息都會帶上 "id"， "id" 從 1 開始，homeassistant server 回傳時也會帶上相同的 "id"，以表明是針對哪一個 "id" 的回應。
- homeassistant server 回傳的 message 可能是一般 payload `{"type":"xxx", "id": yyy, ...}` 也可能是回傳一個 payload 的陣列。
- client 端在開發時，不能假設送出一個訊息後下一個收到的訊息就是針對該訊息的回應，因為：
  - client 可能連發，所以可能會連續接收
  - 回傳時可能是無序的
  - 回傳時，可能是多個回應訊息組成的陣列

### sending message examples

```
{"type":"hardware/info","id":44}
```

```
{"type":"supervisor/api","endpoint":"/host/info","method":"get","id":45}
```

### reveived message examples

```
[{"id":42,"type":"result","success":true,"result":{"logged_in":false,"cloud":"disconnected","http_use_ssl":false}},{"id":44,"type":"result","success":true,"result":{"hardware":[]}}]
```

```
{"id":45,"type":"result","success":true,"result":{"agent_version":"1.7.2","apparmor_version":"3.1.2","chassis":"embedded","virtualization":"","cpe":"cpe:2.3:o:home-assistant:haos:15.2:*:production:*:*:*:generic-x86-64:*","deployment":"production","disk_free":845.7,"disk_total":916.2,"disk_used":33.2,"disk_life_time":null,"features":["reboot","shutdown","services","network","hostname","timedate","os_agent","haos","resolved","journal","disk","mount"],"hostname":"homeassistant","llmnr_hostname":"homeassistant","kernel":"6.12.23-haos","operating_system":"Home Assistant OS 15.2","timezone":"Etc/UTC","dt_utc":"2025-10-02T09:33:13.214059+00:00","dt_synchronized":true,"use_ntp":true,"startup_time":0.935632,"boot_timestamp":1757841446991959,"broadcast_llmnr":true,"broadcast_mdns":true}}
```
