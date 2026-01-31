---
name: user-based-entity-sharing
description: 將 Entity/Entity Group 分享機制從 Token-based 改為 User-based，支援權限控制與過期管理
status: complete
created: 2026-01-16T16:05:48Z
---

# PRD: User-Based Entity Sharing

## Executive Summary

重構現有的 Entity 與 Entity Group 分享機制，從匿名 Token-based 存取改為基於用戶登入的權限控制系統。此功能讓 HA Administrator 可以將 IoT 設備分享給特定 Odoo 用戶，並設定「僅查看」或「可控制」權限，同時支援權限過期時間與到期提醒通知。

**核心價值：**

- 更安全的存取控制（必須登入 Odoo 帳號）
- 細粒度權限管理（查看/控制權限分離）
- 權限時效管理（過期時間 + 到期提醒）
- Portal 用戶友善的 `/my` 頁面整合

## Problem Statement

### 現狀問題

1. **安全性不足**：目前的 Token-based 機制允許任何持有連結的人存取，連結外洩風險高
2. **無法追蹤存取者**：匿名存取無法得知是誰在使用分享的設備
3. **權限管理粗糙**：無法針對不同用戶設定不同權限（查看 vs 控制）
4. **缺乏時效控制**：分享一旦建立就永久有效，無法自動過期
5. **Portal 整合不足**：被分享的用戶無法在自己的 Portal 頁面看到被分享的內容

### 為何現在需要

- 企業客戶要求：多租戶場景需要更嚴格的存取控制
- 合規需求：需要能追蹤誰在何時存取了哪些設備
- 用戶體驗：Portal 用戶希望在「我的帳戶」頁面集中管理被分享的設備

## User Stories

### Persona 定義與權限對應

| Persona | 描述 | Odoo 權限對應 | 存取方式 |
|---------|------|--------------|---------|
| **Administrator** | 系統管理員，可設定分享 | `base.group_system` | 直接登入 Odoo Backend |
| **HA Manager** | HA 管理員，可設定分享 | `group_ha_manager` | 直接登入 Odoo Backend |
| **Internal User** | 一般內部用戶 | `base.group_user` | 登入 Odoo Backend 或 Portal |
| **Portal User** | 外部 Portal 用戶 | `base.group_portal` | 登入 Odoo Portal |

---

### Persona 1: Administrator / HA Manager

**US1.1: 設定分享權限**

```
As an Administrator or HA Manager
I want to 將 Entity/Entity Group 分享給特定 Odoo 用戶
So that 我可以控制誰能存取哪些設備
```

**Acceptance Criteria:**

- [ ] Entity 與 Entity Group Form View 有 "Share" 按鈕
- [ ] 點擊後開啟分享設定 Wizard
- [ ] 可選擇要分享給的用戶（支援多選）
- [ ] 可設定權限類型：「僅查看」或「可控制」
- [ ] 可設定過期時間（可選）
- [ ] 分享後用戶立即生效

**US1.2: 管理分享記錄**

```
As an Administrator or HA Manager
I want to 查看和管理已分享的記錄
So that 我可以隨時調整或撤銷分享權限
```

**Acceptance Criteria:**

- [ ] Entity/Entity Group 表單顯示已分享給哪些用戶
- [ ] 可查看每個分享的權限類型和過期時間
- [ ] 可手動撤銷（刪除）分享記錄
- [ ] 可修改現有分享的權限或過期時間

**US1.3: 接收過期提醒**

```
As an Administrator or HA Manager
I want to 在分享即將過期時收到通知
So that 我可以決定是否延長分享期限
```

**Acceptance Criteria:**

- [ ] 過期前 7 天發送提醒通知
- [ ] 通知包含：Entity/Group 名稱、被分享用戶、過期時間
- [ ] 通知可直接連結到分享管理頁面

---

### Persona 2: Internal User / Portal User（被分享者）

**US2.1: 在 Portal 查看被分享的設備**

```
As a Portal User
I want to 在「我的帳戶」頁面看到被分享給我的設備
So that 我可以方便地存取這些設備
```

**Acceptance Criteria:**

