---
name: user-based-entity-sharing
status: backlog
created: 2026-01-16T16:27:56Z
updated: 2026-01-17T00:48:55Z
progress: 0%
prd: .claude/prds/user-based-entity-sharing.md
github: https://github.com/WOOWTECH/odoo-addons/issues/46
---

# Epic: User-Based Entity Sharing

## Overview

將現有的 Entity/Entity Group 分享機制從 Token-based 匿名存取改為 User-based 登入存取。主要工作包括：

1. **新增 `ha.entity.share` 模型** - 記錄分享關係、權限類型、過期時間
2. **修改 Portal Controller** - 從 `auth='public'` + token 驗證改為 `auth='user'` + share 記錄驗證
3. **建立 Share Wizard** - 讓管理員設定分享對象、權限、過期時間
4. **Portal /my 頁面整合** - 讓被分享者在 `/my` 看到並存取被分享的設備
5. **通知機制** - 過期前 7 天發送提醒

## Architecture Decisions

### AD1: 使用獨立的 `ha.entity.share` 模型而非 Many2many

**決定**: 建立獨立的 `ha.entity.share` 模型

**理由**:
- 需要儲存額外屬性（permission, expiry_date, notification_sent）
- 便於查詢「某用戶被分享的所有 entity」
- 便於實作過期通知追蹤

### AD2: 保留但不使用 `portal.mixin` 的 `access_token`

**決定**: 保留 `portal.mixin` 繼承，但不再使用 `access_token` 欄位

**理由**:
- 避免移除 mixin 造成的遷移問題
- Chatter 功能仍需要 `mail.thread`
- 未來如需恢復 token 機制較容易

### AD3: 複用現有 Portal Templates

**決定**: 修改現有 `portal_templates.xml` 而非建立新模板

**理由**:
- 現有 OWL 組件（PortalEntityInfo, PortalEntityController, PortalGroupInfo）可複用
- 只需移除 `accessToken` 相關參數，改用 session-based 驗證
- 控制 UI 只需根據 `permission` 欄位決定是否顯示

### AD4: `/my/ha` 頁面結構

**決定**: `/my` → `/my/ha` → `/my/ha/<instance_id>` (含 Entity/Group 分頁)

**理由**:
- 符合 Odoo Portal 標準結構
- 支援 Multi-Instance 架構
- 用戶只看到有被分享內容的 Instance

## Technical Approach

### Backend Changes

#### 1. Model Layer (`models/ha_entity_share.py`)
```python
class HAEntityShare(models.Model):
    _name = 'ha.entity.share'
    _description = 'Entity/Group Share Record'

    entity_id = fields.Many2one('ha.entity', ondelete='cascade')
    group_id = fields.Many2one('ha.entity.group', ondelete='cascade')
    user_id = fields.Many2one('res.users', required=True, ondelete='cascade')
    permission = fields.Selection([('view', 'View Only'), ('control', 'Can Control')])
    expiry_date = fields.Datetime()
    notification_sent = fields.Boolean(default=False)

    # Computed
    ha_instance_id = fields.Many2one('ha.instance', compute='_compute_ha_instance_id', store=True)
    is_expired = fields.Boolean(compute='_compute_is_expired')
```

#### 2. Controller Layer (`controllers/portal.py`)

修改重點：
- 將 `auth='public'` 改為 `auth='user'`
- 移除 `_verify_token()` 方法
- 新增 `_check_share_access(entity_id, user_id, permission)` 方法
- 控制端點額外檢查 `permission == 'control'`

新增路由：
- `GET /my/ha` - HA Instance 列表
- `GET /my/ha/<int:instance_id>` - Instance 詳細頁 (Entity/Group 分頁)

#### 3. Wizard Layer (`wizards/ha_entity_share_wizard.py`)

```python
class HAEntityShareWizard(models.TransientModel):
    _name = 'ha.entity.share.wizard'

    user_ids = fields.Many2many('res.users')
    permission = fields.Selection([('view', 'View'), ('control', 'Control')])
    expiry_date = fields.Datetime()

    def action_share(self):
        # 為每個用戶建立 ha.entity.share 記錄
```

### Frontend Changes

#### 1. Portal Templates 修改

- 移除 `accessToken` 參數傳遞
- 控制 Card 根據 `permission` 決定是否顯示
- 新增 `/my/ha` 相關模板

#### 2. OWL 組件調整

- `PortalEntityController`: 移除 token header，改用 session cookie
- 新增 `permission` prop 決定是否啟用控制

### Infrastructure

#### Cron Jobs (`data/cron.xml`)

```xml
<!-- 每日檢查即將過期的分享 -->
<record id="ir_cron_check_expiring_shares" model="ir.cron">
    <field name="name">Check Expiring Entity Shares</field>
    <field name="model_id" ref="model_ha_entity_share"/>
    <field name="code">model._cron_check_expiring_shares()</field>
    <field name="interval_number">1</field>
    <field name="interval_type">days</field>
</record>
```

## Implementation Strategy

### 簡化策略

1. **複用現有程式碼**: 最大程度複用現有 Portal templates 和 OWL 組件
2. **增量修改**: 先加新功能，再移除舊功能，確保平滑過渡
3. **測試先行**: 先修改現有測試，再實作功能

### 風險緩解

