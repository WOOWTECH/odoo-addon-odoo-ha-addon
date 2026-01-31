---
name: share_entities
description: Portal Access & External Token Sharing for Entity and Entity Group
status: complete
created: 2026-01-01T15:47:11Z
updated: 2026-01-09T08:57:48Z
---

# PRD: share_entities

## Executive Summary

實作 Entity 與 Entity Group 的外部 Token 分享機制，讓 HA Manager 可以透過安全的連結將 IoT 設備資訊分享給外部用戶（Portal 用戶或匿名訪客）。此功能參照 Odoo 原生 Project/Task 的分享邏輯，為 `ha.entity` 與 `ha.entity.group` 啟用 Portal Access。

**核心價值：**

- 安全地將 IoT 設備狀態分享給外部利益相關者
- 無需 Odoo 帳號即可透過連結查看設備資訊
- 支援即時狀態更新（WebSocket）
- 整合 Odoo Portal 標準 UX

## Problem Statement

### 現狀問題

1. **資料封閉性**：目前 Entity 資料僅限於 Odoo 內部用戶存取，無法分享給外部客戶、供應商或合作夥伴
2. **整合困難**：需要將設備狀態資訊整合到其他業務流程（如客戶支援、設施管理報告）時，缺乏標準機制
3. **協作受限**：多方利益相關者（如設施管理員、租戶、維護人員）無法便捷地共同監控同一組設備

### 為何現在需要

- 客戶需求：多個客戶反映需要將設備狀態分享給外部人員
- 業務擴展：BMS (Building Management System) 場景需要與租戶共享建築設備資訊
- 技術成熟：Odoo 18 的 Portal 機制已足夠成熟支援此功能

## User Stories

### Persona 定義與權限對應

本功能涉及三種使用者角色，以下說明其與現有權限系統的對應關係：

| Persona                    | 描述                                    | Odoo 權限對應      | 存取方式                |
| -------------------------- | --------------------------------------- | ------------------ | ----------------------- |
| **Persona 1: HA Manager**  | 內部管理員，負責設定分享、管理連結      | `group_ha_manager` | 直接登入 Odoo           |
| **Persona 2: 外部訪客**    | 任何擁有分享連結的人（無需帳號）        | 無（Token 驗證）   | 分享連結 + access_token |
| **Persona 3: Portal 用戶** | 被邀請的外部用戶（有 Odoo Portal 帳號） | Portal User        | Email 邀請 → 登入       |

**重要說明：**

- 外部訪客（Persona 2）和 Portal 用戶（Persona 3）**不需要** `group_ha_user` 或 `group_ha_manager` 權限
- Token 驗證機制獨立於現有權限系統，通過 `access_token` 直接授權存取特定記錄
- 只有 **HA Manager** 可以建立和管理分享連結

**技術說明：**

- 外部訪客的 Token 驗證獨立於 ir.rule，通過 `access_token` 欄位（由 `portal.mixin` 提供）驗證
- Controller 中使用 `sudo()` 讀取資料，繞過現有的 `ir.rule` 多實例過濾（`ha.current.instance.filter.mixin`）
- 敏感欄位（如完整 `attributes` JSON 中的某些資訊）應在 Controller 中進行 whitelist 過濾

---

### Persona 1: HA Manager（原 IT 管理員）

**US1.1: 設定分享權限**

```
As an HA Manager
I want to 在 Entity/Entity Group 表單中啟用分享功能
So that 我可以控制哪些設備可以被分享
```

**Acceptance Criteria:**

- [ ] Entity 與 Entity Group Form View 有 "Share" 按鈕
- [ ] 點擊後開啟標準 `portal.share` Wizard
- [ ] 可產生公開連結（Token-based）
- [ ] 可發送 Email 邀請給 Portal 用戶

**US1.2: 管理分享連結**

```
As an HA Manager
I want to 查看和撤銷已分享的連結
So that 我可以控制外部存取權限
```

**Acceptance Criteria:**

- [ ] 可查看已產生的分享連結列表
- [ ] 可手動撤銷/重新產生 access token
- [ ] 可設定連結過期時間（可選）

### Persona 2: 外部訪客（Token 授權）

**US2.1: 透過連結查看設備狀態**

```
As an 外部訪客
I want to 透過分享連結查看設備當前狀態
So that 我可以即時了解設備運行情況
```

**Acceptance Criteria:**

