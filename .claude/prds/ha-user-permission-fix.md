---
name: ha-user-permission-fix
description: 修復 ha_user 被加入 Entity Group 後無法存取 ha.instance 的 regression bug
status: complete
created: 2026-01-18T08:11:00Z
updated: 2026-01-18T09:29:06Z
priority: P0
type: bug-fix
---

# PRD: ha_user 權限修復

## Executive Summary

這是一個 **P0 優先順序的 regression bug**。當 ha_user 被加入某個 Entity Group 的 `user_ids` 後，應該能夠在 `ha_instance_dashboard` 看到相關內容，但目前會出現權限錯誤。此功能以前正常運作，與 Portal 功能無關。

## Glossary

| 術語 | 定義 |
|------|------|
| ha_user | 擁有 `group_ha_user` 群組的 Odoo 使用者，具有有限的 HA 存取權限 |
| ha_manager | 擁有 `group_ha_manager` 群組的 Odoo 使用者，具有完整的 HA 管理權限 |
| Entity Group | `ha.entity.group` 模型，用於將多個 entity 分組並授權給特定用戶 |
| ir.rule | Odoo 的 record-level security 機制，控制使用者可存取的記錄 |

## Problem Statement

### 問題現象

ha_user 已被加入某個 Entity Group 的 `user_ids` 後，嘗試存取 `ha_instance_dashboard` 時出現以下錯誤：

```
You are not allowed to access 'Home Assistant Instance' (ha.instance) records.
This operation is allowed for the following groups:
- Administration/Home Assistant Manager
- Administration/Home Assistant User
```

### 問題本質

- 這是 **regression bug**（以前正常運作的功能現在失效）
- 與 Portal 功能無關
- 影響所有被授權的 ha_user 用戶

## User Stories

### US1: ha_user 存取授權實例

```
As a ha_user who has been added to an Entity Group
I want to see the related HA instance in the dashboard
So that I can monitor and control the devices I'm authorized to access
```

**Acceptance Criteria:**
- 被加入 Entity Group 後**立即**可以看到內容
- 不需要重新登入或等待
- 只能看到被授權的 Entity Group 相關實例

### US2: ha_manager 權限不受影響

```
As a ha_manager
I want my existing permissions to remain unchanged
So that I can continue to manage all instances
```

**Acceptance Criteria:**
- ha_manager 的所有權限維持不變
- 不會因為此修復造成其他問題

## Requirements

### Functional Requirements

| ID | 需求 | 優先順序 |
|----|------|---------|
| FR1 | ha_user 加入 Entity Group 後立即可存取對應 instance | P0 |
| FR2 | ha_user 只能看到授權的 instance（不能超權） | P0 |
| FR3 | ha_manager 權限維持不變 | P0 |
| FR4 | 無需重新登入即可生效 | P1 |

### Non-Functional Requirements

| ID | 需求 | 目標 |
|----|------|------|
| NFR1 | 權限檢查效能 | < 100ms |
| NFR2 | 快取一致性 | 權限變更後首次請求即生效（< 5 秒） |
| NFR3 | 向後相容 | 不破壞現有配置 |

## Technical Analysis

### 可能原因

1. **ir.rule 快取延遲**
   - Odoo 18 的 rule invalidation 機制可能未即時更新
   - 當 `user_ids` 變更時，`user.ha_entity_group_ids` 可能未同步更新

2. **Rule 配置問題**
   - `security/security.xml` 中的規則可能有邏輯錯誤

3. **API 端點問題**
   - `controllers/controllers.py:1247` 的 `get_instances()` 可能未正確處理權限

### 相關檔案

| 檔案 | 行號 | 說明 |
|------|------|------|
| `security/security.xml` | 34-45 | ha_instance ir.rule |
| `security/ir.model.access.csv` | 2-3 | ha.instance 訪問規則 |
| `models/res_users.py` | 18 | `ha_entity_group_ids` 多對多關係定義 |
| `controllers/controllers.py` | 1247 | `get_instances()` RPC 端點 |
| `static/src/actions/ha_instance_dashboard/ha_instance_dashboard.js` | 56 | `loadInstances()` 方法 |

