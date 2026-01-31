# 實例切換事件處理技術文件

## 概述

本文件說明 Odoo HA Addon 中的多實例切換機制，以及如何正確響應 `instance_switched` 全域事件。此機制確保當使用者從 Systray 切換 Home Assistant 實例時，所有頁面組件能夠自動重新載入對應的數據。

### 用途

- **全域實例管理**：允許使用者在不同 Home Assistant 實例之間快速切換
- **即時數據同步**：切換實例後，所有頁面自動顯示新實例的數據
- **鬆耦合架構**：通過事件系統實現組件間通信，避免直接依賴

### 應用場景

- 多個 Home Assistant 實例管理（生產環境、測試環境、不同地點）
- Dashboard 和其他頁面需要響應實例切換
- 需要保持當前選中實例狀態的所有組件

---

## 架構設計

### 多實例切換架構

```
┌─────────────────────┐         ┌──────────────────┐         ┌─────────────────────┐
│  HaInstanceSystray  │ switch  │  HaDataService   │ notify  │  Dashboard          │
│  (Systray Component)│────────>│  (Service Layer) │────────>│  (Page Component)   │
│                     │         │                  │         │                     │
│  selectInstance()   │         │ switchInstance() │         │ instanceSwitched    │
│                     │         │ trigger callback │         │ Handler()           │
│                     │         │                  │         │                     │
│  Emits:             │         │  Stores:         │         │  Listens:           │
│  - instance_switched│         │  - current ID    │         │  - instance_switched│
│                     │         │  - callbacks[]   │         │  - reloadAllData()  │
└─────────────────────┘         └──────────────────┘         └─────────────────────┘
        │                              │                              │
        │                              │                              │
        v                              v                              v
   觸發切換                        管理狀態                        重載數據
   (user click)                  (trigger events)              (refresh UI)
```

### 事件流程

```
1. 使用者點擊 Systray 中的實例
   └─> HaInstanceSystray.selectInstance(instanceId)

2. Systray 呼叫 Service 切換實例
   └─> haDataService.switchInstance(instanceId)
   └─> RPC: /odoo_ha_addon/switch_instance

3. Service 觸發全域事件
   └─> haDataService.triggerGlobalCallbacks('instance_switched', {
         instanceId: newId,
         instanceName: newName
       })

4. 所有訂閱的組件收到通知
   └─> Dashboard.instanceSwitchedHandler({ instanceId, instanceName })
   └─> 其他組件的 handlers...

5. 組件重新載入數據
   └─> Dashboard.reloadAllData()
   └─> Promise.all([
         loadWebSocketStatus(),
         loadHardwareInfo(),
         loadNetworkInfo(),
         loadHaUrls()
       ])
```

---

## 核心組件

### 1. `HaDataService` 服務層

位置：`static/src/services/ha_data_service.js`

#### 全域狀態回調系統

**設計理念**：

- ✅ **中央調度器**：所有全域事件通過 Service 統一管理
- ✅ **發布-訂閱模式**：組件訂閱事件，Service 通知所有訂閱者
- ✅ **類型安全**：使用字符串常量作為事件類型

**核心方法**：