- [ ] 無需登入即可透過連結存取
- [ ] 顯示 Entity 基本資訊：名稱、狀態、最後更新時間、所屬 Area
- [ ] 頁面自動透過 WebSocket 接收即時更新
- [ ] 連結失效時顯示友善錯誤頁面

**US2.2: 查看 Entity Group 內容**

```
As an 外部訪客
I want to 透過 Entity Group 連結查看所有包含的設備
So that 我可以一次監控多個相關設備
```

**Acceptance Criteria:**

- [ ] 顯示 Group 基本資訊
- [ ] 列表顯示所有包含的 Entities 及其當前狀態
- [ ] 每個 Entity 狀態即時更新

**US2.3: 透過 Portal 控制設備** _(新增)_

```
As an 外部訪客
I want to 透過分享連結控制 switch/light/fan 類型的設備
So that 我可以遠端開關設備
```

**Acceptance Criteria:**

- [ ] Portal 頁面顯示 Control Card（僅 switch/light/fan domain）
- [ ] Toggle 按鈕正確顯示當前狀態 (on/off)
- [ ] 點擊後透過 Token 驗證的 API 發送控制命令
- [ ] 控制後狀態即時更新
- [ ] 顯示 Loading 狀態和錯誤處理
- [ ] 只允許白名單 actions：toggle, turn_on, turn_off

### Persona 3: Portal 用戶（Email 邀請）

**US3.1: 透過邀請查看設備**

```
As a Portal 用戶
I want to 透過 Email 邀請存取分享給我的設備
So that 我可以持續監控被授權的設備
```

**Acceptance Criteria:**

- [ ] 收到邀請 Email 後可透過連結登入並查看
- [ ] 登入後可在 Portal 首頁看到被分享的設備列表
- [ ] 無需每次都透過 Email 連結存取

**US3.2: 在 Chatter 留言互動**

```
As a Portal 用戶
I want to 在設備頁面留言提問或報告問題
So that 我可以與內部維護人員溝通
```

**Acceptance Criteria:**

- [ ] 設備頁面底部顯示 Chatter 區塊
- [ ] Portal 用戶可以新增留言
- [ ] 內部用戶可以回覆留言
- [ ] 新留言時雙方收到通知

## Requirements

### Functional Requirements

#### FR1: Model Layer

| ID    | Requirement                                            | Priority |
| ----- | ------------------------------------------------------ | -------- |
| FR1.1 | `ha.entity` 繼承 `portal.mixin` 和 `mail.thread`       | Must     |
| FR1.2 | `ha.entity.group` 繼承 `portal.mixin` 和 `mail.thread` | Must     |
| FR1.3 | 實作 `_compute_access_url` 回傳外部存取路徑            | Must     |
| FR1.4 | 新增 `access_token_expiry` 欄位（可選過期時間）        | Should   |
| FR1.5 | Token 過期檢查邏輯                                     | Should   |

##### FR1 實現備註

**現有繼承結構**:
`ha.entity` 和 `ha.entity.group` 目前已繼承：

- `ha.current.instance.filter.mixin` - 多實例過濾（自動依 session 過濾資料）
- `mail.thread` - 郵件/Chatter 功能 ✅ 已有
- `mail.activity.mixin` - 活動追蹤

**Portal 實現注意事項**:

1. `ha.current.instance.filter.mixin` 可能影響 Portal 的資料讀取，需確保 `sudo()` 操作繞過此過濾
2. 新增 `portal.mixin` 時需排在繼承列表最後：
   ```python
   _inherit = ['ha.current.instance.filter.mixin', 'mail.thread', 'mail.activity.mixin', 'portal.mixin']
   ```

#### FR2: Controller Layer

| ID    | Requirement                                                     | Priority |
| ----- | --------------------------------------------------------------- | -------- |
| FR2.1 | 建立 `/portal/entity/<int:entity_id>` 路由 (auth='public')      | Must     |
| FR2.2 | 建立 `/portal/entity_group/<int:group_id>` 路由 (auth='public') | Must     |
| FR2.3 | 實作 access_token 驗證邏輯                                      | Must     |
| FR2.4 | 驗證通過後使用 `sudo()` 讀取資料                                | Must     |
| FR2.5 | Token 無效或過期時回傳 403 錯誤頁面                             | Must     |
| FR2.6 | 支援無痕模式/匿名訪問                                           | Must     |
| FR2.7 | 建立 `/portal/entity/<int:entity_id>/control` JSON 端點         | Must     |
| FR2.8 | 控制端點使用 action 白名單（toggle, turn_on, turn_off）         | Must     |
| FR2.9 | 控制端點僅支援 switch/light/fan domain                          | Must     |