- [ ] `/my` 頁面顯示 "Home Assistant" 按鈕/區塊
- [ ] 只顯示有被分享內容的 HA Instance
- [ ] 點擊後進入 `/my/ha/<instance_id>` 頁面
- [ ] 頁面有 Entity 和 Entity Group 兩個分頁
- [ ] 列表顯示設備名稱、狀態、權限類型

**US2.2: 查看 Entity 狀態**

```
As a Portal User with 'view' permission
I want to 查看被分享 Entity 的當前狀態
So that 我可以監控設備運行情況
```

**Acceptance Criteria:**

- [ ] 顯示 Entity 基本資訊：名稱、狀態、最後更新時間
- [ ] 頁面即時更新狀態（Polling 或 WebSocket）
- [ ] 無控制按鈕或控制功能被禁用

**US2.3: 控制 Entity**

```
As a Portal User with 'control' permission
I want to 控制被分享的 Entity
So that 我可以遠端操作設備
```

**Acceptance Criteria:**

- [ ] 顯示控制 UI（Toggle、滑桿等，依 domain 類型）
- [ ] 支援 switch/light/fan/climate/cover/scene/script/automation
- [ ] 控制後狀態即時更新
- [ ] 顯示操作中狀態和錯誤處理

**US2.4: 查看 Entity Group 內容**

```
As a Portal User
I want to 查看被分享 Entity Group 中的所有設備
So that 我可以一次監控多個相關設備
```

**Acceptance Criteria:**

- [ ] 顯示 Group 基本資訊
- [ ] 列表顯示所有包含的 Entities
- [ ] 每個 Entity 根據分享權限顯示對應 UI

---

## Requirements

### Functional Requirements

#### FR1: Model Layer - 分享記錄模型

| ID | Requirement | Priority |
|----|-------------|----------|
| FR1.1 | 建立 `ha.entity.share` 模型 | Must |
| FR1.2 | 欄位：`entity_id` (Many2one to ha.entity, optional) | Must |
| FR1.3 | 欄位：`group_id` (Many2one to ha.entity.group, optional) | Must |
| FR1.4 | 欄位：`user_id` (Many2one to res.users, required) | Must |
| FR1.5 | 欄位：`permission` (Selection: view/control) | Must |
| FR1.6 | 欄位：`expiry_date` (Datetime, optional) | Must |
| FR1.7 | 欄位：`notification_sent` (Boolean, default False) | Must |
| FR1.8 | 約束：`entity_id` 和 `group_id` 必須二選一 | Must |
| FR1.9 | 約束：同一 entity/group + user 組合不可重複 | Must |

**模型設計：**

```python
class HAEntityShare(models.Model):
    _name = 'ha.entity.share'
    _description = 'Entity/Group Share Record'

    entity_id = fields.Many2one('ha.entity', ondelete='cascade')
    group_id = fields.Many2one('ha.entity.group', ondelete='cascade')
    user_id = fields.Many2one('res.users', required=True, ondelete='cascade')
    permission = fields.Selection([
        ('view', 'View Only'),
        ('control', 'Can Control')
    ], required=True, default='view')
    expiry_date = fields.Datetime('Expiry Date')
    notification_sent = fields.Boolean('Expiry Notification Sent', default=False)

    # Computed
    ha_instance_id = fields.Many2one(
        'ha.instance',
        compute='_compute_ha_instance_id',
        store=True
    )
    is_expired = fields.Boolean(compute='_compute_is_expired')

    _sql_constraints = [
        ('entity_or_group_required',
         'CHECK((entity_id IS NOT NULL AND group_id IS NULL) OR (entity_id IS NULL AND group_id IS NOT NULL))',
         'Must specify either entity_id or group_id, not both'),
        ('unique_entity_user',
         'UNIQUE(entity_id, user_id)',
         'Entity already shared with this user'),
        ('unique_group_user',
         'UNIQUE(group_id, user_id)',
         'Group already shared with this user'),
    ]
```

#### FR2: 移除 Token-based 存取

| ID | Requirement | Priority |
|----|-------------|----------|
| FR2.1 | 移除 `/portal/entity/<id>` 的 access_token 驗證 | Must |
| FR2.2 | 移除 `/portal/entity_group/<id>` 的 access_token 驗證 | Must |
| FR2.3 | 改為檢查 `ha.entity.share` 記錄驗證權限 | Must |
| FR2.4 | 未登入用戶導向登入頁面 | Must |
| FR2.5 | 無權限用戶顯示 403 錯誤頁面 | Must |