1. **向後相容**: 舊的 token URL 顯示友善錯誤訊息，引導用戶登入
2. **權限檢查**: 在 Controller 層統一檢查，避免遺漏

## Task Breakdown Preview

將 PRD 的 7 個 Phase 整合為 6 個精簡任務：

- [ ] **Task 1: Model & Security** - `ha.entity.share` 模型 + access rules + 單元測試
- [ ] **Task 2: Share Wizard & Form UI** - Wizard + Entity/Group Form 分享列表顯示
- [ ] **Task 3: Controller Refactoring** - 移除 token 驗證，改用 share 記錄驗證
- [ ] **Task 4: Portal /my Integration** - `/my/ha` 路由和模板
- [ ] **Task 5: Notification System** - Cron job + 過期提醒通知
- [ ] **Task 6: Testing & QA** - E2E 測試 + Security 審查 + 文件更新

## Dependencies

### 現有程式碼依賴

| File | 變更類型 | 說明 |
|------|---------|------|
| `models/__init__.py` | 新增 | import ha_entity_share |
| `models/ha_entity_share.py` | 新增 | 新模型 |
| `wizards/__init__.py` | 新增 | 新目錄 |
| `wizards/ha_entity_share_wizard.py` | 新增 | Share Wizard |
| `controllers/portal.py` | 修改 | auth 改為 user，權限檢查邏輯 |
| `views/portal_templates.xml` | 修改 | 移除 accessToken，新增 /my/ha 模板 |
| `views/ha_entity_views.xml` | 修改 | 加入分享列表 One2many |
| `views/ha_entity_group_views.xml` | 修改 | 加入分享列表 One2many |
| `security/ir.model.access.csv` | 修改 | 新增 ha.entity.share 權限 |
| `data/cron.xml` | 修改 | 新增過期檢查 cron |
| `static/src/portal/*.js` | 修改 | 移除 token header |
| `tests/test_portal_*.py` | 修改 | 更新測試 |

### External Dependencies

- Odoo Portal module (已存在)
- mail module (已存在)

## Success Criteria (Technical)

| Criteria | Target | 驗證方式 |
|----------|--------|---------|
| 所有 Portal 路由需登入 | 100% | 未登入用戶被導向 `/web/login` |
| 權限檢查正確 | 100% | 無權限用戶看到 403 |
| 控制權限正確 | 100% | view 權限用戶無法控制設備 |
| 過期處理正確 | 100% | 過期分享無法存取 |
| 通知發送正確 | 100% | 過期前 7 天收到通知 |
| 測試通過 | 100% | 所有單元測試和整合測試通過 |

## Estimated Effort

| Task | 預估時間 |
|------|---------|
| Task 1: Model & Security | 1 天 |
| Task 2: Share Wizard & Form UI | 1 天 |
| Task 3: Controller Refactoring | 1.5 天 |
| Task 4: Portal /my Integration | 1.5 天 |
| Task 5: Notification System | 0.5 天 |
| Task 6: Testing & QA | 1 天 |
| **Total** | **6.5 天** |

## Tasks Created

- [ ] #47 - Model & Security - ha.entity.share (parallel: true)
- [ ] #48 - Share Wizard & Form UI (parallel: false, depends_on: [47])
- [ ] #49 - Controller Refactoring - User-based Auth (parallel: false, depends_on: [47])
- [ ] #50 - Portal /my Integration (parallel: false, depends_on: [47, 49])
- [ ] #51 - Notification System - Expiry Reminder (parallel: true, depends_on: [47])
- [ ] #52 - Testing & QA (parallel: false, depends_on: [47, 48, 49, 50, 51])

**Summary:**
- Total tasks: 6
- Parallel tasks: 2 (#47, #51)
- Sequential tasks: 4 (#48, #49, #50, #52)
- Estimated total effort: 52 hours (~6.5 days)

**Execution Order:**
```
       ┌─────────────────────────────────────────┐
       │          #47: Model & Security          │ ← Start here
       └─────────────────┬───────────────────────┘
                         │
         ┌───────────────┼───────────────┐
         ▼               ▼               ▼
   ┌───────────┐   ┌───────────┐   ┌───────────┐
   │ #48:      │   │ #49:      │   │ #51:      │ ← Can run in parallel
   │ Wizard    │   │ Controller│   │ Notif.    │
   └─────┬─────┘   └─────┬─────┘   └───────────┘
         │               │
         │               ▼
         │         ┌───────────┐
         │         │ #50:      │
         │         │ Portal /my│
         │         └─────┬─────┘
         │               │
         └───────────────┼───────────────────────┐
                         ▼                       │
                   ┌───────────┐                 │
                   │ #52:      │ ← Final step    │
                   │ Testing   │ ←───────────────┘
                   └───────────┘
```

## Notes

### 移除清單

完成後需移除/清理的程式碼：

1. `controllers/portal.py`:
   - `_verify_token()` 方法
   - `_get_access_token()` 方法
   - `_verify_entity_access()` 中的 token 邏輯
   - `_verify_group_access()` 中的 token 邏輯

2. `views/portal_templates.xml`:
   - `accessToken` 參數傳遞

3. `static/src/portal/*.js`:
   - `X-Portal-Token` header 設定

4. `tests/test_portal_*.py`:
   - Token 相關測試案例