#### FR3: UI/UX - Internal

| ID    | Requirement                                     | Priority |
| ----- | ----------------------------------------------- | -------- |
| FR3.1 | Entity Form View Header 加入 "Share" 按鈕       | Must     |
| FR3.2 | Entity Group Form View Header 加入 "Share" 按鈕 | Must     |
| FR3.3 | 按鈕呼叫標準 `portal.share` Wizard              | Must     |
| FR3.4 | 支援連結生成功能                                | Must     |
| FR3.5 | 支援 Email 邀請功能                             | Must     |
| FR3.6 | 分享時可設定過期時間選項                        | Should   |

#### FR4: View Layer - Portal

| ID    | Requirement                                        | Priority |
| ----- | -------------------------------------------------- | -------- |
| FR4.1 | Entity Portal Template 繼承 `portal.portal_layout` | Must     |
| FR4.2 | 包含麵包屑導航 (Breadcrumbs)                       | Must     |
| FR4.3 | 顯示 Entity 基本資訊（名稱、狀態、最後更新、Area） | Must     |
| FR4.4 | 包含 Chatter 區塊                                  | Must     |
| FR4.5 | Entity Group Template 顯示 Group 資訊              | Must     |
| FR4.6 | Entity Group Template 列表顯示所屬 Entities        | Must     |

#### FR5: Real-time Updates

| ID    | Requirement                    | Priority |
| ----- | ------------------------------ | -------- |
| FR5.1 | Portal 頁面整合 WebSocket 連線 | Must     |
| FR5.2 | Entity 狀態變化時自動更新頁面  | Must     |
| FR5.3 | 顯示連線狀態指示器             | Should   |
| FR5.4 | 斷線時自動重連                 | Should   |

##### FR5 技術實現備註

**現有架構限制**:
現有 Odoo Bus 廣播機制 (`ha_realtime_update.py`) 只支援已登入的 `res.users`，
Portal 用戶和匿名訪客無法直接使用現有的即時更新機制。

**建議實現方案** (擇一):

| 方案                    | 複雜度 | 即時性 | 說明                                                     |
| ----------------------- | ------ | ------ | -------------------------------------------------------- |
| **A: 擴展 Bus Channel** | 中     | 高     | 為 Portal 建立專用 channel，修改 `_broadcast_to_users()` |
| **B: Polling Fallback** | 低     | 低     | Portal 頁面使用定時輪詢 (每 5-10 秒)                     |
| **C: 獨立 WebSocket**   | 高     | 高     | 建立 `/portal/ha/websocket` 獨立端點                     |

**推薦方案 B (Polling)** 作為 MVP，理由：

1. 實現簡單，不需修改現有 Bus 架構
2. 對外部用戶而言，5-10 秒延遲通常可接受
3. 後續可升級為方案 A 或 C

### Non-Functional Requirements

#### NFR1: Security

| ID     | Requirement                                      | Target                  |
| ------ | ------------------------------------------------ | ----------------------- |
| NFR1.1 | Access Token 使用安全隨機產生                    | 32+ characters          |
| NFR1.2 | Token 驗證必須防止時序攻擊                       | Use hmac.compare_digest |
| NFR1.3 | sudo() 操作僅限於當前 record                     | Record-level only       |
| NFR1.4 | 敏感資料（如 attributes）不暴露給外部            | Whitelist fields        |
| NFR1.5 | 控制端點使用 domain + action 白名單              | PORTAL_CONTROL_ACTIONS  |
| NFR1.6 | 控制端點 Token 驗證使用 constant-time comparison | hmac.compare_digest     |

#### NFR2: Performance

| ID     | Requirement               | Target       |
| ------ | ------------------------- | ------------ |
| NFR2.1 | Portal 頁面載入時間       | < 2 seconds  |
| NFR2.2 | WebSocket 狀態更新延遲    | < 500ms      |
| NFR2.3 | Entity Group 最大列表數量 | 100 entities |

#### NFR3: Compatibility

| ID     | Requirement | Target                                            |
| ------ | ----------- | ------------------------------------------------- |
| NFR3.1 | 瀏覽器支援  | Chrome, Firefox, Safari, Edge (latest 2 versions) |
| NFR3.2 | 響應式設計  | Mobile-friendly                                   |
| NFR3.3 | Odoo 版本   | 18.0                                              |

## Success Criteria

