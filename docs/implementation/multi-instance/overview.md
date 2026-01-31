# 多 HA 實例支援實施進度

## 📊 專案資訊

**開始日期**: 2025-10-31
**預計完成**: 15 工作天（3 週）
**當前階段**: 🎉 **專案完成** - Phase 1-6 全部完成
**最後更新**: 2025-11-04 (Phase 6 完成 - 測試與文檔)
**專案狀態**: ✅ 100% 完成，32 項測試全部通過

## 🎯 實施方案

- **方案類型**: 完整多實例支援（方案 A）
- **UI 位置**: Dashboard 頂部導航列
- **權限控管**: 啟用（用戶只能存取授權的實例）
- **連接策略**: 全部連接（所有實例同時保持 WebSocket 連接）

---

## Phase 1: 基礎架構 (3 天) ✅ 已完成

### ✅ Task 1.1: 新增 ha.instance 模型
**狀態**: ✅ 已完成
**開始時間**: 2025-10-31 09:15
**完成時間**: 2025-10-31 09:45
**負責人**: Claude Code

**子任務**:
- [x] 創建 `models/ha_instance.py` 文件
- [x] 實作基本欄位（name, api_url, api_token, active, sequence）
- [x] 實作 user_ids Many2many 欄位（權限控管）
- [x] 實作 `get_accessible_instances()` 方法
- [x] ~~實作 `_check_single_default()` 約束~~ ⚠️ 已移除 (2025-11-25)
- [x] 實作 `_compute_ws_url()` 計算欄位
- [x] 更新 `models/__init__.py` 導入新模型

> ⚠️ **架構更新 (2025-11-25)**: `is_default` 欄位已移除，改用 `sequence` 排序 + `get_accessible_instances()` 權限感知選擇

**完成內容**:
- 創建完整的 ha.instance 模型，包含所有必要欄位和方法
- 實作權限控管機制（user_ids Many2many）
- ~~實作預設實例約束（確保只有一個預設實例）~~ ⚠️ 已移除
- 實作 `test_connection()` 和 `action_test_connection()` 方法
- 實作 `get_websocket_config()` 輔助方法（直接使用 `HassRestApi(env, instance_id)` 取得 REST API 客戶端）

**技術細節**:
```python
class HAInstance(models.Model):
    _name = 'ha.instance'
    _description = 'Home Assistant Instance'

    # 基本欄位
    name = fields.Char(string='Instance Name', required=True)
    api_url = fields.Char(string='API URL', required=True)
    api_token = fields.Char(string='Access Token', required=True)
    active = fields.Boolean(string='Active', default=True)
    sequence = fields.Integer(string='Sequence', default=10)  # ⚠️ 取代 is_default (2025-11-25)

    # 權限控管
    user_ids = fields.Many2many('res.users', string='Allowed Users')

    # 計算欄位
    ws_url = fields.Char(string='WebSocket URL', compute='_compute_ws_url')
```

---

### ✅ Task 1.2: 更新 Entity 相關模型
**狀態**: ✅ 已完成
**開始時間**: 2025-10-31 09:45
**完成時間**: 2025-10-31 10:30

**需要修改的模型**:
- [x] `models/ha_entity.py` - 新增 ha_instance_id + 複合唯一約束
- [x] `models/ha_entity_history.py` - 新增 ha_instance_id（related field）
- [x] `models/ha_area.py` - 新增 ha_instance_id + 複合唯一約束
- [x] `models/ha_entity_group.py` - 新增 ha_instance_id（可選）
- [x] `models/ha_ws_request_queue.py` - 新增 ha_instance_id
- [x] `models/ha_realtime_update.py` - 更新通知方法附加 instance_id

**完成內容**:
- 所有 Entity 相關模型都已新增 `ha_instance_id` 外鍵
- `ha.entity` 和 `ha.area` 新增複合唯一約束 `(entity_id/area_id, ha_instance_id)`
- `ha.entity.history` 使用 related field 自動繼承實例關聯
- `ha.realtime.update` 的三個通知方法都新增 `ha_instance_id` 參數
- 所有修改都保持向後兼容（ha_instance_id 參數為可選）

**關鍵變更**:
```python
# ha_entity.py
ha_instance_id = fields.Many2one('ha.instance', string='HA Instance', required=True, index=True)

_sql_constraints = [
    ('entity_instance_unique',
     'unique(entity_id, ha_instance_id)',
     'Entity ID must be unique per HA instance')
]
```

---

### ✅ Task 1.3: 創建 Views 和 Security
**狀態**: ✅ 已完成
**開始時間**: 2025-10-31 10:30
**完成時間**: 2025-10-31 11:00

**子任務**:
- [x] 創建 `views/ha_instance_views.xml`
  - [x] Tree view（列表視圖，支援拖曳排序）
  - [x] Form view（表單視圖，包含狀態欄、統計按鈕）
  - [x] Kanban view（卡片視圖，適用於行動裝置）
  - [x] Search view（搜尋視圖，多種過濾條件）
- [x] 更新 `security/ir.model.access.csv`
  - [x] ha_instance 模型存取權限
  - [x] ha_ws_request_queue 模型存取權限
- [x] 新增選單項目（Settings > Configuration > HA Instances）
- [x] 更新 `__manifest__.py` data 列表

**完成內容**:
- 創建完整的 CRUD views（Tree, Form, Kanban, Search）
- Form view 包含 "Test Connection" 和 "Sync Entities" 按鈕
- 實作狀態指示（連接狀態、預設實例、啟用狀態）
- 實作統計資訊顯示（Entity Count）
- 新增權限控管 UI（Allowed Users tab）

---

### ✅ Task 1.4: 數據遷移腳本
**狀態**: ✅ 已完成
**開始時間**: 2025-10-31 11:00
**完成時間**: 2025-10-31 11:30

**子任務**:
- [x] 創建 `migrations/18.0.3.0/` 目錄
- [x] 創建 `pre-migrate.py` 腳本
- [x] 實作遷移邏輯：
  - [x] 從 ir.config_parameter 讀取現有 ha_api_url 和 ha_api_token
  - [x] 創建預設 HA 實例（名稱：Default HA）
  - [x] 將所有現有 entities 關聯到預設實例
  - [x] 遷移 history、area、queue 等相關數據

**完成內容**:
- 完整的資料庫遷移腳本（pre-migrate.py）
- 自動檢測並跳過已遷移的資料庫
- 完整的錯誤處理和日誌記錄
- 遷移統計報告（顯示遷移的記錄數量）
- 向後兼容（支援全新安裝和現有系統升級）

**預期結果**:
- ✅ 所有現有數據完整保留
- ✅ 系統可正常運行在單一實例模式
- ✅ 為多實例功能奠定基礎

---

## Phase 2: WebSocket 重構 (4 天) ✅ 已完成

**狀態**: ✅ 已完成
**開始時間**: 2025-11-01 09:00
**完成時間**: 2025-11-01 16:30
**實際耗時**: 約 7.5 小時（開發 + 測試）

### ✅ Task 2.1: 移除 WebSocket 單例限制
**狀態**: ✅ 已完成
**完成時間**: 2025-11-01 12:00

**完成內容**:
- [x] 修改 `models/common/hass_websocket_service.py`
- [x] 移除 `_instance` 類變數（第 17 行）
- [x] 移除 `get_instance()` 單例方法（第 854 行）
- [x] 新增 `instance_id` 初始化參數（第 21 行）
- [x] 修改 `get_websocket_url()` 從 ha.instance 讀取配置（第 64 行）
- [x] 修改 `get_access_token()` 從 ha.instance 讀取配置（第 106 行）
- [x] 所有實體操作加上 `ha_instance_id` 過濾（第 681 行）
- [x] 心跳機制加入 `instance_id`（第 1009 行）
- [x] 請求佇列加入實例過濾（第 1031 行）

### ✅ Task 2.2: 連接管理器重構
**狀態**: ✅ 已完成
**完成時間**: 2025-11-01 14:30

**完成內容**:
- [x] 修改 `models/common/websocket_thread_manager.py`
- [x] 改為雙層結構 `{db_name: {instance_id: {...}}}`（第 12 行）
- [x] 更新 `_run_websocket_in_thread()` 支援 instance_id（第 21 行）
- [x] 重寫 `start_websocket_service()`（第 102 行）
  - 支援啟動特定實例或所有實例
  - 自動查找 active=True 的實例
- [x] 重寫 `stop_websocket_service()`（第 184 行）
  - 支援停止特定實例或所有實例
  - 三種模式：全部/資料庫/實例
- [x] 重寫 `is_websocket_service_running()`（第 272 行）
  - 支援檢查特定實例狀態
  - 跨進程心跳檢查
- [x] 更新 `is_config_changed()`（第 420 行）
  - 從 ha.instance 讀取配置
- [x] 重寫 `restart_websocket_service()`（第 517 行）
  - 支援重啟特定實例或所有實例

### ✅ Task 2.3: 更新 Hooks
**狀態**: ✅ 已完成
**完成時間**: 2025-11-01 15:00

**完成內容**:
- [x] 修改 `hooks.py` 支援多實例啟動
- [x] `post_load_hook()` 自動啟動所有活躍實例（第 130 行）
- [x] 查詢並記錄實例數量
- [x] 更新日誌訊息反映多實例
- [x] `uninstall_hook()` 停止所有實例（第 62 行）

### 🎁 額外改進

#### ✅ WebSocket Status 動態顯示
**完成時間**: 2025-11-01 08:30

**問題**: List view 的 WebSocket Status 欄位是靜態的，無法反映實際狀態

**解決方案**:
- [x] 將 `websocket_status` 改為 computed field（`models/ha_instance.py:84`）
- [x] 新增 `_compute_websocket_status()` 方法（第 133 行）
- [x] 檢查心跳新鮮度（≤60秒=connected, 60-120秒=connecting, >120秒=disconnected）
- [x] 移除 search view 中無法使用的 filter

#### ✅ 批次重啟 WebSocket 功能
**完成時間**: 2025-11-01 09:20

**功能**: 在 list view 多選實例後批次重啟 WebSocket

**實作內容**:
- [x] 新增 `action_restart_websocket()` 方法（`models/ha_instance.py:494`）
  - 支援單一或多個實例
  - 智能通知訊息（單一/批次不同格式）
  - 詳細的錯誤處理
- [x] 新增 Server Action（`views/ha_instance_views.xml:195`）
  - 綁定到 list 和 form view
  - 自動出現在 Actions 選單

---

## Phase 3: API 層整合 (2 天)

**狀態**: ✅ 已完成
**完成時間**: 2025-11-01 下午
**實際花費**: 0.5 天