### 相關 ir.rule 配置

**位置**：`security/security.xml:34-45`

```xml
<!-- 規則 1: HA User 可以看到有權限 groups 的實例 (只讀) -->
<record id="ha_instance_user_rule" model="ir.rule">
    <field name="name">HA Instance: User Access (via Groups)</field>
    <field name="model_id" ref="model_ha_instance"/>
    <field name="domain_force">[
        ('id', 'in', user.ha_entity_group_ids.mapped('ha_instance_id').ids)
    ]</field>
    <field name="groups" eval="[(4, ref('group_ha_user'))]"/>
    <field name="perm_read" eval="True"/>
    <field name="perm_write" eval="False"/>
    <field name="perm_create" eval="False"/>
    <field name="perm_unlink" eval="False"/>
</record>
```

## Proposed Solutions

### 方案 1：觸發 rule 快取清除（推薦）

在 `ha.entity.group.user_ids` 的 inverse 方法中觸發 rule 快取清除：

```python
def _inverse_user_ids(self):
    # ... existing logic ...
    self.env['ir.rule'].clear_caches()
```

**優點**：最小改動，針對性強
**缺點**：每次變更都會清除快取

### 方案 2：修改 ir.rule domain_force

使用更直接的查詢語法：

```python
domain_force="[('id', 'in', user.ha_entity_group_ids.ha_instance_id.ids)]"
```

**優點**：可能解決 ORM 解析問題
**缺點**：需要驗證語法正確性

### 方案 3：在 get_instances() 中手動過濾

```python
def get_instances(self):
    user = request.env.user
    allowed_instances = user.ha_entity_group_ids.mapped('ha_instance_id')
    instances = request.env['ha.instance'].sudo().browse(allowed_instances.ids)
    # ... rest of logic ...
```

**優點**：繞過 ir.rule 問題
**缺點**：需要維護額外邏輯

## Success Criteria

| 驗收項目 | 驗證方式 |
|---------|---------|
| ha_user 加入 Entity Group 後立即可存取 | Playwright MCP E2E 測試 |
| 不需要重新登入或等待 | Playwright MCP E2E 測試（連續操作驗證） |
| ha_user 只能看到被授權的實例 | 後端單元測試 (`test_security.py`) |
| ha_manager 權限不受影響 | 後端單元測試（回歸測試） |
| 新增對應的測試案例 | Code review |

## Investigation Steps

1. **確認使用者設定**
   - 驗證 ha_user 確實在 Entity Group 的 `user_ids` 中
   - 檢查 `res.users` 模型中 `ha_entity_group_ids` 欄位的值

2. **檢查 ir.rule 快取**
   ```python
   # 在 Odoo shell 中執行
   env['ir.rule'].clear_caches()
   env['ha.instance'].search([])
   ```

3. **驗證 API 端點**
   - 以 ha_user 身份呼叫 `get_instances()` RPC
   - 檢查返回值或錯誤訊息

4. **檢查最近 commit**
   - 調查是否有權限相關改動導致 regression

## Test Plan

### Playwright MCP 自動化驗證

使用 Playwright MCP 進行 E2E 測試，驗證完整使用者流程。