```javascript
export const haDataService = {
  // 全域回調儲存
  _globalCallbacks: {
    'instance_switched': [],  // 實例切換事件
    'websocket_status': [],   // WebSocket 狀態變更
    'entity_update_all': [],  // 實體更新
    // ... 其他事件類型
  },

  /**
   * 訂閱全域狀態變更
   * @param {string} eventType - 事件類型 ('instance_switched', 'websocket_status', etc.)
   * @param {function} callback - 回調函數
   */
  onGlobalState(eventType, callback) {
    if (!this._globalCallbacks[eventType]) {
      this._globalCallbacks[eventType] = [];
    }
    this._globalCallbacks[eventType].push(callback);
    console.log(`[HaDataService] Registered callback for '${eventType}'`);
  },

  /**
   * 取消訂閱全域狀態變更
   * @param {string} eventType - 事件類型
   * @param {function} callback - 要移除的回調函數
   */
  offGlobalState(eventType, callback) {
    if (!this._globalCallbacks[eventType]) return;

    const index = this._globalCallbacks[eventType].indexOf(callback);
    if (index > -1) {
      this._globalCallbacks[eventType].splice(index, 1);
      console.log(`[HaDataService] Unregistered callback for '${eventType}'`);
    }
  },

  /**
   * 觸發全域回調
   * @param {string} eventType - 事件類型
   * @param {object} data - 事件數據
   */
  triggerGlobalCallbacks(eventType, data) {
    const callbacks = this._globalCallbacks[eventType] || [];
    console.log(`[HaDataService] Triggering ${callbacks.length} callbacks for '${eventType}'`);

    callbacks.forEach(callback => {
      try {
        callback(data);
      } catch (error) {
        console.error(`[HaDataService] Callback error for '${eventType}':`, error);
      }
    });
  },

  /**
   * 切換 HA 實例
   * @param {number} instanceId - 目標實例 ID
   * @returns {Promise<object>} API 回應 {success, data, error}
   */
  async switchInstance(instanceId) {
    try {
      const result = await rpc('/odoo_ha_addon/switch_instance', {
        instance_id: instanceId
      });

      if (result.success) {
        // 清除快取（新實例的數據不同）
        this.clearCache();

        // 觸發 instance_switched 事件
        this.triggerGlobalCallbacks('instance_switched', {
          instanceId: instanceId,
          instanceName: result.data.instance_name
        });

        console.log(`[HaDataService] Switched to instance: ${result.data.instance_name}`);
      }

      return result;
    } catch (error) {
      console.error('[HaDataService] Failed to switch instance:', error);
      return { success: false, error: error.message };
    }
  },
};
```

#### 事件類型定義

| 事件類型 | 觸發時機 | 數據格式 |
|---------|---------|---------|
| `instance_switched` | 使用者切換 HA 實例 | `{instanceId: number, instanceName: string}` |
| `websocket_status` | WebSocket 連線狀態變更 | `{status: string, message: string}` |
| `entity_update_all` | 實體狀態更新 | `{entityId: string, state: object}` |
| `history_update` | 歷史數據更新 | `{entityId: string, data: array}` |

---

### 2. `HaInstanceSystray` 發送端

位置：`static/src/components/ha_instance_systray/ha_instance_systray.js`

#### 實例切換邏輯

**職責**：

- 顯示當前選中的 HA 實例
- 提供實例列表供使用者選擇
- 呼叫 Service 執行實例切換
- **不直接觸發事件**（由 Service 統一處理）

**核心實現**：

```javascript
class HaInstanceSystray extends Component {
  static template = "odoo_ha_addon.HaInstanceSystray";

  setup() {
    this.haDataService = useService("ha_data");
    this.state = useState({
      instances: [],
      currentId: null,
      loading: true,
    });

    // 訂閱實例切換事件（與其他組件同步）
    this.instanceSwitchedHandler = ({ instanceId, instanceName }) => {
      console.log('[HaInstanceSystray] Instance switched to:', instanceName);
      this.state.currentId = instanceId;  // 同步本地狀態
    };
    this.haDataService.onGlobalState('instance_switched', this.instanceSwitchedHandler);

    onMounted(async () => {
      await this.loadInstances();
    });

    onWillUnmount(() => {
      // ⚠️ 清理：防止 memory leak
      this.haDataService.offGlobalState('instance_switched', this.instanceSwitchedHandler);
    });
  }

  /**
   * 切換到指定的 HA 實例
   * @param {number} instanceId - 目標實例 ID
   */
  async selectInstance(instanceId) {
    // 避免重複切換
    if (instanceId === this.state.currentId) {
      return;
    }

    try {
      console.log('[HaInstanceSystray] Switching to instance:', instanceId);

      // 呼叫 Service 執行切換（Service 會觸發事件）
      const result = await this.haDataService.switchInstance(instanceId);

      if (result.success) {
        console.log('[HaInstanceSystray] Successfully switched to:', result.data.instance_name);
        // state 會由 instanceSwitchedHandler 自動更新
      } else {
        console.error('[HaInstanceSystray] Failed to switch instance:', result.error);
        // TODO: 顯示錯誤通知
      }
    } catch (error) {
      console.error('[HaInstanceSystray] Error switching instance:', error);
    }
  }

  async loadInstances() {
    try {
      const result = await this.haDataService.getInstances();
      if (result.success) {
        this.state.instances = result.data.instances;
        this.state.currentId = result.data.current_instance_id;
      }
    } catch (error) {
      console.error('[HaInstanceSystray] Error loading instances:', error);
    } finally {
      this.state.loading = false;
    }
  }
}
```