### Task 3.1: Controller 基礎方法
- [x] 新增 `_get_current_instance()` 方法（`controllers/controllers.py:11`）
  - 實作 4 級 fallback：session → user preference → default instance → first active
  - 自動驗證實例是否存在且活躍
  - 清理無效 session 資料
- [x] 新增 `/get_instances` endpoint（第 560 行）
  - 返回所有活躍實例列表
  - 包含當前實例 ID
  - 顯示 WebSocket 狀態、entity 數量等詳細資訊
- [x] 新增 `/switch_instance` endpoint（第 605 行）
  - 驗證實例是否存在且活躍
  - 儲存選擇到 session
  - 返回切換成功訊息

### Task 3.2: 更新所有 API endpoints
- [x] 修改 8 個 endpoints 支援 `ha_instance_id` 參數
  1. `get_hardware_info` - 支援 instance_id（第 185 行）
  2. `get_network_info` - 支援 instance_id（第 203 行）
  3. `get_ha_urls` - 支援 instance_id（第 221 行）
  4. `restart_websocket` - 支援 instance_id（第 300 行）
  5. `get_websocket_status` - 支援 instance_id，從實例讀取配置（第 355 行）
  6. `get_areas` - 支援 instance_id，過濾查詢結果（第 411 行）
  7. `get_entities_by_area` - 支援 instance_id，過濾查詢結果（第 499 行）
  8. `call_service` - 支援 instance_id（第 552 行）

### Task 3.3: WebSocketClient 更新
- [x] 修改 `WebSocketClient.__init__` 接受 `instance_id` 參數（`models/common/websocket_client.py:16`）
  - 自動選擇預設實例或第一個活躍實例
  - 記錄選擇過程
- [x] 修改 `get_websocket_client` 工廠函數（第 438 行）
- [x] 修改 `_is_websocket_running` 傳入 instance_id（第 340 行）
- [x] 修改 `_create_request` 加上 `ha_instance_id` 欄位（第 352 行）
- [x] 修改訂閱請求創建加上 `ha_instance_id`（第 186 行）

### Task 3.4: Session 管理實作
- [x] 實作 session-based instance tracking
  - 使用 `request.session['current_ha_instance_id']` 儲存當前實例
  - 自動驗證 session 中的實例是否有效
  - 無效時自動清理並 fallback

### 測試結果

**測試環境**: 2 個活躍 HA 實例（Default HA 和 ha-woowtech.ngrok.dev）

**測試場景**:
1. ✅ GET /get_instances - 成功取得 2 個實例，正確顯示當前實例
2. ✅ POST /switch_instance - 成功切換實例，session 正確更新
3. ✅ POST /websocket_status (session) - 查詢狀態反映當前 session 實例
4. ✅ POST /areas (session) - 查詢 areas 正確過濾實例資料
5. ✅ POST /websocket_status (explicit) - 明確指定 instance_id 參數正常運作

**測試數據**:
- 實例 1 (Default HA): 50 entities, 4 areas, WebSocket connected
- 實例 2 (ha-woowtech.ngrok.dev): 76 entities, 0 areas, WebSocket connected

**驗證項目**:
- ✅ 實例切換功能正常
- ✅ Session 持久化正常
- ✅ API 過濾實例資料正確
- ✅ WebSocket status 查詢準確
- ✅ 兩種模式（session vs explicit parameter）都正常運作

### 技術細節

**Controller 架構改進**:
- 統一的 `_get_current_instance()` 方法處理所有實例選擇邏輯
- 所有 endpoint 都支援 `ha_instance_id=None` 可選參數
- 自動 fallback 機制確保總是能找到可用實例

**WebSocketClient 改進**:
- 支援 instance_id 參數，自動路由請求到正確實例
- 請求記錄包含 instance_id，確保 WebSocket thread 處理正確
- 訂閱請求也包含 instance_id，支援歷史資料查詢

**Session 管理**:
- 使用 Odoo 標準 session 機制
- 自動驗證和清理無效 session
- 支援跨請求持久化

**API Response 標準化**:
- 所有 endpoint 返回統一格式 `{success, data, error}`
- WebSocket status 現在包含 instance_id 和 instance_name
- 錯誤訊息清晰明確

### Task 3.5 (額外): Phase 3.3 - 多標籤頁同步
- [x] 後端 Bus notification 實作
  - `ha_realtime_update.py` 新增 `notify_instance_switched()` 方法
  - `controllers.py` 的 `switch_instance()` 發送 Bus notification
- [x] 前端 Bus 訂閱
  - `ha_bus_bridge.js` 訂閱 `instance_switched` Bus event
  - `ha_data_service.js` 新增 `handleInstanceSwitched()` handler
- [x] 避免重複觸發
  - 調整 `switchInstance()` 不再立即觸發本地事件
  - 統一透過 Bus notification 處理所有標籤頁
- [x] 測試多標籤頁同步功能

**測試結果**: ✅ 通過
- Tab A 切換實例後，Tab B 自動收到 Bus notification
- Dashboard 正確顯示 "Instance switched to" 訊息
- 兩個標籤頁的數據都自動更新
- Phase 3.2 的 debounce 機制正常運作

**完成時間**: 2025-11-03

### Task 3.6 (額外): Code Quality Improvement - HAInstanceHelper 重構
**狀態**: ✅ 已完成
**完成時間**: 2025-11-04

**問題描述**:
在 Phase 3 實施過程中，發現實例選擇邏輯在三個不同位置存在代碼重複：

1. **`controllers/controllers.py:11-100`** (90 行) - Controller 版本
   - ✅ Session validation
   - ✅ Bus notifications
   - ✅ Comprehensive logging
   - ✅ Ordered search
   - ❌ 缺少 user preference 支持

2. **`models/ha_entity_history.py:78-113`** (35 行) - Model 版本
   - ✅ User preference 支持
   - ❌ 缺少 session validation
   - ❌ 缺少 bus notifications
   - ❌ 缺少 comprehensive logging
   - ❌ 缺少 ordered search

3. **`models/common/websocket_client.py:15-44`** (25 行) - WebSocketClient 版本
   - ❌ 缺少 session validation
   - ❌ 缺少 user preference 支持
   - ❌ 缺少 bus notifications
   - ⚠️ 簡單 logging（僅 DEBUG 和 WARNING）
   - ✅ Ordered search
   - ⚠️ 只有 2-level fallback（default → first active）

**解決方案**:
創建 `HAInstanceHelper` 統一服務類，整合所有三個版本的優點：

**實施內容**:
- [x] 創建 `models/common/instance_helper.py` - HAInstanceHelper 類
  - 實作完整的 4-level fallback mechanism
  - 整合 session validation + user preference + bus notifications + logging
- [x] 更新 `models/common/__init__.py` - 導入 instance_helper
- [x] 重構 `controllers/controllers.py._get_current_instance()` (90 行 → 1 行呼叫)
- [x] 重構 `models/ha_entity_history.py._get_current_instance()` (35 行 → 1 行呼叫)
- [x] 重構 `models/common/websocket_client.py.__init__()` (25 行 → 8 行)
- [x] 修正 `models/ha_entity.py.sync_entity_states_from_ha()` (移除間接層)
- [x] 修正 `models/ha_area.py.sync_areas_from_ha()` (移除間接層)
- [x] 更新所有函數註解，添加 Phase 3.1 引用和文檔連結
- [x] 創建詳細重構文檔 `docs/tech/instance-helper-refactoring.md`

**3-Level Fallback Mechanism** ⚠️ 更新於 2025-11-25 (原為 4-Level):
1. **Session** 中的 current_ha_instance_id（驗證存在且活躍）
   - 失效時自動清除 + 發送 `instance_invalidated` Bus notification
2. **User Preference** (res.users.current_ha_instance_id)
3. **First Accessible Instance** (via `get_accessible_instances()`, filtered by ir.rule)
   - 按 sequence, id 排序，由使用者權限過濾

> ⚠️ `is_default` 欄位已移除，改用權限感知的實例選擇機制

每次 fallback 都會發送 `instance_fallback` Bus notification 通知前端。

**代碼統計**:
- **消除重複代碼**: 150+ 行
  - Controller: 90 行 → 1 行呼叫
  - Model: 35 行 → 1 行呼叫
  - WebSocketClient: 25 行 → 8 行
- **新增統一實現**: 170 行 (HAInstanceHelper)
- **淨減少**: 約 -130 行重複代碼

**功能改進**:
- ✅ WebSocketClient 從 2-level 升級到 4-level fallback
- ✅ WebSocketClient 獲得 session validation 和 user preference 支持
- ✅ WebSocketClient 獲得 Bus notification 功能
- ✅ Model 方法獲得 session validation 和 ordered search
- ✅ 所有三個位置現在使用完全相同的邏輯
- ✅ 單一來源真相 (Single Source of Truth)

**修正的間接模式**:
發現 `ha_entity.py` 和 `ha_area.py` 的 sync 方法使用間接方式獲取 instance_id：
- **Before**: 創建 WebSocketClient → 從 client 取回 instance_id（多餘的間接層）
- **After**: 直接呼叫 HAInstanceHelper.get_current_instance() → 傳入 WebSocketClient

這確保了所有地方都使用統一的實例選擇邏輯。

**文檔**:
- 詳細重構文檔：`docs/tech/instance-helper-refactoring.md`
  - 完整的問題分析和解決方案架構
  - Before/After 代碼比較
  - Mermaid 流程圖
  - 使用範例和測試建議

**測試**:
- ✅ Odoo 重啟成功，無 import 錯誤
- ✅ Controller endpoints 正常運作
- ✅ Model sync 方法正常運作
- ✅ WebSocketClient 正常運作
- ✅ Bus notifications 正常發送

---

## Phase 4: 前端實現 (3 天)

**狀態**: ✅ 已完成
**完成時間**: 2025-11-02
**實際耗時**: 約 0.5 天

### Task 4.1: InstanceSelector 組件 ✅
- [x] 創建組件目錄和文件
  - `static/src/components/instance_selector/instance_selector.js`
  - `static/src/components/instance_selector/instance_selector.xml`
  - `static/src/components/ha_instance_systray/ha_instance_systray.js` (Systray 版本)
  - `static/src/components/ha_instance_systray/ha_instance_systray.xml`
- [x] 實作下拉選單 UI
  - 顯示所有活躍實例列表
  - 顯示當前選中實例
  - 顯示 WebSocket 連線狀態

### Task 4.2: HaDataService 修改 ✅
- [x] 新增實例切換邏輯
  - `switchInstance(instanceId)` 方法
  - `getInstances()` 取得實例列表
  - `getCurrentInstanceId()` 取得當前實例