| Metric         | Target  | Measurement            |
| -------------- | ------- | ---------------------- |
| 分享連結可用率 | 99.9%   | Token 驗證成功率       |
| 頁面載入時間   | < 2s    | P95 latency            |
| 即時更新延遲   | < 500ms | WebSocket 訊息傳遞時間 |
| 用戶滿意度     | > 4/5   | 使用者回饋             |
| 安全漏洞       | 0       | Security audit         |

## Technical Architecture

### Component Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         HA Manager                               │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐       │
│  │ Entity Form  │ => │ Share Wizard │ => │ Generate URL │       │
│  └──────────────┘    └──────────────┘    └──────────────┘       │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼ (Share Link with Token)
┌─────────────────────────────────────────────────────────────────┐
│                      External User                               │
│                                                                  │
│    /portal/entity/<id>?access_token=xxx                         │
│              │                                                   │
│              ▼                                                   │
│    ┌──────────────────────────────────────────────────────┐     │
│    │                Portal Controller                      │     │
│    │  1. Validate access_token                            │     │
│    │  2. Check expiry (if set)                            │     │
│    │  3. sudo().read() with field whitelist               │     │
│    │  4. Render QWeb template                             │     │
│    └───────────────────────────┬──────────────────────────┘     │
│                                │                                 │
│                                ▼                                 │
│    ┌──────────────────────────────────────────────────────┐     │
│    │              Portal QWeb Template                     │     │
│    │  - portal.portal_layout                              │     │
│    │  - Breadcrumbs                                       │     │
│    │  - Entity Info                                       │     │
│    │  - Chatter                                           │     │
│    │  - WebSocket JS for real-time                        │     │
│    └──────────────────────────────────────────────────────┘     │
│                                │                                 │
│                                ▼                                 │
│    ┌──────────────────────────────────────────────────────┐     │
│    │           Home Assistant (via Odoo)                   │     │
│    │           WebSocket State Updates                     │     │
│    └──────────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────────┘
```

### URL Structure

| Route                                 | Description                 |
| ------------------------------------- | --------------------------- |
| `/portal/entity/<int:entity_id>`      | 單一 Entity 頁面            |
| `/portal/entity_group/<int:group_id>` | Entity Group 頁面（含列表） |

### Data Flow

```
1. HA Manager clicks "Share" button
2. portal.share Wizard generates access_token
3. HA Manager copies URL or sends email invitation
4. External user opens URL
5. Controller validates token
6. Controller reads entity data with sudo()
7. QWeb renders Portal page
8. JavaScript establishes WebSocket connection
9. Entity state changes push to browser
```

## Constraints & Assumptions

### Constraints

1. **Technical**

   - 必須使用 Odoo 18 標準 Portal 機制
   - WebSocket 連線需穿透 Nginx proxy
   - 不能修改核心 `portal.mixin` 行為

2. **Security**

   - 外部用戶不能存取非分享的記錄
   - Token 必須足夠長且隨機
   - 敏感欄位必須過濾

3. **UX**
   - Portal 頁面必須響應式設計
   - 必須與現有 Portal 風格一致

### Assumptions

1. Home Assistant WebSocket 服務持續運行
2. 外部用戶有穩定的網路連線
3. HA Manager 了解分享功能的安全影響
4. Email 服務已正確配置

## Out of Scope

以下功能明確不在本 PRD 範圍內：

1. ~~**Entity 控制權限** - 外部用戶無法控制設備（僅查看）~~ _(已在 v1.1 加入有限控制)_
2. **批量分享選取** - 不支援在列表頁勾選多個 Entities 產生單一連結
3. **歷史資料圖表** - 外部視圖只顯示當前狀態，不含歷史圖表
4. **自訂 Portal 佈局** - 使用標準 Odoo Portal 模板
5. **Mobile App 整合** - 僅 Web 瀏覽器存取
6. **分享權限繼承** - Group 分享不自動包含 Entity 編輯權
7. **進階控制動作** - 僅支援 toggle/turn_on/turn_off，不支援 set_brightness 等

## Dependencies

### External Dependencies

| Dependency        | Type    | Description                                              |
| ----------------- | ------- | -------------------------------------------------------- |
| Odoo Portal       | Module  | 標準 Portal 機制，提供 `portal.mixin` 和 Portal 模板     |
| mail.thread       | Mixin   | Chatter 功能（已在 ha.entity 和 ha.entity.group 中實現） |
| Home Assistant    | Service | 設備狀態來源                                             |
| WebSocket Service | Service | 即時更新通道                                             |

**Manifest 依賴要求**:

```python
# __manifest__.py 需新增 'portal' 依賴
'depends': ['base', 'web', 'mail', 'portal'],  # 新增 'portal'
```

### Internal Dependencies

| Dependency      | Description             |
| --------------- | ----------------------- |
| ha.entity       | 主要分享對象 Model      |
| ha.entity.group | 群組分享對象 Model      |
| ha.instance     | 用於確認 WebSocket 連線 |
| ha_bus_bridge   | 前端即時更新服務        |

## Risks

| Risk             | Probability | Impact | Mitigation                     |
| ---------------- | ----------- | ------ | ------------------------------ |
| Token 外洩       | Medium      | High   | 支援過期機制、撤銷功能         |
| WebSocket 不穩定 | Medium      | Medium | 自動重連、fallback polling     |
| 效能問題         | Low         | Medium | Entity Group 限制 100 entities |
| Portal 相容性    | Low         | High   | 遵循 Odoo Portal 標準          |

## Implementation WBS

### Phase 1: Model Layer (2 days)

- [ ] ha.entity 繼承 portal.mixin, mail.thread
- [ ] ha.entity.group 繼承 portal.mixin, mail.thread
- [ ] 實作 \_compute_access_url
- [ ] 新增 access_token_expiry 欄位
- [ ] 單元測試

### Phase 2: Controller Layer (2 days)

- [ ] Entity Portal Controller
- [ ] Entity Group Portal Controller
- [ ] Token 驗證邏輯
- [ ] 過期檢查邏輯
- [ ] 整合測試

### Phase 3: Internal UI (1 day)

- [ ] Entity Form View Share 按鈕
- [ ] Entity Group Form View Share 按鈕
- [ ] 過期時間選項整合

### Phase 4: Portal Views (2 days)

- [ ] Entity Portal Template
- [ ] Entity Group Portal Template
- [ ] Breadcrumbs 導航
- [ ] Chatter 整合
- [ ] 響應式樣式

### Phase 5: Real-time Updates (2 days)

- [ ] Portal WebSocket 整合
- [ ] 狀態更新推送
- [ ] 連線狀態指示器
- [ ] 自動重連機制

### Phase 6: Portal Entity Control (1 day) _(新增)_

- [ ] 新增 `/portal/entity/<id>/control` JSON 端點
- [ ] 實作 action 白名單驗證
- [ ] Portal Template 新增 Control Card UI
- [ ] Toggle 按鈕 + 狀態即時更新
- [ ] 單元測試

### Phase 7: Testing & Polish (1 day)

- [ ] E2E 測試
- [ ] Security 審查
- [ ] 文件撰寫
- [ ] Bug fixes

## Appendix

### Reference: Odoo Project Sharing

參考 Odoo 標準模組中的分享實作：

- `addons/project/models/project.py` - Project 繼承 portal.mixin
- `addons/project/controllers/portal.py` - Portal Controller
- `addons/project/views/project_portal_templates.xml` - Portal Templates

### Field Whitelist for External Access

```python
PORTAL_ENTITY_FIELDS = [
    'name',
    'entity_id',       # HA entity_id (e.g., sensor.temperature)
    'entity_state',    # 實體狀態（注意：欄位名為 entity_state，非 state）
    'last_changed',    # Datetime 欄位
    'area_id',         # Many2one to 'ha.area'
    'domain',          # 實體類型 (switch, sensor, light, etc.)
    'attributes',      # JSON 欄位，包含 device_class, icon, unit_of_measurement 等
]

# 說明：
# - 'device_class' 和 'icon' 存在於 'attributes' JSON 中，格式如：
#   attributes = {
#       "device_class": "temperature",
#       "icon": "mdi:thermometer",
#       "unit_of_measurement": "°C",
#       ...
#   }
# - 如需友善的狀態顯示，可在實作時新增 'state_display' computed field

PORTAL_GROUP_FIELDS = [
    'name',
    'description',
    'entity_ids',      # Many2many to entities
    'entity_count',    # computed, stored
]

# Portal Control Services Whitelist (v1.1 新增)
# 僅允許這些 domain 的特定 services
PORTAL_CONTROL_SERVICES = {
    'switch': ['toggle', 'turn_on', 'turn_off'],
    'light': ['toggle', 'turn_on', 'turn_off'],
    'fan': ['toggle', 'turn_on', 'turn_off'],
}
```