#### XML 模板（Bootstrap Dropdown）

```xml
<div class="o_ha_instance_systray dropdown">
  <button class="btn btn-sm dropdown-toggle"
          data-bs-toggle="dropdown"
          t-att-disabled="state.loading">
    <t t-if="currentInstance">
      <span class="oe_topbar_name" t-esc="currentInstance.name"/>
      <i t-att-class="'fa fa-circle ms-1 ' + getStatusClass(currentInstance.websocket_status)"/>
    </t>
  </button>

  <ul class="dropdown-menu">
    <t t-foreach="state.instances" t-as="instance" t-key="instance.id">
      <li>
        <a href="#" class="dropdown-item"
           t-on-click.prevent="() => this.selectInstance(instance.id)">
          <i t-if="isCurrentInstance(instance.id)" class="fa fa-check text-success"/>
          <span t-esc="instance.name"/>
        </a>
      </li>
    </t>
  </ul>
</div>
```

**⚠️ 關鍵實現細節**：

1. **使用 Bootstrap Native Dropdown**：`data-bs-toggle="dropdown"`（不使用 Odoo Dropdown 組件）
2. **事件回調**：`t-on-click.prevent="() => this.selectInstance(instance.id)"`
3. **狀態同步**：通過訂閱 `instance_switched` 事件保持與其他組件同步

---

### 3. `Dashboard` 接收端

位置：`static/src/actions/dashboard/dashboard.js`

#### 數據重載邏輯

**職責**：

- 訂閱 `instance_switched` 事件
- 切換實例後重新載入所有 Dashboard 數據
- 顯示當前實例的 WebSocket、硬體、網路資訊

**核心實現**：

```javascript
class WoowHaInfoDashboard extends Component {
  static template = "odoo_ha_addon.Dashboard";
  static components = { DashboardItem };

  setup() {
    this.state = useState({
      websocket: { connected: false, url: '載入中...', ... },
      hardware: { loading: true, data: null, ... },
      network: { loading: true, data: null, ... },
      haUrls: { loading: true, data: null, ... },
    });

    this.haDataService = useService("ha_data");

    // ⚠️ 關鍵：訂閱實例切換事件
    this.instanceSwitchedHandler = ({ instanceId, instanceName }) => {
      console.log('Dashboard: Instance switched to', instanceName);
      // 重新加載所有數據
      this.reloadAllData();
    };
    this.haDataService.onGlobalState('instance_switched', this.instanceSwitchedHandler);

    // 其他事件訂閱
    this.wsStatusHandler = ({ status, message }) => { /* ... */ };
    this.haDataService.onGlobalState('websocket_status', this.wsStatusHandler);

    this.entityUpdateHandler = () => {
      this.haDataService.clearCache();
    };
    this.haDataService.onGlobalState('entity_update_all', this.entityUpdateHandler);

    onMounted(() => {
      // 初始載入所有數據
      Promise.all([
        this.loadWebSocketStatus(),
        this.loadHardwareInfo(),
        this.loadNetworkInfo(),
        this.loadHaUrls(),
      ]).catch((error) => {
        console.error('Failed to load initial dashboard data:', error);
      });

      // 定時更新（每 5 秒）
      this.interval = setInterval(() => {
        this.loadWebSocketStatus();
      }, 5000);
    });

    onWillUnmount(() => {
      // ⚠️ 必須清理所有事件監聽，防止 memory leak
      this.haDataService.offGlobalState('websocket_status', this.wsStatusHandler);
      this.haDataService.offGlobalState('entity_update_all', this.entityUpdateHandler);
      this.haDataService.offGlobalState('instance_switched', this.instanceSwitchedHandler);

      // 清理 intervals
      if (this.interval) clearInterval(this.interval);
      if (this.hardwareInterval) clearInterval(this.hardwareInterval);
      if (this.networkInterval) clearInterval(this.networkInterval);
      if (this.haUrlsInterval) clearInterval(this.haUrlsInterval);

      console.log('Dashboard: Cleanup complete');
    });
  }

  /**
   * ⚠️ 核心方法：重新加載所有 Dashboard 數據
   * 當實例切換時由 instanceSwitchedHandler 呼叫
   */
  async reloadAllData() {
    console.log('[Dashboard] Reloading all data after instance switch');

    await Promise.all([
      this.loadWebSocketStatus(),
      this.loadHardwareInfo(),
      this.loadNetworkInfo(),
      this.loadHaUrls(),
    ]).catch((error) => {
      console.error('[Dashboard] Failed to reload data:', error);
    });
  }

  async loadWebSocketStatus() {
    try {
      const result = await rpc("/odoo_ha_addon/websocket_status");
      if (result.success) {
        this.state.websocket.connected = result.data.is_running;
        this.state.websocket.url = result.data.current_url;
        // ...
      }
    } catch (error) {
      console.error("Failed to load WebSocket status:", error);
    }
  }

  async loadHardwareInfo() { /* ... */ }
  async loadNetworkInfo() { /* ... */ }
  async loadHaUrls() { /* ... */ }
}
```