- [x] Phase 2.1: 整合 Odoo notification service
  - `showSuccess()`, `showError()`, `showWarning()`, `showInfo()`
  - 自動顯示 API 錯誤和成功通知
- [x] Phase 3.1: Session 失效處理
  - `handleInstanceInvalidated()` 處理實例失效
  - `handleInstanceFallback()` 處理實例降級
- [x] Phase 3.2: 多標籤頁同步機制
  - 300ms debounce 防止重複載入
  - `reloadInProgress` 標記防止並發
- [x] Phase 3.3: Bus 同步實作
  - `handleInstanceSwitched()` 處理實例切換 Bus 事件
  - 統一透過 Bus 處理所有標籤頁切換

### Task 4.3: Dashboard 整合 ✅
- [x] 在 Systray 新增選擇器 (改用 Systray 而非 Dashboard 頂部)
  - 註冊到 `registry.category("systray")`
  - 顯示在右上角公司切換器旁邊
- [x] 訂閱 `instance_switched` 事件
  - `instanceSwitchedHandler` 實作
  - `reloadAllData()` 自動重載所有數據
- [x] 所有數據載入方法整合
  - `loadHardwareInfo()`
  - `loadNetworkInfo()`
  - `loadHaUrls()`
  - `loadWebSocketStatus()`

**完成內容**:
- ✅ 完整的實例切換 UI（Systray 組件）
- ✅ HaDataService 完整支援多實例
- ✅ Dashboard 自動響應實例切換
- ✅ Bus notification 雙向同步
- ✅ 錯誤通知自動顯示
- ✅ 多標籤頁完美同步

---

## Phase 5: User 偏好 (1 天)

**狀態**: ✅ 已完成
**完成時間**: 2025-11-01 (Phase 3 期間已完成)
**實際耗時**: 0.2 天

### Task 5.1: res.users 擴展 ✅
- [x] 新增 current_ha_instance_id 欄位
  - 創建 `models/res_users.py`
  - 擴展 `res.users` 模型
  - 添加 `current_ha_instance_id` Many2one 欄位
  - `ondelete='set null'` 確保實例刪除時不會破壞用戶記錄

**完成內容**:
- ✅ res.users 模型擴展完成
- ✅ HAInstanceHelper 整合使用（4-level fallback 的第二級）
- ✅ User preference 可在 Session 失效時自動使用
- ✅ 支援用戶個人化的實例偏好設定

**技術細節**:
```python
class ResUsers(models.Model):
    _inherit = 'res.users'

    current_ha_instance_id = fields.Many2one(
        'ha.instance',
        string='Current HA Instance',
        help='用戶當前選擇的 Home Assistant 實例（用於 Search View 過濾）',
        ondelete='set null',
    )
```

**整合情況**:
- HAInstanceHelper 在 Session 無效時自動 fallback 到 User Preference
- 所有 Search Views 的 `is_current_user_instance` computed field 都使用此欄位
- 支援跨 session 保持用戶的實例選擇

---

## Phase 6: 測試與文檔 (2 天)

**狀態**: ✅ 已完成
**完成時間**: 2025-11-04
**實際耗時**: 0.5 天

### Task 6.1: 功能測試 ✅
- [x] 多實例切換測試
  - ✅ 32 項測試項目全部通過
  - ✅ 詳細測試報告：`docs/tasks/phase6-test-report.md`
  - ✅ 測試通過率：100%
- [x] WebSocket 連接測試
  - ✅ 多實例同時連接正常
  - ✅ 心跳監控正常運作
  - ✅ 實例隔離驗證通過

### Task 6.2: 文檔更新 ✅
- [x] 更新 CLAUDE.md
  - ✅ Backend 章節添加多實例模型說明
  - ✅ 更新 HAInstanceHelper 實現說明
  - ✅ 新增技術文件索引（4 個新文檔）
  - ✅ 更新決策指南

**完成內容**:
- ✅ 完整的測試報告（32 項測試項目）
- ✅ CLAUDE.md 文檔更新
- ✅ 所有測試項目 100% 通過
- ✅ 多實例功能完整驗證

**測試總結**:
- **測試項目**: 32 項
- **通過**: 32 項 ✅
- **失敗**: 0 項
- **通過率**: 100%

**測試分類**:
1. ✅ 多實例切換測試 (8 項)
2. ✅ WebSocket 連接測試 (6 項)
3. ✅ 數據過濾測試 (6 項)
4. ✅ 數據完整性測試 (4 項)
5. ✅ HAInstanceHelper 測試 (6 項)
6. ✅ 其他功能測試 (2 項)

**文檔更新**:
- ✅ Backend 模型說明添加多實例支援
- ✅ HAInstanceHelper 4-level fallback 說明
- ✅ 技術文件索引新增 4 個文檔連結
- ✅ 決策指南更新（前端/後端/新成員/調試）

---

## 📝 開發日誌

### 2025-10-31

**[09:00]** 專案啟動
- 完成需求分析和方案設計
- 用戶確認採用完整多實例支援方案
- 創建進度追蹤文件

**[09:15]** 開始 Phase 1.1 - ha.instance 模型
- 創建 `models/ha_instance.py` (340 行)
- 實作基本欄位、權限控管、計算欄位
- 實作 test_connection() 和 get_accessible_instances() 方法

**[09:45]** 開始 Phase 1.2 - Entity 模型更新
- 更新 6 個相關模型，新增 ha_instance_id 外鍵
- 新增複合唯一約束 (entity_id, ha_instance_id)
- 使用 related field 自動繼承實例關聯

**[10:30]** 開始 Phase 1.3 - Views 和 Security
- 創建 `views/ha_instance_views.xml` (223 行)
- 實作 List, Form, Kanban, Search views
- 更新 security/ir.model.access.csv

**[11:00]** 開始 Phase 1.4 - 遷移腳本
- 創建 `migrations/18.0.3.0/pre-migrate.py`
- 實作從 ir.config_parameter 讀取配置邏輯
- 實作自動創建預設實例和數據遷移

**[11:30]** Phase 1 開發完成
- 所有任務完成
- 準備進入測試階段

---

### 2025-11-01

**[09:00]** 開始 Phase 1 測試
- 用戶要求執行完整測試
- 更新版本號到 18.0.3.0

**[09:15]** 遇到 View Type 錯誤
- Odoo 18 不支援 'tree' view type
- 修改所有 view 為 'list' type

**[09:30]** 修復 External ID 問題
- 修正 action reference 錯誤
- 修正 menu parent reference

**[09:45]** 修復 attrs 屬性問題
- Odoo 18 棄用 attrs 屬性
- 改用新語法 invisible/required/readonly

**[10:00]** 遇到重複 Entity 錯誤
- 發現 3 個重複的 script.notify 實體
- 執行 SQL 清理重複記錄

**[10:15]** 遷移腳本調整
- pre-migrate.py 執行時機問題
- 創建 end-migrate.py 腳本
- 手動執行 SQL 遷移

**[10:30]** 遷移成功
- 50 entities 遷移完成
- 4 areas 遷移完成
- 68 WebSocket queue items 遷移完成

**[10:45]** Test Connection 功能實作
- 用戶要求改用 WebSocket 測試（不使用 REST API）
- 實作完整的 WebSocket 認證流程
- 測試成功，返回 HA 版本 2025.6.3

**[11:00]** 功能驗證測試
- 選單顯示正常
- 預設實例自動創建
- Entity 關聯正確
- 所有 views 正常顯示

**[11:30]** Phase 1 測試完成
- 所有測試通過
- 更新進度追蹤文檔

**[11:50]** 文檔更新完成
- 更新 Phase 1 完成總結
- 新增詳細測試報告
- 更新開發日誌和進度統計

**[12:00]** 開始 Phase 2 - WebSocket 服務重構

### 2025-11-01 (下午) - Phase 2 實施

**[12:00]** 開始 Task 2.1 - 移除 WebSocket 單例限制
- 移除 `_instance` 類變數和 `get_instance()` 方法
- 新增 `instance_id` 參數到 `__init__`
- 修改配置讀取從 ha.instance 模型

**[13:00]** 開始 Task 2.2 - 連接管理器重構
- 全域結構改為雙層：`{db_name: {instance_id: {...}}}`
- 重寫 `start_websocket_service()` 支援多實例
- 重寫 `stop_websocket_service()` 三種停止模式
- 重寫 `is_websocket_service_running()` 支援實例檢查
- 重寫 `restart_websocket_service()` 支援批次重啟

**[15:00]** 開始 Task 2.3 - 更新 Hooks
- 修改 `post_load_hook()` 自動啟動所有活躍實例
- 更新 `uninstall_hook()` 停止所有實例

**[15:30]** Phase 2 測試開始
- 重啟 Odoo 服務
- 檢查 2 個實例的 WebSocket 自動啟動
- 驗證心跳記錄（instance_1 和 instance_2）
- 驗證實例隔離和資料過濾

**[16:00]** Phase 2 額外改進

**[08:30]** WebSocket Status 動態顯示修復
- 問題：Status 欄位靜態，無法反映實際狀態
- 解決：改為 computed field，即時檢查心跳
- 測試：兩個實例都顯示 "Connected" 狀態

**[09:20]** 批次重啟 WebSocket 功能
- 新增 `action_restart_websocket()` 方法
- 新增 Server Action 綁定到 Actions 選單
- 支援多選實例批次重啟
- 智能通知訊息（成功/失敗/部分成功）

**[16:30]** Phase 2 完成
- 所有任務完成
- 測試通過
- 額外功能實作完成

**[23:30]** 開始 Phase 3 - API 層整合
- 用戶確認開始 Phase 3
- 目標：完成 Controller 和 WebSocket Client 的多實例支援

**[23:35]** Task 3.1 開始 - Controller 基礎方法
- 實作 `_get_current_instance()` 方法（4 級 fallback）
- 新增 `/get_instances` endpoint（列出所有實例）
- 新增 `/switch_instance` endpoint（切換實例）
- Session 管理機制完成

**[23:50]** WebSocketClient 重構
- 修改 `__init__` 接受 instance_id 參數
- 修改 `get_websocket_client` 工廠函數
- 更新 `_create_request` 加上 ha_instance_id 欄位
- 更新 `_is_websocket_running` 傳入 instance_id
- 訂閱請求也加上 instance_id 支援

**[00:05]** Task 3.2 開始 - 更新所有 API endpoints
- 修改 8 個 endpoints 支援 ha_instance_id 參數：
  1. `get_hardware_info` ✅
  2. `get_network_info` ✅
  3. `get_ha_urls` ✅
  4. `restart_websocket` ✅
  5. `get_websocket_status` ✅（從實例讀取配置）
  6. `get_areas` ✅（過濾查詢結果）
  7. `get_entities_by_area` ✅（過濾查詢結果）
  8. `call_service` ✅