#### FR3: Controller Layer

| ID | Requirement | Priority |
|----|-------------|----------|
| FR3.1 | 修改 `/portal/entity/<id>` 改為 `auth='user'` | Must |
| FR3.2 | 修改 `/portal/entity_group/<id>` 改為 `auth='user'` | Must |
| FR3.3 | 實作基於 `ha.entity.share` 的權限檢查 | Must |
| FR3.4 | 控制端點檢查用戶是否有 'control' 權限 | Must |
| FR3.5 | 建立 `/my/ha` 路由顯示 HA Instance 列表 | Must |
| FR3.6 | 建立 `/my/ha/<int:instance_id>` 路由顯示分享內容 | Must |
| FR3.7 | 建立 `/my/ha/<int:instance_id>/entities` 分頁 | Must |
| FR3.8 | 建立 `/my/ha/<int:instance_id>/groups` 分頁 | Must |

#### FR4: UI - Share Wizard

| ID | Requirement | Priority |
|----|-------------|----------|
| FR4.1 | 建立 `ha.entity.share.wizard` TransientModel | Must |
| FR4.2 | 支援多用戶選擇 (Many2many to res.users) | Must |
| FR4.3 | 支援權限類型選擇 | Must |
| FR4.4 | 支援過期時間設定 | Should |
| FR4.5 | Entity Form View 的 Share 按鈕呼叫此 Wizard | Must |
| FR4.6 | Entity Group Form View 的 Share 按鈕呼叫此 Wizard | Must |

#### FR5: UI - 分享管理

| ID | Requirement | Priority |
|----|-------------|----------|
| FR5.1 | Entity Form View 顯示已分享用戶列表 | Must |
| FR5.2 | Entity Group Form View 顯示已分享用戶列表 | Must |
| FR5.3 | 可直接在列表中編輯權限和過期時間 | Should |
| FR5.4 | 可刪除分享記錄 | Must |

#### FR6: UI - Portal /my 頁面

| ID | Requirement | Priority |
|----|-------------|----------|
| FR6.1 | `/my` 頁面新增 "Home Assistant" 區塊 | Must |
| FR6.2 | 只顯示有分享內容的 HA Instance | Must |
| FR6.3 | `/my/ha/<instance_id>` 顯示 Entity/Group 分頁 | Must |
| FR6.4 | Entity 分頁顯示被分享的 Entities 列表 | Must |
| FR6.5 | Group 分頁顯示被分享的 Entity Groups 列表 | Must |
| FR6.6 | 列表顯示權限類型和過期時間 | Should |

#### FR7: 通知機制

| ID | Requirement | Priority |
|----|-------------|----------|
| FR7.1 | Cron Job 每日檢查即將過期的分享（7 天內） | Must |
| FR7.2 | 發送 Odoo 內部通知給分享建立者 | Must |
| FR7.3 | 通知內容包含 Entity/Group 名稱、用戶、過期時間 | Must |
| FR7.4 | 標記已發送通知避免重複發送 | Must |
| FR7.5 | Cron Job 清理已過期的分享記錄 | Should |

### Non-Functional Requirements

#### NFR1: Security

| ID | Requirement | Target |
|----|-------------|--------|
| NFR1.1 | 所有 Portal 路由必須 `auth='user'` | Mandatory |
| NFR1.2 | 權限檢查必須驗證 `ha.entity.share` 記錄 | Mandatory |
| NFR1.3 | 控制操作必須驗證 'control' 權限 | Mandatory |
| NFR1.4 | 過期的分享記錄視為無權限 | Mandatory |

#### NFR2: Performance

| ID | Requirement | Target |
|----|-------------|--------|
| NFR2.1 | 權限檢查查詢時間 | < 50ms |
| NFR2.2 | /my/ha 頁面載入時間 | < 2 seconds |
| NFR2.3 | 分享記錄索引 | user_id, entity_id, group_id |

#### NFR3: Compatibility

