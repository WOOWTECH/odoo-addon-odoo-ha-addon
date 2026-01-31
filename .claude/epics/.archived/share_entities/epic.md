---
name: share_entities
status: completed
created: 2026-01-02T15:47:08Z
updated: 2026-01-03T04:23:57Z
progress: 100%
prd: .claude/prds/share_entities.md
github: https://github.com/WOOWTECH/odoo-addons/issues/2
---

# Epic: share_entities

## Overview

為 `ha.entity` 和 `ha.entity.group` 實作 Portal Access 機制，讓 HA Manager 可以透過標準 Odoo 分享功能將設備資訊分享給外部用戶。

**核心技術方案：**
- 利用 Odoo 標準 `portal.mixin` 提供 Token 機制
- 利用標準 `portal.share` Wizard 處理分享 UI
- 使用 Polling (5 秒) 作為 MVP 的即時更新方案
- 最大化複用現有架構，最小化新增代碼

## Architecture Decisions

### AD1: 使用標準 portal.mixin
**決策：** 直接繼承 `portal.mixin`，不自定義 Token 機制

**理由：**
- `portal.mixin` 已提供 `access_token` 欄位和 `_portal_ensure_token()` 方法
- Token 產生邏輯經過驗證，安全性有保障
- 與標準 `portal.share` Wizard 無縫整合

### AD2: MVP 使用 Polling 而非 WebSocket
**決策：** Portal 頁面使用 5 秒輪詢更新狀態，不整合現有 Bus 機制

**理由：**
- 現有 `ha_realtime_update.py` 只支援已登入的 `res.users`
- 修改 Bus 架構風險高，Polling 實現簡單
- 5 秒延遲對外部用戶可接受
- 後續可升級為 WebSocket (非 MVP 範圍)

### AD3: sudo() 繞過 ir.rule
**決策：** Portal Controller 使用 `sudo()` 讀取資料，繞過多實例過濾

**理由：**
- `ha.current.instance.filter.mixin` 會阻擋匿名用戶存取
- Token 已提供足夠的存取控制
- 需在 Controller 層實施 field whitelist

### AD4: 複用標準 portal.share Wizard
**決策：** 不建立自定義分享 Wizard，直接使用 Odoo 標準 `portal.share`

**理由：**
- 減少代碼量，降低維護成本
- 標準 UI/UX 使用者熟悉
- 自動整合 Email 邀請功能

### AD5: Portal Entity Control 使用白名單機制 *(v1.1 新增)*
**決策：** 控制端點使用 domain + action 雙重白名單，僅支援 switch/light/fan 的基本操作

**理由：**
- 安全性：限制可控制的設備類型和動作，防止未授權操作
- 簡單性：只支援 toggle/turn_on/turn_off，不支援複雜動作如 set_brightness
- Token 驗證使用 constant-time comparison 防止 timing attack
- 與現有 WebSocket API 整合，複用 `call_websocket_api` 方法

**白名單定義：**
```python
PORTAL_CONTROL_SERVICES = {
    'switch': ['toggle', 'turn_on', 'turn_off'],
    'light': ['toggle', 'turn_on', 'turn_off'],
    'fan': ['toggle', 'turn_on', 'turn_off'],
}
```

## Technical Approach

### Backend Changes

#### Models (2 files修改)
```python
# models/ha_entity.py - 新增 portal.mixin
class HAEntity(models.Model):
    _inherit = ['ha.current.instance.filter.mixin', 'mail.thread',
                'mail.activity.mixin', 'portal.mixin']

    def _compute_access_url(self):
        for record in self:
            record.access_url = f'/portal/entity/{record.id}'

# models/ha_entity_group.py - 同上
```

#### Controller (1 新檔案)
```python
# controllers/portal.py
class HAPortalController(http.Controller):
    # Token 驗證支援兩種方式（header 優先）：
    # - X-Portal-Token header（推薦）
    # - access_token query/body param（向後相容）

    @http.route('/portal/entity/<int:entity_id>', auth='public')
    def portal_entity(self, entity_id, access_token=None, **kw):
        # 1. Token validation (header or param)
        # 2. sudo().read() with whitelist
        # 3. Render template

    @http.route('/portal/entity/<int:entity_id>/state', type='json', auth='public')
    def portal_entity_state(self, entity_id, **kw):
        # Polling endpoint - returns JSON
        # Token via X-Portal-Token header

    @http.route('/portal/entity/<int:entity_id>/control', type='json', auth='public')
    def portal_entity_control(self, entity_id, action=None, **kw):
        # 1. Token validation (constant-time, header or param)
        # 2. Action whitelist check (PORTAL_CONTROL_SERVICES)
        # 3. Call WebSocket API
        # 4. Return updated entity state
```

#### Manifest
```python
# __manifest__.py
'depends': ['base', 'web', 'mail', 'portal'],  # 新增 'portal'
```

### Frontend Changes

#### Portal Templates (1 新檔案)
```xml
<!-- views/portal_templates.xml -->
<template id="portal_entity" inherit_id="portal.portal_layout">
    <!-- Entity info, Chatter, polling JS -->
</template>

<template id="portal_entity_group">
    <!-- Group info, Entity list -->
</template>
```

#### Internal UI (2 files修改)
```xml
<!-- views/ha_entity_views.xml - 新增 Share 按鈕 -->
<button name="action_share" type="object" string="Share"/>

<!-- views/ha_entity_group_views.xml - 同上 -->
```