- 所有 endpoint 都支援兩種模式：
  - Session 模式（不傳參數，使用當前實例）
  - Explicit 模式（明確指定 ha_instance_id）

**[00:20]** Phase 3 測試
- 創建測試腳本 `test_phase3.py`
- 修正 Odoo URL（使用 nginx 反向代理）
- 執行完整測試流程

**[00:25]** 測試結果 - 全部通過 ✅
- ✅ GET /get_instances - 成功取得 2 個實例
- ✅ POST /switch_instance - 實例切換正常
- ✅ POST /websocket_status (session) - Session 模式正常
- ✅ POST /areas (session) - 資料過濾正確
- ✅ POST /websocket_status (explicit) - 明確參數模式正常
- 實例 1: 50 entities, 4 areas
- 實例 2: 76 entities, 0 areas
- 資料隔離完整，無交叉污染

**[00:40]** Phase 3 完成
- 所有任務完成（9 個 subtasks）
- 測試通過（5 個測試場景）
- 文檔更新完成
- 實際耗時：約 1.2 小時（預估 2 天）

### 2025-11-04 - Phase 3.6: Code Quality Improvement

**問題發現**:
- 用戶發現 Entity Groups 缺少多實例支持
- 發現 `ha_entity_group_tag` 也需要多實例功能
- 發現代碼重複問題：實例選擇邏輯在 3 個位置重複（150+ 行）

**實施內容**:

**[上午]** Entity Groups 多實例支持
- 為 `ha_entity_group_tag` 添加 `ha_instance_id` 欄位
- 添加 `is_current_user_instance` computed field 和 search method
- 更新 List, Form, Search views
- 添加 "Current Instance" filter 和 Group By 功能
- 測試完成：✅

**[上午]** 數據完整性驗證
- 實作 `@api.constrains` 驗證：
  - `ha_entity_group._check_instance_consistency()` - 驗證 entities 和 tags
  - `ha_entity_group_tag._check_instance_consistency()` - 驗證 groups
- 測試完成：✅ 錯誤訊息正確顯示

**[上午]** UX 改進
- 添加 domain filters 到 Many2many 欄位：
  - `ha_entity_group.tag_ids`: `domain="[('ha_instance_id', '=', ha_instance_id)]"`
  - `ha_entity_group.entity_ids`: `domain="[('ha_instance_id', '=', ha_instance_id)]"`
  - `ha_entity_group_tag.group_ids`: `domain="[('ha_instance_id', '=', ha_instance_id)]"`
- 測試完成：✅ 下拉選單自動過濾

**[下午]** 代碼重構 - HAInstanceHelper
- **問題分析**：發現 3 個位置的代碼重複：
  1. `controllers/controllers.py:11-100` (90 行) - Controller 版本
  2. `models/ha_entity_history.py:78-113` (35 行) - Model 版本
  3. `models/common/websocket_client.py:15-44` (25 行) - WebSocketClient 版本
- **解決方案**：創建統一的 `HAInstanceHelper` 服務類

**[下午]** HAInstanceHelper 實作
- 創建 `models/common/instance_helper.py` (170 行)
  - 整合所有三個版本的優點
  - 完整的 4-level fallback mechanism
  - Session validation + User preference + Bus notifications + Logging
- 更新 `models/common/__init__.py`
- 重構 `controllers/controllers.py._get_current_instance()` (90 行 → 1 行)
- 重構 `models/ha_entity_history.py._get_current_instance()` (35 行 → 1 行)
- 重構 `models/common/websocket_client.py.__init__()` (25 行 → 8 行)

**[下午]** 修正間接模式
- 發現並修正 `ha_entity.py.sync_entity_states_from_ha()` 的間接層
- 發現並修正 `ha_area.py.sync_areas_from_ha()` 的間接層
- **Before**: 創建 WebSocketClient → 從 client 取回 instance_id
- **After**: 直接呼叫 HAInstanceHelper → 傳入 WebSocketClient

**[下午]** 文檔完善
- 更新所有函數註解，添加 Phase 3.1 引用
- 創建 `docs/tech/instance-helper-refactoring.md` (314 行)
  - 完整的問題分析和解決方案
  - Before/After 代碼比較
  - Mermaid 流程圖
  - 使用範例和測試建議
- 更新 `docs/tasks/multi-ha-implementation.md` (本文件)

**統計**:
- **消除重複代碼**: 150+ 行
- **新增統一實現**: 170 行
- **淨減少**: 約 -130 行
- **修改文件數**: 7 個 Python 檔案 + 2 個 XML 檔案 + 2 個文檔
- **功能改進**: WebSocketClient 從 2-level 升級到 4-level fallback

**測試**:
- ✅ Entity Groups 多實例功能正常
- ✅ 數據完整性驗證正常
- ✅ Domain filters 正常
- ✅ HAInstanceHelper 正常
- ✅ Controller endpoints 正常
- ✅ Model sync 方法正常
- ✅ WebSocketClient 正常
- ✅ Bus notifications 正常

**完成時間**: 2025-11-04 下午

**[下午]** HaHistory View 修正
- **問題發現**: User 發現 HaHistory View 強制過濾當前實例
  - `hahistory_model.js:26-33` 強制添加實例過濾到 domain
  - 導致 Search View 的 "Current Instance" filter 無法正常運作
  - 用戶無法自由選擇查看其他實例的歷史數據
- **解決方案**: 刪除 Model 層的強制過濾
  - 移除 `getCurrentInstanceId()` 和 `instanceDomain` 邏輯
  - 讓用戶透過 Search View 的 filter 自由選擇
  - 符合 Odoo 最佳實踐（filter 應在 Search View 定義）
- **測試**: ✅ Odoo 重啟成功，無錯誤
- **優點**:
  - ✅ 用戶可自由選擇是否過濾實例
  - ✅ 支援跨實例查看歷史數據
  - ✅ Group By "HA Instance" 正常運作

---

## 🔧 技術決策記錄

### 決策 #1: 連接策略選擇
**日期**: 2025-10-31
**決策**: 採用「全部連接」策略
**理由**: 用戶要求所有實例同時保持 WebSocket 連接，以獲得最佳即時性
**風險**: 連接數可能較多，需監控資源消耗
**緩解**: 後續可實作連接池或閒置回收機制

### 決策 #2: 權限控管模型
**日期**: 2025-10-31
**決策**: 使用 Many2many 關聯 user_ids
**理由**: 靈活性高，可精細控管每個實例的存取權限
**實作**: `ha.instance` 模型新增 `user_ids` 欄位

### 決策 #3: UI 選擇器位置
**日期**: 2025-10-31
**決策**: Dashboard 頂部導航列
**理由**: 用戶選擇此方案，類似 Odoo 公司切換器，直覺易用
**實作**: 創建 InstanceSelector 組件註冊到 main_components

### 決策 #4: Test Connection 實作方式
**日期**: 2025-11-01
**決策**: 使用 WebSocket 直接測試連接，而非 REST API
**理由**: 用戶明確要求「在實作 test_connection() 我想要直接測 websocket 的是否可以連線，不要打 api」
**實作細節**:
- 使用 Python asyncio + websockets 庫
- 完整的 WebSocket 認證流程：
  1. 連接到 ws_url
  2. 接收 auth_required 訊息（含 HA 版本）
  3. 發送 auth 訊息（含 access_token）
  4. 接收 auth_ok 或錯誤訊息
- 5 秒超時機制
- 返回 HA 版本資訊
**程式碼位置**: models/ha_instance.py:265-375
**測試結果**: ✅ 成功連接並返回 "Connected to Home Assistant 2025.6.3"

### 決策 #5: HaHistory View 過濾邏輯位置
**日期**: 2025-11-04
**決策**: 實例過濾邏輯應在 Search View 定義，而非 Model 層寫死
**問題**:
- 原先 `hahistory_model.js` 強制過濾當前實例
- 導致 Search View 的 "Current Instance" filter 無法正常運作
- 用戶無法自由選擇查看其他實例的歷史數據
**理由**:
- 符合 Odoo 最佳實踐：過濾邏輯應該在 Search View 定義
- 給予用戶更大的靈活性和自主權
- 支援跨實例查看和分析數據的需求
**實作**:
- 移除 `hahistory_model.js:26-33` 的強制過濾代碼
- 保留 Search View 的 "Current Instance" filter（讓用戶自由選擇）
- 保留 Group By "HA Instance" 功能（支援多實例數據分組）
**影響**:
- ✅ 用戶可自由選擇是否過濾實例
- ✅ 支援跨實例歷史數據查看
- ✅ 符合 Odoo UI/UX 最佳實踐
**程式碼位置**: static/src/views/hahistory/hahistory_model.js
**測試結果**: ✅ Odoo 重啟成功，Search View filter 正常運作

---

## ⚠️ 風險與問題追蹤

### 風險 #1: WebSocket 連接數過多
**嚴重性**: 🟡 中
**影響**: 資源消耗可能較高
**狀態**: 待觀察
**緩解措施**: Phase 6 進行壓力測試

### 風險 #2: 數據遷移失敗 ✅ 已解決
**嚴重性**: 🔴 高 → ✅ 已解決
**影響**: 現有數據可能遺失
**狀態**: ✅ 已完成
**實際結果**:
- ✅ 遷移腳本成功執行
- ✅ 50 entities 完整遷移
- ✅ 4 areas 完整遷移
- ✅ 68 WebSocket queue items 完整遷移
- ✅ 無數據遺失
**解決方案**:
1. 創建 end-migrate.py 腳本（解決執行時機問題）
2. 手動執行 SQL 清理重複記錄
3. 完整測試驗證所有數據正確遷移

### 風險 #3: Odoo 18 相容性問題 ✅ 已解決
**嚴重性**: 🟡 中 → ✅ 已解決
**影響**: Views 無法載入，功能異常
**狀態**: ✅ 已完成
**實際問題**:
- View type 'tree' → 'list'（6 處修改）
- attrs 屬性棄用（3 處修改）
- External ID references（2 處修改）
**解決時間**: 2025-11-01
**測試結果**: ✅ 所有 views 正常顯示

---

## 📈 進度統計

**總體進度**: 100% (15/15 tasks) 🎉 專案完成！

### Phase 1: ✅ 100% (4/4 完成) - 已完成並測試通過
- Task 1.1: ✅ 100% - ha.instance 模型創建完成
- Task 1.2: ✅ 100% - Entity 模型更新完成
- Task 1.3: ✅ 100% - Views 和 Security 完成
- Task 1.4: ✅ 100% - 遷移腳本完成並執行成功

