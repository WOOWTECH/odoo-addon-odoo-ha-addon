---
created: 2026-01-01T15:23:16Z
last_updated: 2026-01-18T15:12:55Z
version: 1.5
author: Claude Code PM System
---

# Project Progress

## Current Status

### Branch
- **Current Branch:** `main`
- **Git Status:** Clean (no uncommitted changes)

### Recent Commits (Last 10)
| Hash | Message |
|------|---------|
| b0b3844 | docs: mark all PRDs as complete |
| 57536c5 | chore: archive completed epic share-wizard-ui-fix |
| e204d86 | Merge epic: share-wizard-ui-fix |
| 20bf620 | docs: mark share-wizard-ui-fix epic as completed |
| 5a098dd | fix: remove group wrapper from share wizard alert to fix UI layout |
| 7bbfc53 | docs: add PRD and epic for share-wizard-ui-fix |
| e2ef730 | docs: update context files after ha-user-permission-fix epic completion |
| fdd55ec | Merge pull request #62 from WOOWTECH:epic/ha-user-permission-fix |
| bd0f16f | docs: update security tests to reflect Odoo ORM cache behavior |
| 2106ddb | refactor: remove unnecessary ir.rule cache clearing from ha_entity_group |

## Completed Work

### Epic: share-wizard-ui-fix (100% Complete) - MERGED

修復 Entity Share Wizard 的已分享使用者提示訊息顯示為多行的 UI 問題。

**Completed Tasks:**
1. **#001 修改 XML** - 移除外層 group wrapper，將 invisible 屬性移到 div 上
2. **#002 E2E 驗證** - 使用 Playwright MCP 驗證 UI 修復

**Root Cause:**
- 外層 `<group>` 標籤導致 Odoo group 佈局系統介入，使 alert div 產生非預期分行

**Files Modified:**
- `views/ha_entity_share_wizard_views.xml` - 移除 group wrapper

**GitHub:** Epic 已合併

### Epic: ha-user-permission-fix (100% Complete) - MERGED

修復 ha_user 被加入 Entity Group 後無法存取 `ha.instance` 的 regression bug。

**Completed Tasks:**
1. **#60 調查與修復** - 確認 ir.rule 快取問題，使用 registry.clear_cache() 清除快取
2. **#61 測試與驗證** - 新增 test_security.py 測試權限變更立即生效

**Root Cause Analysis:**
- Odoo ORM 快取導致 ir.rule 權限變更未立即生效
- 使用 `registry.clear_cache()` 替代已棄用的 `clear_caches()`

**Files Modified:**
- `models/ha_entity.py` - 新增 user_ids 變更時清除快取
- `models/ha_entity_group.py` - 新增 user_ids 變更時清除快取

**Files Added:**
- `tests/test_security.py` - ir.rule 權限測試

**GitHub:** PR #62 已合併

### Epic: deprecate-portal-token (100% Complete) - MERGED

移除 `portal.mixin` 繼承和 token-based 分享機制，清理 model 層的 token 遺留程式碼。

**Completed Tasks:**
1. **#55 Model Layer** - 移除 portal.mixin、action_share_portal()
2. **#56 View Layer** - 移除 "Share via Link" 按鈕
3. **#57 Testing & Cleanup** - 刪除 test_portal_mixin.py、驗證功能正常

**Files Modified:**
- `models/ha_entity.py` - 移除 portal.mixin 繼承
- `models/ha_entity_group.py` - 移除 portal.mixin 繼承
- `views/ha_entity_views.xml` - 移除 Share via Link 按鈕
- `views/ha_entity_group_views.xml` - 移除 Share via Link 按鈕

**Files Deleted:**
- `tests/test_portal_mixin.py` - Token 機制測試

**GitHub:** PR #58 已合併

### Epic: user-based-entity-sharing (Active)

新增 User-based entity sharing 機制，替代 token-based 分享。

**New Features:**
- `models/ha_entity_share.py` - 分享記錄模型
- `wizard/ha_entity_share_wizard.py` - 分享精靈
- `tests/test_entity_share.py` - 分享測試
- `tests/test_share_wizard.py` - 精靈測試
- `tests/test_portal_my_ha.py` - Portal my/ha 測試

**GitHub:** PR #53 已合併

### Epic: share_entities (100% Complete) - ARCHIVED

Portal Access & External Token Sharing - 此 epic 已完成並歸檔。
後續由 deprecate-portal-token 移除 token 機制，保留 user-based portal。

**GitHub:** PR #9 已關閉（由後續 PR 取代）

### Archived Epics
- `share_entities` → `.claude/epics/.archived/share_entities/`
- `user-based-entity-sharing` → `.claude/epics/.archived/user-based-entity-sharing/`
- `deprecate-portal-token` → `.claude/epics/deprecate-portal-token/` (completed)
- `ha-user-permission-fix` → `.claude/epics/ha-user-permission-fix/` (completed)
- `share-wizard-ui-fix` → `.claude/epics/archived/share-wizard-ui-fix/` (completed)

### Active Epics
| Epic | Status | Progress |
|------|--------|----------|
| `portal-ui-redesign` | backlog | - |

## New Documentation Added

- `AGENTS.md` - Agent 使用說明
- `COMMANDS.md` - 命令參考
- `CONTEXT_ACCURACY.md` - Context 準確度說明
- `LOCAL_MODE.md` - 本地開發模式
- `README_CCPM.md` - CCPM 系統文件
- `docs/architecture/user-based-sharing.md` - User-based sharing 架構
- `docs/guides/i18n-development.md` - i18n 開發指南
- `docs/backlog-prd/ha-user-permission-fix.md` - HA 用戶權限修復 PRD
- `docs/backlog-prd/user-permission-ui-improvements.md` - UI 改進 PRD

## Testing Status
- Controller tests: `tests/test_controllers.py`
- Portal controller tests: `tests/test_portal_controller.py`
- Entity share tests: `tests/test_entity_share.py`
- Share wizard tests: `tests/test_share_wizard.py`
- Portal my/ha tests: `tests/test_portal_my_ha.py`
- Permission tests: `tests/test_share_permissions.py`
- Security tests: `tests/test_security.py` (NEW - ir.rule 權限測試)

## Immediate Next Steps

1. 考慮下一個 epic 從 backlog PRDs 中選擇
2. Portal UI Redesign epic 待啟動
3. User permission UI improvements PRD 待評估

## Blockers

- None currently identified

## Notes

- Project 現在使用 user-based sharing 替代 token-based sharing
- Portal 頁面需要登入才能存取
- Docker environment for Odoo 18 development
- WebSocket integration with Home Assistant for real-time updates
- 新增 CCPM 完整文件套件

## Update History
- 2026-01-18: share-wizard-ui-fix epic 已完成並合併，修復 Share Wizard alert UI 跑版問題
- 2026-01-18: ha-user-permission-fix epic 已完成並合併 (PR #62)
- 2026-01-18: 重大更新 - deprecate-portal-token 已合併，user-based-entity-sharing 已合併
- 2026-01-03: Added portal entity control (#10), translated portal templates to zh_TW
- 2026-01-02: Completed share_entities epic, created PR #9