**⚠️ 前置條件**：
- 必須先將 worktree 變更同步到 main 專案（見 [Development Environment](#development-environment)）
- 確認 Docker container 已重啟並載入最新程式碼

**測試環境**：
- URL: `http://localhost`
- Database: `odoo`
- 測試帳號: `admin` / `admin` (管理者), `ha_user` (測試用戶)

**測試流程**：

```
1. 以 admin 登入
   - browser_navigate → http://localhost/web/login
   - browser_fill_form → 帳號密碼
   - browser_click → 登入按鈕

2. 將 ha_user 加入 Entity Group
   - 導航到 Entity Group 編輯頁面
   - 新增用戶到 user_ids

3. 登出並以 ha_user 登入
   - 登出 admin
   - 以 ha_user 登入

4. 驗證 ha_instance_dashboard 存取
   - browser_navigate → /web#action=ha_instance_dashboard
   - browser_snapshot → 確認頁面內容
   - 驗證：應該看到被授權的 instance，不應出現權限錯誤
```

**驗證點**：
- [ ] 無 "You are not allowed to access" 錯誤
- [ ] 可以看到被授權的 instance 卡片
- [ ] 可以點擊進入 instance 詳情

### 負面測試案例

| 測試案例 | 預期結果 | 驗證方式 |
|---------|---------|---------|
| 未授權用戶嘗試存取 instance | 顯示權限錯誤 | Playwright MCP |
| 用戶被移除 Entity Group 後 | 無法再存取該 instance | Playwright MCP |
| ha_user 嘗試修改 instance 設定 | 失敗（只有讀取權限） | 後端單元測試 |

### 後端單元測試

新增測試案例於 `tests/test_security.py`：

```python
def test_ha_user_can_access_instance_after_group_assignment(self):
    """ha_user should see instance immediately after being added to group"""
    # 1. Create entity group
    # 2. Add ha_user to group
    # 3. Verify ha_user can read instance

def test_ha_user_cannot_access_instance_without_group(self):
    """ha_user should NOT see instance if not in any group"""
    # 1. Ensure ha_user is not in any group
    # 2. Verify ha_user cannot read instance

def test_ha_user_loses_access_after_group_removal(self):
    """ha_user should lose access after being removed from group"""
    # 1. Add ha_user to group
    # 2. Verify ha_user can read instance
    # 3. Remove ha_user from group
    # 4. Verify ha_user cannot read instance
```

## Out of Scope

- Portal 相關功能修改
- ha_manager 權限變更
- 新增權限層級
- UI/UX 改進

## Development Environment

### Worktree 開發

開發將在 git worktree 中進行：

| 項目 | 說明 |
|------|------|
| **Worktree 名稱** | `ha-user-permission-fix` |
| **Worktree 相對路徑** | `../odoo-server.worktrees/ha-user-permission-fix` |
| **Main 專案相對路徑** | `../odoo-server` (從 worktree 目錄) |
| **Addon 路徑** | `data/18/addons/odoo_ha_addon` |

### Worktree 同步指令

開發完成後，需要同步到主專案才能進行 Docker 測試。請根據您的環境設定變數：

```bash
# 設定變數（請根據您的環境調整）
MAIN_PROJECT="<your-main-project-path>"  # Main odoo-server 目錄
WORKTREE="<your-worktree-path>"          # Worktree 目錄
ADDON_PATH="data/18/addons/odoo_ha_addon"

# 同步 git 追蹤的檔案到主專案並重啟
cd "$WORKTREE" && git ls-files "$ADDON_PATH" | rsync -av --files-from=- "$WORKTREE/" "$MAIN_PROJECT/" && \
cd "$MAIN_PROJECT" && docker compose restart web
```

**注意**：
- E2E 測試前**必須**先執行同步
- Docker 掛載的是 main 專案目錄，不是 worktree
- 同步後重啟 web container 才會載入新程式碼

## Dependencies

- 無外部依賴
- 需要 Odoo 18 環境進行測試

## Constraints

- 必須向後相容現有配置
- 不能影響 ha_manager 權限
- 修復必須即時生效（無需重新登入）

## Risk Assessment

| 風險 | 可能性 | 影響 | 緩解措施 |
|------|--------|------|---------|
| 快取清除影響效能 | 中 | 中 | 限制清除範圍，只清除受影響的規則 |
| ha_manager 權限受影響 | 低 | 高 | 執行完整回歸測試套件 |
| 修改 ir.rule 語法導致解析錯誤 | 低 | 高 | 同步到 main 後先行測試 |

## Rollback Plan

如果修復造成問題：

1. **立即回滾**：
   ```bash
   git revert HEAD
   # 同步到 main 並重啟
   ```

2. **驗證回滾**：
   - 確認 ha_manager 權限正常
   - 確認系統穩定運作

3. **通知相關人員**：
   - 更新 Issue 狀態
   - 記錄失敗原因供後續分析

## Estimated Effort

| 任務 | 預估時間 |
|------|---------|
| 調查根因 | 1 小時 |
| 實作修復 | 1 小時 |
| 測試驗證 | 1 小時 |
| **總計** | **3 小時** |