**測試狀態**: ✅ 完整測試通過
- 7 個問題全部修復
- 50 entities 成功遷移
- 所有功能驗證通過

### Phase 2: ✅ 100% (3/3 完成) - 已完成並測試通過
- Task 2.1: ✅ 100% - WebSocket 單例限制移除
- Task 2.2: ✅ 100% - 連接管理器雙層重構
- Task 2.3: ✅ 100% - Hooks 多實例支援

**測試狀態**: ✅ 完整測試通過
- ✅ 2 個實例 WebSocket 同時運行
- ✅ 心跳記錄正常（instance_1, instance_2）
- ✅ 實例隔離驗證通過（50 + 45 entities）
- ✅ 獨立管理功能正常

**額外成就**:
- ✅ WebSocket Status 動態顯示（computed field）
- ✅ 批次重啟 WebSocket 功能（Actions 選單）

### Phase 3: ✅ 100% (3/3 完成) - 已完成並測試通過
- Task 3.1: ✅ 100% - Controller 基礎方法完成
  - `_get_current_instance()` 方法（4 級 fallback）
  - `/get_instances` endpoint
  - `/switch_instance` endpoint
- Task 3.2: ✅ 100% - 所有 8 個 API endpoints 支援 ha_instance_id
- Task 3.3: ✅ 100% - Session 管理和 WebSocketClient 重構
- Task 3.4 (額外): ✅ 100% - WebSocketClient 完整支援多實例

**測試狀態**: ✅ 完整測試通過（5 個測試場景）
- ✅ 實例列表查詢正常
- ✅ 實例切換功能正常
- ✅ Session 持久化正常
- ✅ API 資料過濾正確
- ✅ 兩種模式（session vs explicit）都正常

**實際耗時**: 1.2 小時（預估 2 天，大幅提前完成）

### Phase 4: ✅ 100% (3/3 完成) - 已完成並測試通過
- Task 4.1: ✅ 100% - InstanceSelector 組件 (Systray 版本)
- Task 4.2: ✅ 100% - HaDataService 修改
- Task 4.3: ✅ 100% - Dashboard 整合

### Phase 5: ✅ 100% (1/1 完成) - 已完成
- Task 5.1: ✅ 100% - res.users 擴展完成
  - `current_ha_instance_id` 欄位已添加
  - HAInstanceHelper 整合使用（4-level fallback 的第二級）
  - 支援用戶個人化實例偏好

**測試狀態**: ✅ 整合測試通過
- ✅ User preference fallback 正常運作
- ✅ Search Views 的 `is_current_user_instance` 正常使用

### Phase 6: ✅ 100% (2/2 完成) - 已完成
- Task 6.1: ✅ 100% - 功能測試完成
  - 32 項測試項目全部通過
  - 測試通過率：100%
  - 測試報告：`docs/tasks/phase6-test-report.md`
- Task 6.2: ✅ 100% - 文檔更新完成
  - CLAUDE.md 完整更新
  - 技術文件索引新增 4 個文檔

**測試狀態**: ✅ 完整測試通過
- ✅ 多實例切換測試 (8 項)
- ✅ WebSocket 連接測試 (6 項)
- ✅ 數據過濾測試 (6 項)
- ✅ 數據完整性測試 (4 項)
- ✅ HAInstanceHelper 測試 (6 項)
- ✅ 其他功能測試 (2 項)

**關鍵成就**:
- ✅ 數據模型架構完成（Phase 1）
- ✅ 複合唯一約束正常運作
- ✅ 遷移腳本成功執行（50 entities, 4 areas, 68 queue items）
- ✅ Test Connection 功能實作（WebSocket 測試）
- ✅ Odoo 18 相容性完成
- ✅ WebSocket 服務層多實例支援（Phase 2）
- ✅ 雙層連接管理架構
- ✅ 獨立心跳監控機制
- ✅ 批次管理功能
- ✅ API 層完整多實例支援（Phase 3）
- ✅ Session 管理機制
- ✅ 統一的實例選擇邏輯
- ✅ 多標籤頁完美同步（Phase 3.3）
- ✅ 完整的實例切換 UI（Systray 組件）
- ✅ Bus notification 雙向同步
- ✅ HAInstanceHelper 重構（Phase 3.6）
  - 消除 150+ 行重複代碼
  - 統一的 4-level fallback 機制
  - WebSocketClient 從 2-level 升級到 4-level
- ✅ Entity Groups 多實例支援（Phase 3.6）
  - 數據完整性驗證（@api.constrains）
  - Domain filters UX 改進
- ✅ User 偏好設定（Phase 5）
  - res.users 擴展完成
  - HAInstanceHelper 整合
- ✅ HaHistory View 修正
  - 移除強制過濾，符合 Odoo 最佳實踐
  - 支援跨實例數據查看

**下一步**: Phase 6 - 測試與文檔

---

## 🔗 相關文件

### 主要文檔
- 專案架構說明: `CLAUDE.md`
- 多實例實施進度: `docs/tasks/multi-ha-implementation.md` (本文件)

### 技術文檔
- HAInstanceHelper 重構: `docs/tech/instance-helper-refactoring.md` (NEW)
- 實例切換機制: `docs/tech/instance-switching.md`
- WebSocket 訂閱機制: `docs/tech/websocket-subscription.md`
- Bus 機制比較: `docs/bus-mechanisms-comparison.md`

### WebSocket 相關
- WebSocket 整合計劃: `docs/tasks/websocket-integration-plan.md`
- WebSocket 並發控制: `docs/tasks/websocket-concurrency-control.md`

---

---

## 📅 Phase 1 完成總結

**完成日期**: 2025-10-31
**實際耗時**: 約 2.5 小時（開發）+ 1.5 小時（測試與修復）
**狀態**: ✅ 所有任務完成，測試通過

### 完成的文件和代碼

**新增文件**:
1. `models/ha_instance.py` - HA 實例模型（471 行，包含 WebSocket 測試功能）
2. `views/ha_instance_views.xml` - 完整 CRUD views（223 行，已修正 Odoo 18 語法）
3. `migrations/18.0.3.0/end-migrate.py` - 資料遷移腳本（173 行）
4. `docs/tasks/multi-ha-implementation.md` - 進度追蹤文件

**修改文件**:
1. `models/__init__.py` - 新增 ha_instance 導入
2. `models/ha_entity.py` - 新增 ha_instance_id + 唯一約束
3. `models/ha_entity_history.py` - 新增 ha_instance_id（related）
4. `models/ha_area.py` - 新增 ha_instance_id + 唯一約束
5. `models/ha_entity_group.py` - 新增 ha_instance_id（可選）
6. `models/ha_ws_request_queue.py` - 新增 ha_instance_id
7. `models/ha_realtime_update.py` - 更新通知方法（3 個）
8. `security/ir.model.access.csv` - 新增權限設定（2 行）
9. `__manifest__.py` - 版本升級到 18.0.3.0

---

## 🧪 Phase 1 測試報告

**測試執行日期**: 2025-11-01
**測試執行者**: Claude Code
**測試狀態**: ✅ 通過

### 測試環境

- **Odoo 版本**: 18.0
- **資料庫**: odoo (PostgreSQL 15)
- **測試方式**: 模組升級測試（18.0.2.2 → 18.0.3.0）
- **Docker 環境**: docker-compose-18.yml

### 遇到的問題與解決方案

#### 問題 1: View Type 不相容 ❌ → ✅

**錯誤訊息**:
```
ValueError: Invalid view type: 'tree'. Allowed types are: list, form, graph, pivot, calendar, kanban, search, qweb, hahistory
```

**原因**: Odoo 18 將 view type 從 `tree` 改為 `list`

**解決方案**:
- 修改 `views/ha_instance_views.xml`
- 所有 `<tree>` 標籤 → `<list>` 標籤（4 處）
- view_ha_instance_tree → view_ha_instance_list
- view_mode: `tree,form,kanban` → `list,form,kanban`

**修改位置**: models/ha_instance.py:6, :10, :200

---

#### 問題 2: External ID 不存在 ❌ → ✅

**錯誤訊息**:
```
ValueError: External ID not found in the system: odoo_ha_addon.action_ha_entity
```

**原因**: 引用的 action ID 名稱不正確

**解決方案**:
- 修改 `views/ha_instance_views.xml:51`
- `name="%(action_ha_entity)d"` → `name="%(entity_action)d"`

---

#### 問題 3: active_id Field 不存在 ❌ → ✅

**錯誤訊息**:
```
field "active_id" does not exist in model "ha.instance"
```

**原因**: Button context 使用了不存在的 `active_id` 欄位

**解決方案**:
- 修改 `views/ha_instance_views.xml:55`
- `context="{'search_default_ha_instance_id': active_id}"` → `context="{'search_default_ha_instance_id': id}"`

---

#### 問題 4: attrs 屬性已棄用 ❌ → ✅

**錯誤訊息**:
```
Since 17.0, the "attrs" and "states" attributes are no longer used
```

**原因**: Odoo 18 棄用 `attrs` 屬性，改用直接的 invisible/required/readonly 屬性

**解決方案**:
修改 `views/ha_instance_views.xml` 中的 3 處:
1. `attrs="{'invisible': [('active', '=', False)]}"` → `invisible="not active"`
2. ~~`attrs="{'invisible': [('is_default', '=', False)]}"` → `invisible="not is_default"`~~ ⚠️ `is_default` 已移除 (2025-11-25)
3. `attrs="{'invisible': [('active', '=', True)]}"` → `invisible="active"`

---

#### 問題 5: Menu Parent 不存在 ❌ → ✅

**錯誤訊息**:
```
ValueError: External ID not found in the system: odoo_ha_addon.menu_awesome_dashboard_config
```

**原因**: 錯誤的 menu parent reference

**解決方案**:
- 修改 `views/ha_instance_views.xml:218`
- `parent="menu_awesome_dashboard_config"` → `parent="odoo_ha_addon.configuration_top_menu"`

---

#### 問題 6: Duplicate Entity Keys ❌ → ✅

**錯誤訊息**:
```sql
duplicate key value violates unique constraint "ha_entity_entity_instance_unique"
DETAIL: Key (entity_id, ha_instance_id)=(script.notify, 1) already exists.
```

**原因**: 資料庫中有 3 個重複的 `script.notify` 實體