#### Polling JavaScript (內嵌於 Template)
```javascript
// 5秒輪詢更新狀態（使用 X-Portal-Token header）
setInterval(() => {
    fetch(`/portal/entity/${entityId}/state`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-Portal-Token': token
        },
        body: JSON.stringify({ jsonrpc: '2.0', method: 'call', params: {}, id: Date.now() })
    })
    .then(res => res.json())
    .then(data => updateUI(data.result));
}, 5000);
```

## Implementation Strategy

### Phase 1: Foundation (Model + Manifest)
1. 新增 `portal` 依賴到 `__manifest__.py`
2. `ha.entity` 繼承 `portal.mixin`，實作 `_compute_access_url`
3. `ha.entity.group` 同上
4. 測試 Token 產生功能

### Phase 2: Controller + Templates
1. 建立 `controllers/portal.py`
2. 實作 Token 驗證邏輯
3. 建立 Portal QWeb Templates
4. 測試匿名存取

### Phase 3: UI Integration
1. Form View 新增 Share 按鈕
2. 整合 `portal.share` Wizard
3. 實作 Polling 機制
4. E2E 測試

## Task Breakdown Preview

| # | Task | 描述 | 預估 |
|---|------|------|------|
| 1 | Model Layer | 新增 portal.mixin、_compute_access_url | 0.5d |
| 2 | Portal Controller | routes、Token 驗證、Polling endpoint | 1d |
| 3 | Portal Templates | Entity + Group QWeb templates | 1d |
| 4 | Share Button UI | Form View 按鈕、整合 portal.share | 0.5d |
| 5 | Polling Frontend | JavaScript auto-refresh | 0.5d |
| 6 | Testing | Unit tests、Integration tests、文件 | 0.5d |
| 7 | Portal Entity Control | 控制端點、action 白名單、Control Card UI | 0.5d |

**Total: 7 tasks, ~4.5 days**

## Dependencies

### External (Module)
| Dependency | Required | Notes |
|------------|----------|-------|
| `portal` | Yes | 需新增到 manifest |
| `mail` | Already | 已存在 |

### Internal (Code)
| Dependency | Impact |
|------------|--------|
| `ha.current.instance.filter.mixin` | sudo() 繞過 |
| `ha_realtime_update.py` | 不修改，使用 Polling |

## Success Criteria (Technical)

| Criteria | Verification |
|----------|--------------|
| Token 產生正確 | 32+ 字元，安全隨機 |
| 匿名存取成功 | 無痕模式可開啟 |
| Field whitelist 有效 | 敏感欄位不暴露 |
| Polling 正常 | 5 秒更新一次 |
| Share Wizard 整合 | 標準 UI 可用 |
| Control 白名單有效 | 只允許 switch/light/fan + toggle/turn_on/turn_off |
| Control UI 正常 | Toggle 按鈕顯示正確狀態，控制後即時更新 |

## Estimated Effort

| Phase | Effort |
|-------|--------|
| Model Layer | 0.5 day |
| Controller | 1 day |
| Templates | 1 day |
| UI Integration | 0.5 day |
| Polling | 0.5 day |
| Testing | 0.5 day |
| Portal Entity Control | 0.5 day |
| **Total** | **4.5 days** |

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| portal.mixin 與現有 mixin 衝突 | 調整繼承順序，portal.mixin 放最後 |
| sudo() 資料洩漏 | 嚴格實施 field whitelist |
| Polling 效能 | 限制 Entity Group 最多 100 entities |
| 未授權設備控制 | domain + action 雙重白名單，constant-time token 驗證 |

## Files to Create/Modify

### New Files
- `controllers/portal.py` - Portal controller
- `views/portal_templates.xml` - QWeb templates

### Modified Files
- `__manifest__.py` - 新增 'portal' dependency
- `models/ha_entity.py` - 新增 portal.mixin
- `models/ha_entity_group.py` - 新增 portal.mixin
- `views/ha_entity_views.xml` - Share 按鈕
- `views/ha_entity_group_views.xml` - Share 按鈕

## Tasks Created

| # | Issue | Task Name | Status | Dependencies |
|---|-------|-----------|--------|--------------|
| 1 | [#3](https://github.com/WOOWTECH/odoo-addons/issues/3) | Model Layer - Add portal.mixin | closed | - |
| 2 | [#4](https://github.com/WOOWTECH/odoo-addons/issues/4) | Portal Controller - Routes and Token Validation | closed | #3 |
| 3 | [#5](https://github.com/WOOWTECH/odoo-addons/issues/5) | Portal Templates - QWeb Views | closed | #4 |
| 4 | [#6](https://github.com/WOOWTECH/odoo-addons/issues/6) | Share Button UI - Form View Integration | closed | #3 |
| 5 | [#7](https://github.com/WOOWTECH/odoo-addons/issues/7) | Polling Frontend - Auto-refresh JavaScript | closed | #4, #5 |
| 6 | [#8](https://github.com/WOOWTECH/odoo-addons/issues/8) | Testing and Documentation | closed | #3-#7 |
| 7 | [#10](https://github.com/WOOWTECH/odoo-addons/issues/10) | Portal Entity Control | closed | #3-#8 |

**Total: 7 tasks (7 closed, 0 open)**