---

## 常見錯誤與解決方案

### 錯誤 1: 切換實例後數據未重新載入

**症狀**：

使用者在 Systray 切換實例後，Dashboard 中只有部分數據更新（如 WebSocket 狀態），其他數據（硬體資訊、網路資訊）仍顯示舊實例的數據。

**錯誤原因**：

在移除 Dashboard 的 InstanceSelector 組件時，誤刪了 `instanceSwitchedHandler` 和 `reloadAllData()` 方法。

**錯誤代碼範例**：

```javascript
// ✗ 錯誤：移除了事件監聽器
setup() {
  this.state = useState({ ... });
  this.haDataService = useService("ha_data");

  // ❌ 缺少 instanceSwitchedHandler
  // ❌ 沒有訂閱 'instance_switched' 事件

  this.wsStatusHandler = ({ status, message }) => { /* ... */ };
  this.haDataService.onGlobalState('websocket_status', this.wsStatusHandler);

  onWillUnmount(() => {
    this.haDataService.offGlobalState('websocket_status', this.wsStatusHandler);
    // ❌ 缺少 instance_switched 的清理
  });
}

// ❌ reloadAllData() 方法被誤刪
```

**正確修復**：

```javascript
// ✓ 正確：保留事件監聽和數據重載邏輯
setup() {
  this.state = useState({ ... });
  this.haDataService = useService("ha_data");

  // ✅ 訂閱實例切換事件
  this.instanceSwitchedHandler = ({ instanceId, instanceName }) => {
    console.log('Dashboard: Instance switched to', instanceName);
    this.reloadAllData();  // ✅ 重新載入所有數據
  };
  this.haDataService.onGlobalState('instance_switched', this.instanceSwitchedHandler);

  // 其他事件訂閱...

  onWillUnmount(() => {
    // ✅ 清理所有事件監聽
    this.haDataService.offGlobalState('instance_switched', this.instanceSwitchedHandler);
    this.haDataService.offGlobalState('websocket_status', this.wsStatusHandler);
    // ...
  });
}

// ✅ 保留 reloadAllData() 方法
async reloadAllData() {
  await Promise.all([
    this.loadWebSocketStatus(),
    this.loadHardwareInfo(),
    this.loadNetworkInfo(),
    this.loadHaUrls(),
  ]);
}
```

**關鍵要點**：

1. **UI 簡化 ≠ 功能移除**：移除 Dashboard 的 InstanceSelector UI 組件時，必須保留響應實例切換的邏輯
2. **事件監聽必須保留**：組件需要監聽全域事件以響應使用者操作
3. **數據重載是必需的**：切換實例後，所有與實例相關的數據都需要重新載入

---

### 錯誤 2: Memory Leak（未清理事件監聽器）

**症狀**：

組件卸載後，事件回調仍然被觸發，導致錯誤或 memory leak。

**錯誤原因**：

在 `onWillUnmount` 中未正確清理事件監聽器。

**錯誤代碼範例**：

```javascript
// ✗ 錯誤：未清理事件監聽
setup() {
  this.instanceSwitchedHandler = ({ instanceId, instanceName }) => {
    this.reloadAllData();
  };
  this.haDataService.onGlobalState('instance_switched', this.instanceSwitchedHandler);

  onWillUnmount(() => {
    // ❌ 忘記清理 instance_switched 監聽器
    console.log('Component unmounted');
  });
}
```

**正確修復**：