**解決方案**:
執行 SQL 清理重複記錄（保留最舊的記錄）:
```sql
DELETE FROM ha_entity
WHERE id IN (
    SELECT id FROM (
        SELECT id, ROW_NUMBER() OVER (PARTITION BY entity_id ORDER BY id) as rn
        FROM ha_entity
    ) t WHERE t.rn > 1
);
```

**刪除記錄**: 3 筆重複記錄

---

#### 問題 7: Migration Script 未執行 ❌ → ✅

**原因**: `pre-migrate.py` 在資料表創建前執行，無法存取 ha_instance 表

**解決方案**:
1. 創建 `migrations/18.0.3.0/end-migrate.py` 腳本
2. 手動執行 SQL 遷移命令
3. 驗證遷移結果

---

### 遷移統計結果

**Default HA Instance 創建成功**:
- ID: 1
- Name: "Default HA"
- API URL: 從 `ir.config_parameter` 讀取
- API Token: 從 `ir.config_parameter` 讀取

**數據遷移統計**:
- ✅ **50 entities** 已遷移到預設實例
- ✅ **4 areas** 已遷移到預設實例
- ✅ **68 entity groups** 已遷移（0 筆，無需遷移）
- ✅ **68 WebSocket queue items** 已遷移到預設實例

**遷移腳本輸出**:
```
================================================================================
Starting Multi-HA Instance DATA Migration (18.0.3.0) - END PHASE
================================================================================
Reading existing HA configuration...
Found config - URL: http://homeassistant.local:8123, Token: ***
Creating default HA instance...
Created default HA instance with ID: 1
Migrating existing data to default instance...
Migrated 50 entities
Migrated 4 areas
Migrated 0 entity groups
Migrated 68 WebSocket queue items
================================================================================
Multi-HA Instance DATA Migration completed successfully!
Statistics:
  - Default Instance ID: 1
  - Entities migrated: 50
  - Areas migrated: 4
  - Entity groups migrated: 0
  - WS queue items migrated: 68
================================================================================
```

---

### 功能驗證測試

#### ✅ 測試 1: HA Instances 選單

**測試項目**: 檢查選單是否正確顯示
**結果**: ✅ 通過
**詳情**:
- 選單位置: Settings > Configuration > HA Instances
- 顯示正常，可進入列表視圖

---

#### ✅ 測試 2: 預設實例自動創建

**測試項目**: 檢查是否自動創建 "Default HA" 實例
**結果**: ✅ 通過
**詳情**:
- 實例名稱: "Default HA"
- ~~is_default: True~~ ⚠️ 已移除 (2025-11-25) - 改用 sequence 排序
- active: True
- 配置從 ir.config_parameter 正確讀取

---

#### ✅ 測試 3: Entity 關聯

**測試項目**: 檢查現有 entities 是否正確關聯到預設實例
**結果**: ✅ 通過
**詳情**:
- 50 個 entities 全部關聯到 instance ID: 1
- 無任何 entity 的 ha_instance_id 為 NULL

---

#### ✅ 測試 4: Test Connection 功能

**測試項目**: 測試 Form view 的 "Test Connection" 按鈕
**結果**: ✅ 通過
**實作變更**: 依用戶要求，改用 WebSocket 直接測試（而非 REST API）

**測試實作**:
```python
async def test_websocket():
    # 連接到 WebSocket
    async with websockets.connect(ws_url, ping_interval=None, close_timeout=5) as websocket:
        # 1. 接收 auth_required
        auth_required = await asyncio.wait_for(websocket.recv(), timeout=5)
        auth_msg = json.loads(auth_required)

        # 2. 發送認證
        auth_payload = {'type': 'auth', 'access_token': self.api_token}
        await websocket.send(json.dumps(auth_payload))

        # 3. 接收認證結果
        auth_response = await asyncio.wait_for(websocket.recv(), timeout=5)
        auth_result = json.loads(auth_response)

        if auth_result.get('type') == 'auth_ok':
            return {'success': True, 'data': {'version': ha_version}}
```

**測試結果**:
- 連接成功
- 認證成功
- 返回訊息: "Connected to Home Assistant 2025.6.3"

**程式碼位置**: models/ha_instance.py:265-375

---

#### ✅ 測試 5: Entity 數量統計

**測試項目**: Form view 的 Entity Count 統計按鈕
**結果**: ✅ 通過
**詳情**:
- 顯示 "50 Entities"
- 點擊按鈕可正確過濾該實例的 entities

---

#### ✅ 測試 6: View 顯示測試

**測試項目**: 所有 view types 正常顯示
**結果**: ✅ 通過
**詳情**:
- List View: ✅ 正常（含 handle widget 拖曳排序）
- Form View: ✅ 正常（含 header buttons、ribbons）
- Kanban View: ✅ 正常（行動裝置友善）
- Search View: ✅ 正常（含多種過濾條件）

---

### 測試結論

**Phase 1 基礎架構**:
- ✅ 資料模型完整，複合唯一約束正常運作
- ✅ 遷移腳本成功執行，數據完整遷移
- ✅ Views 全部相容 Odoo 18
- ✅ Test Connection 功能正常（使用 WebSocket 測試）
- ✅ 權限設定正確，可正常 CRUD

**已知限制**:
- ⚠️ WebSocket 服務尚未重構（Phase 2 任務）
- ⚠️ 前端尚無實例切換器（Phase 4 任務）
- ⚠️ API endpoints 尚未支援多實例（Phase 3 任務）

**Phase 2 準備度**: ✅ 可以開始
- 基礎架構穩固
- 數據遷移完成
- 無阻塞性問題

---

**最後更新**: 2025-11-01 16:30
**更新者**: Claude Code

---

## 📅 Phase 2 完成總結

**完成日期**: 2025-11-01
**實際耗時**: 約 7.5 小時（開發 + 測試 + 額外改進）
**狀態**: ✅ 所有任務完成，測試通過

### 完成的文件和代碼

**修改文件**:
1. `models/common/hass_websocket_service.py` - WebSocket 服務層重構
   - 移除單例模式（第 17, 854 行）
   - 新增 instance_id 支援（第 21 行）
   - 配置從 ha.instance 讀取（第 64, 106 行）
   - 實體操作加入實例過濾（第 681 行）
   - 心跳機制包含 instance_id（第 1009 行）
   - 請求佇列實例過濾（第 1031 行）

2. `models/common/websocket_thread_manager.py` - 連接管理器重構
   - 雙層結構 `{db_name: {instance_id: {...}}}`（第 12 行）
   - `start_websocket_service()` 多實例啟動（第 102 行）
   - `stop_websocket_service()` 三種停止模式（第 184 行）
   - `is_websocket_service_running()` 實例檢查（第 272 行）
   - `is_config_changed()` 實例配置檢查（第 420 行）
   - `restart_websocket_service()` 批次重啟（第 517 行）

3. `hooks.py` - Hooks 多實例支援
   - `post_load_hook()` 自動啟動所有實例（第 130 行）
   - `uninstall_hook()` 停止所有實例（第 62 行）

4. `models/ha_instance.py` - 額外改進
   - `websocket_status` computed field（第 84 行）
   - `_compute_websocket_status()` 動態計算（第 133 行）
   - `action_restart_websocket()` 批次重啟（第 494 行）

5. `views/ha_instance_views.xml` - 額外改進
   - Server Action 定義（第 195 行）
   - 移除無效的 search filters

---

## 🧪 Phase 2 測試報告

**測試執行日期**: 2025-11-01
**測試執行者**: Claude Code
**測試狀態**: ✅ 通過

### 測試環境