| ID | Requirement | Target |
|----|-------------|--------|
| NFR3.1 | 瀏覽器支援 | Chrome, Firefox, Safari, Edge (latest 2 versions) |
| NFR3.2 | 響應式設計 | Mobile-friendly |
| NFR3.3 | Odoo 版本 | 18.0 |

## Success Criteria

| Metric | Target | Measurement |
|--------|--------|-------------|
| 分享功能可用率 | 99.9% | 權限驗證成功率 |
| 頁面載入時間 | < 2s | P95 latency |
| 用戶滿意度 | > 4/5 | 使用者回饋 |
| 安全漏洞 | 0 | Security audit |
| 過期通知準確率 | 100% | 通知發送成功率 |

## Technical Architecture

### Data Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    Administrator / HA Manager                    │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐       │
│  │ Entity Form  │ => │ Share Wizard │ => │ ha.entity    │       │
│  │              │    │ - Users      │    │ .share       │       │
│  │              │    │ - Permission │    │ records      │       │
│  │              │    │ - Expiry     │    │              │       │
│  └──────────────┘    └──────────────┘    └──────────────┘       │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼ (Share Record Created)
┌─────────────────────────────────────────────────────────────────┐
│                      Portal User (Shared User)                   │
│                                                                  │
│    /my  =>  /my/ha  =>  /my/ha/<instance_id>                    │
│                                │                                 │
│              ┌─────────────────┼─────────────────┐              │
│              ▼                                   ▼              │
│    ┌──────────────────┐              ┌──────────────────┐       │
│    │  Entities Tab    │              │   Groups Tab     │       │
│    │  - List shared   │              │  - List shared   │       │
│    │  - View/Control  │              │  - View members  │       │
│    └──────────────────┘              └──────────────────┘       │
└─────────────────────────────────────────────────────────────────┘
```

### URL Structure

| Route | Description |
|-------|-------------|
| `/my` | Portal 首頁，顯示 HA 區塊 |
| `/my/ha` | HA Instance 列表（只顯示有分享的） |
| `/my/ha/<int:instance_id>` | 特定 Instance 的分享內容 |
| `/my/ha/<int:instance_id>/entities` | Entity 分頁 |
| `/my/ha/<int:instance_id>/groups` | Entity Group 分頁 |
| `/portal/entity/<int:entity_id>` | Entity 詳細頁面（需登入+權限） |
| `/portal/entity_group/<int:group_id>` | Entity Group 詳細頁面（需登入+權限） |

### Permission Check Flow

```python
def _check_entity_access(self, entity_id, user_id, required_permission='view'):
    """
    Check if user has access to entity.

    Args:
        entity_id: ha.entity record ID
        user_id: res.users record ID
        required_permission: 'view' or 'control'

    Returns:
        bool: True if access granted
    """
    share = self.env['ha.entity.share'].sudo().search([
        ('entity_id', '=', entity_id),
        ('user_id', '=', user_id),
        '|',
        ('expiry_date', '=', False),
        ('expiry_date', '>', fields.Datetime.now())
    ], limit=1)

    if not share:
        return False

    if required_permission == 'control':
        return share.permission == 'control'

    return True  # 'view' permission grants read access
