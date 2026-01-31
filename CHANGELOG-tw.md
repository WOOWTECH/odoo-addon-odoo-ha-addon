# 變更日誌

所有此專案的重要變更都會記錄在此文件中。

此格式基於 [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)，
此專案遵循 [語義化版本](https://semver.org/spec/v2.0.0.html)。

## [Unreleased]

## [18.0.6.2] - 2026-01-21

### 新增功能

#### Portal 增強

- 新增 Portal 麵包屑導航，提升使用者導向
- 新增 PortalLiveStatus 元件，於側邊欄即時顯示狀態
- 在實體表單檢視中新增實體控制面板

#### 實體表單檢視

- 新增響應式佈局支援，改善行動裝置體驗
- 修正實體表單檢視中的屬性解析

### 修復

#### Portal

- 修正 portal 實體網格溢出問題，統一卡片最小寬度（150px）
- 新增群組分享的存取檢查備援機制（修正透過群組分享存取時的權限問題）
- 修正 portal 實體控制回應處理器中的屬性路徑

### 變更

#### UI 重構

- 簡化實體控制器 UI 以符合 portal 風格
- 簡化 portal 實體控制器 UI 結構
- 從 PortalEntityInfo 移除未使用的 LiveStatusCard 子範本
- 移除冗餘元素以簡化群組標頭 UI

### 文件

- 新增分享功能使用指南（含截圖說明）

## [18.0.6.1] - 2026-01-18

### 變更

#### 分享機制遷移（Token-Based 改為 User-Based）

- 將 Token 驗證的 Portal 存取改為用戶驗證（`auth='user'`）
- Portal 路由現在需要 Odoo 登入，未登入用戶將被導向登入頁面
- 新增 `/my/ha` 頁面讓用戶查看所有被分享的實體和群組
- 基於實例的導航：`/my/ha/<instance_id>` 顯示各 HA 實例的實體/群組

### 新增功能

#### ha.entity.share 模型

- 新增 `ha.entity.share` 模型，用於追蹤實體/群組與用戶之間的分享關係
- SQL 約束：實體/群組互斥、用戶組合唯一性
- 計算欄位：`ha_instance_id`、`is_expired`、`display_name`
- 支援 `is_expired` 欄位的搜尋功能與適當的 domain 過濾
- 輔助方法：`get_shares_for_user()`、`get_shared_entities_for_user()`、`get_shared_groups_for_user()`

#### 分享精靈（ha.entity.share.wizard）

- 新增精靈支援多用戶批次建立/更新分享
- 依據上下文自動填入預設值（從實體/群組表單檢視）
- 權限等級選擇：僅檢視或可控制
- 可選的過期時間設定
- 重複處理：更新現有分享而非建立重複記錄
- 顯示現有分享數量和用戶清單

#### 基於權限的存取控制

- 兩種權限等級：`view`（唯讀）和 `control`（可操作設備）
- 檢視權限顯示實體狀態但隱藏控制介面
- 控制權限可透過 `/portal/call-service` 端點操作設備
- 對控制操作進行 domain 和 service 白名單驗證

#### 過期管理

- 分享的可選過期時間
- 排程任務：`_cron_check_expiring_shares()` - 過期前 7 天通知分享建立者
- 排程任務：`_cron_cleanup_expired_shares()` - 移除過期超過 30 天的分享
- 過期的分享會自動從存取檢查中排除

#### Portal /my/ha 整合

- `/my/ha` 路由顯示當前用戶擁有分享的所有 HA 實例
- `/my/ha/<instance_id>` 路由以分頁顯示實體/群組
- 每個實例的實體數量和群組數量
- 權限徽章顯示（檢視/控制）
- 無分享時顯示空狀態訊息

#### UI 增強

- 新增滑桿進度指示器樣式，適用於亮度、風扇速度和窗簾位置控制

### 修復

#### 分享精靈 UI

- 移除分享精靈警示的群組包裝器，修復 UI 佈局問題

#### 權限系統

- 當實體群組 `user_ids` 變更時清除 ir.rule 快取，確保權限即時更新
- 使用 `registry.clear_cache()` 取代已棄用的 `model.clear_caches()`，相容 Odoo 18

#### Portal

- 防止 portal 實體控制器在雙欄佈局中溢出
- 新增 portal 範本的繁體中文翻譯
- 對齊 portal HA 卡片與標準 Odoo portal 分類結構

#### 排程任務

- 移除 cron.xml 中已棄用的 `numbercall` 欄位，相容 Odoo 18

### 移除

#### Portal Token 機制（已棄用）

- 從 `ha.entity` 和 `ha.entity.group` 模型移除 `portal.mixin` 繼承
- 移除 `action_share_portal` 方法和「透過連結分享」按鈕
- 刪除過時的 `test_portal_mixin.py` 測試檔案
- Token 驗證存取已完全由用戶驗證取代

### 安全性

- 所有 Portal 路由使用 `auth='user'` 要求 Odoo 登入
- 透過 `ha.entity.share` 記錄控制存取（無法透過 URL 操作繞過）
- 欄位白名單（`PORTAL_ENTITY_FIELDS`、`PORTAL_GROUP_FIELDS`）防止敏感資料曝露
- `sudo()` 僅用於讀取操作，不用於寫入
- 服務白名單（`PORTAL_CONTROL_SERVICES`）限制允許的控制操作
- 過期的分享會自動拒絕存取
- 新增 ir.rule 權限變更的安全性測試

## [18.0.6.0] - 2025-01-10

### 新增功能

#### Portal 分享（Token 驗證存取）

- `ha.entity` 和 `ha.entity.group` 模型支援 portal mixin
- 實體與群組表單檢視新增分享按鈕，支援 token 產生
- Portal 控制器支援 HMAC token 驗證（防止計時攻擊）
- 實體與群組分享頁面的 Portal QWeb 範本
- 輪詢優化，支援頁面可見度控制與視覺回饋
- Portal 實體控制，支援 switch/light/fan/cover/climate/automation/scene/script 領域
- 統一的 Portal call-service API，透過 JSON-RPC（`/portal/entity/<id>/call-service`）
- PortalEntityInfo 與 PortalGroupInfo OWL 元件
- Portal 群組實體以響應式卡片網格佈局顯示
- Header-based token 驗證（`X-Portal-Token`）

#### Portal UI 重新設計（IoT 風格介面）

- CSS 自訂屬性主題系統，支援明/暗模式
- IoT 切換開關樣式，用於二元控制
- 數值滑桿樣式，用於亮度/速度/位置控制
- 感測器顯示樣式，用於數值與二元感測器
- 狀態變更動畫，支援減少動態效果（無障礙功能）
- 響應式斷點與觸控目標優化
- 符合 WCAG AA 標準的顏色對比度（綠色按鈕 5.48:1）

#### 歷史同步效能

- 平行歷史同步，支援可配置的最大 workers 數量
- 過期訂閱清理機制
- 批次訂閱有效性檢查（單一資料庫查詢優化）

#### 實例資料管理

- 擴展實例資料清除範圍，包含設備、標籤與實體標籤
- 新增 Sync Registry 按鈕，按順序同步 Labels、Areas 與 Devices

#### 測試

- 實體控制器元件的 Playwright E2E 測試
- E2E 測試配置（`tests/e2e_tests/e2e_config.yaml`）

### 變更

#### Portal 架構

- 統一 portal token 處理與存取驗證
- fetchState 遷移至 JSON-RPC（移除已棄用的 HTTP 端點）
- call-service 端點中將 `entity_id` 重新命名為 `record_id` 以提升清晰度
- 移除已棄用的 `portal_entity_control` 端點

#### 實體控制器重構

- 將共用實體控制邏輯提取為可重用 hooks（`useEntityControl`）
- 使用 `buildActionsFromConfig` 輔助函式統一 action 建構
- 統一實體控制器 action 命名慣例
- Portal 實體控制器使用宣告式 `owl-component` 標籤

#### UI/UX

- 停用自動暗色模式，預設使用淺色主題
- Portal 範本翻譯為繁體中文

### 修復

- 防止卸載 addon 時誤刪 HA 資料
- CSS `max()` 搭配 `env()` 的 SASS 編譯器相容性處理
- Portal 服務中 JSON-RPC 回應包裝器處理
- Portal API 呼叫使用 Odoo record ID（原本誤用 HA entity_id）
- 並行存取時 subscription 清理的 KeyError 問題
- 平行歷史同步任務的逾時處理

### 文件

- CLAUDE.md 新增 portal 分享功能文件
- E2E 測試章節更新為使用 Playwright MCP
- 新增 portal UI 測試指南與範例測試連結
- 格式化 share_entities PRD markdown 表格
- 說明清除實例資料只影響 Odoo，不影響 Home Assistant

## [18.0.5.0] - 2025-12-03

### 新增功能

#### Glances 儀表板整合

- 新增 Glances 設備探索與實體取得的後端 API
  - `/glances_devices`：透過 config/device_registry/list 取得設備
  - `/glances_device_entities`：取得設備實體及其狀態
- 新增 GlancesBlock 元件，在 HA Info 頁面顯示設備卡片
- 新增 GlancesDeviceDashboard 動作，用於詳細實體檢視
  - 依類型分組實體（CPU、記憶體、磁碟、網路等）
  - 根據數值顯示顏色編碼狀態指示器
- ha_data_service 擴充 `getGlancesDevices`/`getGlancesDeviceEntities` 方法

#### 即時更新

- Glances 儀表板的事件驅動快取失效機制
- 訂閱 Home Assistant 的 `device_registry_updated` WebSocket 事件
- 設備新增或移除時自動清除 Glances 快取

### 變更

#### 程式碼品質

- 將計時器間隔提取至 `constants.js` 以提升可維護性
- 將魔術數字（30000ms、300000ms 等）集中至單一常數檔案

#### 清理

- 移除死碼：未使用的通知方法（`_notify_entity_update`、`_notify_ha_websocket_status`、`notify_entity_update`）

### 文件

- 更新文件以反映實際實作
- 修正文件中 TransientModel → Model with bus.listener.mixin
- 將範例中的 `notify_entity_update` 替換為 `notify_entity_state_change`
- 更新 5 個文件中的方法清單與程式碼範例

## [18.0.4.2] - 2025-11-27

### 新增功能

#### 多實例支援

- POS 風格設定頁面，用於 HA 實例配置
- 基於群組的權限系統，支援明確授權
- 實例資料清除精靈，支援多語系
- 實例同步時間戳追蹤
- 在實體清單檢視中顯示 `ha_instance_id` 欄位
- 從儀表板直接開啟新增 HA 實例的彈出表單

#### 國際化

- 完整的多語系支援，含繁體中文翻譯
- 全模組多語言支援

#### 安裝與相依套件

- 在 `pre_init_hook` 中自動安裝 Python 相依套件
- 支援 Debian/Ubuntu pip 安裝的 `--break-system-packages` 參數
- websockets 套件改用延遲載入以支援自動安裝

### 修復

#### 無障礙

- 標準化 ARIA alert 角色以符合無障礙規範

#### 權限與安全

- 使用正確的 Odoo API 進行權限檢查
- 新增實例建立彈出視窗的錯誤處理與權限檢查
- 安裝時自動授予管理員 HA Manager 權限
- 防止 API token 在除錯日誌中曝露

#### 安裝

- 移除 `external_dependencies` 以支援 `pre_init_hook` 自動安裝

#### 資料完整性

- 為不應複製的欄位加入 `copy=False`
- 移除 `entity_count` 和 `area_count` 的錯誤 `@api.depends`
- 修正測試中 `get_websocket_client` 的 mock patch 路徑

#### UI/UX

- 將必填欄位改為條件式以允許新增實例按鈕
- 移除彈出表單的自訂 footer，改用預設儲存行為
- 解決 fa icons 和 alerts 的檢視驗證警告
- 新增簡化的新增 HA 實例彈出表單

### 變更

#### 架構

- 移除 `is_default` 欄位，改採基於權限的實例選擇機制
- 以實例儀表板入口頁面取代系統匣切換器
- 提取 `HACurrentInstanceFilterMixin` 以減少程式碼重複
- 將選單定義整合至 `dashboard_menu.xml`
- 使用 related fields 簡化 HA 實例欄位對應

#### 效能

- 恢復 `get_areas` 中的 `cr.commit()` 以改善並行處理
- 將指紋更新延遲至儲存動作，而非測試連線時

#### 程式碼品質

- 改善交易管理與國際化
- 將 logger 移至模組層級
- 改善全域設定的視覺區隔

### 文件

- 重新組織文件結構
- 重構 CLAUDE.md 並拆分為模組化文件
- 新增 `sudo()` 使用說明，供安全稽核參考
- 更新文件以反映 `is_default` 欄位移除
- 更新架構圖以反映實際實作
- 更新自動安裝 hooks 與疑難排解文件

### 測試

- 新增 `get_areas` 與區域同步功能的單元測試

## [18.0.2.2] - 2025-10-28

### 修復

- 移除 HA Info 儀表板的 Layout 元件依賴，改善 ir.actions.client 相容性
- 移除實體屬性檢視中 ACE 編輯器的 JSON 模式配置

## [18.0.2.1] - 2025-10-28

### 新增功能

#### 實體控制器

- Cover（窗簾/捲簾）實體控制器，支援即時屬性同步（位置、傾斜角度）
- Fan（風扇）實體控制器，支援即時屬性同步（速度、方向）
- Automation（自動化）實體控制器支援
- Scene（場景）實體控制器支援
- Script（腳本）實體控制器支援

#### 儀表板功能

- 網路資訊儀表板，支援 fullWidth 版面配置
- 在網路儀表板中顯示 Home Assistant 共享 URL

### 修復

- 修復實體控制器按鈕的事件冒泡問題，避免不必要的表單檢視導航
- 改善儀表板滾動行為，正確整合 Odoo Layout
- 修復區域儀表板中的 PostgreSQL 序列化衝突，加入重試機制與 savepoint 隔離

### 效能優化

- 透過平行資料擷取優化儀表板初始載入速度

### 重構

- 使用統一包裝器（`_standardize_response()`）標準化所有 HTTP 端點回應格式
- 所有端點現在都回傳一致的 `{success: bool, data: dict, error: str}` 格式

### 文件

- API 回應格式標準化文件

## [18.0.2.0] - 2025-10-22

### 新增功能

#### WebSocket 整合

- 與 Home Assistant 的 WebSocket 即時連線支援
- 跨進程 WebSocket 請求佇列系統（`ha.ws.request.queue` 模型）
- WebSocket 狀態監控與即時通知
- 可配置的 WebSocket 心跳間隔與設定介面
- 智慧重試機制與重啟冷卻保護
- WebSocket 服務的多資料庫支援
- WebSocket 硬體資訊與控制介面

#### 歷史資料管理

- 歷史資料串流的 WebSocket 訂閱機制
- 完整的歷史資料 API 端點
- 歷史檢視的搜尋 UI 支援，含篩選與分組功能
- 歷史清單檢視中的實體名稱與 entity_id 顯示欄位
- 圖表資料結構強化，加入 entity_name 與 entity_id_string 欄位

#### 即時通知

- 集中式 bus bridge 模式實作（`HaBusBridge`）
- 透過 Odoo bus 的統一即時通知系統
- 即時狀態變更通知，包含新舊狀態追蹤
- 前端的即時 WebSocket 狀態更新

#### 實體管理

- 實體群組標籤系統，支援多對多關係
- 實體群組的顏色欄位支援，含 many2many_tags 小工具
- 自訂實體群組標籤排序的序列欄位
- HA 實體的友善名稱欄位
- 基於區域的儀表板，含 Home Assistant 區域管理

#### 設備控制

- 統一的 `EntityController` 元件，支援各領域專屬控制
- 設備控制 API 實作
- Home Assistant 設備的完整控制流程

#### UI/UX 改進

- 現代化的設定介面，含專屬 WOOW HA 區段
- 儀表板 action 重新命名為 `ha_info_dashboard` 以提升清晰度
- ACE 編輯器顯示的 JSON 轉字串轉換

### 變更

- 將 `state` 欄位重新命名為 `entity_state` 以避免與 Odoo 保留欄位衝突
- WebSocket 請求佇列模型重新命名，加入 `ha` 前綴以保持一致性（`ws.request.queue` → `ha.ws.request.queue`）
- 將 `view_mode` 從 `tree` 更新為 `list` 以符合 Odoo 18 相容性
- 提取 `WebSocketClient` 並統一 API 呼叫邏輯
- 將 WebSocket 心跳間隔改為動態可配置
- 更新選單配置以提升組織架構

### 修復

- 實體示範中無法使用 `ha_data` 服務的錯誤處理
- 資料庫序列化失敗的重試機制
- WebSocket API 呼叫的時區處理
- 容器重啟後保留 HA 設定

### 移除

- 測試程式碼與未使用的感測器模型
- queue_job 依賴項

### 文件

- 歷史端點的完整 WebSocket API 文件
- Bus 機制比較指南（useBus vs bus_service.subscribe）
- Home Assistant 歷史記錄去重策略研究
- 文件結構重組
- WebSocket 訂閱實作文件（v1.2）
- last_changed 與 last_updated 欄位說明

### 基礎設施

- Odoo 的 Nginx 反向代理配置，支援 WebSocket
- 強化卸載 hook，含完整資料清理

## [18.0.1.1] - 前一個版本

初始版本，具備基本的 Home Assistant 整合功能。

### 新增功能

- 從 Home Assistant 同步基本實體
- 實體顯示的儀表板檢視
- 與 Home Assistant 的 REST API 整合
- HA 連線設定的配置管理