```javascript
// ✓ 正確：完整清理
setup() {
  this.instanceSwitchedHandler = ({ instanceId, instanceName }) => {
    this.reloadAllData();
  };
  this.haDataService.onGlobalState('instance_switched', this.instanceSwitchedHandler);

  onWillUnmount(() => {
    // ✅ 清理所有事件監聽器
    this.haDataService.offGlobalState('instance_switched', this.instanceSwitchedHandler);
    console.log('Component cleanup complete');
  });
}
```

**最佳實踐**：

```javascript
// 建議：清理所有訂閱
onWillUnmount(() => {
  // 事件監聽器清理
  this.haDataService.offGlobalState('instance_switched', this.instanceSwitchedHandler);
  this.haDataService.offGlobalState('websocket_status', this.wsStatusHandler);
  this.haDataService.offGlobalState('entity_update_all', this.entityUpdateHandler);

  // Interval 清理
  if (this.interval) clearInterval(this.interval);
  if (this.hardwareInterval) clearInterval(this.hardwareInterval);

  console.log('All resources cleaned up');
});
```

---

### 錯誤 3: 直接操作 DOM 而非使用 Reactive State

**症狀**：

數據更新後 UI 未自動刷新，需要手動刷新頁面。

**錯誤原因**：

直接修改普通物件而非 `useState()` 返回的 reactive state。

**錯誤代碼範例**：

```javascript
// ✗ 錯誤：非 reactive state
setup() {
  this.data = {  // ❌ 普通物件，非 reactive
    websocket: { connected: false },
    hardware: { data: null },
  };

  this.instanceSwitchedHandler = () => {
    this.data.websocket.connected = true;  // ❌ 修改不會觸發 UI 更新
  };
}
```

**正確修復**：

```javascript
// ✓ 正確：使用 reactive state
setup() {
  this.state = useState({  // ✅ Reactive state
    websocket: { connected: false },
    hardware: { data: null },
  });

  this.instanceSwitchedHandler = () => {
    this.state.websocket.connected = true;  // ✅ 自動觸發 UI 更新
  };
}
```

---

### 錯誤 4: 忘記清除快取

**症狀**：

切換實例後顯示的仍是舊實例的快取數據。

**錯誤原因**：

`HaDataService` 有快取機制，切換實例後未清除快取。

**錯誤代碼範例**：

```javascript
// ✗ 錯誤：未清除快取
async switchInstance(instanceId) {
  const result = await rpc('/odoo_ha_addon/switch_instance', {
    instance_id: instanceId
  });

  if (result.success) {
    // ❌ 忘記清除快取
    this.triggerGlobalCallbacks('instance_switched', { ... });
  }

  return result;
}
```

**正確修復**：

```javascript
// ✓ 正確：清除快取
async switchInstance(instanceId) {
  const result = await rpc('/odoo_ha_addon/switch_instance', {
    instance_id: instanceId
  });

  if (result.success) {
    this.clearCache();  // ✅ 清除快取
    this.triggerGlobalCallbacks('instance_switched', { ... });
  }

  return result;
}
```

---

## 最佳實踐

### 1. 事件訂閱標準流程

**完整的組件生命週期管理**：

```javascript
class MyComponent extends Component {
  setup() {
    this.haDataService = useService("ha_data");
    this.state = useState({ /* ... */ });

    // 1️⃣ 定義 handler（儲存為實例屬性，以便清理）
    this.instanceSwitchedHandler = ({ instanceId, instanceName }) => {
      console.log(`[MyComponent] Instance switched to ${instanceName}`);
      this.handleInstanceSwitch(instanceId);
    };

    // 2️⃣ 訂閱事件
    this.haDataService.onGlobalState('instance_switched', this.instanceSwitchedHandler);

    // 3️⃣ 掛載時載入初始數據
    onMounted(async () => {
      await this.loadInitialData();
    });

    // 4️⃣ 卸載時清理所有訂閱
    onWillUnmount(() => {
      this.haDataService.offGlobalState('instance_switched', this.instanceSwitchedHandler);
      console.log('[MyComponent] Cleanup complete');
    });
  }

  async handleInstanceSwitch(instanceId) {
    // 處理實例切換邏輯
  }

  async loadInitialData() {
    // 載入初始數據
  }
}
```

---

### 2. 批次數據重載

**使用 `Promise.all()` 並行載入**：

