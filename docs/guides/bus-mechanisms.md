# Odoo 18 Bus 機制對比：useBus() vs bus_service.subscribe()

> 本文檔說明 Odoo 18 中兩種不同的事件訂閱機制的差異與使用場景

## 目錄

- [核心差異](#核心差異)
- [useBus() - OWL Component Hook](#usebus---owl-component-hook)
- [bus_service.subscribe() - Odoo Bus Service](#bus_servicesubscribe---odoo-bus-service)
- [完整對比表](#完整對比表)
- [實際應用範例](#實際應用範例)
- [常見錯誤與解決方案](#常見錯誤與解決方案)
- [最佳實踐建議](#最佳實踐建議)

---

## 核心差異

兩者是**完全不同的系統**，服務於不同的通訊場景：

| 機制 | 通訊範圍 | 適用場景 |
|------|---------|---------|
| `useBus()` | 前端內部 | 組件間通訊 |
| `bus_service.subscribe()` | 後端→前端 | 即時推送通知 |

**類比**：
- `useBus()` = 室內對講機（只能在前端內部使用）
- `bus_service.subscribe()` = 手機（可以接收後端的遠程訊息）

---

## useBus() - OWL Component Hook

### 基本概念

`useBus()` 是 OWL 框架提供的 Hook，用於監聽前端 JavaScript 的 EventBus 事件。

### 導入方式

```javascript
import { useBus } from "@web/core/utils/hooks";
```

### 使用語法

```javascript
export class MyComponent extends Component {
  setup() {
    useBus(this.env.bus, 'event_name', (event) => {
      console.log('收到事件:', event.detail);
    });
  }
}
```

### 特點

- 🎯 **事件來源**：前端 JavaScript 代碼
- 📍 **事件總線**：`this.env.bus`（OWL EventBus）
- 🔄 **觸發方式**：`this.env.bus.trigger('event_name', data)`
- ✅ **優勢**：簡單、輕量、適合組件間通訊
- ❌ **限制**：無法接收後端通知

### 完整範例

#### 發送事件（ComponentA）
```javascript
export class ComponentA extends Component {
  sendMessage() {
    this.env.bus.trigger('custom_event', {
      message: 'Hello from A'
    });
  }
}
```

#### 接收事件（ComponentB）
```javascript
export class ComponentB extends Component {
  setup() {
    useBus(this.env.bus, 'custom_event', (event) => {
      console.log(event.detail.message); // 'Hello from A'
    });
  }
}
```

### 使用場景

✅ **適合使用的場景**：
- 父子組件間通訊
- 兄弟組件間通訊
- 不涉及後端的本地事件
- UI 狀態同步（純前端）

❌ **不適合使用的場景**：
- 接收後端推送的通知
- 跨用戶的即時通訊
- WebSocket 實時數據

---

## bus_service.subscribe() - Odoo Bus Service

### 基本概念

`bus_service` 是 Odoo 的核心服務，透過 WebSocket (`/bus/websocket`) 與後端的 bus.bus 系統通訊，實現即時推送功能。

### 導入方式

```javascript
import { useService } from "@web/core/utils/hooks";
```

### 使用語法

```javascript
export class MyComponent extends Component {
  setup() {
    const busService = useService("bus_service");

    // 訂閱通知類型
    busService.subscribe('notification_type', (payload) => {
      console.log('收到後端通知:', payload);
    });

    // 啟動 bus service
    busService.start();
  }
}
```

### 特點

- 🎯 **事件來源**：後端 Python 代碼
- 📍 **通訊協議**：WebSocket (`/bus/websocket`)
- 🔄 **發送方式**：`bus.bus._sendone()` 或 `_bus_send()`
- ✅ **優勢**：即時、跨進程、多用戶廣播
- 🔑 **關鍵**：需要訂閱 channel（partner channel 自動訂閱）

### 完整範例

#### 後端發送通知（Python）
```python
class HaRealtimeUpdate(models.Model):
    _name = 'ha.realtime.update'
    _inherit = ['bus.listener.mixin']

    def _bus_channel(self):
        """定義 channel - 返回當前用戶的 partner"""
        return self.env.user.partner_id

    @api.model
    def notify_ha_websocket_status(self, status, message):
        """廣播 WebSocket 狀態給所有用戶"""
        users = self.env['res.users'].search([('id', '!=', 1)])
        for user in users:
            user.partner_id._bus_send(
                'ha_websocket_status',  # notification_type
                {
                    'status': status,
                    'message': message,
                    'timestamp': datetime.now().isoformat()
                }
            )
```

#### 前端接收通知（JavaScript）
```javascript
export class HaBusBridge extends Component {
  setup() {
    const busService = useService("bus_service");
    const haDataService = useService("ha_data");

    // 訂閱後端發送的通知類型
    busService.subscribe('ha_websocket_status', (payload) => {
      console.log('[Bus] 收到 WebSocket 狀態:', payload);
      // payload = { status: 'connected', message: '...', timestamp: '...' }
      haDataService.handleServiceStatus(payload);
    });

    busService.start();
  }
}
```

### Channel 機制說明

#### 什麼是 Channel？

Channel 是 Odoo Bus 的通訊頻道，決定誰能接收到通知：

```python
# 後端發送到特定 channel
user.partner_id._bus_send('notification_type', message)
# 相當於: bus.bus._sendone(
#   ('dbname', 'res.partner', partner_id),  # ← channel
#   'notification_type',
#   message
# )
```

#### Partner Channel 自動訂閱

Odoo 18 會自動為每個登入用戶訂閱其 partner channel：

```javascript
// 當用戶登入時，Odoo 自動執行：
busService.addChannel(`res.partner,${user.partner_id}`);
```

因此，只要後端發送到 `user.partner_id`，前端就能接收！

### 使用場景

✅ **適合使用的場景**：
- 後端事件推送（資料更新、狀態變更）
- 多用戶協作通知
- WebSocket 即時通訊
- 跨進程的狀態同步

❌ **不適合使用的場景**：
- 純前端的 UI 事件
- 不需要後端參與的組件通訊

---

## 完整對比表

| 特性 | `useBus()` | `bus_service.subscribe()` |
|------|-----------|---------------------------|
| **導入來源** | `@web/core/utils/hooks` | `useService("bus_service")` |
| **事件總線** | `this.env.bus` (EventBus) | Odoo Bus (WebSocket) |
| **事件來源** | 前端 JavaScript | 後端 Python |
| **觸發方式** | `bus.trigger(type, data)` | `_bus_send(type, message)` |
| **通訊協議** | 本地 JavaScript 事件 | WebSocket (`/bus/websocket`) |
| **跨進程** | ❌ 不支援 | ✅ 支援 |
| **跨用戶** | ❌ 不支援 | ✅ 支援 |
| **需要 Channel** | ❌ 不需要 | ✅ 需要（自動訂閱 partner） |
| **適用範圍** | 組件間本地通訊 | 後端→前端即時推送 |
| **網絡請求** | 無 | 有（WebSocket 連線） |
| **性能開銷** | 極低 | 低（WebSocket 保持連線） |
| **離線支援** | ✅ 完全離線可用 | ❌ 需要網絡連線 |

---

## 實際應用範例

### 情境 1：前端組件間通訊（用 useBus）

**需求**：表單組件填寫完成後，通知列表組件刷新

```javascript
// FormComponent.js - 發送事件
export class FormComponent extends Component {
  async saveForm() {
    await this.orm.create('model.name', this.formData);

    // 通知其他組件刷新
    this.env.bus.trigger('form_saved', {
      model: 'model.name'
    });
  }
}

// ListComponent.js - 接收事件
export class ListComponent extends Component {
  setup() {
    useBus(this.env.bus, 'form_saved', async (event) => {
      if (event.detail.model === 'model.name') {
        await this.loadData();  // 重新載入列表
      }
    });
  }
}
```

✅ 正確使用 `useBus()`，因為是純前端通訊

---

### 情境 2：後端推送即時通知（用 bus_service）

**需求**：Home Assistant WebSocket 連線狀態變更時，通知前端 Dashboard

#### 後端實作（Python）
```python
# models/ha_realtime_update.py
class HaRealtimeUpdate(models.Model):
    _name = 'ha.realtime.update'
    _inherit = ['bus.listener.mixin']

    def _bus_channel(self):
        return self.env.user.partner_id

    @api.model
    def notify_ha_websocket_status(self, status, message):
        """廣播 WebSocket 狀態給所有在線用戶"""
        users = self.env['res.users'].search([('id', '!=', 1)])
        for user in users:
            user.partner_id._bus_send('ha_websocket_status', {
                'status': status,
                'message': message,
                'timestamp': datetime.now().isoformat()
            })
```

#### 前端實作（JavaScript）
```javascript
// static/src/services/ha_bus_bridge.js
export class HaBusBridge extends Component {
  setup() {
    const busService = useService("bus_service");
    const haDataService = useService("ha_data");

    busService.subscribe('ha_websocket_status', (payload) => {
      console.log('[HaBusBridge] WebSocket 狀態:', payload);
      haDataService.handleServiceStatus(payload);
    });

    busService.start();
  }
}

// static/src/actions/dashboard/dashboard.js
export class Dashboard extends Component {
  setup() {
    const haDataService = useService("ha_data");
    this.state = useState({
      websocket: { connected: false, message: '' }
    });

    // 訂閱 WebSocket 狀態變更
    this.wsStatusHandler = ({ status, message }) => {
      this.state.websocket.connected = (status === 'connected');
      this.state.websocket.message = message;
    };

    haDataService.onGlobalState('websocket_status', this.wsStatusHandler);
  }
}
```

✅ 正確使用 `bus_service.subscribe()`，因為需要接收後端通知

---

## 常見錯誤與解決方案

### ❌ 錯誤 1：使用 useBus 接收後端通知

```javascript
// ❌ 錯誤做法 - 永遠收不到後端通知
useBus(this.env.bus, 'ha_websocket_status', (event) => {
  console.log('永遠不會執行');
});
```

**問題**：`useBus()` 監聽的是前端 EventBus，後端通知走 WebSocket

**解決方案**：
```javascript
// ✅ 正確做法
const busService = useService("bus_service");
busService.subscribe('ha_websocket_status', (payload) => {
  console.log('成功接收:', payload);
});
busService.start();
```

---

### ❌ 錯誤 2：忘記啟動 bus service

```javascript
// ❌ 錯誤做法
const busService = useService("bus_service");
busService.subscribe('ha_websocket_status', callback);
// 忘記調用 start()
```

**問題**：WebSocket 連線未建立

**解決方案**：
```javascript
// ✅ 正確做法
const busService = useService("bus_service");
busService.subscribe('ha_websocket_status', callback);
busService.start();  // ← 必須調用
```

---

### ❌ 錯誤 3：後端發送到錯誤的 channel

```python
# ❌ 錯誤做法
def _bus_channel(self):
    return self  # 返回 model 記錄，前端沒訂閱這個 channel
```

**問題**：前端只自動訂閱 partner channel，無法接收其他 channel 的通知

**解決方案**：
```python
# ✅ 正確做法
def _bus_channel(self):
    return self.env.user.partner_id  # 返回 partner，前端會自動訂閱
```

---

### ❌ 錯誤 4：混淆 event.detail 與 payload

```javascript
// useBus 使用 event.detail
useBus(this.env.bus, 'event_name', (event) => {
  console.log(event.detail);  // ← 前端事件
});

// bus_service 直接傳 payload
busService.subscribe('notification_type', (payload) => {
  console.log(payload);  // ← 後端通知，無需 .detail
});
```

---

## 最佳實踐建議

### 1. 選擇正確的機制

```
需要接收後端通知？
├─ 是 → 使用 bus_service.subscribe()
└─ 否 → 純前端組件通訊？
    ├─ 是 → 使用 useBus()
    └─ 否 → 考慮使用 props 或 service
```

### 2. Bus Bridge 模式（推薦）

集中管理所有 bus 訂閱，避免重複訂閱：

```javascript
// ha_bus_bridge.js - 單一訂閱點
export class HaBusBridge extends Component {
  setup() {
    const busService = useService("bus_service");
    const haDataService = useService("ha_data");

    // 集中訂閱所有通知類型
    busService.subscribe('ha_entity_update', (payload) => {
      haDataService.handleEntityUpdate(payload);
    });

    busService.subscribe('ha_websocket_status', (payload) => {
      haDataService.handleServiceStatus(payload);
    });

    busService.start();
  }
}

// 註冊為全域組件
registry.category("main_components").add("ha_bus_bridge", {
  Component: HaBusBridge,
});
```

### 3. Service 層分發

使用 Service 層接收 bus 通知，再透過 callback 分發給需要的組件：

```javascript
// ha_data_service.js
export class HaDataService {
  constructor() {
    this.globalStateCallbacks = {
      websocket_status: [],
      entity_update: []
    };
  }

  handleServiceStatus(data) {
    // 處理通知並觸發 callbacks
    this.triggerGlobalCallbacks('websocket_status', data);
  }

  onGlobalState(eventType, callback) {
    this.globalStateCallbacks[eventType].push(callback);
  }

  triggerGlobalCallbacks(eventType, data) {
    this.globalStateCallbacks[eventType].forEach(cb => cb(data));
  }
}
```

### 4. 清理訂閱

在組件銷毀時記得清理訂閱：

```javascript
export class MyComponent extends Component {
  setup() {
    const haDataService = useService("ha_data");

    this.statusHandler = (data) => {
      console.log(data);
    };

    haDataService.onGlobalState('websocket_status', this.statusHandler);

    onWillUnmount(() => {
      haDataService.offGlobalState('websocket_status', this.statusHandler);
    });
  }
}
```

### 5. 錯誤處理

```javascript
busService.subscribe('ha_websocket_status', (payload) => {
  try {
    haDataService.handleServiceStatus(payload);
  } catch (error) {
    console.error('處理 bus 通知時發生錯誤:', error);
  }
});
```

---

## 架構圖

### 前端組件通訊（useBus）
```
ComponentA
    │
    ├─ trigger('event')
    │
    ▼
this.env.bus (EventBus)
    │
    ├─ useBus() 監聽
    │
    ▼
ComponentB
```

### 後端到前端通知（bus_service）
```
Python 後端
    │
    ├─ _bus_send('type', data)
    │
    ▼
bus.bus (Odoo Bus)
    │
    ├─ WebSocket (/bus/websocket)
    │
    ▼
前端 bus_service
    │
    ├─ subscribe('type', callback)
    │
    ▼
HaBusBridge
    │
    ├─ 轉發給 Service
    │
    ▼
HaDataService
    │
    ├─ 觸發 callbacks
    │
    ▼
Dashboard Component
```

---

## 相關資源

### Odoo 官方文檔
- [Bus Service Documentation](https://www.odoo.com/documentation/18.0/developer/reference/frontend/services.html#bus-service)
- [bus.listener.mixin](https://github.com/odoo/odoo/blob/18.0/addons/bus/models/bus_listener_mixin.py)
- [OWL Hooks](https://github.com/odoo/owl/blob/master/doc/reference/hooks.md)

### 本項目相關文件
- `static/src/services/ha_bus_bridge.js` - Bus Bridge 實作
- `static/src/services/ha_data_service.js` - Service 層實作
- `models/ha_realtime_update.py` - 後端通知發送

---

## 版本記錄

| 日期 | 版本 | 更新內容 |
|------|------|---------|
| 2025-10-14 | 1.0 | 初始版本，整理 useBus 與 bus_service 差異 |

---

## 作者

Eugene @ WOOW Tech

本文檔基於實際開發 Odoo 18 Home Assistant 整合專案的經驗整理。