```

## Constraints & Assumptions

### Constraints

1. **Technical**
   - 必須使用 Odoo 18 標準 Portal 機制
   - 分享記錄須支援 Multi-Instance 架構
   - 不能影響現有 Entity/Entity Group 的資料結構

2. **Security**
   - 所有 Portal 路由必須要求登入
   - 權限檢查必須在 Controller 層執行
   - 過期的分享視為無權限

3. **UX**
   - Portal 頁面必須響應式設計
   - 必須與現有 Portal 風格一致

### Assumptions

1. 所有被分享的用戶都有 Odoo 帳號（Internal User 或 Portal User）
2. Administrator 和 HA Manager 了解分享功能的影響
3. Email 服務已正確配置（用於通知）

## Out of Scope

以下功能明確不在本 PRD 範圍內：

1. **匿名存取** - 移除後不再支援無帳號存取
2. **批量分享** - 不支援在列表頁勾選多個 Entity 一次分享
3. **分享連結** - 不再產生可分享的公開連結
4. **歷史資料圖表** - 外部視圖只顯示當前狀態
5. **Mobile App 整合** - 僅 Web 瀏覽器存取
6. **角色繼承** - Entity Group 的分享不自動繼承到 Entity

## Dependencies

### External Dependencies

| Dependency | Type | Description |
|------------|------|-------------|
| Odoo Portal | Module | Portal 機制和模板 |
| mail | Module | 通知功能 |
| Home Assistant | Service | 設備狀態和控制來源 |

### Internal Dependencies

| Dependency | Description |
|------------|-------------|
| ha.entity | 主要分享對象 Model |
| ha.entity.group | 群組分享對象 Model |
| ha.instance | Multi-Instance 支援 |

## Migration Plan

### 資料遷移

由於原有的 Token-based 機制沒有記錄「誰」在使用，無法自動遷移。建議：

1. **通知現有用戶**：在移除前通知所有使用分享連結的情況
2. **手動重新分享**：Administrator 需手動將原本的分享重新設定給具體用戶
3. **保留舊路由一段時間**：舊 `/portal/entity/<id>?access_token=xxx` 顯示友善錯誤訊息，引導用戶登入

### 移除清單

1. `portal.mixin` 的 `access_token` 欄位使用（保留欄位但不使用）
2. `_verify_token()` 相關方法
3. `_get_access_token()` 相關方法
4. Token 驗證相關的錯誤頁面可保留（403/404）

## Implementation WBS

### Phase 1: Model Layer (2 days)

- [ ] 建立 `ha.entity.share` 模型
- [ ] 實作 computed fields (ha_instance_id, is_expired)
- [ ] 實作 SQL constraints
- [ ] 單元測試

### Phase 2: Share Wizard (1 day)

- [ ] 建立 `ha.entity.share.wizard` TransientModel
- [ ] 實作多用戶選擇邏輯
- [ ] 實作權限和過期時間設定
- [ ] 整合到 Entity/Entity Group Form View

### Phase 3: Controller Refactoring (2 days)

- [ ] 修改 `/portal/entity/<id>` 為 `auth='user'`
- [ ] 修改 `/portal/entity_group/<id>` 為 `auth='user'`
- [ ] 實作基於 `ha.entity.share` 的權限檢查
- [ ] 修改控制端點檢查 'control' 權限
- [ ] 移除 Token 驗證相關程式碼
- [ ] 整合測試

### Phase 4: Portal /my Integration (2 days)

- [ ] `/my` 頁面新增 HA 區塊
- [ ] 建立 `/my/ha` Instance 列表頁面
- [ ] 建立 `/my/ha/<instance_id>` 分頁頁面
- [ ] Entity 分頁 UI
- [ ] Entity Group 分頁 UI
- [ ] 響應式樣式

### Phase 5: Share Management UI (1 day)

- [ ] Entity Form View 顯示分享列表
- [ ] Entity Group Form View 顯示分享列表
- [ ] Inline 編輯/刪除功能

### Phase 6: Notification System (1 day)

- [ ] Cron Job：檢查即將過期的分享
- [ ] 發送 Odoo 內部通知
- [ ] 標記已通知記錄
- [ ] (Optional) Cron Job 清理過期記錄

### Phase 7: Testing & Polish (1 day)

- [ ] E2E 測試
- [ ] Security 審查
- [ ] 文件撰寫
- [ ] Bug fixes

## Appendix

### 現有系統參考

現有的 Token-based 分享實作：

- `controllers/portal.py` - Portal Controller（將被修改）
- `models/ha_entity.py` - 繼承 portal.mixin（將保留但不使用 access_token）
- `models/ha_entity_group.py` - 繼承 portal.mixin（將保留但不使用 access_token）

### Field Whitelist (保持不變)

```python
PORTAL_ENTITY_FIELDS = [
    'id', 'name', 'entity_id', 'entity_state',
    'last_changed', 'area_id', 'domain', 'attributes',
]

PORTAL_GROUP_FIELDS = [
    'id', 'name', 'description', 'entity_ids', 'entity_count',
]
```

### 權限類型說明

| Permission | 可查看狀態 | 可控制設備 | 適用場景 |
|------------|-----------|-----------|---------|
| `view` | ✅ | ❌ | 監控、報告用途 |
| `control` | ✅ | ✅ | 操作人員、管理人員 |