```javascript
// ✓ 好的做法：並行載入
async reloadAllData() {
  console.log('[Component] Reloading all data');

  await Promise.all([
    this.loadDataA(),
    this.loadDataB(),
    this.loadDataC(),
  ]).catch((error) => {
    console.error('[Component] Failed to reload data:', error);
  });
}

// ✗ 避免：序列載入（效能差）
async reloadAllData() {
  await this.loadDataA();  // ❌ 等待 A 完成
  await this.loadDataB();  // ❌ 等待 B 完成
  await this.loadDataC();  // ❌ 等待 C 完成
}
```

---

### 3. 錯誤處理與日誌

**適當的日誌層級**：

```javascript
// INFO: 重要的狀態變更
console.log('[Component] Instance switched to:', instanceName);
console.log('[Component] Data reload complete');

// DEBUG: 詳細處理過程（生產環境可關閉）
console.debug('[Component] Loading hardware info...');
console.debug('[Component] Current state:', this.state);

// WARN: 非致命問題
console.warn('[Component] Failed to load hardware info, using cached data');

// ERROR: 錯誤和異常
console.error('[Component] Critical error during reload:', error);
```

**統一錯誤處理**：

```javascript
async reloadAllData() {
  try {
    await Promise.all([
      this.loadDataA(),
      this.loadDataB(),
      this.loadDataC(),
    ]);
    console.log('[Component] Reload successful');
  } catch (error) {
    console.error('[Component] Reload failed:', error);
    // 可選：顯示使用者通知
    this.state.error = '資料載入失敗，請稍後再試';
  }
}
```

---

### 4. Reactive State 使用規範

**正確使用 `useState()`**：

```javascript
// ✓ 正確：使用 reactive state
setup() {
  this.state = useState({
    data: null,
    loading: false,
    error: null,
  });

  this.instanceSwitchedHandler = () => {
    this.state.loading = true;  // ✅ 自動觸發 UI 更新
    this.reloadData().then(() => {
      this.state.loading = false;  // ✅ 自動觸發 UI 更新
    });
  };
}
```

**避免直接修改 nested objects**：

```javascript
// ✗ 錯誤：修改 nested object 可能不觸發更新
this.state.websocket.connected = true;  // ⚠️ 可能不觸發更新

// ✓ 正確：重新賦值整個物件
this.state.websocket = {
  ...this.state.websocket,
  connected: true,
};

// 或使用 Object.assign
Object.assign(this.state.websocket, { connected: true });
```

---

### 5. 防止重複切換

**檢查當前實例**：

```javascript
async selectInstance(instanceId) {
  // ✅ 避免重複切換
  if (instanceId === this.state.currentId) {
    console.log('[Component] Already on this instance');
    return;
  }

  console.log('[Component] Switching to instance:', instanceId);
  const result = await this.haDataService.switchInstance(instanceId);
  // ...
}
```

---

### 6. 清除快取時機

**切換實例時清除**：

```javascript
async switchInstance(instanceId) {
  const result = await rpc('/odoo_ha_addon/switch_instance', {
    instance_id: instanceId
  });

  if (result.success) {
    // ✅ 清除快取（新實例的數據不同）
    this.clearCache();

    // 觸發事件
    this.triggerGlobalCallbacks('instance_switched', {
      instanceId: instanceId,
      instanceName: result.data.instance_name
    });
  }

  return result;
}
```

**實體更新時清除**：

```javascript
setup() {
  this.entityUpdateHandler = () => {
    console.log('Entity updated, clearing cache');
    this.haDataService.clearCache();  // ✅ 清除快取以重新載入
  };
  this.haDataService.onGlobalState('entity_update_all', this.entityUpdateHandler);
}
```

---

## 測試與驗證

### 手動測試流程

1. **載入 Dashboard 頁面**
   - 確認初始數據正確載入（WebSocket、硬體、網路資訊）
   - 檢查 console 無錯誤訊息

2. **切換實例（從 Systray）**
   - 點擊 Systray 中的不同實例
   - 確認 Dashboard 中所有數據自動更新
   - 檢查 console 顯示 `[Dashboard] Instance switched to ...`
   - 檢查 console 顯示 `[Dashboard] Reloading all data after instance switch`

3. **驗證數據正確性**
   - WebSocket 狀態顯示新實例的連線狀態
   - 硬體資訊顯示新實例的硬體資料
   - 網路資訊顯示新實例的網路配置
   - HA URLs 顯示新實例的存取網址