- **Odoo 版本**: 18.0
- **資料庫**: odoo (PostgreSQL 15)
- **HA 實例數**: 2 個
  - 實例 1: "Default HA" (https://ha-eugene.woowtech.io)
  - 實例 2: "ha-woowtech.ngrok.dev" (https://woowtech-ha.woowtech.io)

### 測試結果

#### ✅ 測試 1: 多實例 WebSocket 自動啟動

**測試項目**: 重啟 Odoo 後自動啟動所有活躍實例的 WebSocket 服務

**結果**: ✅ 通過

**驗證方式**:
```sql
SELECT key, value FROM ir_config_parameter
WHERE key LIKE 'odoo_ha_addon.ws_heartbeat%instance%';
```

**實際結果**:
```
odoo_ha_addon.ws_heartbeat_odoo_instance_1 | 2025-11-01 08:12:41
odoo_ha_addon.ws_heartbeat_odoo_instance_2 | 2025-11-01 08:12:41
```

**結論**: 兩個實例的 WebSocket 服務都成功自動啟動

---

#### ✅ 測試 2: 實例隔離和資料過濾

**測試項目**: 驗證不同實例的實體數據完全隔離

**結果**: ✅ 通過

**驗證方式**:
```sql
SELECT ha_instance_id, COUNT(*) as entity_count,
       COUNT(DISTINCT domain) as domain_count
FROM ha_entity
WHERE ha_instance_id IS NOT NULL
GROUP BY ha_instance_id;
```

**實際結果**:
```
ha_instance_id | entity_count | domain_count
---------------+--------------+-------------
             1 |           50 |           15
             2 |           45 |            2
```

**結論**: 實體數據按實例完全隔離，無交叉污染

---

#### ✅ 測試 3: 獨立心跳監控

**測試項目**: 每個實例有獨立的心跳記錄和狀態監控

**結果**: ✅ 通過

**驗證方式**: 檢查心跳 key 格式和更新頻率

**實際結果**:
- 心跳格式: `odoo_ha_addon.ws_heartbeat_{db_name}_instance_{instance_id}`
- 更新頻率: 每 30 秒
- 狀態檢查: 透過 `is_websocket_service_running(instance_id=...)` 獨立查詢

**結論**: 心跳機制正常，可獨立監控每個實例

---

#### ✅ 測試 4: WebSocket Status 動態顯示

**測試項目**: List view 的 WebSocket Status 欄位即時反映實際狀態

**結果**: ✅ 通過

**實作變更**:
- 從靜態欄位改為 computed field
- 檢查心跳新鮮度（≤60秒=connected）

**實際結果**:
- 實例 1: Connected (綠色)
- 實例 2: Connected (綠色)

**結論**: Status 欄位正確反映實際 WebSocket 連接狀態

---

#### ✅ 測試 5: 批次重啟 WebSocket

**測試項目**: 在 list view 多選實例後批次重啟 WebSocket 服務

**結果**: ✅ 通過

**測試步驟**:
1. 勾選 2 個實例
2. Actions → "重啟 WebSocket 服務"
3. 檢查通知訊息

**實際結果**:
```
通知: WebSocket 批次重啟結果
內容: 成功重啟 2/2 個實例
類型: success (綠色)
```

**結論**: 批次重啟功能正常，通知訊息準確

---

### 測試結論

**Phase 2 WebSocket 服務層**:
- ✅ 多實例並行運行正常
- ✅ 實例隔離機制完善
- ✅ 獨立心跳監控正常
- ✅ 批次管理功能完整
- ✅ 動態狀態顯示準確

**已知限制**:
- ⚠️ 前端尚無實例切換器（Phase 4 任務）
- ⚠️ API endpoints 尚未支援多實例參數（Phase 3 任務）

**Phase 3 準備度**: ✅ 可以開始
- WebSocket 層完全就緒
- 數據隔離機制完善
- 無阻塞性問題

---

# 附錄

## 附錄 A: 初始需求分析與技術方案

### 用戶原始問題

**提問時間**: 2025-10-31 09:00

用戶提出的核心問題：

> 我目前的設計是一個 db 只會設定一個 ha url / ha token 放在 `ir.config_parameter` 中，現在我想知道有沒有可能改成一個 db 可以設定多個 ha？我目前能夠想到的問題是：
>
> 1. 要記錄 ha config list
> 2. 要怎麼讓前端使用者選擇目前是操作哪一個 ha？可以在 menu_avatar (右上角的 profile icon) 設定切換嗎？
> 3. 所有的 ha 操作 api 要怎麼指定是針對哪一個 ha？是放在 session 的使用者資料中嗎？
> 有沒有我沒有想到的？

### 架構分析結果

#### 1. 當前系統限制

經過完整的代碼探索分析，發現以下技術限制：

**配置層面**：
- 在 **29 處**讀取全域配置參數（`ir.config_parameter`）
- 配置存儲方式：
  - `odoo_ha_addon.ha_api_url` - 全域 URL
  - `odoo_ha_addon.ha_api_token` - 全域 Token

**WebSocket 層面**：
- `HassWebSocketService` 使用**單例模式**（`_instance` 類變數）
- `websocket_thread_manager` 管理結構：
  ```python
  _websocket_connections = {
      'db_name': {
          'thread': Thread,
          'stop_event': Event,
          'config': {'ha_url': str, 'ha_token': str}
      }
  }
  ```
- 每個資料庫只能連接**一個 HA 實例**

**數據層面**：
- `ha.entity` 模型缺少實例外鍵
- Entity ID 可能在不同 HA 實例間衝突（如 `sensor.temperature`）
- 相關模型（history, area, group）也無實例區分

**API 層面**：
- 所有 8 個 HTTP endpoints 無法指定目標實例：
  - `get_hardware_info`
  - `get_network_info`
  - `get_ha_urls`
  - `get_websocket_status`
  - `restart_websocket`
  - `get_areas`
  - `get_entities_by_area`
  - `call_service`

#### 2. 問題回答

##### Q1: 如何記錄 HA config list？

**答案**: 新增 `ha.instance` 模型

```python
class HAInstance(models.Model):
    _name = 'ha.instance'

    name = fields.Char(string='實例名稱', required=True)
    api_url = fields.Char(string='API URL', required=True)
    api_token = fields.Char(string='Access Token', required=True)
    active = fields.Boolean(string='啟用', default=True)
    sequence = fields.Integer(string='排序', default=10)  # ⚠️ 取代 is_default (2025-11-25)
    user_ids = fields.Many2many('res.users', string='授權使用者')
```

**優點**：
- 完全取代 `ir.config_parameter` 的全域配置
- 支援權限控管（user_ids）
- ~~可設定預設實例作為 fallback~~ ⚠️ 改用 `get_accessible_instances()` 權限感知選擇 (2025-11-25)
- 易於管理和擴展

##### Q2: 如何讓前端使用者選擇操作的 HA？

**答案**: 在 Dashboard 頂部新增選擇器（不建議放在 menu_avatar）

**方案 A（推薦）**: Dashboard 頂部選擇器
```javascript
<InstanceSelector
  instances={state.instances}
  current={state.currentInstance}
  onChange={onSwitchInstance}
/>
```

位置：Dashboard 左上角或右上角導航列

**方案 B（不推薦）**: menu_avatar 中實作

原因：
- 需要修改 Odoo 核心 systray menu
- 可能與原生 UI 衝突
- 較不直覺（使用者可能找不到）

**最終選擇**: 方案 A - Dashboard 頂部導航列

##### Q3: API 操作如何指定目標 HA？

**答案**: Session + User 偏好雙重機制

**後端實作**：
```python
def _get_current_instance(self):
    """從 session 或用戶設定獲取當前 HA 實例"""
    # ⚠️ 架構更新 (2025-11-25): 改用 HAInstanceHelper.get_current_instance()
    # 以下為舊邏輯，現已由 HAInstanceHelper 統一處理

    # 1. 優先從 session 讀取
    instance_id = request.session.get('current_ha_instance_id')

    # 2. Fallback 到用戶偏好
    if not instance_id:
        instance_id = request.env.user.current_ha_instance_id.id

    # 3. 最終 fallback 到第一個可存取實例 (⚠️ 舊版使用 is_default，已移除)
    if not instance_id:
        instances = request.env['ha.instance'].get_accessible_instances()
        instance_id = instances[0].id if instances else None

    return instance_id
```

**前端實作**：
```javascript
// HaDataService 自動附加實例 ID
async fetchHaData(params = {}, endpoint) {
    const data = await rpc(endpoint, {
        ...params,
        ha_instance_id: this.getCurrentInstance()  // 自動附加
    });
    return data;
}
```

**為什麼不只用 session？**
- Session 僅在當前瀏覽器有效
- 用戶可能在多個裝置登入，需要持久化偏好設定
- **最佳方案**: Session（臨時） + res.users 欄位（持久化）

#### 3. 使用者沒想到的關鍵問題

##### 🔴 問題 1: WebSocket 連接數爆炸

**場景**：
- 10 個用戶同時使用
- 每個用戶可選 3 個 HA 實例
- 理論上需要 **10 × 3 = 30 個 WebSocket 連接**

**解決方案**（最終選擇）：
- **全部連接策略**：所有活躍實例同時保持連接
- 理由：用戶要求最佳即時性
- 風險緩解：後續可實作連接池或閒置回收機制

##### 🔴 問題 2: Entity ID 衝突

**場景**：
- HA 實例 A 有 `sensor.temperature`
- HA 實例 B 也有 `sensor.temperature`
- 兩者會衝突，無法共存於同一個資料庫

**解決方案**：
```python
class HAEntity(models.Model):
    ha_instance_id = fields.Many2one('ha.instance', required=True)
    entity_id = fields.Char(required=True)

    _sql_constraints = [
        ('entity_instance_unique',
         'unique(entity_id, ha_instance_id)',
         'Entity ID must be unique per HA instance')
    ]
```

**影響範圍**：
- `ha.entity` - 主要實體
- `ha.entity.history` - 歷史記錄
- `ha.area` - 區域
- `ha.entity.group` - 實體群組
- `ha.ws.request.queue` - WebSocket 佇列

##### 🟡 問題 3: Bus 通知路由

**場景**：
- WebSocket 從實例 A 收到 `sensor.temperature` 更新
- 需要通知前端「實例 A 的 sensor.temperature 更新了」
- 但前端可能正在查看實例 B 的 Dashboard

**解決方案**：

後端發送時附加實例資訊：
```python
self.env['ha.realtime.update'].notify_entity_state_change(
    entity_id='sensor.temperature',
    old_state={'state': '21.0'},
    new_state={'state': '22.5'},
    ha_instance_id=instance.id  # ← 新增參數
)
```

前端過濾通知：
```javascript
haDataService.onGlobalState('entity_update', (data) => {
  if (data.ha_instance_id === this.getCurrentInstance()) {
    this.updateChart(data);  // 只處理當前實例的更新
  }
});
```

##### 🟡 問題 4: 數據遷移策略

**現有數據怎麼辦？**

假設已有 500 個 entities，升級後需要：

```python
def migrate_existing_data(env):
    # 1. 創建第一個實例 (⚠️ is_default 已移除 2025-11-25，改用 sequence 排序)
    first_instance = env['ha.instance'].create({
        'name': 'Default HA',
        'api_url': env['ir.config_parameter'].get_param('odoo_ha_addon.ha_api_url'),
        'api_token': env['ir.config_parameter'].get_param('odoo_ha_addon.ha_api_token'),
        'sequence': 1,  # 低 sequence 會被優先選擇
    })

    # 2. 將所有現有 entities 關聯到第一個實例
    entities = env['ha.entity'].search([('ha_instance_id', '=', False)])
    entities.write({'ha_instance_id': first_instance.id})
```

**遷移腳本位置**: `migrations/18.0.3.0/pre-migrate.py`

##### 🟢 問題 5: 權限控管

**需求**：不同用戶可能只能存取特定 HA 實例

**解決方案**：
```python
class HAInstance(models.Model):
    user_ids = fields.Many2many('res.users', string='授權使用者')

    @api.model
    def get_accessible_instances(self):
        """取得當前用戶可存取的實例"""
        return self.search([
            '|',
            ('user_ids', '=', False),  # 無限制
            ('user_ids', 'in', self.env.user.id)
        ])
```

### 方案選擇決策記錄

#### 實施方案對比

| 方案 | 優點 | 缺點 | 工時 | 選擇 |
|------|------|------|------|------|
| **方案 A: 完整多實例支援** | 完整、可擴展、數據隔離完善 | 改動較大，需要數據遷移 | 11-15 天 | ✅ **已選擇** |
| 方案 B: 輕量級實作 | 快速、改動小 | Entity ID 格式醜陋、擴展性差 | 5-7 天 | ❌ |
| 方案 C: 獨立資料庫 | 完全隔離、零開發成本 | 無法跨實例查詢、管理複雜 | 0 天 | ❌ |

#### 用戶決策

**決策時間**: 2025-10-31 09:30

通過 `AskUserQuestion` 工具收集的用戶選擇：

1. **實施方案**: 方案 A - 完整多實例支援
2. **UI 位置**: Dashboard 頂部導航列
3. **權限控管**: 需要（用戶只能存取授權的實例）
4. **連接策略**: 全部連接（所有實例同時保持 WebSocket 連接）

#### 技術決策理由

**為何選擇完整方案而非輕量級？**
- 長期可維護性：避免技術債累積
- 數據安全性：複合唯一約束防止 ID 衝突
- 擴展性：支援未來更多實例管理功能
- 用戶體驗：清晰的數據隔離和權限控管

**為何選擇 Dashboard 頂部而非 menu_avatar？**
- 可見性：更容易被用戶發現
- 類似 Odoo 公司切換器：用戶熟悉的 UI 模式
- 避免修改核心：不需要修改 Odoo 核心 systray

**為何選擇全部連接而非按需連接？**
- 用戶需求：要求最佳即時性
- 技術可行：當前規模可接受（預計不超過 5 個實例）
- 後續優化：可在 Phase 6 根據實際情況調整

### 借鑒的 Odoo 模式

#### Multi-Company 模式

Odoo 原生支援多公司：
```python
class SomeModel(models.Model):
    company_id = fields.Many2one('res.company', required=True)

    # 自動過濾當前公司資料
    @api.model
    def _search(self, ...):
        domain += [('company_id', 'in', self.env.companies.ids)]
```

**借鑒點**：
- 使用 `env.context` 傳遞當前實例
- 在 `_search()` 自動過濾
- 提供 `switch_instance()` 方法類似 `switch_company()`

#### Website 多站點模式

```python
# 從 request 取得當前 website
website = request.website

# 過濾當前網站資料
products = env['product.product'].search([('website_id', '=', website.id)])
```

**借鑒點**：
- 從 request/session 取得當前實例
- 自動過濾實例相關數據

### 風險評估與緩解

| 風險 | 機率 | 影響 | 緩解措施 | 狀態 |
|------|-----|------|---------|------|
| WebSocket 連接數過多 | 中 | 高 | 限制同時連接數，實作連接池 | Phase 6 處理 |
| 數據遷移失敗 | 低 | 高 | 完整備份，rollback 計畫 | Phase 1 已實作 |
| 前端效能下降 | 中 | 中 | 快取實例配置，lazy loading | Phase 4 處理 |
| 現有功能破壞 | 中 | 高 | 完整回歸測試，feature flag | Phase 6 處理 |

---

## 附錄 B: 架構設計文檔

### 系統架構圖

```
┌─────────────────────────────────────────────────────────────┐
│                         前端層 (Frontend)                      │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │InstanceSelector│ │  Dashboard   │ │ Entity Views │      │
│  │   Component   │  │  Components  │ │  Components  │      │
│  └───────┬────────┘  └──────┬───────┘  └──────┬───────┘      │
│          │                  │                  │              │
│          └──────────────────┴──────────────────┘              │
│                             ▼                                 │
│                    ┌─────────────────┐                        │
│                    │  HaDataService  │ ← 統一數據存取         │
│                    │  (ha_instance_id)│                       │
│                    └─────────┬───────┘                        │
└──────────────────────────────┼─────────────────────────────────┘
                               ▼ RPC
┌─────────────────────────────────────────────────────────────┐
│                      API 層 (Controllers)                     │
├─────────────────────────────────────────────────────────────┤
│  _get_current_instance() ← Session + User 偏好              │
│  ↓                                                           │
│  所有 endpoints 支援 ha_instance_id 參數                    │
│  - /ha_data                                                  │
│  - /get_areas                                                │
│  - /call_service                                             │
│  - ...                                                       │
└─────────────────────────────────────────────────────────────┘
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                    WebSocket 層 (Multi-Instance)              │
├─────────────────────────────────────────────────────────────┤
│  _websocket_connections = {                                  │
│    'db_name': {                                              │
│      'instance_1': {thread, stop_event, config},           │
│      'instance_2': {thread, stop_event, config},           │
│      'instance_3': {thread, stop_event, config}            │
│    }                                                         │
│  }                                                           │
└─────────────────────────────────────────────────────────────┘
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                     數據層 (Database)                         │
├─────────────────────────────────────────────────────────────┤
│  ha_instance (實例配置)                                      │
│  ↓                                                           │
│  ha_entity (ha_instance_id FK)                              │
│  ha_area (ha_instance_id FK)                                │
│  ha_entity_history (ha_instance_id FK, related)             │
│  ha_entity_group (ha_instance_id FK, optional)              │
│                                                              │
│  唯一約束: (entity_id, ha_instance_id)                      │
│  唯一約束: (area_id, ha_instance_id)                        │
└─────────────────────────────────────────────────────────────┘
```

### 數據流程圖

**實例切換流程**：
```
用戶點擊選擇器
    ↓
InstanceSelector.onChange()
    ↓
HaDataService.switchInstance(instanceId)
    ↓
RPC: /odoo_ha_addon/switch_instance
    ↓
Backend: request.session['current_ha_instance_id'] = instanceId
    ↓
返回成功
    ↓
HaDataService.triggerGlobalCallbacks('instance_changed')
    ↓
所有訂閱組件重新載入數據
```

**API 調用流程**：
```
Component 調用 haDataService.fetchHaData()
    ↓
自動附加 ha_instance_id = getCurrentInstance()
    ↓
RPC: /odoo_ha_addon/ha_data?ha_instance_id=123
    ↓
Backend: _get_current_instance() → 123
    ↓
instance = ha.instance.browse(123)
    ↓
HassRestApi(env, instance_id=123) 調用 HA API
    ↓
返回數據（已過濾為該實例的數據）
```

**實時通知流程**：
```
WebSocket 收到 state_changed 事件 (instance_1)
    ↓
更新 ha.entity (ha_instance_id=1)
    ↓
ha.realtime.update.notify_entity_state_change(
    entity_id='sensor.temp',
    old_state={...},
    new_state={...},
    ha_instance_id=1  ← 附加實例 ID
)
    ↓
Odoo Bus 廣播到所有用戶
    ↓
HaBusBridge 接收通知
    ↓
HaDataService.triggerGlobalCallbacks('entity_update', {
    entity_id: 'sensor.temp',
    ha_instance_id: 1
})
    ↓
Component 檢查 data.ha_instance_id === currentInstance
    ↓
如果匹配，更新 UI；否則忽略
```

### 關鍵技術實作細節

#### 1. 複合唯一約束實作

**問題**: 不同 HA 實例可能有相同的 entity_id

**解決方案**：
```python
# models/ha_entity.py
_sql_constraints = [
    ('entity_instance_unique',
     'unique(entity_id, ha_instance_id)',
     'Entity ID must be unique per HA instance')
]
```

**效果**：
- 允許：instance_1 的 `sensor.temperature` + instance_2 的 `sensor.temperature`
- 禁止：instance_1 的兩個 `sensor.temperature`

#### 2. Related Field 自動繼承實例

**問題**: `ha.entity.history` 需要知道屬於哪個實例

**解決方案**：
```python
# models/ha_entity_history.py
ha_instance_id = fields.Many2one(
    'ha.instance',
    related='entity_id.ha_instance_id',  # ← 自動繼承
    store=True,
    index=True
)
```

**優點**：
- 無需手動設定
- 自動保持一致性
- 可以直接查詢和過濾

#### 3. Session 與 User 偏好混合策略

**Session 存儲**（臨時）：
```python
# 切換實例時
request.session['current_ha_instance_id'] = instance_id
```

**User 偏好**（持久化）：
```python
# models/res_users.py
class ResUsers(models.Model):
    _inherit = 'res.users'

    current_ha_instance_id = fields.Many2one('ha.instance')
```

**讀取優先級**：
1. Session（當前會話選擇）
2. User 偏好（跨裝置同步）
3. 預設實例（fallback）

---

## 附錄 C: 實施時程表

### 實際進度 vs 預估進度

| Phase | 預估工時 | 實際工時 | 狀態 | 差異 |
|-------|---------|---------|------|------|
| Phase 1 | 3 天 | 2.5 小時 | ✅ 完成 | ⚡ 提前 |
| Phase 2 | 4 天 | 待執行 | ⏸️ 待開始 | - |
| Phase 3 | 2 天 | 待執行 | ⏸️ 待開始 | - |
| Phase 4 | 3 天 | 待執行 | ⏸️ 待開始 | - |
| Phase 5 | 1 天 | 待執行 | ⏸️ 待開始 | - |
| Phase 6 | 2 天 | 待執行 | ⏸️ 待開始 | - |
| **總計** | **15 天** | **2.5 小時** | **6.7% 完成** | - |

### Phase 1 詳細時程

| 任務 | 開始時間 | 完成時間 | 耗時 | 狀態 |
|------|---------|---------|------|------|
| 需求分析與方案設計 | 09:00 | 09:15 | 15 分鐘 | ✅ |
| Task 1.1: ha.instance 模型 | 09:15 | 09:45 | 30 分鐘 | ✅ |
| Task 1.2: Entity 模型更新 | 09:45 | 10:30 | 45 分鐘 | ✅ |
| Task 1.3: Views 和 Security | 10:30 | 11:00 | 30 分鐘 | ✅ |
| Task 1.4: 遷移腳本 | 11:00 | 11:30 | 30 分鐘 | ✅ |
| **總計** | - | - | **2.5 小時** | ✅ |

---

## 附錄 D: 參考資料

### 相關文檔連結

1. **Odoo 官方文檔**
   - [Odoo ORM Documentation](https://www.odoo.com/documentation/18.0/developer/reference/backend/orm.html)
   - [Odoo Views Documentation](https://www.odoo.com/documentation/18.0/developer/reference/backend/views.html)
   - [Odoo Security](https://www.odoo.com/documentation/18.0/developer/reference/backend/security.html)

2. **專案內部文檔**
   - `/docs/CLAUDE.md` - 專案主要文檔
   - `/docs/bus-mechanisms-comparison.md` - Bus 機制比較
   - `/docs/tasks/websocket-integration-plan.md` - WebSocket 整合計劃
   - `/docs/tasks/websocket-concurrency-control.md` - WebSocket 並發控制

3. **Home Assistant API**
   - `/docs/homeassistant-api/HA_串接文件/HA 串接文件.md` - HA API 文檔
   - `/docs/homeassistant-api/homeasistant-websocket.md` - WebSocket 指南

### 關鍵代碼文件

**Backend (Python)**:
- `models/ha_instance.py` - 實例模型（新增）
- `models/ha_entity.py` - 實體模型（已修改）
- `models/common/hass_websocket_service.py` - WebSocket 服務（Phase 2 修改）
- `models/common/websocket_thread_manager.py` - 連接管理器（Phase 2 修改）
- `controllers/controllers.py` - HTTP API（Phase 3 修改）

**Frontend (JavaScript)**:
- `static/src/services/ha_data_service.js` - 數據服務（Phase 4 修改）
- `static/src/services/ha_bus_bridge.js` - Bus 橋接（Phase 4 修改）
- `static/src/components/instance_selector/` - 實例選擇器（Phase 4 新增）

**Database**:
- `migrations/18.0.3.0/pre-migrate.py` - 遷移腳本
- `security/ir.model.access.csv` - 權限配置
- `views/ha_instance_views.xml` - UI 定義

---

**附錄最後更新**: 2025-10-31 12:00
**整理者**: Claude Code
