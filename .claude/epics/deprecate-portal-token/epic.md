---
name: deprecate-portal-token
status: backlog
created: 2026-01-17T18:24:32Z
updated: 2026-01-17T18:38:39Z
progress: 0%
prd: .claude/prds/deprecate-portal-token.md
github: https://github.com/WOOWTECH/odoo-addons/issues/54
---

# Epic: Portal Access Token 機制移除

## Overview

移除 `portal.mixin` 繼承和 token-based 分享機制（`action_share_portal()`），清理 model 層的 token 遺留程式碼。

**重要**：Portal 頁面保留給已登入用戶使用，Controller 已經是 user-based。

## 範圍澄清

### 要移除的（Token 機制）
- `portal.mixin` 繼承（ha_entity.py, ha_entity_group.py）
- `action_share_portal()` 方法
- "Share via Link" 按鈕
- `tests/test_portal_mixin.py` 測試

### 要保留的（User-based Portal）
- `controllers/portal.py` ✅
- `views/portal_templates.xml` ✅
- `static/src/portal/` ✅
- `/portal/entity/*` 和 `/my/ha/*` 路由 ✅
- `action_share()` 方法 ✅

## Technical Approach

這是一個小範圍的清理任務，主要修改 4 個檔案、刪除 1 個測試檔案。

### 修改檔案清單

| 檔案 | 修改內容 |
|------|---------|
| `models/ha_entity.py` | 移除 portal.mixin、action_share_portal() |
| `models/ha_entity_group.py` | 移除 portal.mixin、action_share_portal() |
| `views/ha_entity_views.xml` | 移除 Share via Link 按鈕 |
| `views/ha_entity_group_views.xml` | 移除 Share via Link 按鈕 |

### 刪除檔案

| 檔案 | 說明 |
|------|------|
| `tests/test_portal_mixin.py` | Token 機制測試 |

## Task Breakdown Preview

精簡為 3 個任務：

- [ ] **Task 1: 更新 Model 層** - 移除 portal.mixin 繼承和 action_share_portal() 方法
- [ ] **Task 2: 更新 View 層** - 移除 "Share via Link" 按鈕
- [ ] **Task 3: 清理測試與驗證** - 刪除 token 測試、驗證功能正常

## Dependencies

### 任務依賴關係
```
Task 1 (Model) + Task 2 (View) [可並行]
    ↓
Task 3 (驗證)
```

## Success Criteria

| 驗收項目 | 檢查方式 |
|---------|---------|
| portal.mixin 移除 | grep 無 portal.mixin 引用 |
| action_share_portal 移除 | grep 無 action_share_portal 引用 |
| Portal 頁面正常 | `/portal/entity/*` 可存取（需登入） |
| User-based sharing 正常 | `action_share()` 功能正常 |
| 測試通過 | Portal controller 測試通過 |

## Estimated Effort

| 項目 | 預估 |
|------|------|
| 總任務數 | 3 |
| 預估時間 | 30 分鐘 |
| 複雜度 | 低 |

## Tasks Created

- [ ] #55 - 更新 Model 層 (parallel: true)
- [ ] #56 - 更新 View 層 (parallel: true)
- [ ] #57 - 清理測試與驗證 (parallel: false, depends: #55, #56)

Total tasks: 3
Parallel tasks: 2 (#55, #56 可並行執行)
Sequential tasks: 1 (#57)
Estimated total effort: 0.5 hours