4. **離開並返回 Dashboard**
   - 導航到其他頁面
   - 返回 Dashboard
   - 確認仍顯示當前選中實例的數據

5. **檢查 Memory Leak**
   - 在 Dashboard 和其他頁面間多次切換
   - 切換多個實例
   - 檢查 console 顯示 `[Dashboard] Cleanup complete`
   - 使用瀏覽器 Performance Monitor 確認無 memory leak

### Console 日誌檢查清單

**正常流程應該看到**：

```
[HaInstanceSystray] Switching to instance: 2
[HaDataService] Switched to instance: Production HA
[HaDataService] Triggering 3 callbacks for 'instance_switched'
[HaInstanceSystray] Instance switched to: Production HA
[Dashboard] Instance switched to Production HA
[Dashboard] Reloading all data after instance switch
[Dashboard] Reload successful
```

**錯誤情況**：

```
❌ [Dashboard] Instance switched to Production HA
   (但沒有看到 "Reloading all data" → 缺少 reloadAllData())

❌ TypeError: Cannot read properties of undefined
   (可能是未清理的 handler 試圖存取已卸載組件的 state)

❌ [HaDataService] Callback error for 'instance_switched': ...
   (回調函數內部錯誤，需檢查 handler 實現)
```

---

## 擴展與未來改進

### 支援更多組件

**其他需要響應實例切換的組件**：

```javascript
// Area Dashboard
class AreaDashboard extends Component {
  setup() {
    this.haDataService = useService("ha_data");

    this.instanceSwitchedHandler = ({ instanceId, instanceName }) => {
      console.log('[AreaDashboard] Instance switched');
      this.reloadAreas();  // 重新載入區域列表
    };
    this.haDataService.onGlobalState('instance_switched', this.instanceSwitchedHandler);

    onWillUnmount(() => {
      this.haDataService.offGlobalState('instance_switched', this.instanceSwitchedHandler);
    });
  }
}

// Entity Kanban View
class EntityKanbanController extends Component {
  setup() {
    this.haDataService = useService("ha_data");

    this.instanceSwitchedHandler = ({ instanceId, instanceName }) => {
      console.log('[EntityKanban] Instance switched');
      this.model.load();  // 重新載入實體列表
    };
    this.haDataService.onGlobalState('instance_switched', this.instanceSwitchedHandler);

    onWillUnmount(() => {
      this.haDataService.offGlobalState('instance_switched', this.instanceSwitchedHandler);
    });
  }
}
```

### 新增事件類型

**定義新的全域事件**：

```javascript
// 在 HaDataService 中新增
export const haDataService = {
  _globalCallbacks: {
    'instance_switched': [],
    'websocket_status': [],
    'entity_update_all': [],
    'area_updated': [],         // ✨ 新增：區域更新事件
    'automation_triggered': [], // ✨ 新增：自動化觸發事件
  },

  // 觸發區域更新事件
  notifyAreaUpdated(areaId, areaName) {
    this.triggerGlobalCallbacks('area_updated', { areaId, areaName });
  },
};
```

### 優化建議

1. **快取策略優化**
   - 實例級別的快取（不同實例使用不同快取 key）
   - 智能快取失效（只清除受影響的數據）

2. **Loading 狀態管理**
   - 全域 loading indicator
   - 防止重複載入（debounce）

3. **錯誤恢復機制**
   - 自動重試
   - 降級到快取數據

---

## 相關文件

- **Session-Based Instance 架構**：`docs/tech/session-instance.md` - 後端架構設計和 API 使用指南
  - 適用場景：理解架構決策、實現新 API endpoint、調試 Session 問題
  - 重點內容：優先級降級、Session 存儲、API 設計模式
- **Service Layer**: `static/src/services/ha_data_service.js`
- **Systray Component**: `static/src/components/ha_instance_systray/`
- **Dashboard Action**: `static/src/actions/dashboard/`
- **Backend API**: `controllers/http_controllers.py` (`switch_instance` endpoint)
- **Bus Notification System**: `docs/tech/bus-mechanisms-comparison.md`

---

## 版本歷史

- **v1.0** (2025-11-02): 初始版本
  - 完整的 instance_switched 事件處理機制
  - HaInstanceSystray 和 Dashboard 整合
  - 常見錯誤與最佳實踐總結
  - 基於 Phase 4 多實例支持實作經驗
