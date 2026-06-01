# 雙向控制測試計畫 (Bidirectional Control Test Plan)

## 概述

全面自動化測試，驗證 Odoo HA 整合模組中所有 17 個 entity domain 的三向同步控制能力。

## 環境

| 組件 | 端點 |
|------|------|
| Odoo Backend | http://localhost:9077 (admin/admin) |
| Odoo Portal | http://localhost:9077/my/ha/1 (portal/portal, user_id=7) |
| HA Core | https://woowtech-ha.woowtech.io (via Odoo WebSocket) |

## 測試架構

```
Direction A: Odoo Backend → HA Core → Odoo Backend (verify round-trip)
Direction B: Odoo Portal → HA Core → Odoo Portal (verify round-trip)
Direction C: HA Core → Odoo Backend + Portal (verify propagation)
```

### 限制說明

- HA MCP 工具連接到不同的 HA 實例，無法直接用於 Direction C
- Direction C 透過 Odoo Backend 的 call_service RPC 觸發 HA 動作，再驗證 Portal state endpoint 反映變更
- 所有測試使用 Playwright (UI) + JSON-RPC (API) 混合方式

## 測試範圍

### 可控制域 (Controllable Domains) - 12 個

| Domain | 測試動作 | 測試實體 (Odoo ID) |
|--------|----------|-------------------|
| switch | toggle, turn_on, turn_off | switch.6_gang_switch (86) |
| light | toggle | light.jie_dai_qu_guang_zhuo (63) |
| climate | set_temperature, set_hvac_mode | climate.room_air_conditioner (101) |
| input_boolean | toggle | input_boolean.test111 (39) |
| input_number | set_value | input_number.efwghweiogehqhjgqiwoh (40) |
| input_text | set_value | input_text.dfowjoefjo (111) |
| automation | toggle, trigger | automation.shi_nei_... (331) |
| scene | turn_on (activate) | scene.qi_ci_wo (41) |
| script | turn_on (run) | script.ai (113) |
| button | press | button.smart_wired_gateway_pro_shi_bie (83) |
| select | select_option | (needs available entity) |
| media_player | toggle | (needs available entity) |

### 唯讀域 (Read-only Domains) - 2 個

| Domain | 測試項目 | 測試實體 |
|--------|---------|---------|
| sensor | 顯示狀態值 | sensor.backup_backup_manager_state (30) |
| binary_sensor | 顯示狀態 + 圖示 | binary_sensor.iphone_focus (119) |

### 不可測試域 (Unavailable) - 3 個

| Domain | 原因 |
|--------|------|
| cover | HA 無此類實體 |
| fan | HA 無此類實體 |
| number | 所有實體 unavailable |

## 測試方法

### Direction A: Backend → HA → Backend

1. 以 admin 登入 Odoo Backend
2. 透過 JSON-RPC 呼叫 `ha.entity` 的 `call_service` 方法
3. 等待 WebSocket 同步 (3-5秒)
4. 透過 JSON-RPC 讀取實體最新狀態
5. 驗證狀態已變更

### Direction B: Portal → HA → Portal

1. 以 portal 使用者登入
2. 透過 HTTP POST 呼叫 `/my/ha/1/entity/<id>/service`
3. 等待同步 (3-5秒)
4. 透過 HTTP GET 呼叫 `/my/ha/1/entity/<id>/state`
5. 驗證狀態已變更

### Direction C: Backend Control → Portal Verify

1. 以 admin 透過 JSON-RPC 控制實體
2. 等待同步
3. 以 portal 使用者讀取 state endpoint
4. 驗證 Portal 看到的狀態與 Backend 一致

## 驗證策略

- **狀態比對**: 控制前後狀態不同即通過 (toggle 類)
- **值比對**: 設定值 = 回傳值 (set_value 類)
- **時間容忍**: 最多等待 10 秒進行狀態同步
- **Unavailable 處理**: 實體 unavailable 則跳過並記錄

## 測試報告格式

```
=== 雙向控制測試報告 ===
測試時間: 2026-06-01T10:30:00Z
總測試: XX | 通過: XX | 失敗: XX | 跳過: XX

[Domain] switch
  ✅ A: Backend→HA toggle (off→on)
  ✅ B: Portal→HA toggle (on→off)
  ✅ C: Backend→Portal sync verified

[Domain] sensor
  ✅ Read-only display verified
  ⏭️ No control actions (read-only domain)
```
