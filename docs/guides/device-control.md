# Home Assistant 裝置控制流程

本文件說明如何從 Odoo 前端控制 Home Assistant 裝置的完整流程。

---

## 📋 目錄

1. [架構概覽](#架構概覽)
2. [控制流程](#控制流程)
3. [即時通知流程](#即時通知流程)
4. [核心組件說明](#核心組件說明)
5. [API 參考](#api-參考)
6. [實作範例](#實作範例)
7. [常見問題](#常見問題)

---

## 架構概覽

### 系統架構圖

```
┌─────────────────────────────────────────────────────────────────┐
│                         Frontend (Browser)                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────┐                                                │
│  │  Component   │  (StandaloneEntityCard / EntityDemo)           │
│  │              │  - 顯示實體狀態                                 │
│  │              │  - 處理使用者互動                               │
│  └──────┬───────┘                                                │
│         │                                                         │
│         ↓                                                         │
│  ┌──────────────────────┐                                        │
│  │  EntityController    │  - Domain-specific 控制器               │
│  │  + useEntityControl  │  - 統一控制介面                         │
│  └──────┬───────────────┘                                        │
│         │                                                         │
│         ↓                                                         │
│  ┌──────────────────────┐                                        │
│  │  HaDataService       │  - callService() 發送控制指令           │
│  │                      │  - 快取管理                             │
│  │                      │  - Callback 系統                        │
│  └──────┬───────────────┘                                        │
│         │                                                         │
│         │ RPC                                                     │
│         ↓                                                         │
├─────────────────────────────────────────────────────────────────┤
│                        Backend (Odoo)                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────────────┐                                        │
│  │  Controller          │  /odoo_ha_addon/call_service           │
│  │  call_service()      │  - 參數驗證                             │
│  │                      │  - 呼叫 WebSocket API                   │
│  └──────┬───────────────┘                                        │
│         │                                                         │
│         ↓                                                         │
│  ┌──────────────────────┐                                        │
│  │  WebSocket Client    │  - 持久化 WebSocket 連線                │
│  │                      │  - 訊息佇列管理                         │
│  │                      │  - 錯誤處理與重試                       │
│  └──────┬───────────────┘                                        │
│         │                                                         │
│         │ WebSocket                                               │
│         ↓                                                         │
├─────────────────────────────────────────────────────────────────┤
│                    Home Assistant                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────────────┐                                        │
│  │  WebSocket API       │  - 接收 call_service 指令               │
│  │                      │  - 執行裝置控制                         │
│  │                      │  - 發送 state_changed 事件              │
│  └──────┬───────────────┘                                        │
│         │                                                         │
│         ↓                                                         │
│  ┌──────────────────────┐                                        │
│  │  Physical Device     │  實際裝置 (Switch/Light/Climate)        │
│  └──────────────────────┘                                        │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## 控制流程

### 完整的控制流程 (12 步驟)

```
1. 使用者互動
   └─> 使用者點擊 Toggle 按鈕 / 拖動滑桿 / 輸入溫度

2. Component Event Handler
   └─> EntityController 觸發對應的事件處理器
       - onToggleSwitch()
       - onSetBrightness()
       - onSetTemperature()

3. Hook Actions
   └─> useEntityControl 呼叫對應的 action
       - actions.toggleSwitch()
       - actions.setBrightness()
       - actions.setTemperature()

4. Service Layer
   └─> haDataService.callService(domain, service, service_data)
       - domain: 'switch', 'light', 'climate', etc.
       - service: 'toggle', 'turn_on', 'set_temperature', etc.
       - service_data: { entity_id, brightness, temperature, ... }

5. Frontend RPC
   └─> rpc("/odoo_ha_addon/call_service", { domain, service, service_data })

6. Backend Controller
   └─> controllers.py: call_service()
       - 參數驗證 (domain, service, entity_id)
       - 呼叫 _call_websocket_api()

7. WebSocket Client
   └─> websocket_client.py: call_websocket_api()
       - 建立 WebSocket 訊息
       - 加入請求佇列
       - 等待回應

8. Home Assistant WebSocket
   └─> HA 接收 call_service 訊息
       {
         "type": "call_service",
         "domain": "switch",
         "service": "toggle",
         "service_data": {
           "entity_id": "switch.living_room"
         }
       }

9. Device Control
   └─> HA 執行實際的裝置控制
       - 發送指令到裝置
       - 更新內部狀態

10. State Change Event
    └─> HA 發送 state_changed 事件
        {
          "type": "event",
          "event": {
            "event_type": "state_changed",
            "data": {
              "entity_id": "switch.living_room",
              "old_state": {"state": "off"},
              "new_state": {"state": "on"}
            }
          }
        }

11. Backend Processing
    └─> WebSocket 接收事件
        └─> 透過 Odoo Bus 廣播到前端
            └─> ha.realtime.update.notify_entity_state_change()

12. Frontend Update
    └─> HaBusBridge 接收 Bus 事件
        └─> HaDataService 觸發 entity callbacks
            └─> useEntityControl 更新 state
                └─> Component 自動 re-render (useState)
```

---

## 即時通知流程

### WebSocket Event → Frontend Update

```
Home Assistant
    │
    │ WebSocket Event (state_changed)
    ↓
WebSocket Client (Backend)
    │
    │ 解析事件
    ↓
ha.realtime.update Model
    │
    │ notify_entity_state_change()
    │ ├─> _broadcast_to_users()
    │ └─> user.partner_id._bus_send()
    ↓
Odoo Bus System
    │
    │ 廣播到所有 online users
    ↓
Browser (Frontend)
    │
    │ WebSocket Connection (/bus/websocket_worker_bundle)
    ↓
HaBusBridge Component
    │
    │ bus_service.subscribe()
    │ 監聽: ha_entity_update, ha_websocket_status, ha_history_update
    ↓
HaDataService
    │
    │ handleEntityUpdate(data)
    │ ├─> clearCacheForEntity()
    │ └─> triggerUpdateCallbacks()
    ↓
useEntityControl Hook
    │
    │ stateChangeHandler(data)
    │ └─> state.entityState = new_state
    ↓
Component
    │
    │ useState() 觸發 re-render
    └─> UI 自動更新
```

---

## 核心組件說明

### 1. Frontend: HaDataService

**檔案**: `static/src/services/ha_data_service.js`

**職責**:
- 統一管理所有 HA API 呼叫
- 快取管理 (30 秒 TTL)
- Callback 系統 (實體更新通知)
- 清除相關快取

**關鍵方法**:
```javascript
// 呼叫 HA service
async callService(domain, service, serviceData)

// 註冊實體更新回調
onEntityUpdate(entity_id, callback)

// 移除回調
offEntityUpdate(entity_id, callback)

// 處理更新事件 (由 HaBusBridge 呼叫)
handleEntityUpdate(data)
```

---

### 2. Frontend: useEntityControl Hook

**檔案**: `static/src/components/entity_controller/hooks/useEntityControl.js`

**職責**:
- 提供統一的裝置控制邏輯
- 管理 loading 和 error 狀態
- 訂閱實體即時更新
- Optimistic UI updates

**回傳值**:
```javascript
{
  state: {
    entityState: string,  // 當前狀態
    isLoading: boolean,   // 載入中
    error: string|null    // 錯誤訊息
  },
  actions: {
    toggleSwitch(),
    toggleLight(),
    setBrightness(brightness),
    setTemperature(temperature),
    setHvacMode(mode),
    callService(service, serviceData)  // 通用方法
  },
  entityId: string,
  domain: string
}
```

---

### 3. Frontend: EntityController Component

**檔案**: `static/src/components/entity_controller/entity_controller.js`

**職責**:
- 根據 entity.domain 渲染對應的控制器
- 統一的控制介面
- 錯誤顯示

**支援的 Domain**:
- `switch`: Toggle 按鈕 + Form Switch
- `light`: Toggle 按鈕 + Brightness 滑桿
- `sensor`: 唯讀顯示 + 單位
- `climate`: 溫度控制 + HVAC 模式
- `generic`: 通用顯示 (未支援的 domain)

---

### 4. Backend: Controller Endpoint

**檔案**: `controllers/controllers.py`

**路由**: `/odoo_ha_addon/call_service`

**參數**:
```python
{
  "domain": str,           # 'switch', 'light', 'climate', etc.
  "service": str,          # 'toggle', 'turn_on', 'set_temperature', etc.
  "service_data": dict     # { "entity_id": "...", ... }
}
```

**回應**:
```python
{
  "success": bool,
  "data": dict,    # HA 回應資料
  "error": str     # 錯誤訊息 (if success=False)
}
```

**驗證**:
- domain 和 service 必填
- service_data 必須包含 entity_id

---

### 5. Backend: WebSocket Client

**檔案**: `models/common/websocket_client.py`

**職責**:
- 維護與 HA 的 WebSocket 連線
- 管理訊息佇列
- 處理回應與錯誤
- 自動重連機制

**WebSocket 訊息格式**:
```python
{
  "id": unique_id,            # 訊息 ID
  "type": "call_service",     # 訊息類型
  "domain": "switch",         # Entity domain
  "service": "toggle",        # Service name
  "service_data": {           # Service 參數
    "entity_id": "switch.living_room"
  }
}
```

---

## API 參考

### HaDataService.callService()

```javascript
/**
 * 呼叫 Home Assistant service
 * @param {string} domain - Entity domain
 * @param {string} service - Service name
 * @param {Object} serviceData - Service data (must include entity_id)
 * @returns {Promise<Object>} Service call result
 */
async callService(domain, service, serviceData)
```

#### 範例

```javascript
const haDataService = useService("ha_data");

// Toggle a switch
await haDataService.callService('switch', 'toggle', {
  entity_id: 'switch.living_room'
});

// Turn on light with brightness
await haDataService.callService('light', 'turn_on', {
  entity_id: 'light.bedroom',
  brightness: 128  // 0-255
});

// Set climate temperature
await haDataService.callService('climate', 'set_temperature', {
  entity_id: 'climate.living_room',
  temperature: 22
});

// Set HVAC mode
await haDataService.callService('climate', 'set_hvac_mode', {
  entity_id: 'climate.living_room',
  hvac_mode: 'heat'  // 'heat', 'cool', 'auto', 'off'
});
```

---

### useEntityControl Hook

```javascript
import { useEntityControl } from "../entity_controller/hooks/useEntityControl";

// In component setup()
const { state, actions, entityId, domain } = useEntityControl(entityData);

// Use actions
await actions.toggleSwitch();
await actions.setBrightness(200);
await actions.setTemperature(23);
```

---

## 實作範例

### 範例 1: 建立自訂控制按鈕

```javascript
/** @odoo-module **/
import { Component } from "@odoo/owl";
import { useEntityControl } from "./hooks/useEntityControl";

export class CustomSwitch extends Component {
  static template = "my_module.CustomSwitch";
  static props = {
    entity: { type: Object }
  };

  setup() {
    const { state, actions } = useEntityControl(this.props.entity);
    this.state = state;
    this.actions = actions;
  }

  async onClick() {
    await this.actions.toggleSwitch();
  }
}
```

```xml
<t t-name="my_module.CustomSwitch">
  <button
    class="btn"
    t-att-class="{ 'btn-primary': state.entityState === 'on' }"
    t-on-click="onClick"
    t-att-disabled="state.isLoading"
  >
    <i t-if="state.isLoading" class="fa fa-spinner fa-spin"/>
    <t t-else="">
      <t t-esc="state.entityState === 'on' ? 'ON' : 'OFF'"/>
    </t>
  </button>

  <t t-if="state.error">
    <div class="alert alert-danger">
      <t t-esc="state.error"/>
    </div>
  </t>
</t>
```

---

### 範例 2: 直接呼叫 Service (不使用 hook)

```javascript
/** @odoo-module **/
import { Component } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

export class DirectControl extends Component {
  setup() {
    this.haDataService = useService("ha_data");
  }

  async toggleDevice() {
    try {
      await this.haDataService.callService('switch', 'toggle', {
        entity_id: 'switch.living_room'
      });
      console.log("Device toggled successfully");
    } catch (error) {
      console.error("Failed to toggle device:", error);
    }
  }
}
```

---

### 範例 3: 批次控制多個裝置

```javascript
async controlMultipleDevices() {
  const devices = [
    { entity_id: 'switch.living_room' },
    { entity_id: 'switch.bedroom' },
    { entity_id: 'switch.kitchen' }
  ];

  // 平行執行
  const promises = devices.map(device =>
    this.haDataService.callService('switch', 'turn_on', device)
  );

  try {
    await Promise.all(promises);
    console.log("All devices turned on");
  } catch (error) {
    console.error("Some devices failed:", error);
  }
}
```

---

## 常見問題

### Q1: 為什麼控制指令發送後 UI 沒有更新？

**A**: 檢查以下項目：

1. **WebSocket 連線狀態**: 確認 WebSocket 服務正常運行
   ```javascript
   // 在瀏覽器 console 檢查
   console.log(this.haDataService);
   ```

2. **Bus 訂閱**: 確認 HaBusBridge 正常運行
   - 開啟 Chrome DevTools → Network → WS
   - 找到 `/bus/websocket_worker_bundle` 連線
   - 檢查是否有 `ha_entity_update` 事件

3. **Callback 註冊**: 確認組件有正確訂閱更新
   ```javascript
   haDataService.onEntityUpdate(entity_id, callback);
   ```

---

### Q2: 如何知道控制指令是否成功？

**A**: 使用 `callService` 的回傳值：

```javascript
try {
  const result = await haDataService.callService('switch', 'toggle', {
    entity_id: 'switch.test'
  });

  if (result.success) {
    console.log("Success:", result.data);
  }
} catch (error) {
  console.error("Failed:", error.message);
}
```

---

### Q3: 如何支援新的 Domain？

**A**: 三個步驟：

1. **新增控制器模板**:
   建立 `static/src/components/entity_controller/controllers/{domain}_controller.xml`

2. **實作控制邏輯**:
   在 `useEntityControl.js` 的 `actions` 中加入對應方法

3. **註冊到主模板**:
   在 `entity_controller.xml` 加入條件分支

4. **更新 manifest**:
   在 `__manifest__.py` 註冊新檔案

---

### Q4: Optimistic Update vs Server Update 的差異？

**A**:

| 策略 | 優點 | 缺點 | 使用時機 |
|------|------|------|----------|
| **Optimistic** | 立即回應，UX 好 | 可能不一致 | 高可靠性網路 |
| **Server Update** | 保證一致性 | 延遲明顯 | 關鍵操作 |

目前實作使用 **Optimistic Update**：
```javascript
// 立即更新 UI
const newState = state.entityState === 'on' ? 'off' : 'on';
state.entityState = newState;

// 但真實狀態會透過 WebSocket 更新
// 如果失敗，WebSocket 會回傳原狀態
```

---

### Q5: 如何處理控制失敗？

**A**: 使用 error state：

```javascript
const { state, actions } = useEntityControl(entityData);

// state.error 會自動設定
if (state.error) {
  // 顯示錯誤訊息
  console.error(state.error);
}

// 或手動處理
try {
  await actions.toggleSwitch();
} catch (error) {
  // 自訂錯誤處理
}
```

---

## 參考文件

- [Home Assistant WebSocket API](https://developers.home-assistant.io/docs/api/websocket)
- [Home Assistant Service Calls](https://www.home-assistant.io/docs/scripts/service-calls/)
- [Odoo Bus System](https://www.odoo.com/documentation/18.0/developer/reference/frontend/services.html#bus-service)
- [OWL Framework](https://github.com/odoo/owl)

---

## 更新日誌

- **2025-10-15**: 初始版本，完整控制流程文件
