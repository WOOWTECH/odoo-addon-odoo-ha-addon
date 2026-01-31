---
name: ha-user-permission-fix
status: completed
created: 2026-01-18T09:34:34Z
updated: 2026-01-18T10:10:17Z
progress: 100%
prd: .claude/prds/ha-user-permission-fix.md
github: https://github.com/WOOWTECH/odoo-addons/issues/59
---

# Epic: ha_user 權限修復

## Overview

修復 ha_user 被加入 Entity Group 後無法存取 `ha.instance` 的 regression bug。這是 P0 優先順序的問題，需要調查 ir.rule 快取機制或 domain_force 配置，並確保權限變更後首次請求即生效。

## Glossary

| 術語 | 定義 |
|------|------|
| ha_user | 擁有 `group_ha_user` 群組的 Odoo 使用者，具有有限的 HA 存取權限 |
| ha_manager | 擁有 `group_ha_manager` 群組的 Odoo 使用者，具有完整的 HA 管理權限 |
| Entity Group | `ha.entity.group` 模型，用於將多個 entity 分組並授權給特定用戶 |
| ir.rule | Odoo 的 record-level security 機制，控制使用者可存取的記錄 |

## Architecture Decisions

### 採用方案：ir.rule 快取清除 + domain_force 語法檢查

1. **主要修復**：檢查並修正 `security/security.xml` 中的 domain_force 語法
2. **輔助修復**：在 user_ids 變更時確保 ir.rule 快取正確清除
3. **不採用**：在 controller 中手動過濾（會繞過權限系統，不是正確做法）

### 技術依據

- ir.rule 是 Odoo 的標準權限控制機制，應該優先確保其正確運作
- `.mapped()` 在 domain_force 中可能有評估問題，需要驗證
- 快取清除是保險措施，確保權限變更立即生效

## Technical Approach

### Backend 修復

**檔案 1：`security/security.xml`**
- 檢查 `ha_instance_user_rule` 的 domain_force 語法
- 驗證 `user.ha_entity_group_ids.mapped('ha_instance_id').ids` 是否正確

**檔案 2：`models/ha_entity_group.py` 或 `models/res_users.py`**
- 確認 user_ids 關聯變更時 ir.rule 快取是否正確清除
- 如有需要，加入 `env['ir.rule'].clear_caches()` 呼叫

### 驗證層面

**E2E 測試：Playwright MCP**
- 正向測試：ha_user 加入 group 後立即可存取
- 負向測試：未授權用戶無法存取、移除權限後無法存取

**後端單元測試：`tests/test_security.py`**
- `test_ha_user_can_access_instance_after_group_assignment`
- `test_ha_user_cannot_access_instance_without_group`
- `test_ha_user_loses_access_after_group_removal`

## Implementation Strategy

### 開發階段

1. **調查階段**：確認 ir.rule 是否為根因
2. **修復階段**：修正 security.xml 或快取邏輯
3. **測試階段**：Playwright MCP + 後端單元測試

### 風險控制

| 風險 | 可能性 | 影響 | 緩解措施 |
|------|--------|------|---------|
| 快取清除影響效能 | 中 | 中 | 限制清除範圍 |
| ha_manager 權限受影響 | 低 | 高 | 完整回歸測試 |
| ir.rule 語法錯誤 | 低 | 高 | 同步到 main 後先測試 |

### Rollback Plan

1. **立即回滾**：`git revert HEAD` 並重啟 Docker
2. **驗證回滾**：確認 ha_manager 權限正常
3. **通知相關人員**：更新 Issue 狀態

## Task Breakdown Preview

此 bug 修復只需 **2 個任務**：

- [ ] **Task 1: 調查與修復** - 確認根因並修正 security.xml 或快取機制
- [ ] **Task 2: 測試與驗證** - Playwright MCP E2E 測試 + 後端單元測試

## Dependencies

- Odoo 18 開發環境
- Worktree `ha-user-permission-fix` 設置
- 無外部依賴

## Success Criteria (Technical)

| 項目 | 驗證方式 |
|------|---------|
| ha_user 加入 Entity Group 後立即可存取 | Playwright MCP E2E 測試 |
| 權限變更後首次請求即生效（< 5 秒） | Playwright MCP E2E 測試 |
| ha_user 只能看到被授權的實例 | 後端單元測試 |
| ha_manager 權限不受影響 | 後端單元測試（回歸） |
| 未授權用戶無法存取 | 負面測試案例 |
| 權限移除後無法存取 | 負面測試案例 |

## Estimated Effort

| 任務 | 預估時間 |
|------|---------|
| Task 1: 調查與修復 | 1.5 小時 |
| Task 2: 測試與驗證 | 1 小時 |
| **總計** | **2.5 小時** |

## Development Environment

| 項目 | 說明 |
|------|------|
| **Worktree 名稱** | `ha-user-permission-fix` |
| **Worktree 相對路徑** | `../odoo-server.worktrees/ha-user-permission-fix` |
| **Addon 路徑** | `data/18/addons/odoo_ha_addon` |

**同步指令**：開發完成後需同步到 main 專案並重啟 Docker 才能進行 E2E 測試。

## Tasks Created

- [x] #60 - 調查與修復 ir.rule 權限問題 (parallel: false) ✅ Closed
- [x] #61 - 測試與驗證權限修復 (parallel: false, depends_on: #60) ✅ Closed

Total tasks: 2
Completed tasks: 2
Estimated total effort: 2.5 hours
